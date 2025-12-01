"""日志服务模块"""

from ...core.logger.log_level import LogLevel
from ...core.logger.redactor import LogRedactor, CustomLogRedactor
from ...core.logger.structured_file_logger import StructuredFileLogger
from ...core.logger.metrics import IMetricsCollector, MetricsCollector, get_global_metrics_collector
from ...core.logger.error_handler import ErrorType, IGlobalErrorHandler
from .logger import ILogger, Logger, get_logger, set_global_config
from .error_handler import (
    GlobalErrorHandler,
    get_global_error_handler,
    handle_error,
    register_error_handler,
    error_handler,
)

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