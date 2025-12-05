"""Repository异常定义

定义数据访问层相关的异常类型，提供统一的错误处理机制。
"""

from typing import Optional, Dict, Any


class RepositoryError(Exception):
    """Repository基础异常"""
    
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


class RepositoryNotFoundError(RepositoryError):
    """记录未找到异常"""
    pass


class RepositoryAlreadyExistsError(RepositoryError):
    """记录已存在异常"""
    pass


class RepositoryOperationError(RepositoryError):
    """Repository操作异常"""
    pass


class RepositoryConnectionError(RepositoryError):
    """数据库连接异常"""
    pass


class RepositoryTransactionError(RepositoryError):
    """事务异常"""
    pass


class RepositoryValidationError(RepositoryError):
    """仓储验证异常"""
    pass


class RepositoryTimeoutError(RepositoryError):
    """仓储超时异常"""
    pass


__all__ = [
    "RepositoryError",
    "RepositoryNotFoundError",
    "RepositoryAlreadyExistsError",
    "RepositoryOperationError",
    "RepositoryConnectionError",
    "RepositoryTransactionError",
    "RepositoryValidationError",
    "RepositoryTimeoutError",
]
