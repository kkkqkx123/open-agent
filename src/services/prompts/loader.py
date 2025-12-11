"""提示词加载器实现

负责从文件系统加载提示词内容。
"""

from pathlib import Path
from typing import Dict, Optional, List
import asyncio
from src.interfaces.dependency_injection import get_logger
import yaml

from ...interfaces import IPromptLoader, IPromptRegistry
from src.interfaces.prompts.exceptions import PromptLoadError

logger = get_logger(__name__)


class PromptLoader(IPromptLoader):
    """提示词加载器实现
    
    负责加载提示词文件内容，支持简单和复合提示词。
    """
    
    def __init__(self, registry: IPromptRegistry) -> None:
        """初始化提示词加载器
        
        Args:
            registry: 提示词注册表实例
        """
        self.registry = registry
        self._cache: Dict[str, str] = {}
        
    async def load_simple_prompt_async(self, file_path: Path) -> str:
        """异步加载简单提示词
        
        从单个文件加载提示词，支持YAML frontmatter。
        
        Args:
            file_path: 提示词文件路径
            
        Returns:
            str: 提示词内容
            
        Raises:
            PromptLoadError: 文件不存在或读取失败
        """
        if not file_path.exists():
            raise PromptLoadError(f"提示词文件不存在: {file_path}")
            
        try:
            # 使用 aiofiles 进行异步文件读取
            import aiofiles
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                content = content.strip()
                
            # 移除元信息部分（如果有）
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2].strip()
                    
            return content
        except Exception as e:
            raise PromptLoadError(
                f"读取提示词文件失败 {file_path}: {e}"
            ) from e
        
    async def load_composite_prompt_async(self, dir_path: Path) -> str:
        """异步加载复合提示词
        
        从目录加载复合提示词。加载顺序：
        1. index.md（如果存在）
        2. 按文件名排序的其他文件
        
        Args:
            dir_path: 提示词目录路径
            
        Returns:
            str: 合并后的提示词内容
            
        Raises:
            PromptLoadError: 目录不存在或文件读取失败
        """
        if not dir_path.exists():
            raise PromptLoadError(f"复合提示词目录不存在: {dir_path}")
            
        try:
            # 加载主文件
            index_file = dir_path / "index.md"
            if not index_file.exists():
                raise PromptLoadError(
                    f"复合提示词缺少index.md: {dir_path}"
                )
                
            content = await self.load_simple_prompt_async(index_file)
            
            # 加载子章节文件
            chapter_files = []
            for file_path in dir_path.iterdir():
                if (file_path.is_file() and
                    file_path.name.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'))):
                    chapter_files.append(file_path)
                    
            # 按文件名排序
            chapter_files.sort(key=lambda x: x.name)
            
            # 并发加载子章节文件
            chapter_tasks = []
            for chapter_file in chapter_files:
                if chapter_file.name != "index.md":  # 跳过已加载的主文件
                    chapter_tasks.append(self.load_simple_prompt_async(chapter_file))
            
            chapter_contents = await asyncio.gather(*chapter_tasks)
            
            # 合并内容
            for chapter_content in chapter_contents:
                content += f"\n\n---\n\n{chapter_content}"
                    
            return content
        except PromptLoadError:
            raise
        except Exception as e:
            raise PromptLoadError(
                f"加载复合提示词失败 {dir_path}: {e}"
            ) from e
        
    async def load_prompt_async(self, category: str, name: str) -> str:
        """异步加载提示词内容
        
        Args:
            category: 提示词类别
            name: 提示词名称
            
        Returns:
            str: 提示词内容
            
        Raises:
            PromptLoadError: 加载失败
        """
        # 在线程池中执行同步加载
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self.load_prompt, category, name)
        except Exception as e:
            raise PromptLoadError(
                f"异步加载提示词 {category}.{name} 失败: {e}"
            ) from e
    
    def load_prompt(self, category: str, name: str) -> str:
        """同步加载提示词内容
        
        Args:
            category: 提示词类别
            name: 提示词名称
            
        Returns:
            str: 提示词内容
            
        Raises:
            PromptLoadError: 加载失败
        """
        try:
            # 获取提示词元数据
            prompt_meta = self.registry.get_prompt_meta(category, name)
            if prompt_meta is None:
                raise PromptLoadError(f"提示词不存在: {category}.{name}")
            
            # 从缓存检查
            cache_key = f"{category}.{name}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            # 返回提示词内容
            content = prompt_meta.content
            self._cache[cache_key] = content
            return content
        except PromptLoadError:
            raise
        except Exception as e:
            raise PromptLoadError(
                f"加载提示词 {category}.{name} 失败: {e}"
            ) from e
    
    async def load_prompts_async(self, category: str) -> Dict[str, str]:
        """异步加载指定类别的所有提示词
        
        Args:
            category: 提示词类别
            
        Returns:
            dict: 提示词字典，键为提示词名称，值为提示词内容
        """
        try:
            # 获取该类别下所有提示词的元数据
            prompts: Dict[str, str] = {}
            
            # 从注册表获取该类别的所有提示词
            prompt_metas = await self.registry.list_by_category(category)
            
            # 并发加载每个提示词的内容
            load_tasks = []
            prompt_names = []
            for prompt_meta in prompt_metas:
                load_tasks.append(self.load_prompt_async(category, prompt_meta.name))
                prompt_names.append(prompt_meta.name)
            
            # 等待所有加载完成
            contents = await asyncio.gather(*load_tasks, return_exceptions=True)
            
            # 处理结果
            for i, content in enumerate(contents):
                if isinstance(content, Exception):
                    logger.error(f"加载提示词 {category}.{prompt_names[i]} 失败: {content}")
                else:
                    prompts[prompt_names[i]] = content  # type: ignore
            
            return prompts
            
        except Exception as e:
            logger.error(f"加载类别 {category} 的提示词失败: {e}")
            return {}
    
    async def load_all(self, registry: IPromptRegistry) -> None:
        """从文件系统加载所有提示词并注册到注册表
        
        Args:
            registry: 提示词注册表
        """
        from pathlib import Path
        import yaml
        import re
        
        # 默认扫描 configs/prompts 目录
        prompts_dir = Path("configs/prompts")
        if not prompts_dir.exists():
            logger.warning(f"提示词目录不存在: {prompts_dir}")
            return
        
        logger.info(f"开始扫描提示词目录: {prompts_dir}")
        
        # 扫描各个类别目录
        for category_dir in prompts_dir.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith('_'):
                continue
            
            category = category_dir.name
            logger.info(f"扫描类别: {category}")
            
            # 扫描类别目录中的所有文件和目录
            for item in category_dir.iterdir():
                if item.name.startswith('_'):
                    continue
                
                if item.is_file() and item.suffix == '.md':
                    # 处理简单提示词文件
                    await self._process_simple_prompt(item, category, category_dir, registry)
                elif item.is_dir():
                    # 检查是否为复合提示词目录（包含 index.md）
                    index_file = item / 'index.md'
                    if index_file.exists():
                        # 处理复合提示词目录
                        await self._process_composite_prompt(item, category, category_dir, registry)
                    else:
                        # 递归扫描子目录中的文件
                        for prompt_file in item.glob("**/*.md"):
                            if prompt_file.name.startswith('_'):
                                continue
                            await self._process_simple_prompt(prompt_file, category, category_dir, registry)
        
        logger.info("提示词扫描和注册完成")
    
    async def _process_simple_prompt(self, prompt_file: Path, category: str, category_dir: Path, registry: "IPromptRegistry") -> None:
        """处理简单提示词文件
        
        Args:
            prompt_file: 提示词文件路径
            category: 提示词类别
            category_dir: 类别目录路径
            registry: 提示词注册表
        """
        try:
            # 读取文件内容
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析 frontmatter
            frontmatter = {}
            prompt_content = content
            
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1])
                        prompt_content = parts[2].strip()
                    except yaml.YAMLError as e:
                        logger.warning(f"解析 frontmatter 失败 {prompt_file}: {e}")
            
            # 生成提示词ID和名称
            relative_path = prompt_file.relative_to(category_dir)
            prompt_id = f"{category}.{relative_path.stem}"
            prompt_name = relative_path.stem
            
            # 创建提示词元数据
            from ...interfaces.prompts.models import (
                PromptMeta, PromptType, PromptStatus, PromptPriority
            )
            
            # 根据类别确定提示词类型
            if category == 'system':
                prompt_type = PromptType.SYSTEM
            elif category == 'user_commands':
                prompt_type = PromptType.USER_COMMAND
            elif category == 'rules':
                prompt_type = PromptType.RULES
            elif category == 'context':
                prompt_type = PromptType.CONTEXT
            elif category == 'examples':
                prompt_type = PromptType.EXAMPLES
            elif category == 'constraints':
                prompt_type = PromptType.CONSTRAINTS
            elif category == 'format':
                prompt_type = PromptType.FORMAT
            else:
                prompt_type = PromptType.CUSTOM
            
            prompt_meta = PromptMeta(
                id=prompt_id,
                name=prompt_name,
                description=frontmatter.get('description', f'{category}类别提示词: {prompt_name}'),
                type=prompt_type,
                content=prompt_content,
                template=None,
                status=PromptStatus.ACTIVE,
                priority=PromptPriority.NORMAL,
                category=category,
                tags=frontmatter.get('tags', []),
                created_by='system',
                updated_by='system',
                validation=None,
                cache_ttl=3600,
                metadata={
                    'file_path': str(prompt_file),
                    'relative_path': str(relative_path),
                    'is_composite': False,
                    **{k: v for k, v in frontmatter.items() if k not in ['description', 'tags']}
                }
            )
            
            # 注册到注册表
            await registry.register(prompt_meta)
            logger.debug(f"注册简单提示词: {prompt_id}")
            
        except Exception as e:
            logger.error(f"处理简单提示词文件失败 {prompt_file}: {e}")
    
    async def _process_composite_prompt(self, prompt_dir: Path, category: str, category_dir: Path, registry: "IPromptRegistry") -> None:
        """处理复合提示词目录
        
        Args:
            prompt_dir: 提示词目录路径
            category: 提示词类别
            category_dir: 类别目录路径
            registry: 提示词注册表
        """
        try:
            # 使用现有的复合提示词加载逻辑
            content = await self.load_composite_prompt_async(prompt_dir)
            
            # 读取 index.md 的 frontmatter
            index_file = prompt_dir / 'index.md'
            frontmatter = {}
            
            with open(index_file, 'r', encoding='utf-8') as f:
                index_content = f.read()
                
            if index_content.startswith('---'):
                parts = index_content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1])
                    except yaml.YAMLError as e:
                        logger.warning(f"解析 frontmatter 失败 {index_file}: {e}")
            
            # 生成提示词ID和名称
            relative_path = prompt_dir.relative_to(category_dir)
            prompt_id = f"{category}.{relative_path.stem}"
            prompt_name = relative_path.stem
            
            # 创建提示词元数据
            from ...interfaces.prompts.models import (
                PromptMeta, PromptType, PromptStatus, PromptPriority
            )
            
            # 根据类别确定提示词类型
            if category == 'system':
                prompt_type = PromptType.SYSTEM
            elif category == 'user_commands':
                prompt_type = PromptType.USER_COMMAND
            elif category == 'rules':
                prompt_type = PromptType.RULES
            elif category == 'context':
                prompt_type = PromptType.CONTEXT
            elif category == 'examples':
                prompt_type = PromptType.EXAMPLES
            elif category == 'constraints':
                prompt_type = PromptType.CONSTRAINTS
            elif category == 'format':
                prompt_type = PromptType.FORMAT
            else:
                prompt_type = PromptType.CUSTOM
            
            prompt_meta = PromptMeta(
                id=prompt_id,
                name=prompt_name,
                description=frontmatter.get('description', f'{category}类别复合提示词: {prompt_name}'),
                type=prompt_type,
                content=content,
                template=None,
                status=PromptStatus.ACTIVE,
                priority=PromptPriority.NORMAL,
                category=category,
                tags=frontmatter.get('tags', []),
                created_by='system',
                updated_by='system',
                validation=None,
                cache_ttl=3600,
                metadata={
                    'file_path': str(prompt_dir),
                    'relative_path': str(relative_path),
                    'is_composite': True,
                    'sub_files': [f.name for f in prompt_dir.iterdir() if f.is_file() and f.suffix == '.md'],
                    **{k: v for k, v in frontmatter.items() if k not in ['description', 'tags']}
                }
            )
            
            # 注册到注册表
            await registry.register(prompt_meta)
            logger.debug(f"注册复合提示词: {prompt_id}")
            
        except Exception as e:
            logger.error(f"处理复合提示词目录失败 {prompt_dir}: {e}")
    
    def clear_cache(self) -> None:
        """清空缓存
        
        清空所有已加载的提示词缓存。
        """
        self._cache.clear()
    
    async def list_prompts_async(self, category: Optional[str] = None) -> List[str]:
        """异步列出提示词
        
        Args:
            category: 提示词类别，如果为None则列出所有提示词名称
            
        Returns:
            list: 提示词名称列表
        """
        prompts: List[str] = []
        if category:
            # 列出指定类别的提示词
            try:
                prompt_metas = await self.registry.list_by_category(category)
                prompts = [meta.name for meta in prompt_metas]
            except Exception as e:
                logger.error(f"列出类别 {category} 的提示词失败: {e}")
        
        return prompts
    
    def list_prompts(self, category: Optional[str] = None) -> List[str]:
        """同步列出提示词
        
        Args:
            category: 提示词类别，如果为None则列出所有提示词名称
            
        Returns:
            list: 提示词名称列表
        """
        # 注意：这是同步实现，依赖于registry的同步方法
        # 如果registry没有同步方法，可能需要异步转同步的转换
        # 为了简单起见，这里返回空列表或使用缓存内容
        prompts: List[str] = []
        
        if category:
            try:
                # 尝试从缓存的键中提取该类别的提示词
                prompts = [
                    key.split('.', 1)[1]
                    for key in self._cache.keys()
                    if key.startswith(f"{category}.")
                ]
            except Exception as e:
                logger.error(f"列出类别 {category} 的提示词失败: {e}")
        
        return prompts
    
    def exists(self, category: str, name: str) -> bool:
        """检查提示词是否存在
        
        Args:
            category: 提示词类别
            name: 提示词名称
            
        Returns:
            bool: 提示词是否存在
        """
        try:
            self.registry.get_prompt_meta(category, name)
            return True
        except Exception:
            return False
