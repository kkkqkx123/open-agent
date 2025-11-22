"""提示词加载器实现

负责从文件系统加载提示词内容。
"""

from pathlib import Path
from typing import Dict, Optional
import asyncio
import logging

from ...interfaces.prompts import IPromptLoader, IPromptRegistry
from ...core.common.exceptions import PromptLoadError

logger = logging.getLogger(__name__)


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
        
    def load_prompt(self, category: str, name: str) -> str:
        """加载提示词内容
        
        Args:
            category: 提示词类别
            name: 提示词名称
            
        Returns:
            str: 提示词内容
            
        Raises:
            PromptLoadError: 加载失败
        """
        cache_key = f"{category}.{name}"
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        try:
            # 获取元信息
            meta = self.registry.get_prompt_meta(category, name)
            
            # 加载提示词
            if meta.is_composite:
                content = self.load_composite_prompt(meta.path)
            else:
                content = self.load_simple_prompt(meta.path)
                
            # 缓存结果
            self._cache[cache_key] = content
            return content
        except Exception as e:
            raise PromptLoadError(
                f"无法加载提示词 {category}.{name}: {e}"
            ) from e
        
    def load_simple_prompt(self, file_path: Path) -> str:
        """加载简单提示词
        
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
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
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
        
    def load_composite_prompt(self, dir_path: Path) -> str:
        """加载复合提示词
        
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
                
            content = self.load_simple_prompt(index_file)
            
            # 加载子章节文件
            chapter_files = []
            for file_path in dir_path.iterdir():
                if (file_path.is_file() and 
                    file_path.name.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'))):
                    chapter_files.append(file_path)
                    
            # 按文件名排序
            chapter_files.sort(key=lambda x: x.name)
            
            # 合并内容
            for chapter_file in chapter_files:
                if chapter_file.name != "index.md":  # 跳过已加载的主文件
                    chapter_content = self.load_simple_prompt(chapter_file)
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
    
    def load_prompts(self, category: str) -> dict:
        """加载指定类别的所有提示词
        
        Args:
            category: 提示词类别
            
        Returns:
            dict: 提示词字典，键为提示词名称，值为提示词内容
        """
        try:
            # 获取该类别下所有提示词的元数据
            prompts = {}
            
            # 尝试从注册表获取该类别的所有提示词
            if hasattr(self.registry, 'list_by_category'):
                # 使用异步方法在同步上下文中运行
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果事件循环正在运行，创建新的任务
                        task = asyncio.create_task(self.registry.list_by_category(category))
                        # 这里需要特殊处理，因为不能在运行中的循环中直接运行
                        logger.warning(f"无法在运行中的事件循环中同步获取类别 {category} 的提示词列表")
                        return prompts
                    else:
                        prompt_metas = loop.run_until_complete(self.registry.list_by_category(category))
                except RuntimeError:
                    # 没有事件循环，创建新的
                    prompt_metas = asyncio.run(self.registry.list_by_category(category))
            else:
                logger.warning(f"注册表不支持按类别列出提示词，无法加载类别 {category}")
                return prompts
            
            # 加载每个提示词的内容
            for prompt_meta in prompt_metas:
                try:
                    content = self.load_prompt(category, prompt_meta.name)
                    prompts[prompt_meta.name] = content
                except Exception as e:
                    logger.error(f"加载提示词 {category}.{prompt_meta.name} 失败: {e}")
                    continue
            
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
            
            # 扫描类别目录中的所有文件
            for prompt_file in category_dir.glob("**/*.md"):
                if prompt_file.name.startswith('_'):
                    continue
                
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
                    from ....interfaces.prompts.models import (
                        PromptMeta, PromptType, PromptStatus, PromptPriority
                    )
                    
                    # 根据类别确定提示词类型
                    if category == 'system':
                        prompt_type = PromptType.SYSTEM
                    elif category == 'user_commands':
                        prompt_type = PromptType.USER
                    elif category == 'rules':
                        prompt_type = PromptType.RULE if hasattr(PromptType, 'RULE') else PromptType.SYSTEM
                    else:
                        prompt_type = PromptType.USER
                    
                    prompt_meta = PromptMeta(
                        id=prompt_id,
                        name=prompt_name,
                        description=frontmatter.get('description', f'{category}类别提示词: {prompt_name}'),
                        type=prompt_type,
                        content=prompt_content,
                        status=PromptStatus.ACTIVE,
                        priority=PromptPriority.NORMAL,
                        category=category,
                        tags=frontmatter.get('tags', []),
                        metadata={
                            'file_path': str(prompt_file),
                            'relative_path': str(relative_path),
                            **{k: v for k, v in frontmatter.items() if k not in ['description', 'tags']}
                        }
                    )
                    
                    # 注册到注册表
                    await registry.register(prompt_meta)
                    logger.debug(f"注册提示词: {prompt_id}")
                    
                except Exception as e:
                    logger.error(f"加载提示词文件失败 {prompt_file}: {e}")
                    continue
        
        logger.info("提示词扫描和注册完成")
    
    def clear_cache(self) -> None:
        """清空缓存
        
        清空所有已加载的提示词缓存。
        """
        self._cache.clear()
