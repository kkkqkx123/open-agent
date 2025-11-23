"""
存储接口模块
"""

from .base import IUnifiedStorage, IStorageFactory
from .backends import ISessionStorageBackendFactory, IThreadStorageBackendFactory
from .association import ISessionThreadAssociationFactory

__all__ = [
    "IUnifiedStorage",
    "IStorageFactory",
    "ISessionStorageBackendFactory",
    "IThreadStorageBackendFactory",
    "ISessionThreadAssociationFactory",
]
