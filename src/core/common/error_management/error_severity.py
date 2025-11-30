"""错误严重度定义"""

from enum import Enum


class ErrorSeverity(Enum):
    """错误严重度"""
    CRITICAL = "critical"    # 必须立即处理
    HIGH = "high"           # 需要立即处理
    MEDIUM = "medium"       # 应该处理
    LOW = "low"             # 可以延迟处理
    INFO = "info"           # 信息性错误