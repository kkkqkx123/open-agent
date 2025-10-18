"""全局错误处理器"""

import functools
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

from ..infrastructure.exceptions import InfrastructureError


class ErrorType(Enum):
    """错误类型枚举"""
    USER_ERROR = "user_error"      # 用户错误（配置错误、参数无效）
    SYSTEM_ERROR = "system_error"  # 系统错误（LLM调用失败、工具超时）
    FATAL_ERROR = "fatal_error"    # 致命错误（内存不足、配置文件损坏）
    NETWORK_ERROR = "network_error" # 网络错误
    VALIDATION_ERROR = "validation_error" # 验证错误
    TIMEOUT_ERROR = "timeout_error" # 超时错误
    PERMISSION_ERROR = "permission_error" # 权限错误
    UNKNOWN_ERROR = "unknown_error" # 未知错误


class ErrorContext:
    """错误上下文"""
    
    def __init__(
        self, 
        error_type: ErrorType, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ):
        """初始化错误上下文
        
        Args:
            error_type: 错误类型
            error: 异常对象
            context: 上下文信息
        """
        self.error_type = error_type
        self.error = error
        self.context = context or {}
        self.traceback = traceback.format_exc()
        self.timestamp: Optional[datetime] = None  # 将在处理时设置
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典表示
        """
        return {
            'error_type': self.error_type.value,
            'error_class': self.error.__class__.__name__,
            'error_message': str(self.error),
            'context': self.context,
            'traceback': self.traceback,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class IGlobalErrorHandler(ABC):
    """全局错误处理器接口"""
    
    @abstractmethod
    def handle_error(
        self, 
        error_type: ErrorType, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """处理错误并返回用户友好消息"""
        pass
    
    @abstractmethod
    def register_error_handler(
        self, 
        error_class: Type[Exception], 
        handler: Callable[[Exception], str]
    ) -> None:
        """注册自定义错误处理器"""
        pass
    
    @abstractmethod
    def wrap_with_error_handler(self, func: Callable) -> Callable:
        """用错误处理器包装函数"""
        pass
    
    @abstractmethod
    def get_error_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取错误历史"""
        pass
    
    @abstractmethod
    def clear_error_history(self) -> None:
        """清除错误历史"""
        pass


