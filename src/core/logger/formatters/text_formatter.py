"""文本格式化器"""

from typing import Any, Dict

from .base_formatter import BaseFormatter
from ..log_level import LogLevel


class TextFormatter(BaseFormatter):
    """文本格式化器"""

    def __init__(
        self,
        fmt: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt: str = "%Y-%m-%d %H:%M:%S",
    ):
        """初始化文本格式化器

        Args:
            fmt: 格式字符串
            datefmt: 日期时间格式
        """
        super().__init__(datefmt)
        self.fmt = fmt

    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录

        Args:
            record: 日志记录

        Returns:
            格式化后的日志字符串
        """
        # 替换格式字符串中的占位符
        formatted = self.fmt
        
        # 替换时间戳
        if "%(asctime)s" in formatted:
            formatted = formatted.replace(
                "%(asctime)s", self.format_time(record.get("timestamp", ""))
            )
        
        # 替换日志器名称
        if "%(name)s" in formatted:
            formatted = formatted.replace(
                "%(name)s", str(record.get("name", "unknown"))
            )
        
        # 替换日志级别
        if "%(levelname)s" in formatted:
            formatted = formatted.replace(
                "%(levelname)s", self.format_level(record.get("level", LogLevel.INFO))
            )
        
        # 替换消息
        if "%(message)s" in formatted:
            formatted = formatted.replace(
                "%(message)s", str(record.get("message", ""))
            )
        
        # 处理其他可能的字段
        formatted = self._format_additional_fields(formatted, record)
        
        return formatted

    def _format_additional_fields(self, formatted: str, record: Dict[str, Any]) -> str:
        """格式化额外字段

        Args:
            formatted: 当前格式化字符串
            record: 日志记录

        Returns:
            更新后的格式化字符串
        """
        # 处理 %(field_name)s 格式的占位符
        import re
        
        # 查找所有 %(field_name)s 格式的占位符
        pattern = r"%\((\w+)\)s"
        matches = re.findall(pattern, formatted)
        
        for field_name in matches:
            placeholder = f"%({field_name})s"
            if placeholder in formatted:
                field_value = record.get(field_name, "")
                formatted = formatted.replace(placeholder, str(field_value))
        
        return formatted