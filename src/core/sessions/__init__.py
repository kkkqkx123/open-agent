"""Sessions核心模块

提供Session相关的核心功能，包括实体定义、接口、基础类和错误处理。
"""

from .core_interfaces import ISessionCore, ISessionValidator, ISessionStateTransition
from .entities import (
    Session,
    UserInteractionEntity,
    UserRequestEntity,
    SessionContext
)
from .base import SessionBase
from .association import SessionThreadAssociation
from src.infrastructure.error_management.impl.sessions import SessionErrorHandler, SessionOperationHandler

# 导出错误处理相关
def register_session_error_handler():
    """注册Session错误处理器到统一错误处理框架"""
    from src.infrastructure.error_management import register_error_handler
    from src.interfaces.sessions.exceptions import (
        SessionThreadException,
        SessionNotFoundError,
        ThreadNotFoundError,
        AssociationNotFoundError,
        SessionThreadInconsistencyError,
        TransactionRollbackError,
        WorkflowExecutionError,
        SynchronizationError,
        ConfigurationValidationError
    )
    
    # 注册Session错误处理器
    session_handler = SessionErrorHandler()
    
    # 注册所有Session相关异常
    session_exceptions = [
        SessionThreadException,
        SessionNotFoundError,
        ThreadNotFoundError,
        AssociationNotFoundError,
        SessionThreadInconsistencyError,
        TransactionRollbackError,
        WorkflowExecutionError,
        SynchronizationError,
        ConfigurationValidationError,
        ValueError  # 处理association.py中的ValueError
    ]
    
    for exception_type in session_exceptions:
        register_error_handler(exception_type, session_handler)

__all__ = [
    # 核心接口
    "ISessionCore",
    "ISessionValidator",
    "ISessionStateTransition",
    
    # 实体定义
    "Session",
    "UserInteractionEntity",
    "UserRequestEntity",
    "SessionContext",
    
    # 基础类和关联
    "SessionBase",
    "SessionThreadAssociation",
    
    # 错误处理
    "SessionErrorHandler",
    "SessionOperationHandler",
    "register_session_error_handler"
]