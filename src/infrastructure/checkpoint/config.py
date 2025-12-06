"""
检查点存储配置管理

提供检查点存储的配置模型和管理功能。
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CheckpointStorageConfig:
    """检查点存储配置"""
    
    # 存储类型
    storage_type: str = "memory"  # memory, sqlite, file
    
    # 内存存储配置
    max_checkpoints: int = 1000
    enable_ttl: bool = False
    default_ttl_seconds: int = 3600
    
    # SQLite存储配置
    db_path: str = "checkpoints.db"
    connection_pool_size: int = 5
    enable_wal_mode: bool = True
    enable_foreign_keys: bool = True
    
    # 文件存储配置
    storage_path: str = "./checkpoints"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointStorageConfig':
        """从字典创建配置"""
        return cls(
            storage_type=data.get("storage_type", "memory"),
            max_checkpoints=data.get("max_checkpoints", 1000),
            enable_ttl=data.get("enable_ttl", False),
            default_ttl_seconds=data.get("default_ttl_seconds", 3600),
            db_path=data.get("db_path", "checkpoints.db"),
            connection_pool_size=data.get("connection_pool_size", 5),
            enable_wal_mode=data.get("enable_wal_mode", True),
            enable_foreign_keys=data.get("enable_foreign_keys", True),
            storage_path=data.get("storage_path", "./checkpoints"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "storage_type": self.storage_type,
            "max_checkpoints": self.max_checkpoints,
            "enable_ttl": self.enable_ttl,
            "default_ttl_seconds": self.default_ttl_seconds,
            "db_path": self.db_path,
            "connection_pool_size": self.connection_pool_size,
            "enable_wal_mode": self.enable_wal_mode,
            "enable_foreign_keys": self.enable_foreign_keys,
            "storage_path": self.storage_path,
        }