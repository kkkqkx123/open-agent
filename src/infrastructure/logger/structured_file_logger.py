"""结构化文件日志记录器

提供结构化日志记录功能，将日志输出到文件。
"""

import threading
from datetime import datetime
from typing import Any, Dict, Optional, List
from pathlib import Path

from .logger import Logger
from .log_level import LogLevel
from .handlers.file_handler import FileHandler
from .formatters.json_formatter import JsonFormatter
from .redactor import LogRedactor
from .config_integration import LoggingConfigIntegration


class StructuredFileLogger(Logger):
    """结构化文件日志记录器

    专门用于将结构化日志输出到文件的记录器。
    默认使用JSON格式输出，便于后续分析和处理。
    """

    def __init__(
        self,
        name: str = "structured_file_logger",
        log_file_path: str = "logs/structured_app.log",
        log_level: LogLevel = LogLevel.INFO,
        redactor: Optional[LogRedactor] = None,
    ):
        """初始化结构化文件日志记录器

        Args:
            name: 日志记录器名称
            log_file_path: 日志文件路径
            log_level: 日志级别
            redactor: 日志脱敏器
        """
        # 确保日志目录存在
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 初始化基础日志记录器
        super().__init__(name=name, redactor=redactor)

        # 设置日志级别
        self.set_level(log_level)

        # 创建文件处理器
        file_handler = FileHandler(
            level=log_level,
            config={
                "path": log_file_path,
                "format": "json",  # 使用JSON格式进行结构化输出
                "rotation": "size",
                "max_size": "10MB",
                "backup_count": 5,
                "encoding": "utf-8",
            }
        )

        # 设置JSON格式化器
        file_handler.set_formatter(JsonFormatter())

        # 添加处理器
        self.add_handler(file_handler)

    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志"""
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志"""
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志"""
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志"""
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """记录严重错误日志"""
        self._log(LogLevel.CRITICAL, message, **kwargs)

    def _log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        """内部日志记录方法

        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        if not self._should_log(level):
            return

        # 创建日志记录
        log_record = self._create_log_record(level, message, **kwargs)

        # 脱敏处理
        redacted_record = self._redact_log_record(log_record)

        # 发送到所有处理器
        with self._lock:
            for handler in self._handlers:
                try:
                    handler.handle(redacted_record)
                except Exception as e:
                    # 避免日志记录本身出错导致程序崩溃
                    print(f"日志处理器错误: {e}")

    def _create_log_record(
        self, level: LogLevel, message: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """创建结构化日志记录

        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外的日志数据

        Returns:
            日志记录字典
        """
        return {
            "name": self.name,
            "level": level.name,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "thread_id": threading.get_ident(),
            **kwargs,
        }