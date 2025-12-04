"""日志服务模块"""

from ...interfaces.logger import LogLevel, ILogRedactor
from ...infrastructure.logger.core.redactor import LogRedactor, CustomLogRedactor
from ...infrastructure.logger.core.structured_file_logger import StructuredFileLogger
from .logger_service import LoggerService, create_logger_service
from .injection import get_logger, set_logger_instance, clear_logger_instance

__all__ = [
    # 核心组件
    "LogLevel",
    "LogRedactor",
    "CustomLogRedactor",
    "StructuredFileLogger",
    # 日志服务
    "LoggerService",
    "create_logger_service",
    # 便利层
    "get_logger",
    "set_logger_instance",
    "clear_logger_instance",
]