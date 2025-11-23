"""控制台日志处理器"""

import sys
from typing import Any, Dict, Optional

from .base_handler import BaseHandler
from ..log_level import LogLevel
from ..formatters.text_formatter import TextFormatter
from ..formatters.color_formatter import ColorFormatter


class ConsoleHandler(BaseHandler):
    """控制台日志处理器"""

    def __init__(
        self, level: LogLevel = LogLevel.INFO, config: Optional[Dict[str, Any]] = None
    ):
        """初始化控制台处理器

        Args:
            level: 日志级别
            config: 配置
        """
        super().__init__(level, config)
        self.stream = config.get("stream", sys.stdout) if config else sys.stdout
        self.use_color = config.get("use_color", False) if config else False

        # 设置默认格式化器
        if self._formatter is None:
            if self.use_color:
                self._formatter = ColorFormatter()
            else:
                self._formatter = TextFormatter()

    def emit(self, record: Dict[str, Any]) -> None:
        """输出日志记录到控制台

        Args:
            record: 日志记录
        """
        formatted_record = self.format(record)
        formatted_msg = formatted_record.get("formatted_message", str(record["message"]))
        
        # 写入到流
        self.stream.write(formatted_msg + "\n")
        self.stream.flush()

    def flush(self) -> None:
        """刷新输出流"""
        if hasattr(self.stream, "flush"):
            self.stream.flush()