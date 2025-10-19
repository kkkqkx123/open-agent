"""文件日志处理器"""

import os
import sys
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from .base_handler import BaseHandler
from ..log_level import LogLevel
from ..formatters.text_formatter import TextFormatter
from ..formatters.json_formatter import JsonFormatter


class FileHandler(BaseHandler):
    """文件日志处理器"""

    def __init__(
        self, level: LogLevel = LogLevel.INFO, config: Optional[Dict[str, Any]] = None
    ):
        """初始化文件处理器

        Args:
            level: 日志级别
            config: 处理器配置
        """
        super().__init__(level, config)

        # 获取配置
        self.file_path = (
            config.get("path", "logs/app.log") if config else "logs/app.log"
        )
        self.format_type = config.get("format", "text") if config else "text"
        self.rotation = config.get("rotation", "none") if config else "none"
        self.max_size = config.get("max_size", "10MB") if config else "10MB"
        self.backup_count = config.get("backup_count", 5) if config else 5
        self.encoding = config.get("encoding", "utf-8") if config else "utf-8"
        self._file_handler: Union[RotatingFileHandler, TimedRotatingFileHandler]

        # 确保日志目录存在
        log_dir = Path(self.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 设置格式化器
        self._setup_formatter()

        # 设置文件处理器
        self._setup_file_handler()

    def emit(self, record: Dict[str, Any]) -> None:
        """输出日志记录到文件

        Args:
            record: 日志记录
        """
        try:
            # 获取格式化后的消息
            formatted_record = self.format(record)
            msg = formatted_record.get("formatted_message", str(record))

            # 创建一个标准logging记录来使用内置处理器
            log_record = logging.LogRecord(
                name=record.get("name", ""),
                level=record["level"].value,
                pathname="",
                lineno=0,
                msg=msg,
                args=(),
                exc_info=None,
            )
            self._file_handler.emit(log_record)
        except Exception:
            self.handleError(record)

    def _setup_formatter(self) -> None:
        """设置格式化器"""
        if self.format_type == "json":
            self.set_formatter(JsonFormatter())
        else:
            self.set_formatter(TextFormatter())

    def _setup_file_handler(self) -> None:
        """设置文件处理器"""
        # 解析最大文件大小
        max_bytes = self._parse_size(self.max_size)

        if self.rotation == "size":
            # 按大小轮转
            self._file_handler = RotatingFileHandler(
                filename=self.file_path,
                maxBytes=max_bytes,
                backupCount=self.backup_count,
                encoding=self.encoding,
            )
        elif self.rotation == "time":
            # 按时间轮转
            when = "midnight"  # 默认每天午夜轮转
            interval = 1
            self._file_handler = TimedRotatingFileHandler(
                filename=self.file_path,
                when=when,
                interval=interval,
                backupCount=self.backup_count,
                encoding=self.encoding,
            )
        else:
            # 不轮转
            self._file_handler = RotatingFileHandler(  # type: ignore
                filename=self.file_path,
                maxBytes=max_bytes * 100,  # 设置一个很大的值，基本不会轮转
                backupCount=0,
                encoding=self.encoding,
            )

    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串

        Args:
            size_str: 大小字符串，如 "10MB"

        Returns:
            字节数
        """
        size_str = size_str.upper()
        if size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            # 默认为字节
            return int(size_str)

    def flush(self) -> None:
        """刷新缓冲区"""
        if hasattr(self._file_handler, "flush"):
            self._file_handler.flush()

    def close(self) -> None:
        """关闭处理器"""
        if hasattr(self._file_handler, "close"):
            self._file_handler.close()
        super().close()

    def set_file_path(self, file_path: str) -> None:
        """设置文件路径

        Args:
            file_path: 文件路径
        """
        # 关闭当前文件处理器
        if hasattr(self._file_handler, "close"):
            self._file_handler.close()

        # 更新路径
        self.file_path = file_path

        # 确保新目录存在
        log_dir = Path(self.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 重新设置文件处理器
        self._setup_file_handler()
