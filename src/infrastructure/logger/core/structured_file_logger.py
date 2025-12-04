"""结构化文件日志记录器"""

import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from .log_level import LogLevel
from .redactor import LogRedactor
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ....interfaces.logger import ILogRedactor


class StructuredFileLogger:
    """结构化文件日志记录器"""

    def __init__(
        self,
        filename: str,
        level: LogLevel = LogLevel.INFO,
        redactor: Optional['ILogRedactor'] = None,
        encoding: str = "utf-8",
    ):
        """初始化结构化文件日志记录器

        Args:
            filename: 日志文件名
            level: 日志级别
            redactor: 脱敏器
            encoding: 文件编码
        """
        self.filename: str = filename
        self.level: LogLevel = level
        self.redactor: 'ILogRedactor' = redactor or LogRedactor()
        self.encoding: str = encoding
        self._lock: threading.Lock = threading.Lock()

        # 确保目录存在
        directory = os.path.dirname(self.filename)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        """记录结构化日志

        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 附加数据
        """
        if level.value < self.level.value:
            return

        # 创建结构化日志记录
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": level.name,
            "message": message,
            "thread_id": threading.get_ident(),
            "process_id": os.getpid(),
            **kwargs,
        }

        # 脱敏处理
        redacted_record = self._redact_record(log_record)

        # 写入文件
        self._write_record(redacted_record)

    def _redact_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """对日志记录进行脱敏

        Args:
            record: 原始日志记录

        Returns:
            脱敏后的日志记录
        """
        redacted_record = {}
        for key, value in record.items():
            if isinstance(value, str):
                redacted_record[key] = self.redactor.redact(value, self.level.name)
            else:
                redacted_record[key] = value
        return redacted_record

    def _write_record(self, record: Dict[str, Any]) -> None:
        """写入日志记录到文件

        Args:
            record: 日志记录
        """
        json_str = json.dumps(record, ensure_ascii=False, default=str)

        with self._lock:
            with open(self.filename, "a", encoding=self.encoding) as f:
                f.write(json_str + "\n")

    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志"""
        self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志"""
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志"""
        self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志"""
        self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """记录严重错误日志"""
        self.log(LogLevel.CRITICAL, message, **kwargs)