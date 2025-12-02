"""TextFormatter 类的单元测试"""

import pytest
from datetime import datetime
from typing import Any, Dict

from src.core.logger.formatters.text_formatter import TextFormatter
from src.core.logger.log_level import LogLevel


class TestTextFormatter:
    """TextFormatter 测试类"""

    def test_init_default_values(self):
        """测试默认值初始化"""
        formatter = TextFormatter()
        
        assert formatter.fmt == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert formatter.datefmt == "%Y-%m-%d %H:%M:%S"

    def test_init_custom_values(self):
        """测试自定义值初始化"""
        custom_fmt = "%(levelname)s: %(message)s"
        custom_datefmt = "%Y/%m/%d %H:%M:%S"
        
        formatter = TextFormatter(fmt=custom_fmt, datefmt=custom_datefmt)
        
        assert formatter.fmt == custom_fmt
        assert formatter.datefmt == custom_datefmt

    def test_format_basic_record(self):
        """测试基本日志记录格式化"""
        formatter = TextFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.INFO,
            "message": "Test message"
        }
        
        result = formatter.format(record)
        expected = "2023-01-15 10:30:45 - test_logger - INFO - Test message"
        assert result == expected

    def test_format_missing_timestamp(self):
        """测试缺少时间戳的记录格式化"""
        formatter = TextFormatter()
        
        record = {
            "name": "test_logger",
            "level": LogLevel.INFO,
            "message": "Test message"
        }
        
        result = formatter.format(record)
        expected = " - test_logger - INFO - Test message"
        assert result == expected

    def test_format_missing_name(self):
        """测试缺少名称的记录格式化"""
        formatter = TextFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "level": LogLevel.INFO,
            "message": "Test message"
        }
        
        result = formatter.format(record)
        expected = "2023-01-15 10:30:45 - unknown - INFO - Test message"
        assert result == expected

    def test_format_missing_level(self):
        """测试缺少日志级别的记录格式化"""
        formatter = TextFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "message": "Test message"
        }
        
        result = formatter.format(record)
        expected = "2023-01-15 10:30:45 - test_logger - INFO - Test message"
        assert result == expected

    def test_format_missing_message(self):
        """测试缺少消息的记录格式化"""
        formatter = TextFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.INFO
        }
        
        result = formatter.format(record)
        expected = "2023-01-15 10:30:45 - test_logger - INFO - "
        assert result == expected

    def test_format_custom_format(self):
        """测试自定义格式"""
        custom_fmt = "%(levelname)s [%(name)s] %(message)s"
        formatter = TextFormatter(fmt=custom_fmt)
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.ERROR,
            "message": "Error occurred"
        }
        
        result = formatter.format(record)
        expected = "ERROR [test_logger] Error occurred"
        assert result == expected

    def test_format_custom_date_format(self):
        """测试自定义日期格式"""
        custom_datefmt = "%Y/%m/%d %H:%M:%S"
        formatter = TextFormatter(datefmt=custom_datefmt)
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.WARNING,
            "message": "Warning message"
        }
        
        result = formatter.format(record)
        expected = "2023/01/15 10:30:45 - test_logger - WARNING - Warning message"
        assert result == expected

    def test_format_additional_fields(self):
        """测试格式化额外字段"""
        custom_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(module)s:%(line)d]"
        formatter = TextFormatter(fmt=custom_fmt)
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.DEBUG,
            "message": "Debug message",
            "module": "test_module",
            "line": 123
        }
        
        result = formatter.format(record)
        expected = "2023-01-15 10:30:45 - test_logger - DEBUG - Debug message [test_module:123]"
        assert result == expected

    def test_format_additional_fields_missing(self):
        """测试格式化缺失的额外字段"""
        custom_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(module)s:%(line)d]"
        formatter = TextFormatter(fmt=custom_fmt)
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.DEBUG,
            "message": "Debug message"
            # 缺少 module 和 line 字段
        }
        
        result = formatter.format(record)
        expected = "2023-01-15 10:30:45 - test_logger - DEBUG - Debug message [:]"
        assert result == expected

    def test_format_complex_record(self):
        """测试复杂记录格式化"""
        formatter = TextFormatter()
        
        record = {
            "timestamp": datetime(2023, 12, 25, 15, 45, 30),
            "name": "complex_logger",
            "level": LogLevel.CRITICAL,
            "message": "Critical error occurred",
            "module": "main",
            "function": "process_data",
            "line": 567,
            "thread": "main_thread",
            "process": 12345
        }
        
        custom_fmt = "%(asctime)s [%(thread)s] %(name)s.%(function)s:%(line)d - %(levelname)s - %(message)s (PID: %(process)s)"
        formatter.fmt = custom_fmt
        
        result = formatter.format(record)
        expected = "2023-12-25 15:45:30 [main_thread] complex_logger.process_data:567 - CRITICAL - Critical error occurred (PID: 12345)"
        assert result == expected

    def test_format_non_string_values(self):
        """测试非字符串值格式化"""
        formatter = TextFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": 123,  # 数字
            "level": LogLevel.INFO,
            "message": {"key": "value"}  # 字典
        }
        
        result = formatter.format(record)
        expected = "2023-01-15 10:30:45 - 123 - INFO - {'key': 'value'}"
        assert result == expected

    def test_format_empty_record(self):
        """测试空记录格式化"""
        formatter = TextFormatter()
        
        record = {}
        
        result = formatter.format(record)
        expected = " - unknown - INFO - "
        assert result == expected

    def test_format_additional_fields_with_special_characters(self):
        """测试包含特殊字符的额外字段格式化"""
        custom_fmt = "%(asctime)s - %(message)s - %(special_field)s"
        formatter = TextFormatter(fmt=custom_fmt)
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "message": "Test message",
            "special_field": "Special value with spaces & symbols!"
        }
        
        result = formatter.format(record)
        expected = "2023-01-15 10:30:45 - Test message - Special value with spaces & symbols!"
        assert result == expected