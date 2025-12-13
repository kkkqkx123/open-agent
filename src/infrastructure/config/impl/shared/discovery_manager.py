"""配置发现管理器实现（重构版）

提供基础的文件系统操作功能，不包含业务逻辑。
这是基础设施层的实现，只依赖于接口层。
"""

from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import logging
import os
import yaml
from datetime import datetime

from src.interfaces.config.loader import IConfigLoader

logger = logging.getLogger(__name__)


class FileSystemHelper:
    """文件系统辅助器
    
    提供基础的文件系统操作功能，不包含业务逻辑。
    """
    
    def __init__(self, base_path: str = "configs"):
        """初始化文件系统辅助器
        
        Args:
            base_path: 基础配置路径
        """
        self.base_path = Path(base_path)
        logger.debug(f"初始化文件系统辅助器，基础路径: {base_path}")
    
    def validate_config_path(self, config_path: str) -> bool:
        """验证配置文件路径是否有效
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            是否有效
        """
        try:
            path = Path(config_path)
            
            # 检查文件是否存在
            if not path.exists():
                return False
            
            # 检查是否为文件
            if not path.is_file():
                return False
            
            # 检查文件扩展名
            if path.suffix.lower() not in ['.yaml', '.yml']:
                return False
            
            # 检查文件是否可读
            if not os.access(path, os.R_OK):
                return False
            
            # 尝试解析文件
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                return True
            except Exception:
                return False
                
        except Exception as e:
            logger.error(f"验证配置路径失败 {config_path}: {e}")
            return False
    
    def get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """获取文件统计信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件统计信息
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    "path": file_path,
                    "exists": False,
                    "error": "文件不存在"
                }
            
            stat = path.stat()
            return {
                "path": str(path),
                "name": path.name,
                "stem": path.stem,
                "suffix": path.suffix,
                "exists": True,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_readable": os.access(path, os.R_OK),
                "is_file": path.is_file(),
                "is_dir": path.is_dir()
            }
            
        except Exception as e:
            logger.error(f"获取文件统计信息失败 {file_path}: {e}")
            return {
                "path": file_path,
                "exists": False,
                "error": str(e)
            }
    
    def find_files_by_pattern(self, search_path: str, pattern: str, extensions: Optional[List[str]] = None) -> List[str]:
        """根据模式查找文件
        
        Args:
            search_path: 搜索路径
            pattern: 文件模式（支持通配符）
            extensions: 文件扩展名列表
            
        Returns:
            匹配的文件路径列表
        """
        try:
            path = Path(search_path)
            
            if not path.exists():
                logger.warning(f"搜索路径不存在: {search_path}")
                return []
            
            files = []
            extensions = extensions or ['.yaml', '.yml']
            
            # 搜索匹配的文件
            for ext in extensions:
                for file_path in path.rglob(f"{pattern}{ext}"):
                    if file_path.is_file():
                        files.append(str(file_path))
            
            # 排序并返回
            files.sort()
            logger.debug(f"在 {search_path} 中找到 {len(files)} 个匹配文件，模式: {pattern}")
            
            return files
            
        except Exception as e:
            logger.error(f"查找文件失败: {e}")
            return []
    
    def get_last_modified(self, file_path: str) -> Optional[datetime]:
        """获取文件最后修改时间
        
        Args:
            file_path: 文件路径
            
        Returns:
            最后修改时间，如果文件不存在则返回None
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return None
            
            stat = path.stat()
            return datetime.fromtimestamp(stat.st_mtime)
            
        except Exception as e:
            logger.error(f"获取最后修改时间失败 {file_path}: {e}")
            return None


