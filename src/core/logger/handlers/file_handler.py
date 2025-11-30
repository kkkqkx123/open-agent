"""文件日志处理器"""

import os
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from .base_handler import BaseHandler
from ..log_level import LogLevel
from ..formatters.text_formatter import TextFormatter


class FileHandler(BaseHandler):
    """文件日志处理器"""

    def __init__(
        self, level: LogLevel = LogLevel.INFO, config: Optional[Dict[str, Any]] = None
    ):
        """初始化文件处理器

        Args:
            level: 日志级别
            config: 配置
        """
        super().__init__(level, config)
        
        # 从配置获取文件路径，如果没有则使用默认路径
        self.filename = config.get("filename", "app.log") if config else "app.log"
        self.mode = config.get("mode", "a") if config else "a"
        self.encoding = config.get("encoding", "utf-8") if config else "utf-8"
        
        # 确保目录存在
        directory = os.path.dirname(self.filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # 打开文件
        self.stream = open(self.filename, self.mode, encoding=self.encoding)
        self._lock = threading.Lock()

        # 设置默认格式化器
        if self._formatter is None:
            self._formatter = TextFormatter()

    def emit(self, record: Dict[str, Any]) -> None:
        """输出日志记录到文件

        Args:
            record: 日志记录
        """
        formatted_record = self.format(record)
        formatted_msg = formatted_record.get("formatted_message", str(record.get("message", "")))
        
        with self._lock:
            try:
                if self.stream is not None:
                    self.stream.write(formatted_msg + "\n")
                    self.stream.flush()
            except Exception:
                self.handleError(record)

    def flush(self) -> None:
        """刷新文件流"""
        with self._lock:
            if self.stream is not None and hasattr(self.stream, "flush"):
                self.stream.flush()

    def close(self) -> None:
        """关闭文件"""
        if self.stream and not self.stream.closed:
            # 直接刷新而不使用锁，避免死锁
            if hasattr(self.stream, "flush"):
                self.stream.flush()
            self.stream.close()
            self.stream = None

    def __del__(self):
        """析构函数"""
        self.close()