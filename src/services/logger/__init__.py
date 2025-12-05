"""日志服务模块 - 纯业务逻辑层

根据重构方案，服务层只导出业务逻辑组件，不导出基础设施组件。
"""

from .logger_service import LoggerService, create_logger_service
from .injection import get_logger, set_logger_instance, clear_logger_instance

__all__ = [
    # 日志服务（纯业务逻辑）
    "LoggerService",
    "create_logger_service",
    # 便利层（向后兼容）
    "get_logger",
    "set_logger_instance",
    "clear_logger_instance",
]