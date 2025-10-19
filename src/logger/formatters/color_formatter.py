"""彩色日志格式化器"""

import sys
from typing import Any, Dict, Optional

from .text_formatter import TextFormatter
from ..log_level import LogLevel


class ColorFormatter(TextFormatter):
    """彩色日志格式化器"""

    # ANSI颜色代码
    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "bg_red": "\033[41m",
        "bg_green": "\033[42m",
        "bg_yellow": "\033[43m",
        "bg_blue": "\033[44m",
        "bg_magenta": "\033[45m",
        "bg_cyan": "\033[46m",
        "bg_white": "\033[47m",
    }

    # 日志级别颜色映射
    LEVEL_COLORS = {
        LogLevel.DEBUG: ("blue", False),
        LogLevel.INFO: ("green", False),
        LogLevel.WARNING: ("yellow", False),
        LogLevel.ERROR: ("red", False),
        LogLevel.CRITICAL: ("bg_red", True),
    }

    def __init__(
        self,
        datefmt: str = "%Y-%m-%d %H:%M:%S",
        fmt: str = "{timestamp} [{level}] {name}: {message}",
        use_colors: Optional[bool] = None,
    ):
        """初始化彩色格式化器

        Args:
            datefmt: 日期时间格式
            fmt: 日志格式模板
            use_colors: 是否使用颜色，None表示自动检测
        """
        super().__init__(datefmt, fmt)

        # 自动检测是否支持颜色
        if use_colors is None:
            self.use_colors = self._supports_color()
        else:
            self.use_colors = use_colors

    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录

        Args:
            record: 日志记录

        Returns:
            格式化后的日志字符串
        """
        if not self.use_colors:
            # 如果不支持颜色，使用父类的方法
            return super().format(record)

        # 获取基本字段
        timestamp = self.format_time(record["timestamp"])
        level = self.format_level(record["level"])
        name = self._get_record_value(record, "name", "unknown")
        message = self._get_record_value(record, "message", "")

        # 应用颜色
        level_color, bold = self.LEVEL_COLORS.get(record["level"], ("white", False))
        colored_level = self._colorize(level, level_color, bold)

        # 格式化基本日志
        formatted = self.fmt.format(
            timestamp=self._colorize(timestamp, "cyan"),
            level=colored_level,
            name=self._colorize(name, "magenta"),
            message=message,
        )

        # 添加额外字段
        extra_fields = self._get_extra_fields(record)
        if extra_fields:
            extra_str = " ".join(
                [
                    f"{k}={self._colorize(str(v), 'blue')}"
                    for k, v in extra_fields.items()
                ]
            )
            formatted += f" {extra_str}"

        return formatted

    def _colorize(self, text: str, color_name: str, bold: bool = False) -> str:
        """给文本添加颜色

        Args:
            text: 文本
            color_name: 颜色名称
            bold: 是否加粗

        Returns:
            带颜色的文本
        """
        if not self.use_colors or color_name not in self.COLORS:
            return text

        color_code = self.COLORS[color_name]
        reset_code = self.COLORS["reset"]

        if bold:
            return f"{self.COLORS['bold']}{color_code}{text}{reset_code}"
        else:
            return f"{color_code}{text}{reset_code}"

    def _supports_color(self) -> bool:
        """检测终端是否支持颜色

        Returns:
            是否支持颜色
        """
        # 检查环境变量
        if "NO_COLOR" in os.environ:
            return False

        if "FORCE_COLOR" in os.environ:
            return True

        # 检查是否是TTY
        if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
            return False

        # 检查TERM环境变量
        term = os.environ.get("TERM", "")
        if "color" in term or term in ("xterm", "xterm-256color", "screen", "tmux"):
            return True

        # 检查COLORTERM环境变量
        colorterm = os.environ.get("COLORTERM", "")
        if colorterm in ("truecolor", "24bit"):
            return True

        return False

    def set_use_colors(self, use_colors: bool) -> None:
        """设置是否使用颜色

        Args:
            use_colors: 是否使用颜色
        """
        self.use_colors = use_colors

    def set_level_color(
        self, level: LogLevel, color_name: str, bold: bool = False
    ) -> None:
        """设置日志级别的颜色

        Args:
            level: 日志级别
            color_name: 颜色名称
            bold: 是否加粗
        """
        if color_name in self.COLORS:
            self.LEVEL_COLORS[level] = (color_name, bold)


class SimpleColorFormatter(ColorFormatter):
    """简单彩色日志格式化器"""

    def __init__(self, datefmt: str = "%H:%M:%S"):
        """初始化简单彩色格式化器

        Args:
            datefmt: 日期时间格式
        """
        fmt = "{timestamp} [{level}] {message}"
        super().__init__(datefmt, fmt)

    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录

        Args:
            record: 日志记录

        Returns:
            格式化后的日志字符串
        """
        if not self.use_colors:
            # 如果不支持颜色，使用简单格式
            timestamp = self.format_time(record["timestamp"])
            level = self.format_level(record["level"])
            message = self._get_record_value(record, "message", "")

            return f"{timestamp} [{level}] {message}"

        # 获取基本字段
        timestamp = self.format_time(record["timestamp"])
        level = self.format_level(record["level"])
        message = self._get_record_value(record, "message", "")

        # 应用颜色
        level_color, bold = self.LEVEL_COLORS.get(record["level"], ("white", False))
        colored_level = self._colorize(level, level_color, bold)

        # 格式化基本日志
        formatted = f"{self._colorize(timestamp, 'cyan')} [{colored_level}] {message}"

        return formatted


# 需要导入os模块
import os
