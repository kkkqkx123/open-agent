"""存储适配器模块

提供统一的存储适配器实现，包括存储后端、工厂和服务。
"""

# 后端实现
from .backends.core.base_backend import BaseStorageBackend

# 工厂实现
from .factory import (
    BackendRegistry,
    StorageFactory,
    get_global_registry,
    get_global_factory,
    create_storage,
    create_storage_async
)

# 服务实现从services层导入
from src.services.storage import (
    StateService,
    HistoryService,
    SnapshotService
)

__all__ = [
    # 后端
    "BaseStorageBackend",
    
    # 工厂
    "BackendRegistry",
    "StorageFactory",
    "get_global_registry",
    "get_global_factory",
    "create_storage",
    "create_storage_async",
    
    # 服务
    "StateService",
    "HistoryService",
    "SnapshotService",
]