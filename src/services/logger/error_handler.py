"""错误处理服务"""

import sys
import traceback
from enum import Enum
from typing import Any, Callable, Dict, Optional, Union
from datetime import datetime
from abc import ABC, abstractmethod

from ...core.logger.log_level import LogLevel


class ErrorType(Enum):
    """错误类型枚举"""
    APPLICATION_ERROR = "application_error"
    CONFIGURATION_ERROR = "configuration_error"
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    SECURITY_ERROR = "security_error"


class IGlobalErrorHandler(ABC):
    """全局错误处理器接口"""
    
    @abstractmethod
    def handle_error(self, error: Union[Exception, str], error_type: ErrorType = ErrorType.APPLICATION_ERROR, **context: Any) -> None:
        """处理错误
        
        Args:
            error: 错误对象或错误消息
            error_type: 错误类型
            **context: 上下文信息
        """
        pass


class BaseErrorHandler(IGlobalErrorHandler):
    """基础错误处理器实现"""
    
    def __init__(self, logger: Optional[Any] = None) -> None:
        """初始化错误处理器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self._handlers: Dict[ErrorType, Callable] = {}
    
    def handle_error(self, error: Union[Exception, str], error_type: ErrorType = ErrorType.APPLICATION_ERROR, **context: Any) -> None:
        """处理错误
        
        Args:
            error: 错误对象或错误消息
            error_type: 错误类型
            **context: 上下文信息
        """
        # 构建错误信息
        error_info = self._build_error_info(error, error_type, **context)
        
        # 记录错误日志
        if self.logger:
            self.logger.error(
                f"错误处理: {error_info['message']}",
                error_type=error_type.value,
                error_info=error_info
            )
        else:
            # 如果没有日志记录器，输出到stderr
            print(f"错误处理: {error_info['message']}", file=sys.stderr)
        
        # 执行特定错误类型的处理程序
        if error_type in self._handlers:
            try:
                self._handlers[error_type](error, **context)
            except Exception as handler_error:
                if self.logger:
                    self.logger.error(f"错误处理器执行失败: {handler_error}")
                else:
                    print(f"错误处理器执行失败: {handler_error}", file=sys.stderr)
    
    def _build_error_info(self, error: Union[Exception, str], error_type: ErrorType, **context: Any) -> Dict[str, Any]:
        """构建错误信息
        
        Args:
            error: 错误对象或错误消息
            error_type: 错误类型
            **context: 上下文信息
            
        Returns:
            错误信息字典
        """
        error_info = {
            "type": error_type.value,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        
        if isinstance(error, Exception):
            error_info["message"] = str(error)
            error_info["exception_type"] = type(error).__name__
            error_info["traceback"] = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        else:
            error_info["message"] = error
            error_info["exception_type"] = "StringError"
            error_info["traceback"] = "".join(traceback.format_stack())
        
        return error_info
    
    def register_handler(self, error_type: ErrorType, handler: Callable) -> None:
        """注册错误处理程序
        
        Args:
            error_type: 错误类型
            handler: 处理程序
        """
        self._handlers[error_type] = handler


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


# 临时导入，稍后会重构
def get_logger(name: str):
    """临时函数，稍后会移除"""
    from .logger import get_logger as _get_logger
    return _get_logger(name)