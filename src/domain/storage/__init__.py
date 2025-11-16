"""
统一存储领域模块

该模块提供统一的存储接口、模型和异常定义，为整个系统提供一致的存储抽象。
"""

from .interfaces import IUnifiedStorage, IStorageFactory
from .models import StorageData
from .exceptions import (
    StorageError,
    StorageConnectionError,
    StorageTransactionError,
    StorageValidationError,
    StorageNotFoundError
)

__all__ = [
    "IUnifiedStorage",
    "IStorageFactory",
    "StorageData",
    "StorageError",
    "StorageConnectionError",
    "StorageTransactionError",
    "StorageValidationError",
    "StorageNotFoundError",
]