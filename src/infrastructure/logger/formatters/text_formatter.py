"""文本日志格式化器"""

from typing import Any, Dict, Optional
from .base_formatter import BaseFormatter


class TextFormatter(BaseFormatter):
    """文本格式化器"""

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
    ):
        """初始化文本格式化器

        Args:
            fmt: 格式字符串，支持占位符：
                {timestamp} - 时间戳
                {level} - 日志级别
                {name} - 日志记录器名称
                {message} - 日志消息
                {thread_id} - 线程ID
                {process_id} - 进程ID
            datefmt: 日期格式
        """
        self.fmt = fmt or "[{timestamp}] {level} {name}: {message}"
        self.datefmt = datefmt or "%Y-%m-%d %H:%M:%S"

    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录

        Args:
            record: 日志记录字典

        Returns:
            格式化后的字符串
        """
        # 准备格式化参数
        format_params = {
            "timestamp": self._format_timestamp(record.get("timestamp")),
            "level": self._get_field_value(record, "level", "UNKNOWN"),
            "name": self._get_field_value(record, "name", ""),
            "message": self._get_field_value(record, "message", ""),
            "thread_id": self._get_field_value(record, "thread_id", ""),
            "process_id": self._get_field_value(record, "process_id", ""),
        }

        # 添加其他字段
        for key, value in record.items():
            if key not in format_params:
                format_params[key] = self._safe_str(value)

        try:
            return self.fmt.format(**format_params)
        except KeyError as e:
            # 格式字符串中包含不存在的字段
            return f"[FORMAT_ERROR] Missing field: {e}. Original: {record}"

    def _format_timestamp(self, timestamp: Any) -> str:
        """格式化时间戳

        Args:
            timestamp: 时间戳

        Returns:
            格式化后的时间字符串
        """
        if not timestamp:
            return ""

        try:
            if isinstance(timestamp, str):
                # 如果是ISO格式字符串，尝试解析
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime(self.datefmt)
            else:
                # 其他类型直接转换为字符串
                return self._safe_str(timestamp)
        except Exception:
            return self._safe_str(timestamp)