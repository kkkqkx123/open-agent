"""基础日志格式化器"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseFormatter(ABC):
    """基础日志格式化器抽象类"""

    @abstractmethod
    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录

        Args:
            record: 日志记录字典

        Returns:
            格式化后的字符串
        """
        pass

    def _get_field_value(self, record: Dict[str, Any], field_name: str, default: Any = "") -> Any:
        """获取字段值，支持嵌套字段

        Args:
            record: 日志记录
            field_name: 字段名，支持点号分隔的嵌套字段
            default: 默认值

        Returns:
            字段值
        """
        if "." in field_name:
            # 处理嵌套字段
            parts = field_name.split(".")
            value = record
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        else:
            return record.get(field_name, default)

    def _safe_str(self, value: Any) -> str:
        """安全转换为字符串

        Args:
            value: 要转换的值

        Returns:
            字符串表示
        """
        if value is None:
            return ""
        try:
            return str(value)
        except Exception:
            return f"<unrepresentable: {type(value).__name__}>"