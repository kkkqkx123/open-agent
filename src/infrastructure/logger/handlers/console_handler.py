"""控制台日志处理器"""

import sys
import threading
from typing import Any, Dict, Optional

from ....interfaces.logger import LogLevel
from ..formatters.text_formatter import TextFormatter
from ..formatters.color_formatter import ColorFormatter
from .base_handler import BaseHandler


class ConsoleHandler(BaseHandler):
    """控制台处理器"""

    def __init__(
        self,
        level: LogLevel = LogLevel.INFO,
        formatter: Optional[TextFormatter] = None,
        stream=None,
        use_colors: Optional[bool] = None,
    ):
        """初始化控制台处理器

        Args:
            level: 日志级别
            formatter: 格式化器
            stream: 输出流，默认为sys.stderr
            use_colors: 是否使用颜色
        """
        super().__init__(level, formatter)
        
        self.stream = stream or sys.stderr
        
        # 如果没有指定格式化器，使用彩色格式化器
        if self.formatter is None:
            self.formatter = ColorFormatter(use_colors=use_colors)

    def handle(self, record: Dict[str, Any]) -> None:
        """处理日志记录，输出到控制台

        Args:
            record: 日志记录字典
        """
        if not self.should_handle(record):
            return

        try:
            formatted_message = self.format_record(record)
            self._write_to_console(formatted_message)
        except Exception as e:
            # 处理失败时的fallback
            error_message = f"ConsoleHandler error: {e}. Original record: {record}"
            self._write_to_console(error_message)

    def _write_to_console(self, message: str) -> None:
        """写入消息到控制台

        Args:
            message: 要写入的消息
        """
        with self._lock:
            try:
                self.stream.write(message + '\n')
                self.stream.flush()
            except Exception:
                # 写入失败时尝试使用sys.stdout
                try:
                    sys.stdout.write(message + '\n')
                    sys.stdout.flush()
                except Exception:
                    # 最后的fallback，静默失败
                    pass

    def flush(self) -> None:
        """刷新缓冲区"""
        with self._lock:
            try:
                if hasattr(self.stream, 'flush'):
                    self.stream.flush()
            except Exception:
                pass

    def close(self) -> None:
        """关闭处理器"""
        self.flush()
        # 控制台处理器不需要关闭流

    def set_stream(self, stream) -> None:
        """设置输出流

        Args:
            stream: 新的输出流
        """
        with self._lock:
            self.stream = stream

    def is_tty(self) -> bool:
        """检查输出流是否是TTY

        Returns:
            是否是TTY
        """
        try:
            return hasattr(self.stream, 'isatty') and self.stream.isatty()
        except Exception:
            return False