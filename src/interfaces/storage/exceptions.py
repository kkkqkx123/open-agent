"""
存储异常定义

定义存储系统相关的异常类型，提供统一的错误处理机制。
"""

from typing import Optional, Dict, Any


class StorageError(Exception):
    """存储基础异常"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class StorageConnectionError(StorageError):
    """存储连接异常"""
    pass


class StorageOperationError(StorageError):
    """存储操作异常"""
    pass


class StorageValidationError(StorageError):
    """存储验证异常"""
    pass


class StorageNotFoundError(StorageError):
    """存储数据未找到异常"""
    pass


class StorageTimeoutError(StorageError):
    """存储超时异常"""
    pass


class StorageCapacityError(StorageError):
    """存储容量异常"""
    pass


class StorageIntegrityError(StorageError):
    """存储完整性异常"""
    pass


class StorageConfigurationError(StorageError):
    """存储配置异常"""
    pass


class StorageMigrationError(StorageError):
    """存储迁移异常"""
    pass


class StorageTransactionError(StorageError):
    """存储事务异常"""
    pass


class StoragePermissionError(StorageError):
    """存储权限异常"""
    pass


class StorageSerializationError(StorageError):
    """存储序列化异常"""
    pass


class StorageCompressionError(StorageError):
    """存储压缩异常"""
    pass


class StorageEncryptionError(StorageError):
    """存储加密异常"""
    pass


class StorageIndexError(StorageError):
    """存储索引异常"""
    pass


class StorageBackupError(StorageError):
    """存储备份异常"""
    pass


class StorageLockError(StorageError):
    """存储锁异常"""
    pass


class StorageQueryError(StorageError):
    """存储查询异常"""
    pass


class StorageHealthError(StorageError):
    """存储健康检查异常"""
    pass


class StorageConsistencyError(StorageError):
    """存储一致性异常"""
    pass


class StorageDistributedTransactionError(StorageError):
    """分布式事务异常"""
    pass