"""日志服务模块"""

from ...interfaces.common_infra import LogLevel
from ...core.logger.redactor import LogRedactor, CustomLogRedactor
from ...core.logger.structured_file_logger import StructuredFileLogger
from .logger_service import LoggerService, LoggerFactory, get_logger, set_global_config
from .error_handler import (
    ErrorType,
    IGlobalErrorHandler,
    BaseErrorHandler,
    GlobalErrorHandler,
    get_global_error_handler,
    handle_error,
    register_error_handler,
    error_handler,
)
from .metrics import IMetricsCollector, MetricsCollector, get_global_metrics_collector

__all__ = [
    # 核心组件
    "LogLevel",
    "LogRedactor",
    "CustomLogRedactor",
    "StructuredFileLogger",
    # 日志服务
    "LoggerService",
    "LoggerFactory",
    "get_logger",
    "set_global_config",
    # 错误处理
    "ErrorType",
    "IGlobalErrorHandler",
    "BaseErrorHandler",
    "GlobalErrorHandler",
    "get_global_error_handler",
    "handle_error",
    "register_error_handler",
    "error_handler",
    # 指标收集
    "IMetricsCollector",
    "MetricsCollector",
    "get_global_metrics_collector",
]