"""
通用存储核心模块

提供存储系统的核心接口、模型和异常定义。
"""

from .interfaces import (
    IStorageBackend,
    IStorageRepository,
    IStorageManager,
    IStorageMonitoring,
    IStorageMigration,
    IStorageTransaction
)

from .models import (
    StorageBackendType,
    StorageOperationType,
    StorageStatus,
    StorageData,
    StorageQuery,
    StorageOperation,
    StorageResult,
    StorageTransaction,
    StorageStatistics,
    StorageHealth,
    StorageConfig,
    StorageBatch,
    StorageMigration,
    StorageBackendInfo
)

from .exceptions import (
    StorageError,
    StorageConnectionError,
    StorageOperationError,
    StorageValidationError,
    StorageNotFoundError,
    StorageTimeoutError,
    StorageCapacityError,
    StorageIntegrityError,
    StorageConfigurationError,
    StorageMigrationError,
    StorageTransactionError,
    StoragePermissionError,
    StorageSerializationError,
    StorageCompressionError,
    StorageEncryptionError
)

from .error_handler import StorageErrorHandler

from .config import (
    StorageType,
    StorageConfigManager,
    MemoryStorageConfig,
    SQLiteStorageConfig,
    FileStorageConfig
)

__all__ = [
    # 接口
    "IStorageBackend",
    "IStorageRepository",
    "IStorageManager",
    "IStorageMonitoring",
    "IStorageMigration",
    "IStorageTransaction",
    
    # 模型
    "StorageBackendType",
    "StorageOperationType",
    "StorageStatus",
    "StorageData",
    "StorageQuery",
    "StorageOperation",
    "StorageResult",
    "StorageTransaction",
    "StorageStatistics",
    "StorageHealth",
    "StorageConfig",
    "StorageBatch",
    "StorageMigration",
    "StorageBackendInfo",
    
    # 异常
    "StorageError",
    "StorageConnectionError",
    "StorageOperationError",
    "StorageValidationError",
    "StorageNotFoundError",
    "StorageTimeoutError",
    "StorageCapacityError",
    "StorageIntegrityError",
    "StorageConfigurationError",
    "StorageMigrationError",
    "StorageTransactionError",
    "StoragePermissionError",
    "StorageSerializationError",
    "StorageCompressionError",
    "StorageEncryptionError",
    
    # 错误处理
    "StorageErrorHandler",
    
    # 配置管理
    "StorageType",
    "StorageConfigManager",
    "MemoryStorageConfig",
    "SQLiteStorageConfig",
    "FileStorageConfig"
]