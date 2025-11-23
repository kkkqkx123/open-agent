"""JSON格式化器"""

import json
from datetime import datetime
from typing import Any, Dict

from .base_formatter import BaseFormatter
from ..log_level import LogLevel


class JsonFormatter(BaseFormatter):
    """JSON格式化器"""

    def __init__(self, datefmt: str = "%Y-%m-%d %H:%M:%S", ensure_ascii: bool = False):
        """初始化JSON格式化器

        Args:
            datefmt: 日期时间格式
            ensure_ascii: 是否确保ASCII编码
        """
        super().__init__(datefmt)
        self.ensure_ascii = ensure_ascii

    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录为JSON

        Args:
            record: 日志记录

        Returns:
            JSON格式的日志字符串
        """
        # 准备JSON可序列化的记录
        json_record = self._prepare_json_record(record)
        
        # 转换为JSON字符串
        return json.dumps(json_record, ensure_ascii=self.ensure_ascii, default=str)

    def _prepare_json_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """准备JSON格式的日志记录

        Args:
            record: 原始日志记录

        Returns:
            JSON可序列化的日志记录
        """
        json_record = {}
        for key, value in record.items():
            if isinstance(value, datetime):
                json_record[key] = value.isoformat()
            elif isinstance(value, LogLevel):
                json_record[key] = value.name
            else:
                json_record[key] = value
        return json_record