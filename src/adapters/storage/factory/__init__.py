"""存储工厂模块

提供存储实例的创建、注册和管理功能。
"""

from .backend_registry import (
    BackendRegistry,
    get_global_registry,
    register_backend,
    unregister_backend
)
from .storage_factory import (
    StorageFactory,
    get_global_factory,
    create_storage,
    create_storage_async
)

__all__ = [
    # 后端注册表
    "BackendRegistry",
    "get_global_registry",
    "register_backend",
    "unregister_backend",
    
    # 存储工厂
    "StorageFactory",
    "get_global_factory",
    "create_storage",
    "create_storage_async",
]