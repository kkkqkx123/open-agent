"""Sessions模块错误处理器
 
为Session操作提供统一的错误处理机制。
"""

from typing import Any, Dict, Optional
import time

from src.interfaces.dependency_injection import get_logger
from src.infrastructure.error_management import BaseErrorHandler, ErrorCategory, ErrorSeverity
from src.interfaces.sessions.exceptions import (
    SessionThreadException,
    SessionNotFoundError,
    ThreadNotFoundError,
    AssociationNotFoundError,
    SessionThreadInconsistencyError,
    TransactionRollbackError,
    WorkflowExecutionError,
    SynchronizationError
)
from src.interfaces.config import ConfigurationValidationError

logger = get_logger(__name__)


class SessionErrorHandler(BaseErrorHandler):
    """Session模块错误处理器"""
    
    def __init__(self):
        """初始化Session错误处理器"""
        super().__init__(ErrorCategory.STATE, ErrorSeverity.MEDIUM)
    
    def can_handle(self, error: Exception) -> bool:
        """检查是否可以处理该错误
        
        Args:
            error: 异常对象
            
        Returns:
            是否可以处理
        """
        return isinstance(error, (
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
        ))
    
    def handle(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """处理Session相关错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        # 添加Session特定的上下文信息
        enhanced_context = self._enhance_context(error, context)
        
        # 记录详细的错误信息
        self._log_session_error(error, enhanced_context)
        
        # 根据错误类型采取不同的处理策略
        if isinstance(error, SessionNotFoundError):
            self._handle_session_not_found_error(error, enhanced_context)
        elif isinstance(error, AssociationNotFoundError):
            self._handle_association_not_found_error(error, enhanced_context)
        elif isinstance(error, SessionThreadInconsistencyError):
            self._handle_inconsistency_error(error, enhanced_context)
        elif isinstance(error, SynchronizationError):
            self._handle_synchronization_error(error, enhanced_context)
        elif isinstance(error, ValueError):
            self._handle_validation_error(error, enhanced_context)
        else:
            # 调用基类处理
            super().handle(error, enhanced_context)
    
    def _enhance_context(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """增强错误上下文信息
        
        Args:
            error: 异常对象
            context: 原始上下文
            
        Returns:
            增强后的上下文
        """
        enhanced_context = context or {}
        enhanced_context.update({
            "module": "sessions",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": time.time()
        })
        
        # 根据错误类型添加特定信息
        if isinstance(error, SessionNotFoundError):
            enhanced_context["session_id"] = getattr(error, 'session_id', 'unknown')
        elif isinstance(error, ThreadNotFoundError):
            enhanced_context["thread_id"] = getattr(error, 'thread_id', 'unknown')
        elif isinstance(error, AssociationNotFoundError):
            enhanced_context["association_id"] = getattr(error, 'association_id', 'unknown')
        elif isinstance(error, ValueError):
            # 处理association.py中的ValueError
            if "session_id" in str(error):
                enhanced_context["validation_field"] = "session_id"
            elif "thread_id" in str(error):
                enhanced_context["validation_field"] = "thread_id"
            elif "thread_name" in str(error):
                enhanced_context["validation_field"] = "thread_name"
        
        return enhanced_context
    
    def _log_session_error(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> None:
        """记录Session错误日志
        
        Args:
            error: 异常对象
            context: 错误上下文
        """
        if isinstance(error, (SessionThreadInconsistencyError, TransactionRollbackError)):
            logger.critical(
                f"Session严重错误: {error}",
                extra={"context": context},
                exc_info=True
            )
        elif isinstance(error, (SessionNotFoundError, AssociationNotFoundError)):
            logger.warning(
                f"Session未找到错误: {error}",
                extra={"context": context},
                exc_info=True
            )
        elif isinstance(error, (SynchronizationError, WorkflowExecutionError)):
            logger.error(
                f"Session操作错误: {error}",
                extra={"context": context},
                exc_info=True
            )
        elif isinstance(error, (ValueError, ConfigurationValidationError)):
            logger.info(
                f"Session验证错误: {error}",
                extra={"context": context},
                exc_info=True
            )
        else:
            logger.error(
                f"Session未知错误: {error}",
                extra={"context": context},
                exc_info=True
            )
    
    def _handle_session_not_found_error(
        self, 
        error: SessionNotFoundError, 
        context: Dict[str, Any]
    ) -> None:
        """处理Session未找到错误
        
        Args:
            error: Session未找到错误
            context: 错误上下文
        """
        logger.warning(f"Session未找到: {context.get('session_id')}")
        
        # 未找到错误可能需要创建默认Session或返回空结果
        self._handle_missing_session(context)
        
        # 根据严重度决定是否抛出异常
        if self.error_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            raise error
    
    def _handle_association_not_found_error(
        self, 
        error: AssociationNotFoundError, 
        context: Dict[str, Any]
    ) -> None:
        """处理关联未找到错误
        
        Args:
            error: 关联未找到错误
            context: 错误上下文
        """
        logger.warning(f"Session-Thread关联未找到: {context.get('association_id')}")
        
        # 关联未找到可能需要创建新关联或返回空结果
        self._handle_missing_association(context)
        
        # 根据严重度决定是否抛出异常
        if self.error_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            raise error
    
    def _handle_inconsistency_error(
        self, 
        error: SessionThreadInconsistencyError, 
        context: Dict[str, Any]
    ) -> None:
        """处理Session-Thread不一致错误
        
        Args:
            error: Session-Thread不一致错误
            context: 错误上下文
        """
        logger.critical(f"Session-Thread数据不一致")
        
        # 不一致错误需要立即修复
        self._repair_inconsistency(context)
        
        # 不一致错误总是抛出
        raise error
    
    def _handle_synchronization_error(
        self, 
        error: SynchronizationError, 
        context: Dict[str, Any]
    ) -> None:
        """处理同步错误
        
        Args:
            error: 同步错误
            context: 错误上下文
        """
        logger.error(f"Session同步失败")
        
        # 同步错误可能需要重试或重新同步
        self._resynchronize_session(context)
        
        # 同步错误通常需要抛出
        raise error
    
    def _handle_validation_error(
        self, 
        error: ValueError, 
        context: Dict[str, Any]
    ) -> None:
        """处理验证错误
        
        Args:
            error: 验证错误
            context: 错误上下文
        """
        logger.info(f"Session数据验证失败: {context.get('validation_field')}")
        
        # 验证错误可能需要修复数据或提供默认值
        self._fix_validation_error(context)
        
        # 验证错误的严重度可能较低，可以根据具体情况决定是否抛出
        if self.error_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            raise error
    
    def _handle_missing_session(self, context: Dict[str, Any]) -> None:
        """处理缺失的Session
        
        Args:
            context: 错误上下文
        """
        logger.info("处理缺失的Session")
        # 这里可以实现具体的处理逻辑，如创建默认Session
    
    def _handle_missing_association(self, context: Dict[str, Any]) -> None:
        """处理缺失的关联
        
        Args:
            context: 错误上下文
        """
        logger.info("处理缺失的Session-Thread关联")
        # 这里可以实现具体的处理逻辑，如创建新关联
    
    def _repair_inconsistency(self, context: Dict[str, Any]) -> None:
        """修复不一致性
        
        Args:
            context: 错误上下文
        """
        logger.critical("修复Session-Thread不一致性")
        # 这里可以实现具体的修复逻辑
    
    def _resynchronize_session(self, context: Dict[str, Any]) -> None:
        """重新同步Session
        
        Args:
            context: 错误上下文
        """
        logger.info("重新同步Session")
        # 这里可以实现具体的重新同步逻辑
    
    def _fix_validation_error(self, context: Dict[str, Any]) -> None:
        """修复验证错误
        
        Args:
            context: 错误上下文
        """
        logger.info("修复Session验证错误")
        # 这里可以实现具体的验证错误修复逻辑


class SessionOperationHandler:
    """Session操作处理器，提供带错误处理的操作包装"""
    
    @staticmethod
    def safe_session_creation(
        creation_func,
        user_id: Optional[str] = None,
        max_retries: int = 2,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """安全Session创建，带重试机制
        
        Args:
            creation_func: 创建函数
            user_id: 用户ID
            max_retries: 最大重试次数
            context: 操作上下文
            
        Returns:
            创建的Session
            
        Raises:
            SessionNotFoundError: 创建失败
        """
        from src.infrastructure.error_management import operation_with_retry
        
        operation_context = context or {}
        operation_context.update({
            "operation": "session_creation",
            "user_id": user_id,
            "max_retries": max_retries
        })
        
        try:
            return operation_with_retry(
                lambda: creation_func(user_id),
                max_retries=max_retries,
                retryable_exceptions=(SessionNotFoundError,),
                context=operation_context
            )
        except Exception as e:
            from src.infrastructure.error_management import handle_error
            handle_error(e, operation_context)
            raise SessionNotFoundError(f"Session创建失败: {e}") from e
    
    @staticmethod
    def safe_session_operation(
        operation_func,
        session_id: str,
        fallback_func=None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """安全Session操作，带降级机制
        
        Args:
            operation_func: 操作函数
            session_id: Session ID
            fallback_func: 降级函数
            context: 操作上下文
            
        Returns:
            操作结果
            
        Raises:
            SessionNotFoundError: Session未找到且无降级策略
        """
        from src.infrastructure.error_management import operation_with_fallback
        
        operation_context = context or {}
        operation_context.update({
            "operation": "session_operation",
            "session_id": session_id
        })
        
        def _operation():
            return operation_func(session_id)
        
        def _fallback():
            if fallback_func:
                return fallback_func(session_id)
            raise SessionNotFoundError(f"Session未找到: {session_id}")
        
        try:
            return operation_with_fallback(
                _operation,
                _fallback,
                fallback_exceptions=(SessionNotFoundError,),
                context=operation_context
            )
        except Exception as e:
            from src.infrastructure.error_management import handle_error
            handle_error(e, operation_context)
            raise
    
    @staticmethod
    def safe_association_creation(
        creation_func,
        session_id: str,
        thread_id: str,
        thread_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """安全关联创建，带验证机制
        
        Args:
            creation_func: 创建函数
            session_id: Session ID
            thread_id: Thread ID
            thread_name: Thread名称
            context: 操作上下文
            
        Returns:
            创建的关联
            
        Raises:
            AssociationNotFoundError: 关联创建失败
        """
        from src.infrastructure.error_management import safe_execution
        
        operation_context = context or {}
        operation_context.update({
            "operation": "association_creation",
            "session_id": session_id,
            "thread_id": thread_id,
            "thread_name": thread_name
        })
        
        def _validate_inputs():
            if not session_id:
                raise ValueError("session_id cannot be empty")
            if not thread_id:
                raise ValueError("thread_id cannot be empty")
            if not thread_name:
                raise ValueError("thread_name cannot be empty")
        
        def _create_association():
            _validate_inputs()
            return creation_func(session_id, thread_id, thread_name)
        
        try:
            return safe_execution(
                _create_association,
                context=operation_context
            )
        except Exception as e:
            from src.infrastructure.error_management import handle_error
            handle_error(e, operation_context)
            raise AssociationNotFoundError(
                session_id,
                thread_id,
                cause=e
            ) from e
    
    @staticmethod
    def safe_user_interaction(
        interaction_func,
        session_id: str,
        interaction_type: str,
        content: str,
        thread_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """安全用户交互处理
        
        Args:
            interaction_func: 交互函数
            session_id: Session ID
            interaction_type: 交互类型
            content: 交互内容
            thread_id: Thread ID
            context: 操作上下文
            
        Returns:
            交互结果
            
        Raises:
            SessionNotFoundError: Session未找到
        """
        from src.infrastructure.error_management import safe_execution
        
        operation_context = context or {}
        operation_context.update({
            "operation": "user_interaction",
            "session_id": session_id,
            "interaction_type": interaction_type,
            "thread_id": thread_id
        })
        
        def _handle_interaction():
            return interaction_func(session_id, interaction_type, content, thread_id)
        
        try:
            return safe_execution(
                _handle_interaction,
                context=operation_context
            )
        except Exception as e:
            from src.infrastructure.error_management import handle_error
            handle_error(e, operation_context)
            raise SessionNotFoundError(f"用户交互处理失败: {e}") from e
    
    @staticmethod
    def safe_session_state_update(
        update_func,
        session_id: str,
        new_status: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """安全Session状态更新
        
        Args:
            update_func: 更新函数
            session_id: Session ID
            new_status: 新状态
            context: 操作上下文
            
        Returns:
            更新是否成功
        """
        from src.infrastructure.error_management import safe_execution
        
        operation_context = context or {}
        operation_context.update({
            "operation": "session_state_update",
            "session_id": session_id,
            "new_status": new_status
        })
        
        def _update_state():
            return update_func(session_id, new_status)
        
        try:
            result = safe_execution(
                _update_state,
                default_return=False,
                context=operation_context
            )
            return result if result is not None else False
        except Exception as e:
            from src.infrastructure.error_management import handle_error
            handle_error(e, operation_context)
            return False


# 注册会话错误处理器
def register_session_error_handler():
    """注册会话错误处理器到统一错误处理框架"""
    from src.infrastructure.error_management import register_error_handler
    session_handler = SessionErrorHandler()
    
    # 注册各种会话异常的处理器
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
        ValueError
    ]
    
    for exception_type in session_exceptions:
        register_error_handler(exception_type, session_handler)
    
    logger.info("会话错误处理器已注册到统一错误处理框架")