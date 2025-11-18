"""存储适配器模块

提供状态存储的适配器实现，支持多种存储后端。
"""

from .interfaces import IStateStorageAdapter, IStorageAdapterFactory, IStorageMigration
from .memory import MemoryStateStorageAdapter
from .sqlite import SQLiteStateStorageAdapter
from .factory import (
    StorageAdapterFactory, 
    StorageAdapterManager,
    get_storage_factory,
    get_storage_manager,
    create_storage_adapter
)

__all__ = [
    # 接口
    "IStateStorageAdapter",
    "IStorageAdapterFactory", 
    "IStorageMigration",
    
    # 实现
    "MemoryStateStorageAdapter",
    "SQLiteStateStorageAdapter",
    
    # 工厂和管理
    "StorageAdapterFactory",
    "StorageAdapterManager",
    "get_storage_factory",
    "get_storage_manager",
    "create_storage_adapter"
]