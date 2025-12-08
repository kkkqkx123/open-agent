"""
错误处理器

提供统一的错误处理机制。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Type
from dataclasses import dataclass
from enum import Enum

from src.services.logger.injection import get_logger
from src.interfaces.llm.converters import IConversionContext


class ErrorSeverity(Enum):
    """错误严重程度"""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorInfo:
    """错误信息"""
    
    error: Exception
    severity: ErrorSeverity
    context: Optional[IConversionContext] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None
    retry_count: int = 0
    
    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            import time
            self.timestamp = time.time()


class IErrorHandler(ABC):
    """错误处理器接口"""
    
    @abstractmethod
    def can_handle(self, error: Exception) -> bool:
        """检查是否可以处理该错误
        
        Args:
            error: 错误对象
            
        Returns:
            bool: 是否可以处理
        """
        pass
    
    @abstractmethod
    def handle(self, error: Exception, context: Optional[IConversionContext] = None) -> Any:
        """处理错误
        
        Args:
            error: 错误对象
            context: 转换上下文
            
        Returns:
            Any: 处理结果
        """
        pass
    
    @abstractmethod
    def get_severity(self, error: Exception) -> ErrorSeverity:
        """获取错误严重程度
        
        Args:
            error: 错误对象
            
        Returns:
            ErrorSeverity: 错误严重程度
        """
        pass


class BaseErrorHandler(IErrorHandler):
    """基础错误处理器
    
    提供错误处理的通用基础实现。
    """
    
    def __init__(self, name: str, handled_types: List[Type[Exception]]):
        """初始化基础错误处理器
        
        Args:
            name: 处理器名称
            handled_types: 可处理的错误类型列表
        """
        self.name = name
        self.handled_types = handled_types
        self.logger = get_logger(__name__)
    
    def can_handle(self, error: Exception) -> bool:
        """检查是否可以处理该错误
        
        Args:
            error: 错误对象
            
        Returns:
            bool: 是否可以处理
        """
        return any(isinstance(error, error_type) for error_type in self.handled_types)
    
    def handle(self, error: Exception, context: Optional[IConversionContext] = None) -> Any:
        """处理错误
        
        Args:
            error: 错误对象
            context: 转换上下文
            
        Returns:
            Any: 处理结果
        """
        severity = self.get_severity(error)
        error_info = ErrorInfo(
            error=error,
            severity=severity,
            context=context,
            metadata={"handler": self.name}
        )
        
        # 记录错误
        self._log_error(error_info)
        
        # 执行具体的错误处理逻辑
        return self._do_handle(error_info)
    
    @abstractmethod
    def _do_handle(self, error_info: ErrorInfo) -> Any:
        """执行具体的错误处理逻辑
        
        Args:
            error_info: 错误信息
            
        Returns:
            Any: 处理结果
        """
        pass
    
    def get_severity(self, error: Exception) -> ErrorSeverity:
        """获取错误严重程度
        
        Args:
            error: 错误对象
            
        Returns:
            ErrorSeverity: 错误严重程度
        """
        # 默认实现：根据错误类型判断严重程度
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, KeyError)):
            return ErrorSeverity.MEDIUM
        elif isinstance(error, (AttributeError, TypeError)):
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.MEDIUM
    
    def _log_error(self, error_info: ErrorInfo) -> None:
        """记录错误
        
        Args:
            error_info: 错误信息
        """
        error_msg = f"错误处理器 {self.name} 处理错误: {error_info.error}"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(error_msg)
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error(error_msg)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(error_msg)
        else:
            self.logger.info(error_msg)


class ConversionErrorHandler(BaseErrorHandler):
    """转换错误处理器
    
    处理转换过程中的错误。
    """
    
    def __init__(self):
        """初始化转换错误处理器"""
        super().__init__(
            name="ConversionErrorHandler",
            handled_types=[ValueError, TypeError, AttributeError, KeyError]
        )
    
    def _do_handle(self, error_info: ErrorInfo) -> Any:
        """执行转换错误处理
        
        Args:
            error_info: 错误信息
            
        Returns:
            Any: 处理结果
        """
        error = error_info.error
        
        # 添加错误到上下文
        if error_info.context:
            error_info.context.add_error(f"转换错误: {error}")
        
        # 根据错误类型进行不同的处理
        if isinstance(error, ValueError):
            return self._handle_value_error(error_info)
        elif isinstance(error, TypeError):
            return self._handle_type_error(error_info)
        elif isinstance(error, AttributeError):
            return self._handle_attribute_error(error_info)
        elif isinstance(error, KeyError):
            return self._handle_key_error(error_info)
        else:
            return None
    
    def _handle_value_error(self, error_info: ErrorInfo) -> Any:
        """处理值错误
        
        Args:
            error_info: 错误信息
            
        Returns:
            Any: 处理结果
        """
        error = error_info.error
        self.logger.debug(f"处理值错误: {error}")
        
        # 尝试提供默认值
        if error_info.context:
            default_value = error_info.context.get_parameter("default_value")
            if default_value is not None:
                return default_value
        
        # 返回None作为默认处理
        return None
    
    def _handle_type_error(self, error_info: ErrorInfo) -> Any:
        """处理类型错误
        
        Args:
            error_info: 错误信息
            
        Returns:
            Any: 处理结果
        """
        error = error_info.error
        self.logger.debug(f"处理类型错误: {error}")
        
        # 尝试类型转换
        if error_info.context:
            target_type = error_info.context.get_parameter("target_type")
            if target_type:
                try:
                    # 这里可以添加更复杂的类型转换逻辑
                    return target_type(str(error))
                except Exception:
                    pass
        
        return None
    
    def _handle_attribute_error(self, error_info: ErrorInfo) -> Any:
        """处理属性错误
        
        Args:
            error_info: 错误信息
            
        Returns:
            Any: 处理结果
        """
        error = error_info.error
        self.logger.debug(f"处理属性错误: {error}")
        
        # 返回空字典作为默认处理
        return {}
    
    def _handle_key_error(self, error_info: ErrorInfo) -> Any:
        """处理键错误
        
        Args:
            error_info: 错误信息
            
        Returns:
            Any: 处理结果
        """
        error = error_info.error
        self.logger.debug(f"处理键错误: {error}")
        
        # 返回None作为默认处理
        return None


class ValidationErrorHandler(BaseErrorHandler):
    """验证错误处理器
    
    处理验证过程中的错误。
    """
    
    def __init__(self):
        """初始化验证错误处理器"""
        super().__init__(
            name="ValidationErrorHandler",
            handled_types=[ValueError, AssertionError]
        )
    
    def _do_handle(self, error_info: ErrorInfo) -> Any:
        """执行验证错误处理
        
        Args:
            error_info: 错误信息
            
        Returns:
            Any: 处理结果
        """
        error = error_info.error
        
        # 添加验证错误到上下文
        if error_info.context:
            error_info.context.add_error(f"验证错误: {error}")
        
        # 收集所有验证错误
        validation_errors = []
        if isinstance(error, ValueError):
            validation_errors.append(str(error))
        elif isinstance(error, AssertionError):
            validation_errors.append(str(error))
        
        # 返回错误列表
        return validation_errors
    
    def get_severity(self, error: Exception) -> ErrorSeverity:
        """获取错误严重程度
        
        Args:
            error: 错误对象
            
        Returns:
            ErrorSeverity: 错误严重程度
        """
        # 验证错误通常是中等严重程度
        return ErrorSeverity.MEDIUM


class ErrorHandlerRegistry:
    """错误处理器注册中心
    
    管理所有错误处理器的注册和查找。
    """
    
    def __init__(self):
        """初始化错误处理器注册中心"""
        self.logger = get_logger(__name__)
        self._handlers: List[IErrorHandler] = []
        self._handler_map: Dict[Type[Exception], List[IErrorHandler]] = {}
    
    def register_handler(self, handler: IErrorHandler) -> None:
        """注册错误处理器
        
        Args:
            handler: 错误处理器
        """
        self._handlers.append(handler)
        
        # 更新类型映射
        if isinstance(handler, BaseErrorHandler):
            for error_type in handler.handled_types:
                if error_type not in self._handler_map:
                    self._handler_map[error_type] = []
                self._handler_map[error_type].append(handler)
        
        self.logger.debug(f"注册错误处理器: {handler.__class__.__name__}")
    
    def unregister_handler(self, handler: IErrorHandler) -> bool:
        """注销错误处理器
        
        Args:
            handler: 错误处理器
            
        Returns:
            bool: 是否成功注销
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
            
            # 更新类型映射
            if isinstance(handler, BaseErrorHandler):
                for error_type in handler.handled_types:
                    if error_type in self._handler_map:
                        if handler in self._handler_map[error_type]:
                            self._handler_map[error_type].remove(handler)
                        if not self._handler_map[error_type]:
                            del self._handler_map[error_type]
            
            self.logger.debug(f"注销错误处理器: {handler.__class__.__name__}")
            return True
        
        return False
    
    def find_handler(self, error: Exception) -> Optional[IErrorHandler]:
        """查找可以处理指定错误的处理器
        
        Args:
            error: 错误对象
            
        Returns:
            Optional[IErrorHandler]: 错误处理器，如果找不到则返回None
        """
        # 首先查找精确匹配的类型
        error_type = type(error)
        if error_type in self._handler_map:
            for handler in self._handler_map[error_type]:
                if handler.can_handle(error):
                    return handler
        
        # 查找父类型匹配
        for handler in self._handlers:
            if handler.can_handle(error):
                return handler
        
        return None
    
    def handle_error(self, error: Exception, context: Optional[IConversionContext] = None) -> Any:
        """处理错误
        
        Args:
            error: 错误对象
            context: 转换上下文
            
        Returns:
            Any: 处理结果
        """
        handler = self.find_handler(error)
        
        if handler:
            return handler.handle(error, context)
        else:
            # 没有找到合适的处理器，记录错误并重新抛出
            self.logger.error(f"未找到合适的错误处理器处理错误: {error}")
            raise error
    
    def get_handlers(self) -> List[IErrorHandler]:
        """获取所有注册的处理器
        
        Returns:
            List[IErrorHandler]: 处理器列表
        """
        return self._handlers.copy()
    
    def clear_handlers(self) -> None:
        """清空所有处理器"""
        self._handlers.clear()
        self._handler_map.clear()
        self.logger.debug("清空所有错误处理器")


# 全局错误处理器注册中心实例
_global_registry: Optional[ErrorHandlerRegistry] = None


def get_error_handler_registry() -> ErrorHandlerRegistry:
    """获取全局错误处理器注册中心实例
    
    Returns:
        ErrorHandlerRegistry: 注册中心实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ErrorHandlerRegistry()
        # 注册默认处理器
        _global_registry.register_handler(ConversionErrorHandler())
        _global_registry.register_handler(ValidationErrorHandler())
    return _global_registry


def handle_error(error: Exception, context: Optional[IConversionContext] = None) -> Any:
    """处理错误的便捷函数
    
    Args:
        error: 错误对象
        context: 转换上下文
        
    Returns:
        Any: 处理结果
    """
    registry = get_error_handler_registry()
    return registry.handle_error(error, context)