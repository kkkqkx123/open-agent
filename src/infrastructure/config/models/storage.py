"""存储配置数据模型

提供基础设施层的存储配置数据结构，不包含业务逻辑。
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from .base import ConfigData


class StorageType(str, Enum):
    """存储类型枚举"""
    MEMORY = "memory"
    SQLITE = "sqlite"
    FILE = "file"


class StorageConfigData(ConfigData):
    """存储配置数据
    
    纯数据容器，用于存储配置的基础数据结构。
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """初始化存储配置数据
        
        Args:
            data: 配置数据字典
        """
        super().__init__(data)
    
    @classmethod
    def create_memory_config(cls, name: str, **kwargs) -> 'StorageConfigData':
        """创建内存存储配置
        
        Args:
            name: 配置名称
            **kwargs: 其他配置参数
            
        Returns:
            存储配置数据实例
        """
        default_config = {
            'max_size': None,
            'max_memory_mb': None,
            'enable_ttl': False,
            'default_ttl_seconds': 3600,
            'cleanup_interval_seconds': 300,
            'enable_compression': False,
            'compression_threshold': 1024,
            'enable_metrics': True,
            'enable_persistence': False,
            'persistence_path': None,
            'persistence_interval_seconds': 600
        }
        default_config.update(kwargs)
        
        return cls({
            'name': name,
            'storage_type': StorageType.MEMORY.value,
            'enabled': True,
            'is_default': False,
            'config': default_config,
            'description': f"内存存储配置: {name}",
            'tags': ['memory']
        })
    
    @classmethod
    def create_sqlite_config(cls, name: str, **kwargs) -> 'StorageConfigData':
        """创建SQLite存储配置
        
        Args:
            name: 配置名称
            **kwargs: 其他配置参数
            
        Returns:
            存储配置数据实例
        """
        default_config = {
            'db_path': 'storage.db',
            'timeout': 30.0,
            'enable_wal_mode': True,
            'enable_foreign_keys': True,
            'connection_pool_size': 5,
            'enable_auto_vacuum': False,
            'cache_size': 2000,
            'temp_store': 'memory',
            'synchronous_mode': 'NORMAL',
            'journal_mode': 'WAL',
            'enable_backup': False,
            'backup_interval_hours': 24,
            'backup_path': 'backups',
            'max_backup_files': 7
        }
        default_config.update(kwargs)
        
        return cls({
            'name': name,
            'storage_type': StorageType.SQLITE.value,
            'enabled': True,
            'is_default': False,
            'config': default_config,
            'description': f"SQLite存储配置: {name}",
            'tags': ['sqlite']
        })
    
    @classmethod
    def create_file_config(cls, name: str, **kwargs) -> 'StorageConfigData':
        """创建文件存储配置
        
        Args:
            name: 配置名称
            **kwargs: 其他配置参数
            
        Returns:
            存储配置数据实例
        """
        default_config = {
            'base_path': 'file_storage',
            'enable_compression': False,
            'compression_threshold': 1024,
            'enable_ttl': False,
            'default_ttl_seconds': 3600,
            'cleanup_interval_seconds': 300,
            'enable_backup': False,
            'backup_interval_hours': 24,
            'backup_path': 'file_storage_backups',
            'max_backup_files': 7,
            'directory_structure': 'flat',
            'file_extension': 'json',
            'enable_metadata': True,
            'max_directory_size': None,
            'max_files_per_directory': 1000
        }
        default_config.update(kwargs)
        
        return cls({
            'name': name,
            'storage_type': StorageType.FILE.value,
            'enabled': True,
            'is_default': False,
            'config': default_config,
            'description': f"文件存储配置: {name}",
            'tags': ['file']
        })
    
    def get_name(self) -> str:
        """获取配置名称
        
        Returns:
            配置名称
        """
        return self.get('name', '')
    
    def get_storage_type(self) -> str:
        """获取存储类型
        
        Returns:
            存储类型
        """
        return self.get('storage_type', '')
    
    def is_enabled(self) -> bool:
        """检查是否启用
        
        Returns:
            是否启用
        """
        return self.get('enabled', True)
    
    def is_default(self) -> bool:
        """检查是否为默认配置
        
        Returns:
            是否为默认配置
        """
        return self.get('is_default', False)
    
    def get_config_data(self) -> Dict[str, Any]:
        """获取配置数据
        
        Returns:
            配置数据字典
        """
        return self.get('config', {})
    
    def get_description(self) -> str:
        """获取描述
        
        Returns:
            描述
        """
        return self.get('description', '')
    
    def get_tags(self) -> List[str]:
        """获取标签
        
        Returns:
            标签列表
        """
        return self.get('tags', [])


class StorageConfigCollectionData(ConfigData):
    """存储配置集合数据
    
    纯数据容器，用于存储配置集合的基础数据结构。
    """
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """初始化存储配置集合数据
        
        Args:
            data: 配置数据字典
        """
        super().__init__(data)
        
        # 设置默认数据结构
        if not self.data:
            self.data = {
                'default_config': None,
                'configs': {}
            }
    
    def get_default_config_name(self) -> Optional[str]:
        """获取默认配置名称
        
        Returns:
            默认配置名称
        """
        return self.get('default_config')
    
    def set_default_config_name(self, name: str) -> None:
        """设置默认配置名称
        
        Args:
            name: 配置名称
        """
        self.set('default_config', name)
    
    def get_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有配置
        
        Returns:
            配置字典
        """
        return self.get('configs', {})
    
    def get_config(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定配置
        
        Args:
            name: 配置名称
            
        Returns:
            配置数据或None
        """
        configs = self.get_configs()
        return configs.get(name)
    
    def add_config(self, config_data: StorageConfigData) -> None:
        """添加配置
        
        Args:
            config_data: 存储配置数据
        """
        configs = self.get_configs()
        configs[config_data.get_name()] = config_data.to_dict()
        
        # 如果是默认配置或没有默认配置，设置为默认
        if config_data.is_default() or self.get_default_config_name() is None:
            self.set_default_config_name(config_data.get_name())
    
    def remove_config(self, name: str) -> bool:
        """移除配置
        
        Args:
            name: 配置名称
            
        Returns:
            是否移除成功
        """
        configs = self.get_configs()
        if name not in configs:
            return False
        
        del configs[name]
        
        # 如果是默认配置，重新选择默认配置
        if self.get_default_config_name() == name:
            self.set_default_config_name(next(iter(configs.keys()), None))
        
        return True
    
    def list_configs(self, storage_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出配置
        
        Args:
            storage_type: 存储类型过滤
            
        Returns:
            配置列表
        """
        configs = list(self.get_configs().values())
        
        if storage_type is not None:
            configs = [config for config in configs if config.get('storage_type') == storage_type]
        
        return configs


__all__ = [
    "StorageType",
    "StorageConfigData",
    "StorageConfigCollectionData"
]