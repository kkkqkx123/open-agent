"""
通用存储核心模块

提供存储系统的核心接口、模型和异常定义。
现在使用统一的存储接口架构。
"""

# 从统一存储接口导入
from src.interfaces.storage import (
    IStorage,
    IStorageFactory,
    IStorageMonitoring,
    IStorageMetrics,
    IStorageAlerting,
    IStorageMigration,
    ISchemaMigration,
    IDataTransformer,
    IMigrationPlanner,
    IStorageTransaction,
    IDistributedTransaction,
    ITransactionRecovery,
    ITransactionManager,
    IConsistencyManager,
    # 异常类型
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
    StorageEncryptionError,
    StorageIndexError,
    StorageBackupError,
    StorageLockError,
    StorageQueryError,
    StorageHealthError,
    StorageConsistencyError,
    StorageDistributedTransactionError
)

# 核心模块特有的接口已迁移到统一接口，从统一接口导入
from src.interfaces.storage import IStorage
from src.interfaces.state.storage.backend import IStorageBackend

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

from src.infrastructure.error_management.impl.storage import StorageErrorHandler

# 从基础设施层导入
from src.infrastructure.config.models.storage import StorageType

__all__ = [
    # 统一存储接口（推荐使用）
    "IStorage",
    "IStorageFactory",
    "IStorageMonitoring",
    "IStorageMetrics",
    "IStorageAlerting",
    "IStorageMigration",
    "ISchemaMigration",
    "IDataTransformer",
    "IMigrationPlanner",
    "IStorageTransaction",
    "IDistributedTransaction",
    "ITransactionRecovery",
    "ITransactionManager",
    "IConsistencyManager",
    
    # 核心模块特有接口（向后兼容）
    "IStorage",
    "IStorageBackend",
    # "IStorageRepository",
    # "IStorageManager",
    
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
    
    # 统一异常类型
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
    "StorageIndexError",
    "StorageBackupError",
    "StorageLockError",
    "StorageQueryError",
    "StorageHealthError",
    "StorageConsistencyError",
    "StorageDistributedTransactionError",
    
    # 错误处理
    "StorageErrorHandler",
    
    # 配置管理
    "StorageType",
]