class DiscoveryManager:
    """配置发现管理器（重构版）
    
    提供基础的配置发现功能，不包含业务逻辑。
    业务逻辑已移至Core层的ConfigDiscoveryService。
    """
    
    def __init__(self, config_loader: Optional[IConfigLoader] = None, base_path: str = "configs"):
        """初始化发现管理器
        
        Args:
            config_loader: 配置加载器
            base_path: 基础配置路径
        """
        self.config_loader = config_loader
        self.base_path = Path(base_path)
        self.fs_helper = FileSystemHelper(base_path)
        self._watchers: Dict[str, Callable] = {}
        
        logger.debug(f"初始化配置发现管理器，基础路径: {base_path}")
    
    def validate_config_path(self, config_path: str) -> bool:
        """验证配置文件路径是否有效
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            是否有效
        """
        return self.fs_helper.validate_config_path(config_path)
    
    def get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """获取文件统计信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件统计信息
        """
        return self.fs_helper.get_file_stats(file_path)
    
    def find_config_files(self, pattern: str = "*", base_path: Optional[str] = None) -> List[str]:
        """查找配置文件
        
        Args:
            pattern: 文件模式（支持通配符）
            base_path: 基础路径，如果为None则使用默认路径
            
        Returns:
            配置文件路径列表
        """
        search_path = base_path or str(self.base_path)
        return self.fs_helper.find_files_by_pattern(search_path, pattern)
    
    def discover_module_configs(self, module_type: str, pattern: str = "*") -> List[str]:
        """发现模块特定配置文件
        
        Args:
            module_type: 模块类型
            pattern: 文件模式（支持通配符）
            
        Returns:
            配置文件路径列表
        """
        try:
            module_path = self.base_path / module_type
            
            if not module_path.exists():
                logger.debug(f"模块配置路径不存在: {module_path}")
                return []
            
            return self.fs_helper.find_files_by_pattern(str(module_path), pattern)
            
        except Exception as e:
            logger.error(f"发现模块配置文件失败 {module_type}: {e}")
            return []
    
    def get_config_info(self, config_path: str) -> Dict[str, Any]:
        """获取配置文件信息
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置文件信息
        """
        try:
            path = Path(config_path)
            
            if not path.exists():
                return {
                    "path": config_path,
                    "exists": False,
                    "error": "文件不存在"
                }
            
            # 基本文件信息
            stat = path.stat()
            info = {
                "path": str(path),
                "name": path.name,
                "stem": path.stem,
                "suffix": path.suffix,
                "exists": True,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_readable": os.access(path, os.R_OK)
            }
            
            # 尝试解析配置内容
            if info["is_readable"] and path.suffix.lower() in ['.yaml', '.yml']:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = yaml.safe_load(f)
                    
                    if content:
                        info["content_type"] = type(content).__name__
                        info["keys"] = list(content.keys()) if isinstance(content, dict) else []
                        
                        # 检查继承关系
                        if isinstance(content, dict) and "_inherit_" in content:
                            info["inheritance"] = content["_inherit_"]
                        
                except Exception as e:
                    info["parse_error"] = str(e)
            
            return info
            
        except Exception as e:
            logger.error(f"获取配置信息失败 {config_path}: {e}")
            return {
                "path": config_path,
                "exists": False,
                "error": str(e)
            }
    
    def get_last_modified(self, config_path: str) -> Optional[datetime]:
        """获取配置文件最后修改时间
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            最后修改时间，如果文件不存在则返回None
        """
        return self.fs_helper.get_last_modified(config_path)
    
    def watch_config_changes(self, config_path: str, callback: Callable) -> None:
        """监听配置文件变化
        
        Args:
            config_path: 配置文件路径
            callback: 变化回调函数
        """
        # 简单实现：存储回调函数
        # 实际的文件监听需要更复杂的实现（如watchdog库）
        self._watchers[config_path] = callback
        logger.debug(f"注册配置文件监听: {config_path}")
    
    def stop_watching(self, config_path: str) -> None:
        """停止监听配置文件变化
        
        Args:
            config_path: 配置文件路径
        """
        if config_path in self._watchers:
            del self._watchers[config_path]
            logger.debug(f"停止监听配置文件: {config_path}")
    
    def get_watched_files(self) -> List[str]:
        """获取正在监听的文件列表
        
        Returns:
            正在监听的文件路径列表
        """
        return list(self._watchers.keys())
    
    def trigger_file_change_callback(self, config_path: str, change_type: str = "modified") -> None:
        """触发文件变化回调（用于测试）
        
        Args:
            config_path: 配置文件路径
            change_type: 变化类型
        """
        if config_path in self._watchers:
            try:
                callback = self._watchers[config_path]
                callback(config_path, {"type": change_type, "timestamp": datetime.now().isoformat()})
                logger.debug(f"触发文件变化回调: {config_path}")
            except Exception as e:
                logger.error(f"执行文件变化回调失败 {config_path}: {e}")