"""Storage核心模块

提供统一存储的核心功能，包括数据模型和错误处理。
"""

from .models import (
    DataType,
    StorageData,
    StorageQuery,
    StorageTransaction,
    StorageStatistics,
    StorageHealth,
    StorageConfig,
    StorageBatch,
    StorageMigration
)
from .error_handler import StorageErrorHandler, StorageOperationHandler

# 导出错误处理相关
def register_storage_error_handler():
    """注册Storage错误处理器到统一错误处理框架"""
    from src.core.common.error_management import register_error_handler
    from src.core.common.exceptions.storage import (
        StorageError,
        StorageConnectionError,
        StorageTransactionError,
        StorageValidationError,
        StorageNotFoundError,
        StoragePermissionError,
        StorageTimeoutError,
        StorageCapacityError,
        StorageIntegrityError,
        StorageConfigurationError,
        StorageMigrationError,
        StorageSerializationError,
        StorageCompressionError,
        StorageEncryptionError,
        StorageIndexError,
        StorageBackupError,
        StorageLockError,
        StorageQueryError,
        StorageHealthError
    )
    
    # 注册Storage错误处理器
    storage_handler = StorageErrorHandler()
    
    # 注册所有存储相关异常
    storage_exceptions = [
        StorageError,
        StorageConnectionError,
        StorageTransactionError,
        StorageValidationError,
        StorageNotFoundError,
        StoragePermissionError,
        StorageTimeoutError,
        StorageCapacityError,
        StorageIntegrityError,
        StorageConfigurationError,
        StorageMigrationError,
        StorageSerializationError,
        StorageCompressionError,
        StorageEncryptionError,
        StorageIndexError,
        StorageBackupError,
        StorageLockError,
        StorageQueryError,
        StorageHealthError
    ]
    
    for exception_type in storage_exceptions:
        register_error_handler(exception_type, storage_handler)

__all__ = [
    # 数据模型
    "DataType",
    "StorageData",
    "StorageQuery", 
    "StorageTransaction",
    "StorageStatistics",
    "StorageHealth",
    "StorageConfig",
    "StorageBatch",
    "StorageMigration",
    
    # 错误处理
    "StorageErrorHandler",
    "StorageOperationHandler",
    "register_storage_error_handler"
]