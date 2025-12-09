"""存储后端工厂层

统一管理和创建存储后端实例。
"""

from .backend_factory import StorageBackendFactory, BackendRegistry

__all__ = [
    "StorageBackendFactory",
    "BackendRegistry"
]