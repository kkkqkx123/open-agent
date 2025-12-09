"""
统一存储接口模块

提供存储系统的统一接口定义，包括基础存储、监控、迁移、事务和异常处理。
这是整个系统的存储抽象层，为所有模块提供统一的存储接口。
"""

from .base import IStorage, IStorageFactory
from .provider import IStorageProvider
from .session_thread import ISessionStorage, IThreadStorage
from .monitoring import IStorageMonitoring, IStorageMetrics, IStorageAlerting
from .migration import IStorageMigration, ISchemaMigration, IDataTransformer, IMigrationPlanner
from .transaction import IStorageTransaction, IDistributedTransaction, ITransactionRecovery, ITransactionManager, IConsistencyManager
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
    StorageEncryptionError,
    StorageIndexError,
    StorageBackupError,
    StorageLockError,
    StorageQueryError,
    StorageHealthError,
    StorageConsistencyError,
    StorageDistributedTransactionError
)

__all__ = [
    # 基础接口
    "IStorage",
    "IStorageFactory",
    "IStorageProvider",
    "ISessionStorage",
    "IThreadStorage",
    
    # 监控接口
    "IStorageMonitoring",
    "IStorageMetrics", 
    "IStorageAlerting",
    
    # 迁移接口
    "IStorageMigration",
    "ISchemaMigration",
    "IDataTransformer",
    "IMigrationPlanner",
    
    # 事务接口
    "IStorageTransaction",
    "IDistributedTransaction",
    "ITransactionRecovery",
    "ITransactionManager",
    "IConsistencyManager",
    
    # 异常类型
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
    "StorageDistributedTransactionError"
]