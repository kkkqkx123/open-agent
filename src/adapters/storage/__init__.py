"""存储适配器模块

提供统一的异步存储适配器实现。
"""

# 导入主要的适配器类
from .adapters.async_adapter import AsyncStateStorageAdapter
from .adapters.sqlite import SQLiteStateStorageAdapter
from .adapters.memory import MemoryStateStorageAdapter
from .adapters.file import FileStateStorageAdapter

# 导入工厂类
from .factory import StorageAdapterFactory, create_storage_adapter

# 导入接口
from .interfaces import (
    ISessionStorageBackendFactory,
    IThreadStorageBackendFactory,
    ISessionThreadAssociationFactory
)

# 导入后端
from .backends.base import ISessionStorageBackend
from .backends.thread_base import IThreadStorageBackend

__all__ = [
    # 适配器类
    'AsyncStateStorageAdapter',
    'SQLiteStateStorageAdapter',
    'MemoryStateStorageAdapter',
    'FileStateStorageAdapter',
    
    # 工厂类
    'StorageAdapterFactory',
    'create_storage_adapter',
    
    # 接口
    'ISessionStorageBackendFactory',
    'IThreadStorageBackendFactory',
    'ISessionThreadAssociationFactory',
    
    # 后端
    'ISessionStorageBackend',
    'IThreadStorageBackend',
]