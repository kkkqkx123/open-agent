"""状态管理异常定义

定义状态管理系统的异常类，包括存储相关异常。
"""

from typing import Optional, Any, Dict


class StateError(Exception):
    """状态管理基础异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """初始化异常
        
        Args:
            message: 错误消息
            details: 错误详情
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class StateValidationError(StateError):
    """状态验证异常"""
    pass


class StateNotFoundError(StateError):
    """状态未找到异常"""
    pass


class StateTimeoutError(StateError):
    """状态操作超时异常"""
    pass


class StateCapacityError(StateError):
    """状态容量超限异常"""
    
    def __init__(self, message: str, required_size: int = 0, available_size: int = 0):
        """初始化容量异常
        
        Args:
            message: 错误消息
            required_size: 所需大小
            available_size: 可用大小
        """
        super().__init__(message)
        self.required_size = required_size
        self.available_size = available_size


# 存储相关异常
class StorageError(StateError):
    """存储基础异常"""
    pass


class StorageConnectionError(StorageError):
    """存储连接异常"""
    pass


class StorageTransactionError(StorageError):
    """存储事务异常"""
    pass


class StorageValidationError(StorageError):
    """存储验证异常"""
    pass


class StorageNotFoundError(StorageError):
    """存储未找到异常"""
    pass


class StorageTimeoutError(StorageError):
    """存储超时异常"""
    pass


class StorageCapacityError(StorageError):
    """存储容量异常"""
    
    def __init__(self, message: str, required_size: int = 0, available_size: int = 0):
        """初始化容量异常
        
        Args:
            message: 错误消息
            required_size: 所需大小
            available_size: 可用大小
        """
        super().__init__(message)
        self.required_size = required_size
        self.available_size = available_size


class StorageConfigurationError(StorageError):
    """存储配置异常"""
    pass


class StorageMigrationError(StorageError):
    """存储迁移异常"""
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
    """存储锁定异常"""
    pass


class StorageQueryError(StorageError):
    """存储查询异常"""
    pass


class StorageHealthError(StorageError):
    """存储健康检查异常"""
    pass