"""BaseFormatter 类的单元测试"""

import pytest
from datetime import datetime
from typing import Any, Dict
from unittest.mock import Mock

from src.core.logger.formatters.base_formatter import BaseFormatter
from src.core.logger.log_level import LogLevel


class ConcreteFormatter(BaseFormatter):
    """用于测试的具体格式化器实现"""

    def format(self, record: Dict[str, Any]) -> str:
        """实现抽象方法"""
        return f"Formatted: {record}"


class TestBaseFormatter:
    """BaseFormatter 测试类"""

    def test_init_default_datefmt(self) -> None:
        """测试默认日期格式初始化"""
        formatter = ConcreteFormatter()
        assert formatter.datefmt == "%Y-%m-%d %H:%M:%S"

    def test_init_custom_datefmt(self) -> None:
        """测试自定义日期格式初始化"""
        custom_datefmt = "%Y/%m/%d %H:%M:%S"
        formatter = ConcreteFormatter(datefmt=custom_datefmt)
        assert formatter.datefmt == custom_datefmt

    def test_format_time(self) -> None:
        """测试时间格式化"""
        formatter = ConcreteFormatter()
        test_time = datetime(2023, 1, 15, 10, 30, 45)
        
        formatted_time = formatter.format_time(test_time)
        assert formatted_time == "2023-01-15 10:30:45"

    def test_format_time_custom_format(self) -> None:
        """测试自定义时间格式化"""
        custom_datefmt = "%Y/%m/%d %H:%M:%S"
        formatter = ConcreteFormatter(datefmt=custom_datefmt)
        test_time = datetime(2023, 1, 15, 10, 30, 45)
        
        formatted_time = formatter.format_time(test_time)
        assert formatted_time == "2023/01/15 10:30:45"

    def test_format_level(self) -> None:
        """测试日志级别格式化"""
        formatter = ConcreteFormatter()
        
        assert formatter.format_level(LogLevel.DEBUG) == "DEBUG"
        assert formatter.format_level(LogLevel.INFO) == "INFO"
        assert formatter.format_level(LogLevel.WARNING) == "WARNING"
        assert formatter.format_level(LogLevel.ERROR) == "ERROR"
        assert formatter.format_level(LogLevel.CRITICAL) == "CRITICAL"

    def test_get_record_value_existing_key(self) -> None:
        """测试获取记录中存在的值"""
        formatter = ConcreteFormatter()
        record = {"key1": "value1", "key2": "value2"}
        
        assert formatter._get_record_value(record, "key1") == "value1"
        assert formatter._get_record_value(record, "key2") == "value2"

    def test_get_record_value_nonexistent_key(self) -> None:
        """测试获取记录中不存在的值"""
        formatter = ConcreteFormatter()
        record = {"key1": "value1"}
        
        assert formatter._get_record_value(record, "nonexistent") is None

    def test_get_record_value_nonexistent_key_with_default(self) -> None:
        """测试获取记录中不存在的值（带默认值）"""
        formatter = ConcreteFormatter()
        record = {"key1": "value1"}
        
        assert formatter._get_record_value(record, "nonexistent", "default") == "default"

    def test_get_record_value_none_value(self) -> None:
        """测试获取记录中的 None 值"""
        formatter = ConcreteFormatter()
        record = {"key1": None}
        
        assert formatter._get_record_value(record, "key1") is None
        assert formatter._get_record_value(record, "key1", "default") is None

    def test_concrete_formatter_format(self) -> None:
        """测试具体格式化器的 format 方法"""
        formatter = ConcreteFormatter()
        record = {"message": "test message", "level": LogLevel.INFO}
        
        result = formatter.format(record)
        assert result == f"Formatted: {record}"

    def test_format_method_is_abstract(self) -> None:
        """测试 format 方法是抽象的"""
        with pytest.raises(TypeError):
            BaseFormatter()  # type: ignore  # 不能直接实例化抽象类

    def test_format_time_with_different_datetime_types(self) -> None:
        """测试不同类型的时间格式化"""
        formatter = ConcreteFormatter()
        
        # 测试 datetime 对象
        dt = datetime(2023, 1, 15, 10, 30, 45)
        assert formatter.format_time(dt) == "2023-01-15 10:30:45"
        
        # 测试其他类型（应该会出错）
        with pytest.raises(AttributeError):
            formatter.format_time("not a datetime")  # type: ignore

    def test_format_level_with_different_log_level_types(self) -> None:
        """测试不同类型的日志级别格式化"""
        formatter = ConcreteFormatter()
        
        # 测试 LogLevel 枚举
        assert formatter.format_level(LogLevel.DEBUG) == "DEBUG"
        
        # 测试其他类型（应该会出错）
        with pytest.raises(AttributeError):
            formatter.format_level("not a log level")  # type: ignore