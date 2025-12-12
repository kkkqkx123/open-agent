"""存储配置模型"""

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import Field, field_validator

from .base import BaseConfig


class StorageType(str, Enum):
    """存储类型枚举"""
    MEMORY = "memory"
    SQLITE = "sqlite"
    FILE = "file"


class MemoryStorageConfig(BaseConfig):
    """内存存储配置"""
    
    max_size: Optional[int] = Field(default=None, description="最大大小")
    max_memory_mb: Optional[int] = Field(default=None, description="最大内存（MB）")
    enable_ttl: bool = Field(default=False, description="是否启用TTL")
    default_ttl_seconds: int = Field(default=3600, description="默认TTL（秒）")
    cleanup_interval_seconds: int = Field(default=300, description="清理间隔（秒）")
    enable_compression: bool = Field(default=False, description="是否启用压缩")
    compression_threshold: int = Field(default=1024, description="压缩阈值")
    enable_metrics: bool = Field(default=True, description="是否启用指标")
    enable_persistence: bool = Field(default=False, description="是否启用持久化")
    persistence_path: Optional[str] = Field(default=None, description="持久化路径")
    persistence_interval_seconds: int = Field(default=600, description="持久化间隔")
    
    @field_validator("max_size", "max_memory_mb", "default_ttl_seconds", "cleanup_interval_seconds", "compression_threshold", "persistence_interval_seconds")
    @classmethod
    def validate_positive_integer(cls, v: Optional[int]) -> Optional[int]:
        """验证正整数"""
        if v is not None and v <= 0:
            raise ValueError("必须为正整数")
        return v


class SQLiteStorageConfig(BaseConfig):
    """SQLite存储配置"""
    
    db_path: str = Field(default="storage.db", description="数据库路径")
    timeout: float = Field(default=30.0, description="超时时间")
    enable_wal_mode: bool = Field(default=True, description="是否启用WAL模式")
    enable_foreign_keys: bool = Field(default=True, description="是否启用外键")
    connection_pool_size: int = Field(default=5, description="连接池大小")
    enable_auto_vacuum: bool = Field(default=False, description="是否启用自动清理")
    cache_size: int = Field(default=2000, description="缓存大小")
    temp_store: str = Field(default="memory", description="临时存储")
    synchronous_mode: str = Field(default="NORMAL", description="同步模式")
    journal_mode: str = Field(default="WAL", description="日志模式")
    enable_backup: bool = Field(default=False, description="是否启用备份")
    backup_interval_hours: int = Field(default=24, description="备份间隔（小时）")
    backup_path: str = Field(default="backups", description="备份路径")
    max_backup_files: int = Field(default=7, description="最大备份文件数")
    
    @field_validator("timeout", "connection_pool_size", "cache_size", "backup_interval_hours", "max_backup_files")
    @classmethod
    def validate_positive_number(cls, v: float) -> float:
        """验证正数"""
        if v <= 0:
            raise ValueError("必须为正数")
        return v
    
    @field_validator("temp_store")
    @classmethod
    def validate_temp_store(cls, v: str) -> str:
        """验证临时存储"""
        valid_values = ["memory", "file", "default"]
        if v not in valid_values:
            raise ValueError(f"临时存储必须是以下之一: {valid_values}")
        return v
    
    @field_validator("synchronous_mode")
    @classmethod
    def validate_synchronous_mode(cls, v: str) -> str:
        """验证同步模式"""
        valid_values = ["OFF", "NORMAL", "FULL", "EXTRA"]
        if v not in valid_values:
            raise ValueError(f"同步模式必须是以下之一: {valid_values}")
        return v
    
    @field_validator("journal_mode")
    @classmethod
    def validate_journal_mode(cls, v: str) -> str:
        """验证日志模式"""
        valid_values = ["DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF"]
        if v not in valid_values:
            raise ValueError(f"日志模式必须是以下之一: {valid_values}")
        return v


