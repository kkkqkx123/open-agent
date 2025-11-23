"""彩色格式化器"""

from typing import Any, Dict

from .text_formatter import TextFormatter
from ..log_level import LogLevel


class ColorFormatter(TextFormatter):
    """彩色格式化器"""

    # ANSI颜色代码
    COLORS = {
        LogLevel.DEBUG: "\033[36m",  # 青色
        LogLevel.INFO: "\033[32m",  # 绿色
        LogLevel.WARNING: "\033[33m",  # 黄色
        LogLevel.ERROR: "\033[31m",  # 红色
        LogLevel.CRITICAL: "\033[35m",  # 紫色
    }
    RESET = "\033[0m"  # 重置颜色

    def __init__(
        self,
        fmt: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt: str = "%Y-%m-%d %H:%M:%S",
    ):
        """初始化彩色格式化器

        Args:
            fmt: 格式字符串
            datefmt: 日期时间格式
        """
        super().__init__(fmt, datefmt)

    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录（带颜色）

        Args:
            record: 日志记录

        Returns:
            格式化后的彩色日志字符串
        """
        # 先使用父类格式化
        formatted = super().format(record)
        
        # 根据日志级别添加颜色
        level = record.get("level", LogLevel.INFO)
        color = self.COLORS.get(level, "")
        
        if color:
            formatted = f"{color}{formatted}{self.RESET}"
        
        return formatted