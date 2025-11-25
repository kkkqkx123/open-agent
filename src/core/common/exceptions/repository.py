"""
Repository相关异常定义
"""

from typing import Optional, Dict, Any


class RepositoryError(Exception):
    """Repository基础异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
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


__all__ = [
    "RepositoryError",
    "RepositoryNotFoundError",
    "RepositoryAlreadyExistsError",
    "RepositoryOperationError",
    "RepositoryConnectionError",
    "RepositoryTransactionError",
]
