"""存储适配器模块

提供各种存储适配器的实现，包括内存、SQLite和文件存储。
"""

from .memory import MemoryStateStorageAdapter
from .sqlite import SQLiteStateStorageAdapter
from .file import FileStateStorageAdapter

from .base import BaseStateStorageAdapter, BaseStorageBackend
from .memory_backend import MemoryStorageBackend
from .sqlite_backend import SQLiteStorageBackend
from .file_backend import FileStorageBackend

from .memory_utils import MemoryStorageUtils
from .sqlite_utils import SQLiteStorageUtils
from .file_utils import FileStorageUtils

from .factory import (
    StorageAdapterFactory,
    StorageAdapterFactoryRegistry,
    MemoryStorageAdapterFactory,
    SQLiteStorageAdapterFactory,
    FileStorageAdapterFactory,
    get_factory_registry,
    create_storage_adapter,
    register_storage_factory,
    register_custom_storage_factory,
    storage_adapter_factory
)

__all__ = [
    # 适配器
    "MemoryStateStorageAdapter",
    "SQLiteStateStorageAdapter",
    "FileStateStorageAdapter",
    
    # 基类
    "BaseStateStorageAdapter",
    "BaseStorageBackend",
    
    # 后端
    "MemoryStorageBackend",
    "SQLiteStorageBackend",
    "FileStorageBackend",
    
    # 工具类
    "MemoryStorageUtils",
    "SQLiteStorageUtils",
    "FileStorageUtils",
    
    # 工厂
    "StorageAdapterFactory",
    "StorageAdapterFactoryRegistry",
    "MemoryStorageAdapterFactory",
    "SQLiteStorageAdapterFactory",
    "FileStorageAdapterFactory",
    "get_factory_registry",
    "create_storage_adapter",
    "register_storage_factory",
    "register_custom_storage_factory",
    "storage_adapter_factory",
]