"""
统一存储基础设施模块

该模块提供统一存储的具体实现，包括基础存储类、
存储工厂和各种存储后端实现。
"""

from .base_storage import BaseStorage
from .interfaces import IStorageBackend, IStorageSerializer, IStorageCache, IStorageMetrics
from .factory import StorageFactory
from .registry import StorageRegistry

__all__ = [
    "BaseStorage",
    "IStorageBackend",
    "IStorageSerializer",
    "IStorageCache",
    "IStorageMetrics",
    "StorageFactory",
    "StorageRegistry",
]