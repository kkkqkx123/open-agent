"""日志服务模块"""

from .log_level import LogLevel
from .logger import ILogger, Logger, get_logger, set_global_config
from .redactor import LogRedactor, CustomLogRedactor
from .structured_file_logger import StructuredFileLogger
from .error_handler import (
    IGlobalErrorHandler,
    GlobalErrorHandler,
    ErrorType,
    get_global_error_handler,
    handle_error,
    register_error_handler,
    error_handler,
)
from .metrics import IMetricsCollector, MetricsCollector, get_global_metrics_collector

__all__ = [
    "ILogger",
    "Logger",
    "LogLevel",
    "get_logger",
    "set_global_config",
    "LogRedactor",
    "CustomLogRedactor",
    "StructuredFileLogger",
    "IGlobalErrorHandler",
    "GlobalErrorHandler",
    "ErrorType",
    "get_global_error_handler",
    "handle_error",
    "register_error_handler",
    "error_handler",
    "IMetricsCollector",
    "MetricsCollector",
    "get_global_metrics_collector",
]