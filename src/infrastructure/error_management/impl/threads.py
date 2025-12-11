"""Threads模块错误处理器

为Thread操作提供统一的错误处理机制。
"""

from typing import Any, Dict, Optional
import time

from src.infrastructure.error_management import BaseErrorHandler, ErrorCategory, ErrorSeverity
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
    SynchronizationError
)
from src.interfaces.config import ConfigurationValidationError

# 延迟初始化logger以避免循环导入
logger = None

def _get_logger():
    global logger
    if logger is None:
        from src.interfaces.dependency_injection import get_logger
        logger = get_logger(__name__)
    return logger


class ThreadErrorHandler(BaseErrorHandler):
    """Thread模块错误处理器"""
    
    def __init__(self):
        """初始化Thread错误处理器"""
        super().__init__(ErrorCategory.STATE, ErrorSeverity.HIGH)
    
    def can_handle(self, error: Exception) -> bool:
        """检查是否可以处理该错误
        
        Args:
            error: 异常对象
            
        Returns:
            是否可以处理
        """
        return isinstance(error, (
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
        ))
    
    def handle(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """处理Thread相关错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        # 添加Thread特定的上下文信息
        enhanced_context = self._enhance_context(error, context)
        
        # 记录详细的错误信息
        self._log_thread_error(error, enhanced_context)
        
        # 根据错误类型采取不同的处理策略
        if isinstance(error, ThreadCreationError):
            self._handle_creation_error(error, enhanced_context)
        elif isinstance(error, ThreadNotFoundError):
            self._handle_not_found_error(error, enhanced_context)
        elif isinstance(error, ThreadRemovalError):
            self._handle_removal_error(error, enhanced_context)
        elif isinstance(error, SessionThreadInconsistencyError):
            self._handle_inconsistency_error(error, enhanced_context)
        elif isinstance(error, SynchronizationError):
            self._handle_synchronization_error(error, enhanced_context)
        elif isinstance(error, WorkflowExecutionError):
            self._handle_workflow_error(error, enhanced_context)
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
            "module": "threads",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": time.time()
        })
        
        # 根据错误类型添加特定信息
        if isinstance(error, (ThreadCreationError, ThreadNotFoundError, ThreadRemovalError)):
            enhanced_context["thread_id"] = getattr(error, 'thread_id', 'unknown')
        elif isinstance(error, SessionNotFoundError):
            enhanced_context["session_id"] = getattr(error, 'session_id', 'unknown')
        elif isinstance(error, DuplicateThreadNameError):
            enhanced_context["thread_name"] = getattr(error, 'thread_name', 'unknown')
        elif isinstance(error, WorkflowExecutionError):
            enhanced_context["workflow_id"] = getattr(error, 'workflow_id', 'unknown')
        
        return enhanced_context
    
    def _log_thread_error(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> None:
        """记录Thread错误日志
        
        Args:
            error: 异常对象
            context: 错误上下文
        """
        log = _get_logger()
        if isinstance(error, (SessionThreadInconsistencyError, TransactionRollbackError)):
            log.critical(
                f"Thread严重错误: {error}",
                extra={"context": context},
                exc_info=True
            )
        elif isinstance(error, (ThreadCreationError, ThreadRemovalError, WorkflowExecutionError)):
            log.error(
                f"Thread操作错误: {error}",
                extra={"context": context},
                exc_info=True
            )
        elif isinstance(error, (ThreadNotFoundError, SessionNotFoundError, AssociationNotFoundError)):
            log.warning(
                f"Thread未找到错误: {error}",
                extra={"context": context},
                exc_info=True
            )
        elif isinstance(error, (DuplicateThreadNameError, ConfigurationValidationError)):
            log.info(
                f"Thread验证错误: {error}",
                extra={"context": context},
                exc_info=True
            )
        else:
            log.error(
                f"Thread未知错误: {error}",
                extra={"context": context},
                exc_info=True
            )
    
    def _handle_creation_error(
        self, 
        error: ThreadCreationError, 
        context: Dict[str, Any]
    ) -> None:
        """处理Thread创建错误
        
        Args:
            error: Thread创建错误
            context: 错误上下文
        """
        _get_logger().error(f"Thread创建失败: {context.get('thread_id')}")
        
        # 创建错误可能需要重试或清理资源
        self._cleanup_failed_creation(context)
        
        # 创建错误通常需要抛出，因为Thread未成功创建
        raise error
    
    def _handle_not_found_error(
        self, 
        error: ThreadNotFoundError, 
        context: Dict[str, Any]
    ) -> None:
        """处理Thread未找到错误
        
        Args:
            error: Thread未找到错误
            context: 错误上下文
        """
        _get_logger().warning(f"Thread未找到: {context.get('thread_id')}")
        
        # 未找到错误可能需要创建默认Thread或返回空结果
        self._handle_missing_thread(context)
        
        # 根据严重度决定是否抛出异常
        if self.error_severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            raise error
    
    def _handle_removal_error(
        self, 
        error: ThreadRemovalError, 
        context: Dict[str, Any]
    ) -> None:
        """处理Thread移除错误
        
        Args:
            error: Thread移除错误
            context: 错误上下文
        """
        _get_logger().error(f"Thread移除失败: {context.get('thread_id')}")
        
        # 移除错误可能需要强制清理或标记为删除
        self._force_thread_removal(context)
        
        # 移除错误通常需要抛出
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
        _get_logger().critical(f"Session-Thread数据不一致")
        
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
        _get_logger().error(f"Thread同步失败")
        
        # 同步错误可能需要重试或重新同步
        self._resynchronize_thread(context)
        
        # 同步错误通常需要抛出
        raise error
    
    def _handle_workflow_error(
        self, 
        error: WorkflowExecutionError, 
        context: Dict[str, Any]
    ) -> None:
        """处理工作流执行错误
        
        Args:
            error: 工作流执行错误
            context: 错误上下文
        """
        _get_logger().error(f"Thread工作流执行失败: {context.get('workflow_id')}")
        
        # 工作流错误可能需要回滚或重试
        self._handle_workflow_failure(context)
        
        # 工作流错误通常需要抛出
        raise error
    
    def _cleanup_failed_creation(self, context: Dict[str, Any]) -> None:
        """清理失败的创建操作
        
        Args:
            context: 错误上下文
        """
        _get_logger().info("清理失败的Thread创建操作")
        # 这里可以实现具体的清理逻辑
    
    def _handle_missing_thread(self, context: Dict[str, Any]) -> None:
        """处理缺失的Thread
        
        Args:
            context: 错误上下文
        """
        _get_logger().info("处理缺失的Thread")
        # 这里可以实现具体的处理逻辑，如创建默认Thread
    
    def _force_thread_removal(self, context: Dict[str, Any]) -> None:
        """强制移除Thread
        
        Args:
            context: 错误上下文
        """
        _get_logger().info("强制移除Thread")
        # 这里可以实现具体的强制移除逻辑
    
    def _repair_inconsistency(self, context: Dict[str, Any]) -> None:
        """修复不一致性
        
        Args:
            context: 错误上下文
        """
        _get_logger().critical("修复Session-Thread不一致性")
        # 这里可以实现具体的修复逻辑
    
    def _resynchronize_thread(self, context: Dict[str, Any]) -> None:
        """重新同步Thread
        
        Args:
            context: 错误上下文
        """
        _get_logger().info("重新同步Thread")
        # 这里可以实现具体的重新同步逻辑
    
    def _handle_workflow_failure(self, context: Dict[str, Any]) -> None:
        """处理工作流失败
        
        Args:
            context: 错误上下文
        """
        _get_logger().info("处理Thread工作流失败")
        # 这里可以实现具体的工作流失败处理逻辑


class ThreadOperationHandler:
    """Thread操作处理器，提供带错误处理的操作包装"""
    
    @staticmethod
    def safe_thread_creation(
        creation_func,
        max_retries: int = 2,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """安全Thread创建，带重试机制
        
        Args:
            creation_func: 创建函数
            max_retries: 最大重试次数
            context: 操作上下文
            
        Returns:
            创建的Thread
            
        Raises:
            ThreadCreationError: 创建失败
        """
        from src.infrastructure.error_management import operation_with_retry
        
        operation_context = context or {}
        operation_context.update({
            "operation": "thread_creation",
            "max_retries": max_retries
        })
        
        try:
            return operation_with_retry(
                creation_func,
                max_retries=max_retries,
                retryable_exceptions=(ThreadCreationError,),
                context=operation_context
            )
        except Exception as e:
            from src.infrastructure.error_management import handle_error
            handle_error(e, operation_context)
            raise ThreadCreationError(
                session_id="unknown",
                thread_config=operation_context,
                cause=e
            ) from e
    
    @staticmethod
    def safe_thread_operation(
        operation_func,
        thread_id: str,
        fallback_func=None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """安全Thread操作，带降级机制
        
        Args:
            operation_func: 操作函数
            thread_id: Thread ID
            fallback_func: 降级函数
            context: 操作上下文
            
        Returns:
            操作结果
            
        Raises:
            ThreadNotFoundError: Thread未找到且无降级策略
        """
        from src.infrastructure.error_management import operation_with_fallback
        
        operation_context = context or {}
        operation_context.update({
            "operation": "thread_operation",
            "thread_id": thread_id
        })
        
        def _operation():
            return operation_func(thread_id)
        
        def _fallback():
            if fallback_func:
                return fallback_func(thread_id)
            raise ThreadNotFoundError(f"Thread未找到: {thread_id}")
        
        try:
            return operation_with_fallback(
                _operation,
                _fallback,
                fallback_exceptions=(ThreadNotFoundError,),
                context=operation_context
            )
        except Exception as e:
            from src.infrastructure.error_management import handle_error
            handle_error(e, operation_context)
            raise
    
    @staticmethod
    def safe_thread_state_transition(
        transition_func,
        thread_id: str,
        current_status: str,
        target_status: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """安全Thread状态转换
        
        Args:
            transition_func: 转换函数
            thread_id: Thread ID
            current_status: 当前状态
            target_status: 目标状态
            context: 操作上下文
            
        Returns:
            转换是否成功
            
        Raises:
            SynchronizationError: 状态转换失败
        """
        from src.infrastructure.error_management import safe_execution
        
        operation_context = context or {}
        operation_context.update({
            "operation": "thread_state_transition",
            "thread_id": thread_id,
            "current_status": current_status,
            "target_status": target_status
        })
        
        def _transition():
            return transition_func(thread_id, current_status, target_status)
        
        try:
            result = safe_execution(
                _transition,
                default_return=False,
                context=operation_context
            )
            return result if result is not None else False
        except Exception as e:
            from src.infrastructure.error_management import handle_error
            handle_error(e, operation_context)
            raise SynchronizationError(
                session_id="unknown",
                sync_operation="thread_state_transition",
                cause=e
            ) from e
    
    @staticmethod
    def safe_batch_thread_operation(
        operations: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """安全批处理Thread操作
        
        Args:
            operations: 操作字典 {thread_id: operation_func}
            context: 操作上下文
            
        Returns:
            操作结果字典
            
        Raises:
            TransactionRollbackError: 批处理失败
        """
        from src.infrastructure.error_management import safe_execution
        
        operation_context = context or {}
        operation_context.update({
            "operation": "batch_thread_operation",
            "thread_count": len(operations)
        })
        
        results = {}
        failed_operations = []
        
        for thread_id, operation in operations.items():
            thread_context = operation_context.copy()
            thread_context["thread_id"] = thread_id
            
            def _execute_operation():
                return operation(thread_id)
            
            try:
                result = safe_execution(
                    _execute_operation,
                    context=thread_context
                )
                if result is not None:
                    results[thread_id] = result
            except Exception as e:
                failed_operations.append(thread_id)
                from src.infrastructure.error_management import handle_error
                handle_error(e, thread_context)
        
        if failed_operations:
            error_msg = f"批处理操作失败，失败的Thread: {failed_operations}"
            from src.infrastructure.error_management import handle_error
            handle_error(Exception(error_msg), operation_context)
            raise TransactionRollbackError(
                operation_id=operation_context.get("operation", "batch_thread_operation"),
                rollback_errors=failed_operations
            )
        
        return results


# 注册线程错误处理器
def register_thread_error_handler():
    """注册线程错误处理器到统一错误处理框架"""
    from src.infrastructure.error_management import register_error_handler
    thread_handler = ThreadErrorHandler()
    
    # 定义线程异常类型
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
    
    # 注册各种线程异常的处理器
    for exception_type in thread_exceptions:
        register_error_handler(exception_type, thread_handler)
    
    _get_logger().info("线程错误处理器已注册到统一错误处理框架")