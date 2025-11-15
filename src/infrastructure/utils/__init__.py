"""基础设施工具模块

提供通用的工具类，可被多个模块使用。
"""

from .env_resolver import EnvResolver
from .redactor import Redactor
from .file_watcher import FileWatcher
from .cache import Cache
from .dict_merger import DictMerger
from .validator import Validator
from .backup_manager import BackupManager

__all__ = [
    "EnvResolver",
    "Redactor",
    "FileWatcher",
    "Cache",
    "DictMerger",
    "Validator",
    "BackupManager",
    "UtilsFactory",
]


class UtilsFactory:
    """工具工厂
    
    提供创建各种工具实例的便捷方法。
    """
    
    @staticmethod
    def create_env_resolver(prefix: str = "") -> EnvResolver:
        """创建环境变量解析器
        
        Args:
            prefix: 环境变量前缀
            
        Returns:
            环境变量解析器实例
        """
        return EnvResolver(prefix)
    
    @staticmethod
    def create_dict_merger() -> DictMerger:
        """创建字典合并器
        
        Returns:
            字典合并器实例
        """
        return DictMerger()
    
    @staticmethod
    def create_redactor(patterns=None, replacement: str = "***") -> Redactor:
        """创建敏感信息脱敏器
        
        Args:
            patterns: 敏感信息模式列表
            replacement: 替换字符串
            
        Returns:
            敏感信息脱敏器实例
        """
        return Redactor(patterns, replacement)
    
    @staticmethod
    def create_file_watcher(watch_path: str, patterns=None) -> FileWatcher:
        """创建文件监听器
        
        Args:
            watch_path: 监听路径
            patterns: 文件模式列表
            
        Returns:
            文件监听器实例
        """
        return FileWatcher(watch_path, patterns)
    
    @staticmethod
    def create_validator() -> Validator:
        """创建数据验证器
        
        Returns:
            数据验证器实例
        """
        return Validator()
    
    @staticmethod
    def create_cache() -> Cache:
        """创建缓存
        
        Returns:
            缓存实例
        """
        return Cache()
    
    @staticmethod
    def create_backup_manager(backup_dir: str = "backups", max_backups: int = 10) -> BackupManager:
        """创建备份管理器
        
        Args:
            backup_dir: 备份目录
            max_backups: 最大备份数量
            
        Returns:
            备份管理器实例
        """
        return BackupManager(backup_dir, max_backups)