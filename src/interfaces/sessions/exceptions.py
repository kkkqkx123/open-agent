"""Session-Thread相关异常定义"""

from typing import Optional, Dict, Any


class SessionThreadException(Exception):
    """Session-Thread相关异常基类"""
    
    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """初始化异常
        
        Args:
            message: 异常消息
            session_id: 会话ID
            thread_id: 线程ID
            details: 详细信息
            cause: 原因异常
        """
        super().__init__(message)
        self.session_id = session_id
        self.thread_id = thread_id
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "exception_type": self.__class__.__name__,
            "message": str(self),
            "session_id": self.session_id,
            "thread_id": self.thread_id,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None
        }


class ThreadCreationError(SessionThreadException):
    """Thread创建失败异常"""
    
    def __init__(
        self,
        session_id: str,
        thread_config: Dict[str, Any],
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Failed to create thread for session {session_id}: {cause}",
            session_id=session_id,
            details={"thread_config": thread_config},
            cause=cause
        )
        self.thread_config = thread_config


class ThreadRemovalError(SessionThreadException):
    """Thread移除失败异常"""
    
    def __init__(
        self,
        session_id: str,
        thread_id: str,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Failed to remove thread {thread_id} from session {session_id}: {cause}",
            session_id=session_id,
            thread_id=thread_id,
            cause=cause
        )


class ThreadTransferError(SessionThreadException):
    """Thread转移失败异常"""
    
    def __init__(
        self,
        thread_id: str,
        from_session_id: str,
        to_session_id: str,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Failed to transfer thread {thread_id} from session {from_session_id} to session {to_session_id}: {cause}",
            session_id=to_session_id,
            thread_id=thread_id,
            details={
                "from_session_id": from_session_id,
                "to_session_id": to_session_id
            },
            cause=cause
        )
        self.from_session_id = from_session_id
        self.to_session_id = to_session_id


class SessionThreadInconsistencyError(SessionThreadException):
    """Session-Thread数据不一致异常"""
    
    def __init__(
        self,
        session_id: str,
        inconsistencies: list,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Session-Thread inconsistency detected in {session_id}: {len(inconsistencies)} issues",
            session_id=session_id,
            details={"inconsistencies": inconsistencies},
            cause=cause
        )
        self.inconsistencies = inconsistencies


class AssociationNotFoundError(SessionThreadException):
    """关联未找到异常"""
    
    def __init__(
        self,
        session_id: str,
        thread_id: str,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Association not found for session {session_id} and thread {thread_id}",
            session_id=session_id,
            thread_id=thread_id,
            cause=cause
        )


class DuplicateThreadNameError(SessionThreadException):
    """重复Thread名称异常"""
    
    def __init__(
        self,
        session_id: str,
        thread_name: str,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Thread name '{thread_name}' already exists in session {session_id}",
            session_id=session_id,
            details={"thread_name": thread_name},
            cause=cause
        )
        self.thread_name = thread_name


class ThreadNotFoundError(SessionThreadException):
    """Thread未找到异常"""
    
    def __init__(
        self,
        thread_id: str,
        session_id: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Thread not found: {thread_id}",
            session_id=session_id,
            thread_id=thread_id,
            cause=cause
        )


class SessionNotFoundError(SessionThreadException):
    """Session未找到异常"""
    
    def __init__(
        self,
        session_id: str,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Session not found: {session_id}",
            session_id=session_id,
            cause=cause
        )


class TransactionRollbackError(SessionThreadException):
    """事务回滚失败异常"""
    
    def __init__(
        self,
        operation_id: str,
        rollback_errors: list,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Transaction rollback failed for operation {operation_id}: {len(rollback_errors)} errors",
            details={
                "operation_id": operation_id,
                "rollback_errors": rollback_errors
            },
            cause=cause
        )
        self.operation_id = operation_id
        self.rollback_errors = rollback_errors


class WorkflowExecutionError(SessionThreadException):
    """工作流执行失败异常"""
    
    def __init__(
        self,
        session_id: str,
        thread_name: str,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Workflow execution failed for thread '{thread_name}' in session {session_id}: {cause}",
            session_id=session_id,
            details={"thread_name": thread_name},
            cause=cause
        )
        self.thread_name = thread_name


class SynchronizationError(SessionThreadException):
    """同步失败异常"""
    
    def __init__(
        self,
        session_id: str,
        sync_operation: str,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Synchronization failed for session {session_id} during {sync_operation}: {cause}",
            session_id=session_id,
            details={"sync_operation": sync_operation},
            cause=cause
        )
        self.sync_operation = sync_operation


class ConfigurationValidationError(SessionThreadException):
    """配置验证失败异常"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        session_id: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            session_id=session_id,
            details={"config_key": config_key} if config_key else {},
            cause=cause
        )
        self.config_key = config_key


class SessionTimeoutError(SessionThreadException):
    """Session超时异常"""
    
    def __init__(
        self,
        session_id: str,
        timeout_type: str,
        timeout_seconds: Optional[int] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Session {session_id} timeout: {timeout_type}",
            session_id=session_id,
            details={
                "timeout_type": timeout_type,
                "timeout_seconds": timeout_seconds
            },
            cause=cause
        )
        self.timeout_type = timeout_type
        self.timeout_seconds = timeout_seconds


class SessionCapacityError(SessionThreadException):
    """Session容量超限异常"""
    
    def __init__(
        self,
        session_id: str,
        capacity_type: str,
        current_usage: int,
        capacity_limit: int,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Session {session_id} capacity exceeded for {capacity_type}: {current_usage}/{capacity_limit}",
            session_id=session_id,
            details={
                "capacity_type": capacity_type,
                "current_usage": current_usage,
                "capacity_limit": capacity_limit
            },
            cause=cause
        )
        self.capacity_type = capacity_type
        self.current_usage = current_usage
        self.capacity_limit = capacity_limit


class SessionPermissionError(SessionThreadException):
    """Session权限错误异常"""
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        required_permission: str,
        operation: str,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Permission denied for user {user_id} on session {session_id}: {operation} requires {required_permission}",
            session_id=session_id,
            details={
                "user_id": user_id,
                "required_permission": required_permission,
                "operation": operation
            },
            cause=cause
        )
        self.user_id = user_id
        self.required_permission = required_permission
        self.operation = operation


# 导出所有异常
__all__ = [
    "SessionThreadException",
    "ThreadCreationError",
    "ThreadRemovalError", 
    "ThreadTransferError",
    "SessionThreadInconsistencyError",
    "AssociationNotFoundError",
    "DuplicateThreadNameError",
    "ThreadNotFoundError",
    "SessionNotFoundError",
    "TransactionRollbackError",
    "WorkflowExecutionError",
    "SynchronizationError",
    "ConfigurationValidationError",
    "SessionTimeoutError",
    "SessionCapacityError",
    "SessionPermissionError",
]