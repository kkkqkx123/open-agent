"""标准错误处理模式"""

import time
from typing import Any, Callable, Dict, Optional, Tuple, Type

from .error_category import ErrorCategory
from .error_severity import ErrorSeverity


def operation_with_retry(
    operation: Callable,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (IOError, TimeoutError),
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """带重试的操作执行模式
    
    Args:
        operation: 要执行的操作
        max_retries: 最大重试次数
        backoff_factor: 退避因子
        retryable_exceptions: 可重试的异常类型
        context: 操作上下文
        
    Returns:
        操作结果
        
    Raises:
        OperationError: 所有重试都失败后抛出
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return operation()
        except retryable_exceptions as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                print(f"操作失败，{wait_time}秒后重试: {e}")
                time.sleep(wait_time)
        except Exception as e:
            # 不可重试的错误 - 直接抛出
            raise
    
    # 所有重试都失败
    raise OperationError(
        f"操作在重试{max_retries}次后失败",
        details={"last_error": str(last_error), "context": context}
    ) from last_error


def operation_with_fallback(
    primary_operation: Callable,
    fallback_operation: Callable,
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """带降级的操作执行模式
    
    Args:
        primary_operation: 主操作
        fallback_operation: 降级操作
        context: 操作上下文
        
    Returns:
        操作结果
        
    Raises:
        OperationError: 主操作和降级都失败后抛出
    """
    try:
        return primary_operation()
    except (TimeoutError, ServiceUnavailableError) as e:
        print(f"主操作失败，尝试降级: {e}")
        try:
            return fallback_operation()
        except Exception as fallback_error:
            raise OperationError(
                f"主操作和降级都失败",
                details={
                    "primary_error": str(e),
                    "fallback_error": str(fallback_error),
                    "context": context
                }
            ) from fallback_error


def safe_execution(
    operation: Callable,
    validation_func: Optional[Callable] = None,
    cleanup_func: Optional[Callable] = None,
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """安全执行模式
    
    Args:
        operation: 要执行的操作
        validation_func: 验证函数
        cleanup_func: 清理函数
        context: 操作上下文
        
    Returns:
        操作结果
        
    Raises:
        OperationError: 操作失败后抛出
    """
    try:
        # 输入验证
        if validation_func:
            validation_func()
        
        # 执行操作
        result = operation()
        
        # 结果验证
        if validation_func:
            validation_func(result)
        
        return result
        
    except DomainSpecificError:
        # 预期的业务错误 - 直接重新抛出
        raise
        
    except Exception as e:
        # 意外错误 - 包装后抛出
        print(f"操作失败: {e}")
        
        # 执行清理操作
        if cleanup_func:
            try:
                cleanup_func()
            except Exception as cleanup_error:
                print(f"清理操作失败: {cleanup_error}")
        
        raise OperationError(
            f"操作失败: {e}",
            details={"original_error": str(e), "context": context}
        ) from e


class OperationError(Exception):
    """操作错误异常"""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.details = details or {}


class ServiceUnavailableError(Exception):
    """服务不可用异常"""
    pass


class DomainSpecificError(Exception):
    """领域特定错误基类"""
    pass