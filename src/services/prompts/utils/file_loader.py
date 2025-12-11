"""文件加载器工具类

提供文件加载和内容处理的工具方法。
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


class FileLoader:
    """文件加载器工具类
    
    支持加载各种格式的提示词文件：
    1. Markdown (.md)
    2. 文本 (.txt)
    3. YAML (.yaml, .yml)
    4. JSON (.json)
    """
    
    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = {
        '.md': 'markdown',
        '.txt': 'text',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json'
    }
    
    # 前置内容模式
    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n',
        re.DOTALL
    )
    
    def __init__(self, base_directory: Optional[str] = None):
        """初始化文件加载器
        
        Args:
            base_directory: 基础目录路径
        """
        self.base_directory = Path(base_directory) if base_directory else Path.cwd()
        logger.debug(f"文件加载器初始化，基础目录: {self.base_directory}")
    
    def load_file(self, file_path: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """加载文件内容
        
        Args:
            file_path: 文件路径（相对或绝对）
            context: 上下文变量，用于处理模板
            
        Returns:
            文件内容，如果加载失败则返回None
        """
        try:
            # 构建完整路径
            full_path = self._resolve_path(file_path)
            
            # 检查文件是否存在
            if not full_path.exists():
                logger.warning(f"文件不存在: {full_path}")
                return None
            
            # 检查文件类型
            file_type = self._get_file_type(full_path)
            if not file_type:
                logger.warning(f"不支持的文件类型: {full_path.suffix}")
                return None
            
            # 读取文件内容
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 处理前置内容
            content = self._process_frontmatter(content)
            
            # 处理模板变量
            if context:
                from .template_renderer import TemplateRenderer
                content = TemplateRenderer.render_template(content, context)
            
            logger.debug(f"文件加载成功: {full_path}")
            return content
            
        except Exception as e:
            logger.error(f"加载文件失败: {file_path}, 错误: {e}")
            return None
    
    def load_file_with_metadata(self, file_path: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """加载文件内容并提取元数据
        
        Args:
            file_path: 文件路径
            context: 上下文变量
            
        Returns:
            包含内容和元数据的字典
        """
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return None
            
            # 读取原始内容
            with open(full_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # 提取前置内容
            frontmatter, content = self._extract_frontmatter(raw_content)
            
            # 处理模板变量
            if context:
                from .template_renderer import TemplateRenderer
                content = TemplateRenderer.render_template(content, context)
            
            # 构建结果
            result = {
                "content": content,
                "metadata": frontmatter or {},
                "file_path": str(full_path),
                "file_type": self._get_file_type(full_path),
                "file_size": len(raw_content),
                "last_modified": full_path.stat().st_mtime
            }
            
            return result
            
        except Exception as e:
            logger.error(f"加载文件元数据失败: {file_path}, 错误: {e}")
            return None
    
    def list_files(self, directory: str, pattern: str = "*", recursive: bool = True) -> List[str]:
        """列出目录中的文件
        
        Args:
            directory: 目录路径
            pattern: 文件名模式
            recursive: 是否递归搜索
            
        Returns:
            文件路径列表
        """
        try:
            dir_path = self._resolve_path(directory)
            
            if not dir_path.exists() or not dir_path.is_dir():
                logger.warning(f"目录不存在或不是目录: {dir_path}")
                return []
            
            files = []
            
            if recursive:
                # 递归搜索
                for file_path in dir_path.rglob(pattern):
                    if file_path.is_file() and self._is_supported_file(file_path):
                        relative_path = file_path.relative_to(self.base_directory)
                        files.append(str(relative_path))
            else:
                # 非递归搜索
                for file_path in dir_path.glob(pattern):
                    if file_path.is_file() and self._is_supported_file(file_path):
                        relative_path = file_path.relative_to(self.base_directory)
                        files.append(str(relative_path))
            
            return sorted(files)
            
        except Exception as e:
            logger.error(f"列出文件失败: {directory}, 错误: {e}")
            return []
    
    def validate_file_path(self, file_path: str) -> List[str]:
        """验证文件路径
        
        Args:
            file_path: 文件路径
            
        Returns:
            验证错误列表
        """
        errors = []
        
        try:
            # 检查路径是否为空
            if not file_path or not file_path.strip():
                errors.append("文件路径不能为空")
                return errors
            
            # 构建完整路径
            full_path = self._resolve_path(file_path)
            
            # 检查文件是否存在
            if not full_path.exists():
                errors.append(f"文件不存在: {full_path}")
                return errors
            
            # 检查是否为文件
            if not full_path.is_file():
                errors.append(f"路径不是文件: {full_path}")
                return errors
            
            # 检查文件类型
            file_type = self._get_file_type(full_path)
            if not file_type:
                errors.append(f"不支持的文件类型: {full_path.suffix}")
            
            # 检查文件大小
            file_size = full_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB
                errors.append(f"文件过大: {file_size} 字节")
            
        except Exception as e:
            errors.append(f"验证文件路径时发生错误: {e}")
        
        return errors
    
    def _resolve_path(self, file_path: str) -> Path:
        """解析文件路径"""
        if os.path.isabs(file_path):
            return Path(file_path)
        else:
            return self.base_directory / file_path
    
    def _get_file_type(self, file_path: Path) -> Optional[str]:
        """获取文件类型"""
        suffix = file_path.suffix.lower()
        return self.SUPPORTED_EXTENSIONS.get(suffix)
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """检查是否为支持的文件类型"""
        return self._get_file_type(file_path) is not None
    
    def _process_frontmatter(self, content: str) -> str:
        """处理前置内容"""
        match = self.FRONTMATTER_PATTERN.match(content)
        if match:
            # 移除前置内容，只保留正文
            return content[match.end():]
        return content
    
    def _extract_frontmatter(self, content: str) -> tuple[Optional[Dict[str, Any]], str]:
        """提取前置内容
        
        Returns:
            (前置内容字典, 正文内容)
        """
        match = self.FRONTMATTER_PATTERN.match(content)
        if match:
            try:
                import yaml
                frontmatter = yaml.safe_load(match.group(1))
                body_content = content[match.end():]
                return frontmatter, body_content
            except Exception as e:
                logger.warning(f"解析前置内容失败: {e}")
                return None, content
        
        return None, content
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                return None
            
            stat = full_path.stat()
            
            return {
                "path": str(full_path),
                "name": full_path.name,
                "stem": full_path.stem,
                "suffix": full_path.suffix,
                "type": self._get_file_type(full_path),
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "is_readable": os.access(full_path, os.R_OK)
            }
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {file_path}, 错误: {e}")
            return None
    
    def search_files(self, directory: str, search_term: str, file_pattern: str = "*") -> List[Dict[str, Any]]:
        """搜索包含特定内容的文件
        
        Args:
            directory: 搜索目录
            search_term: 搜索词
            file_pattern: 文件模式
            
        Returns:
            匹配的文件信息列表
        """
        try:
            files = self.list_files(directory, file_pattern, recursive=True)
            matches = []
            
            for file_path in files:
                content = self.load_file(file_path)
                if content and search_term.lower() in content.lower():
                    file_info = self.get_file_info(file_path)
                    if file_info:
                        # 查找匹配的行
                        lines = content.split('\n')
                        matched_lines = []
                        for i, line in enumerate(lines, 1):
                            if search_term.lower() in line.lower():
                                matched_lines.append({
                                    "line_number": i,
                                    "content": line.strip()
                                })
                        
                        file_info["matched_lines"] = matched_lines
                        matches.append(file_info)
            
            return matches
            
        except Exception as e:
            logger.error(f"搜索文件失败: {directory}, 错误: {e}")
            return []
    
    def create_file_backup(self, file_path: str, backup_suffix: str = ".backup") -> bool:
        """创建文件备份
        
        Args:
            file_path: 文件路径
            backup_suffix: 备份文件后缀
            
        Returns:
            是否创建成功
        """
        try:
            full_path = self._resolve_path(file_path)
            
            if not full_path.exists():
                logger.warning(f"文件不存在，无法创建备份: {full_path}")
                return False
            
            backup_path = full_path.with_suffix(full_path.suffix + backup_suffix)
            
            # 复制文件
            import shutil
            shutil.copy2(full_path, backup_path)
            
            logger.info(f"文件备份创建成功: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"创建文件备份失败: {file_path}, 错误: {e}")
            return False