"""存储错误处理器

提供统一的存储错误处理功能。
"""

import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

from src.core.state.exceptions import (
    StorageError, 
    StorageConnectionError, 
    StorageTimeoutError,
    StorageTransactionError
)

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


class StorageErrorHandler:
    """统一的存储错误处理器
    
    提供存储错误的分类和处理。
    """
    
    @staticmethod
    def handle_storage_error(operation: str, error: Exception) -> StorageError:
        """处理存储错误
        
        Args:
            operation: 操作名称
            error: 原始异常
            
        Returns:
            分类后的存储错误
        """
        logger.error(f"Storage operation {operation} failed: {error}")
        
        # 根据异常类型进行分类
        if isinstance(error, ConnectionError):
            return StorageConnectionError(f"Connection failed during {operation}: {error}")
        elif isinstance(error, TimeoutError):
            return StorageTimeoutError(f"Timeout during {operation}: {error}")
        elif "transaction" in str(error).lower():
            return StorageTransactionError(f"Transaction error during {operation}: {error}")
        elif isinstance(error, StorageError):
            # 已经是存储错误，直接返回
            return error
        else:
            return StorageError(f"Storage operation {operation} failed: {error}")
    
    @staticmethod
    def handle_async_storage_error(operation: str, error: Exception) -> StorageError:
        """处理异步存储错误
        
        Args:
            operation: 操作名称
            error: 原始异常
            
        Returns:
            分类后的存储错误
        """
        # 异步错误的特殊处理
        if "CancelledError" in str(type(error)):
            return StorageTimeoutError(f"Operation {operation} was cancelled: {error}")
        elif "asyncio" in str(type(error)):
            return StorageError(f"Async error during {operation}: {error}")
        
        return StorageErrorHandler.handle_storage_error(operation, error)


def with_error_handling(operation_name: Optional[str] = None, 
                       return_on_error: Optional[Any] = None,
                       reraise: bool = True):
    """错误处理装饰器
    
    Args:
        operation_name: 操作名称，如果为None则使用函数名
        return_on_error: 发生错误时的返回值
        reraise: 是否重新抛出异常
        
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        op_name = operation_name or func.__name__
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                storage_error = StorageErrorHandler.handle_storage_error(op_name, e)
                if reraise:
                    raise storage_error
                else:
                    logger.warning(f"Suppressing error in {op_name}: {storage_error}")
                    return return_on_error
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                storage_error = StorageErrorHandler.handle_async_storage_error(op_name, e)
                if reraise:
                    raise storage_error
                else:
                    logger.warning(f"Suppressing error in {op_name}: {storage_error}")
                    return return_on_error
        
        # 根据函数类型返回相应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore
    
    return decorator


def safe_execute(func: Callable[..., Any], 
                *args, 
                operation_name: Optional[str] = None,
                default_return: Optional[Any] = None,
                **kwargs) -> Any:
    """安全执行函数
    
    Args:
        func: 要执行的函数
        *args: 位置参数
        operation_name: 操作名称
        default_return: 默认返回值
        **kwargs: 关键字参数
        
    Returns:
        函数执行结果或默认返回值
    """
    op_name = operation_name or func.__name__
    try:
        return func(*args, **kwargs)
    except Exception as e:
        storage_error = StorageErrorHandler.handle_storage_error(op_name, e)
        logger.warning(f"Safe execution failed for {op_name}: {storage_error}")
        return default_return


async def safe_execute_async(func: Callable[..., Any], 
                           *args, 
                           operation_name: Optional[str] = None,
                           default_return: Optional[Any] = None,
                           **kwargs) -> Any:
    """安全执行异步函数
    
    Args:
        func: 要执行的异步函数
        *args: 位置参数
        operation_name: 操作名称
        default_return: 默认返回值
        **kwargs: 关键字参数
        
    Returns:
        函数执行结果或默认返回值
    """
    op_name = operation_name or func.__name__
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        storage_error = StorageErrorHandler.handle_async_storage_error(op_name, e)
        logger.warning(f"Safe async execution failed for {op_name}: {storage_error}")
        return default_return


class RetryHandler:
    """重试处理器
    
    提供操作重试功能。
    """
    
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
        """初始化重试处理器
        
        Args:
            max_retries: 最大重试次数
            delay: 初始延迟时间（秒）
            backoff: 退避倍数
        """
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff
    
    def retry(self, operation_name: Optional[str] = None, 
              retry_on: Optional[tuple] = None):
        """重试装饰器
        
        Args:
            operation_name: 操作名称
            retry_on: 需要重试的异常类型
            
        Returns:
            装饰器函数
        """
        def decorator(func: F) -> F:
            op_name = operation_name or func.__name__
            retry_exceptions = retry_on or (StorageConnectionError, StorageTimeoutError)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                current_delay = self.delay
                
                for attempt in range(self.max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        
                        if not isinstance(e, retry_exceptions) or attempt == self.max_retries:
                            break
                        
                        logger.warning(f"Attempt {attempt + 1} failed for {op_name}: {e}. "
                                    f"Retrying in {current_delay}s...")
                        import time
                        time.sleep(current_delay)
                        current_delay *= self.backoff
                
                # 所有重试都失败了
                storage_error = StorageErrorHandler.handle_storage_error(op_name, last_exception)
                raise storage_error
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                current_delay = self.delay
                
                for attempt in range(self.max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        
                        if not isinstance(e, retry_exceptions) or attempt == self.max_retries:
                            break
                        
                        logger.warning(f"Attempt {attempt + 1} failed for {op_name}: {e}. "
                                    f"Retrying in {current_delay}s...")
                        await asyncio.sleep(current_delay)
                        current_delay *= self.backoff
                
                # 所有重试都失败了
                storage_error = StorageErrorHandler.handle_async_storage_error(op_name, last_exception)
                raise storage_error
            
            # 根据函数类型返回相应的包装器
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper  # type: ignore
            else:
                return sync_wrapper  # type: ignore
        
        return decorator