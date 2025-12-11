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
from src.interfaces.storage.base import IStorage

# 核心层
from .core import (
    BaseStorageBackend,
    SessionStorageMixin,
    ThreadStorageMixin,
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
    ThreadBackend
)

# TODO: 修复 factory 模块缺失问题
# 工厂层
# from .factory import (
#     StorageBackendFactory,
#     BackendRegistry
# )

__all__ = [
    # 接口层
    "IStorage",
    "ISessionStorage",
    "IThreadStorage",
    "IStorageProvider",
    
    # 核心层
    "BaseStorageBackend",
    "SessionStorageMixin",
    "ThreadStorageMixin",
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
    
    # 工厂层
    # "StorageBackendFactory",
    # "BackendRegistry"
]