class FileStorageConfig(BaseConfig):
    """文件存储配置"""
    
    base_path: str = Field(default="file_storage", description="基础路径")
    enable_compression: bool = Field(default=False, description="是否启用压缩")
    compression_threshold: int = Field(default=1024, description="压缩阈值")
    enable_ttl: bool = Field(default=False, description="是否启用TTL")
    default_ttl_seconds: int = Field(default=3600, description="默认TTL（秒）")
    cleanup_interval_seconds: int = Field(default=300, description="清理间隔（秒）")
    enable_backup: bool = Field(default=False, description="是否启用备份")
    backup_interval_hours: int = Field(default=24, description="备份间隔（小时）")
    backup_path: str = Field(default="file_storage_backups", description="备份路径")
    max_backup_files: int = Field(default=7, description="最大备份文件数")
    directory_structure: str = Field(default="flat", description="目录结构")
    file_extension: str = Field(default="json", description="文件扩展名")
    enable_metadata: bool = Field(default=True, description="是否启用元数据")
    max_directory_size: Optional[int] = Field(default=None, description="最大目录大小")
    max_files_per_directory: int = Field(default=1000, description="每个目录最大文件数")
    
    @field_validator("default_ttl_seconds", "cleanup_interval_seconds", "compression_threshold", "backup_interval_hours", "max_backup_files", "max_files_per_directory")
    @classmethod
    def validate_positive_integer(cls, v: int) -> int:
        """验证正整数"""
        if v <= 0:
            raise ValueError("必须为正整数")
        return v
    
    @field_validator("directory_structure")
    @classmethod
    def validate_directory_structure(cls, v: str) -> str:
        """验证目录结构"""
        valid_values = ["flat", "by_type", "by_date", "by_agent"]
        if v not in valid_values:
            raise ValueError(f"目录结构必须是以下之一: {valid_values}")
        return v


class StorageConfig(BaseConfig):
    """存储配置"""
    
    name: str = Field(..., description="配置名称")
    storage_type: StorageType = Field(..., description="存储类型")
    enabled: bool = Field(default=True, description="是否启用")
    is_default: bool = Field(default=False, description="是否为默认配置")
    config: Dict[str, Any] = Field(default_factory=dict, description="配置数据")
    description: Optional[str] = Field(default=None, description="描述")
    tags: List[str] = Field(default_factory=list, description="标签")
    
    def get_memory_config(self) -> MemoryStorageConfig:
        """获取内存存储配置"""
        if self.storage_type != StorageType.MEMORY:
            raise ValueError("配置类型不是内存存储")
        return MemoryStorageConfig.from_dict(self.config)
    
    def get_sqlite_config(self) -> SQLiteStorageConfig:
        """获取SQLite存储配置"""
        if self.storage_type != StorageType.SQLITE:
            raise ValueError("配置类型不是SQLite存储")
        return SQLiteStorageConfig.from_dict(self.config)
    
    def get_file_config(self) -> FileStorageConfig:
        """获取文件存储配置"""
        if self.storage_type != StorageType.FILE:
            raise ValueError("配置类型不是文件存储")
        return FileStorageConfig.from_dict(self.config)


class StorageConfigCollection(BaseConfig):
    """存储配置集合"""
    
    default_config: Optional[str] = Field(default=None, description="默认配置名称")
    configs: Dict[str, StorageConfig] = Field(default_factory=dict, description="配置字典")
    
    def get_config(self, name: str) -> Optional[StorageConfig]:
        """获取指定配置"""
        return self.configs.get(name)
    
    def get_default_config(self) -> Optional[StorageConfig]:
        """获取默认配置"""
        if self.default_config is None:
            return None
        return self.configs.get(self.default_config)
    
    def list_configs(self, storage_type: Optional[StorageType] = None) -> List[StorageConfig]:
        """列出配置"""
        configs = list(self.configs.values())
        
        if storage_type is not None:
            configs = [config for config in configs if config.storage_type == storage_type]
        
        return configs
    
    def add_config(self, config: StorageConfig) -> None:
        """添加配置"""
        self.configs[config.name] = config
        
        # 如果是默认配置或没有默认配置，设置为默认
        if config.is_default or self.default_config is None:
            self.default_config = config.name
    
    def remove_config(self, name: str) -> bool:
        """移除配置"""
        if name not in self.configs:
            return False
        
        del self.configs[name]
        
        # 如果是默认配置，重新选择默认配置
        if self.default_config == name:
            self.default_config = next(iter(self.configs.keys()), None)
        
        return True