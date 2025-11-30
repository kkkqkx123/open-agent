"""统一错误处理注册表"""

import logging
from typing import Any, Callable, Dict, Optional, Type

from .error_handler import IErrorHandler
from .error_category import ErrorCategory
from .error_severity import ErrorSeverity


logger = logging.getLogger(__name__)


class ErrorHandlingRegistry:
    """错误处理注册表（单例）"""
    
    _instance = None
    
    def __new__(cls) -> "ErrorHandlingRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """初始化错误处理注册表"""
        if hasattr(self, '_initialized'):
            return
        
        self.handlers: Dict[Type[Exception], IErrorHandler] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self.error_mappings: Dict[str, Dict[str, Any]] = {}
        self._initialized = True
        
        # 初始化默认配置
        self._initialize_defaults()
    
    def register_handler(
        self, 
        exception_type: Type[Exception],
        handler: IErrorHandler
    ) -> None:
        """注册错误处理器
        
        Args:
            exception_type: 异常类型
            handler: 错误处理器
        """
        self.handlers[exception_type] = handler
        logger.info(f"注册错误处理器: {exception_type.__name__} -> {handler.__class__.__name__}")
    
    def register_recovery_strategy(
        self,
        strategy_name: str,
        strategy_func: Callable
    ) -> None:
        """注册恢复策略
        
        Args:
            strategy_name: 策略名称
            strategy_func: 策略函数
        """
        self.recovery_strategies[strategy_name] = strategy_func
        logger.info(f"注册恢复策略: {strategy_name}")
    
    def register_error_mapping(
        self,
        error_code: str,
        mapping: Dict[str, Any]
    ) -> None:
        """注册错误映射
        
        Args:
            error_code: 错误代码
            mapping: 映射配置
        """
        self.error_mappings[error_code] = mapping
        logger.info(f"注册错误映射: {error_code}")
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        handler = self._find_handler(error)
        if handler:
            handler.handle(error, context)
        else:
            # 使用默认处理器
            self._default_handler(error, context)
    
    def _find_handler(self, error: Exception) -> Optional[IErrorHandler]:
        """查找适合的错误处理器
        
        Args:
            error: 异常对象
            
        Returns:
            错误处理器，如果找不到则返回None
        """
        # 首先尝试精确匹配
        handler = self.handlers.get(type(error))
        if handler:
            return handler
        
        # 如果没有精确匹配，查找可以处理该错误的处理器
        for exception_type, handler in self.handlers.items():
            if handler.can_handle(error):
                return handler
        
        return None
    
    def _default_handler(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """默认错误处理
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        logger.error(
            f"未处理的异常: {type(error).__name__}",
            extra={
                "error": str(error),
                "context": context or {}
            }
        )
    
    def _initialize_defaults(self) -> None:
        """初始化默认配置"""
        # 这里可以添加一些默认的错误处理器和恢复策略
        # 例如：
        # self.register_recovery_strategy("retry_with_backoff", self._retry_with_backoff)
        # self.register_recovery_strategy("fallback_to_memory", self._fallback_to_memory)
        
        # 初始化默认的错误映射
        default_mappings = {
            "validation_error": {
                "severity": ErrorSeverity.MEDIUM,
                "category": ErrorCategory.VALIDATION,
                "recovery_strategy": "retry_with_backoff"
            },
            "network_error": {
                "severity": ErrorSeverity.HIGH,
                "category": ErrorCategory.NETWORK,
                "recovery_strategy": "retry_with_backoff"
            },
            "storage_error": {
                "severity": ErrorSeverity.HIGH,
                "category": ErrorCategory.STORAGE,
                "recovery_strategy": "fallback_to_memory"
            }
        }
        
        for error_code, mapping in default_mappings.items():
            self.register_error_mapping(error_code, mapping)
    
    def get_recovery_strategy(self, strategy_name: str) -> Optional[Callable]:
        """获取恢复策略
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            策略函数，如果找不到则返回None
        """
        return self.recovery_strategies.get(strategy_name)
    
    def get_error_mapping(self, error_code: str) -> Optional[Dict[str, Any]]:
        """获取错误映射
        
        Args:
            error_code: 错误代码
            
        Returns:
            映射配置，如果找不到则返回None
        """
        return self.error_mappings.get(error_code)


# 全局错误处理注册表实例
_error_handling_registry: Optional[ErrorHandlingRegistry] = None


def get_error_handling_registry() -> ErrorHandlingRegistry:
    """获取错误处理注册表实例
    
    Returns:
        错误处理注册表实例
    """
    global _error_handling_registry
    if _error_handling_registry is None:
        _error_handling_registry = ErrorHandlingRegistry()
    return _error_handling_registry


def register_error_handler(
    exception_type: Type[Exception],
    handler: IErrorHandler
) -> None:
    """注册错误处理器的便捷函数
    
    Args:
        exception_type: 异常类型
        handler: 错误处理器
    """
    registry = get_error_handling_registry()
    registry.register_handler(exception_type, handler)


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """处理错误的便捷函数
    
    Args:
        error: 异常对象
        context: 错误上下文信息
    """
    registry = get_error_handling_registry()
    registry.handle_error(error, context)