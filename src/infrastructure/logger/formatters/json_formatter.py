"""JSON日志格式化器"""

import json
from typing import Any, Dict, Optional
from .base_formatter import BaseFormatter


class JsonFormatter(BaseFormatter):
    """JSON格式化器"""

    def __init__(
        self,
        ensure_ascii: bool = False,
        indent: Optional[int] = None,
        sort_keys: bool = False,
    ):
        """初始化JSON格式化器

        Args:
            ensure_ascii: 是否确保ASCII编码
            indent: 缩进空格数，None表示紧凑格式
            sort_keys: 是否排序键
        """
        self.ensure_ascii = ensure_ascii
        self.indent = indent
        self.sort_keys = sort_keys

    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录为JSON

        Args:
            record: 日志记录字典

        Returns:
            JSON格式的字符串
        """
        try:
            # 清理记录，确保所有值都可以序列化
            clean_record = self._clean_record(record)
            
            return json.dumps(
                clean_record,
                ensure_ascii=self.ensure_ascii,
                indent=self.indent,
                sort_keys=self.sort_keys,
                default=self._json_default,
            )
        except Exception as e:
            # 序列化失败时的fallback
            fallback_record = {
                "timestamp": record.get("timestamp", ""),
                "level": record.get("level", "ERROR"),
                "name": record.get("name", "JsonFormatter"),
                "message": f"JSON serialization failed: {e}",
                "original_record": str(record),
            }
            return json.dumps(fallback_record, ensure_ascii=self.ensure_ascii)

    def _clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """清理记录，移除不可序列化的值

        Args:
            record: 原始记录

        Returns:
            清理后的记录
        """
        clean_record = {}
        
        for key, value in record.items():
            if self._is_serializable(value):
                clean_record[key] = value
            else:
                clean_record[key] = self._safe_str(value)
        
        return clean_record

    def _is_serializable(self, value: Any) -> bool:
        """检查值是否可以JSON序列化

        Args:
            value: 要检查的值

        Returns:
            是否可序列化
        """
        try:
            json.dumps(value)
            return True
        except (TypeError, ValueError):
            return False

    def _json_default(self, obj: Any) -> str:
        """JSON序列化的默认处理器

        Args:
            obj: 无法序列化的对象

        Returns:
            字符串表示
        """
        try:
            if hasattr(obj, 'isoformat'):
                # datetime对象
                return obj.isoformat()
            elif hasattr(obj, '__dict__'):
                # 有__dict__的对象
                return str(obj.__dict__)
            else:
                # 其他对象
                return str(obj)
        except Exception:
            return f"<unserializable: {type(obj).__name__}>"