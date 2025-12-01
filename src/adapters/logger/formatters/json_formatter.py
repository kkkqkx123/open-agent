"""JSON格式化器"""

import json
from datetime import datetime
from typing import Any, Dict

from .base_formatter import BaseFormatter
from ...core.logger.log_level import LogLevel


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
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                json_record[key] = self._prepare_json_record(value)
            elif isinstance(value, list):
                # 处理列表，对列表中的每个元素进行处理
                json_record[key] = [self._prepare_json_value(item) for item in value]
            else:
                json_record[key] = value
        return json_record

    def _prepare_json_value(self, value: Any) -> Any:
        """准备JSON格式的单个值

        Args:
            value: 原始值

        Returns:
            JSON可序列化的值
        """
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, LogLevel):
            return value.name
        elif isinstance(value, dict):
            return self._prepare_json_record(value)
        elif isinstance(value, list):
            return [self._prepare_json_value(item) for item in value]
        else:
            return value