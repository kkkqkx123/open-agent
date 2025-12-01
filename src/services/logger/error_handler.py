"""服务层错误处理器"""

from typing import Any, Callable, Union, Optional

from ...core.logger.error_handler import BaseErrorHandler, ErrorType
from .logger import get_logger


class GlobalErrorHandler(BaseErrorHandler):
    """全局错误处理器实现"""
    
    def __init__(self, logger: Optional[Any] = None):
        """初始化错误处理器
        
        Args:
            logger: 日志记录器
        """
        super().__init__(logger or get_logger("ErrorHandler"))


# 全局错误处理器实例
_global_error_handler: Optional[GlobalErrorHandler] = None


def get_global_error_handler() -> GlobalErrorHandler:
    """获取全局错误处理器
    
    Returns:
        全局错误处理器实例
    """
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = GlobalErrorHandler()
    return _global_error_handler


def handle_error(error: Union[Exception, str], error_type: ErrorType = ErrorType.APPLICATION_ERROR, **context: Any) -> None:
    """处理错误的便捷函数
    
    Args:
        error: 错误对象或错误消息
        error_type: 错误类型
        **context: 上下文信息
    """
    handler = get_global_error_handler()
    handler.handle_error(error, error_type, **context)


def register_error_handler(error_type: ErrorType, handler: Callable) -> None:
    """注册错误处理程序的便捷函数
    
    Args:
        error_type: 错误类型
        handler: 处理程序
    """
    error_handler_instance = get_global_error_handler()
    error_handler_instance.register_handler(error_type, handler)


def error_handler(error_type: ErrorType) -> Callable:
    """错误处理器装饰器
    
    Args:
        error_type: 错误类型
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(e, error_type, function=func.__name__, args=args, kwargs=kwargs)
                raise
        return wrapper
    return decorator