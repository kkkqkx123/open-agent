"""基础日志处理器"""

import threading
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ....interfaces.logger import IBaseHandler, LogLevel
from ..formatters.base_formatter import BaseFormatter


class BaseHandler(IBaseHandler):
    """基础日志处理器抽象类"""

    def __init__(
        self,
        level: LogLevel = LogLevel.INFO,
        formatter: Optional[BaseFormatter] = None,
    ):
        """初始化基础处理器

        Args:
            level: 日志级别
            formatter: 格式化器
        """
        self.level = level
        self.formatter = formatter
        self._lock = threading.RLock()

    @abstractmethod
    def handle(self, record: Dict[str, Any]) -> None:
        """处理日志记录

        Args:
            record: 日志记录字典
        """
        pass

    @abstractmethod
    def flush(self) -> None:
        """刷新缓冲区"""
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭处理器"""
        pass

    def set_level(self, level: LogLevel) -> None:
        """设置日志级别

        Args:
            level: 日志级别
        """
        with self._lock:
            self.level = level

    def set_formatter(self, formatter: BaseFormatter) -> None:
        """设置格式化器

        Args:
            formatter: 格式化器实例
        """
        with self._lock:
            self.formatter = formatter

    def should_handle(self, record: Dict[str, Any]) -> bool:
        """检查是否应该处理该日志记录

        Args:
            record: 日志记录

        Returns:
            是否应该处理
        """
        record_level = record.get("level")
        if isinstance(record_level, str):
            try:
                record_level = LogLevel[record_level.upper()]
            except (KeyError, AttributeError):
                return True  # 未知级别默认处理
        
        if isinstance(record_level, LogLevel) and hasattr(record_level, 'value'):
            return record_level.value >= self.level.value
        
        return True  # 无法确定级别时默认处理

    def format_record(self, record: Dict[str, Any]) -> str:
        """格式化日志记录

        Args:
            record: 日志记录

        Returns:
            格式化后的字符串
        """
        if self.formatter:
            return self.formatter.format(record)
        
        # 默认格式化
        timestamp = record.get("timestamp", "")
        level = record.get("level", "")
        message = record.get("message", "")
        name = record.get("name", "")
        
        if name:
            return f"[{timestamp}] {level} {name}: {message}"
        else:
            return f"[{timestamp}] {level}: {message}"