class GlobalErrorHandler(IGlobalErrorHandler):
    """全局错误处理器实现"""
    
    def __init__(self, max_history: int = 1000):
        """初始化全局错误处理器
        
        Args:
            max_history: 最大错误历史记录数
        """
        self.max_history = max_history
        
        # 错误处理器映射
        self._error_handlers: Dict[Type[Exception], Callable[[Exception], str]] = {}
        
        # 错误类型映射
        self._error_type_mapping: Dict[Type[Exception], ErrorType] = {
            ValueError: ErrorType.USER_ERROR,
            TypeError: ErrorType.USER_ERROR,
            KeyError: ErrorType.USER_ERROR,
            AttributeError: ErrorType.USER_ERROR,
            InfrastructureError: ErrorType.SYSTEM_ERROR,
            ConnectionError: ErrorType.NETWORK_ERROR,
            TimeoutError: ErrorType.TIMEOUT_ERROR,
            PermissionError: ErrorType.PERMISSION_ERROR,
            FileNotFoundError: ErrorType.USER_ERROR,
            ImportError: ErrorType.SYSTEM_ERROR,
            MemoryError: ErrorType.FATAL_ERROR,
        }
        
        # 错误历史
        self._error_history: List[ErrorContext] = []
        
        # 用户友好消息模板
        self._error_messages = {
            ErrorType.USER_ERROR: "输入参数有误：{error_message}",
            ErrorType.SYSTEM_ERROR: "系统内部错误：{error_message}",
            ErrorType.FATAL_ERROR: "严重系统错误：{error_message}",
            ErrorType.NETWORK_ERROR: "网络连接错误：{error_message}",
            ErrorType.VALIDATION_ERROR: "数据验证失败：{error_message}",
            ErrorType.TIMEOUT_ERROR: "操作超时：{error_message}",
            ErrorType.PERMISSION_ERROR: "权限不足：{error_message}",
            ErrorType.UNKNOWN_ERROR: "未知错误：{error_message}",
        }
        
        # 注册默认错误处理器
        self._register_default_handlers()
    
    def handle_error(
        self, 
        error_type: ErrorType, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """处理错误并返回用户友好消息"""
        import datetime
        
        # 创建错误上下文
        error_context = ErrorContext(error_type, error, context)
        error_context.timestamp = datetime.datetime.now()
        
        # 添加到错误历史
        self._add_to_history(error_context)
        
        # 查找自定义错误处理器
        error_class = error.__class__
        for registered_class, handler in self._error_handlers.items():
            if issubclass(error_class, registered_class):
                try:
                    return handler(error)
                except Exception:
                    # 如果自定义处理器出错，使用默认处理
                    break
        
        # 使用默认消息模板
        message_template = self._error_messages.get(error_type, self._error_messages[ErrorType.UNKNOWN_ERROR])
        user_message = message_template.format(error_message=str(error))
        
        return user_message
    
    def register_error_handler(
        self, 
        error_class: Type[Exception], 
        handler: Callable[[Exception], str]
    ) -> None:
        """注册自定义错误处理器"""
        self._error_handlers[error_class] = handler
    
    def wrap_with_error_handler(self, func: Callable) -> Callable:
        """用错误处理器包装函数"""
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 确定错误类型
                error_type = self._classify_error(e)
                
                # 处理错误
                user_message = self.handle_error(
                    error_type, 
                    e, 
                    {
                        'function': func.__name__,
                        'module': func.__module__,
                        'args': str(args)[:100],  # 限制长度
                        'kwargs': str(kwargs)[:100]  # 限制长度
                    }
                )
                
                # 重新抛出异常或返回错误结果
                # 这里选择重新抛出，让调用者决定如何处理
                raise RuntimeError(user_message) from e
        
        return wrapper
    
    def get_error_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取错误历史"""
        return [context.to_dict() for context in self._error_history[-limit:]]
    
    def clear_error_history(self) -> None:
        """清除错误历史"""
        self._error_history.clear()
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """分类错误
        
        Args:
            error: 异常对象
            
        Returns:
            错误类型
        """
        error_class = error.__class__
        
        # 查找精确匹配
        if error_class in self._error_type_mapping:
            return self._error_type_mapping[error_class]
        
        # 查找父类匹配
        for mapped_class, error_type in self._error_type_mapping.items():
            if issubclass(error_class, mapped_class):
                return error_type
        
        # 默认为未知错误
        return ErrorType.UNKNOWN_ERROR
    
    def _add_to_history(self, error_context: ErrorContext) -> None:
        """添加到错误历史
        
        Args:
            error_context: 错误上下文
        """
        self._error_history.append(error_context)
        
        # 限制历史记录数量
        if len(self._error_history) > self.max_history:
            self._error_history = self._error_history[-self.max_history:]
    
    def _register_default_handlers(self) -> None:
        """注册默认错误处理器"""
        # 配置错误处理器
        def handle_config_error(error: Exception) -> str:
            return f"配置错误：请检查配置文件，{str(error)}"
        
        # 网络错误处理器
        def handle_network_error(error: Exception) -> str:
            return "网络连接失败，请检查网络连接后重试"
        
        # 超时错误处理器
        def handle_timeout_error(error: Exception) -> str:
            return "操作超时，请稍后重试"
        
        # 注册处理器
        self.register_error_handler(InfrastructureError, handle_config_error)
        self.register_error_handler(ConnectionError, handle_network_error)
        self.register_error_handler(TimeoutError, handle_timeout_error)
    
    def set_error_message(self, error_type: ErrorType, message_template: str) -> None:
        """设置错误消息模板
        
        Args:
            error_type: 错误类型
            message_template: 消息模板，可以使用{error_message}占位符
        """
        self._error_messages[error_type] = message_template
    
    def register_error_type_mapping(
        self, 
        error_class: Type[Exception], 
        error_type: ErrorType
    ) -> None:
        """注册错误类型映射
        
        Args:
            error_class: 异常类
            error_type: 错误类型
        """
        self._error_type_mapping[error_class] = error_type
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计
        
        Returns:
            错误统计字典
        """
        from collections import Counter
        
        # 统计错误类型
        error_type_counts = Counter(context.error_type.value for context in self._error_history)
        
        # 统计错误类
        error_class_counts = Counter(context.error.__class__.__name__ for context in self._error_history)
        
        return {
            'total_errors': len(self._error_history),
            'error_types': dict(error_type_counts),
            'error_classes': dict(error_class_counts),
            'recent_errors': [context.to_dict() for context in self._error_history[-10:]]
        }


# 全局错误处理器实例
_global_error_handler: Optional[GlobalErrorHandler] = None


def get_global_error_handler() -> GlobalErrorHandler:
    """获取全局错误处理器实例
    
    Returns:
        全局错误处理器实例
    """
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = GlobalErrorHandler()
    return _global_error_handler


def handle_error(
    error_type: ErrorType, 
    error: Exception, 
    context: Optional[Dict[str, Any]] = None
) -> str:
    """处理错误的便捷函数
    
    Args:
        error_type: 错误类型
        error: 异常对象
        context: 上下文信息
        
    Returns:
        用户友好消息
    """
    return get_global_error_handler().handle_error(error_type, error, context)


def register_error_handler(
    error_class: Type[Exception], 
    handler: Callable[[Exception], str]
) -> None:
    """注册错误处理器的便捷函数
    
    Args:
        error_class: 异常类
        handler: 处理器函数
    """
    get_global_error_handler().register_error_handler(error_class, handler)


def error_handler(error_type: Optional[ErrorType] = None) -> Callable[[Callable], Callable]:
    """错误处理装饰器
    
    Args:
        error_type: 错误类型，如果为None则自动分类
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 确定错误类型
                if error_type is None:
                    classified_type = get_global_error_handler()._classify_error(e)
                else:
                    classified_type = error_type
                
                # 处理错误
                user_message = get_global_error_handler().handle_error(
                    classified_type, 
                    e, 
                    {
                        'function': func.__name__,
                        'module': func.__module__,
                        'args': str(args)[:100],
                        'kwargs': str(kwargs)[:100]
                    }
                )
                
                # 重新抛出异常
                raise RuntimeError(user_message) from e
        
        return wrapper
    return decorator