"""Threads核心模块

提供Thread相关的核心功能，包括实体定义、接口、工厂和错误处理。
"""

from .interfaces import IThreadCore, IThreadBranchCore, IThreadSnapshotCore
from .entities import Thread, ThreadBranch, ThreadSnapshot, ThreadStatus, ThreadType, ThreadMetadata
from .base import ThreadBase
from .factories import ThreadFactory, ThreadBranchFactory, ThreadSnapshotFactory
from src.infrastructure.error_management.impl.threads import ThreadErrorHandler, ThreadOperationHandler

# 导出错误处理相关
def register_thread_error_handler():
    """注册Thread错误处理器到统一错误处理框架"""
    from src.infrastructure.error_management import register_error_handler
    from src.interfaces.sessions.exceptions import (
        SessionThreadException,
        ThreadCreationError,
        ThreadRemovalError,
        ThreadTransferError,
        SessionThreadInconsistencyError,
        AssociationNotFoundError,
        DuplicateThreadNameError,
        ThreadNotFoundError,
        SessionNotFoundError,
        TransactionRollbackError,
        WorkflowExecutionError,
        SynchronizationError,
        ConfigurationValidationError
    )
    
    # 注册Thread错误处理器
    thread_handler = ThreadErrorHandler()
    
    # 注册所有Thread相关异常
    thread_exceptions = [
        SessionThreadException,
        ThreadCreationError,
        ThreadRemovalError,
        ThreadTransferError,
        SessionThreadInconsistencyError,
        AssociationNotFoundError,
        DuplicateThreadNameError,
        ThreadNotFoundError,
        SessionNotFoundError,
        TransactionRollbackError,
        WorkflowExecutionError,
        SynchronizationError,
        ConfigurationValidationError
    ]
    
    for exception_type in thread_exceptions:
        register_error_handler(exception_type, thread_handler)

__all__ = [
    # 核心接口
    "IThreadCore",
    "IThreadBranchCore", 
    "IThreadSnapshotCore",
    
    # 实体定义
    "Thread",
    "ThreadBranch",
    "ThreadSnapshot",
    "ThreadStatus",
    "ThreadType",
    "ThreadMetadata",
    
    # 基础类和工厂
    "ThreadBase",
    "ThreadFactory",
    "ThreadBranchFactory",
    "ThreadSnapshotFactory",
    
    # 错误处理
    "ThreadErrorHandler",
    "ThreadOperationHandler",
    "register_thread_error_handler"
]