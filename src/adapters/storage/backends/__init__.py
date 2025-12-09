"""存储后端重构实现

全新的存储后端架构，按功能拆分，支持组合式开发。
"""

# 接口层 - 从统一接口层导入
from src.interfaces.storage import (
    IStorage,
    ISessionStorage,
    IThreadStorage,
    IStorageProvider
)
from src.interfaces.state.storage import IStorageBackend

# 核心层
from .core import (
    BaseStorageBackend,
    SessionStorageMixin,
    ThreadStorageMixin,
    StorageValidationMixin,
    StorageSerializationMixin,
    StorageBackendError,
    ProviderError
)

# 提供者层
from .providers import (
    BaseStorageProvider,
    SQLiteProvider,
    FileProvider,
    MemoryProvider
)

# 实现层
from .impl import (
    SessionBackend,
    ThreadBackend,
    SQLiteSessionBackend,
    SQLiteThreadBackend,
    FileSessionBackend,
    FileThreadBackend
)

# 工厂层
from .factory import (
    StorageBackendFactory,
    BackendRegistry
)

__all__ = [
    # 接口层
    "IStorage",
    "ISessionStorage",
    "IThreadStorage",
    "IStorageBackend",
    "IStorageProvider",
    
    # 核心层
    "BaseStorageBackend",
    "SessionStorageMixin",
    "ThreadStorageMixin",
    "StorageValidationMixin",
    "StorageSerializationMixin",
    "StorageBackendError",
    "ProviderError",
    
    # 提供者层
    "BaseStorageProvider",
    "SQLiteProvider",
    "FileProvider",
    "MemoryProvider",
    
    # 实现层
    "SessionBackend",
    "ThreadBackend",
    "SQLiteSessionBackend",
    "SQLiteThreadBackend",
    "FileSessionBackend",
    "FileThreadBackend",
    
    # 工厂层
    "StorageBackendFactory",
    "BackendRegistry"
]