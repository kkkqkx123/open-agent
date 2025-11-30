"""统一错误管理模块导出"""

from .error_category import ErrorCategory
from .error_handler import IErrorHandler, BaseErrorHandler
from .error_handling_registry import (
    ErrorHandlingRegistry,
    get_error_handling_registry,
    register_error_handler,
    handle_error
)
from .error_patterns import (
    operation_with_retry,
    operation_with_fallback,
    safe_execution,
    OperationError,
    ServiceUnavailableError,
    DomainSpecificError
)
from .error_severity import ErrorSeverity


__all__ = [
    # 错误分类
    "ErrorCategory",
    # 错误严重度
    "ErrorSeverity",
    # 错误处理器接口
    "IErrorHandler",
    "BaseErrorHandler",
    # 错误处理注册表
    "ErrorHandlingRegistry",
    "get_error_handling_registry",
    "register_error_handler",
    "handle_error",
    # 标准错误处理模式
    "operation_with_retry",
    "operation_with_fallback",
    "safe_execution",
    "OperationError",
    "ServiceUnavailableError",
    "DomainSpecificError"
]