"""JsonFormatter 类的单元测试"""

import json
import pytest
from datetime import datetime
from typing import Any, Dict

from src.core.logger.formatters.json_formatter import JsonFormatter
from src.core.logger.log_level import LogLevel


class TestJsonFormatter:
    """JsonFormatter 测试类"""

    def test_init_default_values(self):
        """测试默认值初始化"""
        formatter = JsonFormatter()
        
        assert formatter.datefmt == "%Y-%m-%d %H:%M:%S"
        assert formatter.ensure_ascii is False

    def test_init_custom_values(self):
        """测试自定义值初始化"""
        custom_datefmt = "%Y/%m/%d %H:%M:%S"
        formatter = JsonFormatter(datefmt=custom_datefmt, ensure_ascii=True)
        
        assert formatter.datefmt == custom_datefmt
        assert formatter.ensure_ascii is True

    def test_format_basic_record(self):
        """测试基本日志记录格式化"""
        formatter = JsonFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.INFO,
            "message": "Test message"
        }
        
        result = formatter.format(record)
        parsed_result = json.loads(result)
        
        assert parsed_result["timestamp"] == "2023-01-15T10:30:45"
        assert parsed_result["name"] == "test_logger"
        assert parsed_result["level"] == "INFO"
        assert parsed_result["message"] == "Test message"

    def test_format_with_datetime(self):
        """测试包含日期时间的记录格式化"""
        formatter = JsonFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45, 123456),
            "created_at": datetime(2023, 1, 14, 8, 15, 30),
            "message": "Test with datetime"
        }
        
        result = formatter.format(record)
        parsed_result = json.loads(result)
        
        assert parsed_result["timestamp"] == "2023-01-15T10:30:45.123456"
        assert parsed_result["created_at"] == "2023-01-14T08:15:30"
        assert parsed_result["message"] == "Test with datetime"

    def test_format_with_log_levels(self):
        """测试包含不同日志级别的记录格式化"""
        formatter = JsonFormatter()
        
        record = {
            "level": LogLevel.ERROR,
            "min_level": LogLevel.DEBUG,
            "max_level": LogLevel.CRITICAL,
            "message": "Test with log levels"
        }
        
        result = formatter.format(record)
        parsed_result = json.loads(result)
        
        assert parsed_result["level"] == "ERROR"
        assert parsed_result["min_level"] == "DEBUG"
        assert parsed_result["max_level"] == "CRITICAL"
        assert parsed_result["message"] == "Test with log levels"

    def test_format_with_complex_data(self):
        """测试包含复杂数据的记录格式化"""
        formatter = JsonFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "level": LogLevel.WARNING,
            "message": "Complex data test",
            "data": {
                "nested": {
                    "value": 123,
                    "list": [1, 2, 3]
                }
            },
            "numbers": [1, 2, 3.14],
            "boolean": True,
            "none_value": None
        }
        
        result = formatter.format(record)
        parsed_result = json.loads(result)
        
        assert parsed_result["timestamp"] == "2023-01-15T10:30:45"
        assert parsed_result["level"] == "WARNING"
        assert parsed_result["message"] == "Complex data test"
        assert parsed_result["data"]["nested"]["value"] == 123
        assert parsed_result["data"]["nested"]["list"] == [1, 2, 3]
        assert parsed_result["numbers"] == [1, 2, 3.14]
        assert parsed_result["boolean"] is True
        assert parsed_result["none_value"] is None

    def test_format_with_unicode_characters(self):
        """测试包含Unicode字符的记录格式化"""
        formatter = JsonFormatter(ensure_ascii=False)
        
        record = {
            "message": "测试消息：包含中文和特殊字符 🚀",
            "emoji": "🎉",
            "chinese": "中文测试",
            "special": "特殊字符：@#$%^&*()"
        }
        
        result = formatter.format(record)
        parsed_result = json.loads(result)
        
        assert parsed_result["message"] == "测试消息：包含中文和特殊字符 🚀"
        assert parsed_result["emoji"] == "🎉"
        assert parsed_result["chinese"] == "中文测试"
        assert parsed_result["special"] == "特殊字符：@#$%^&*()"

    def test_format_with_unicode_ascii(self):
        """测试Unicode字符的ASCII编码"""
        formatter = JsonFormatter(ensure_ascii=True)
        
        record = {
            "message": "测试消息：包含中文",
            "chinese": "中文测试"
        }
        
        result = formatter.format(record)
        parsed_result = json.loads(result)
        
        # Unicode字符应该被转义
        assert "\\u6d4b\\u8bd5" in result
        assert parsed_result["message"] == "测试消息：包含中文"
        assert parsed_result["chinese"] == "中文测试"

    def test_prepare_json_record(self):
        """测试JSON记录准备方法"""
        formatter = JsonFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "level": LogLevel.INFO,
            "normal_string": "normal value",
            "number": 42,
            "boolean": True,
            "none_value": None,
            "list": [1, 2, 3],
            "dict": {"key": "value"}
        }
        
        result = formatter._prepare_json_record(record)
        
        assert result["timestamp"] == "2023-01-15T10:30:45"
        assert result["level"] == "INFO"
        assert result["normal_string"] == "normal value"
        assert result["number"] == 42
        assert result["boolean"] is True
        assert result["none_value"] is None
        assert result["list"] == [1, 2, 3]
        assert result["dict"] == {"key": "value"}

    def test_format_empty_record(self):
        """测试空记录格式化"""
        formatter = JsonFormatter()
        
        record = {}
        
        result = formatter.format(record)
        parsed_result = json.loads(result)
        
        assert parsed_result == {}

    def test_format_nested_objects(self):
        """测试嵌套对象格式化"""
        formatter = JsonFormatter()
        
        record = {
            "level": LogLevel.ERROR,
            "message": "Nested object test",
            "nested": {
                "timestamp": datetime(2023, 1, 15, 10, 30, 45),
                "level": LogLevel.WARNING,
                "data": {
                    "deep": {
                        "value": "deep value"
                    }
                }
            }
        }
        
        result = formatter.format(record)
        parsed_result = json.loads(result)
        
        assert parsed_result["level"] == "ERROR"
        assert parsed_result["message"] == "Nested object test"
        assert parsed_result["nested"]["timestamp"] == "2023-01-15T10:30:45"
        assert parsed_result["nested"]["level"] == "WARNING"
        assert parsed_result["nested"]["data"]["deep"]["value"] == "deep value"

    def test_format_with_custom_objects(self):
        """测试包含自定义对象的记录格式化"""
        formatter = JsonFormatter()
        
        class CustomObject:
            def __init__(self, value):
                self.value = value
            
            def __str__(self):
                return f"CustomObject({self.value})"
        
        record = {
            "message": "Custom object test",
            "custom_obj": CustomObject("test_value"),
            "custom_none": None
        }
        
        result = formatter.format(record)
        parsed_result = json.loads(result)
        
        assert parsed_result["message"] == "Custom object test"
        assert parsed_result["custom_obj"] == "CustomObject(test_value)"
        assert parsed_result["custom_none"] is None

    def test_format_json_output_is_valid(self):
        """测试输出是有效的JSON"""
        formatter = JsonFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "level": LogLevel.CRITICAL,
            "message": "Valid JSON test",
            "data": {"key": "value", "number": 42}
        }
        
        result = formatter.format(record)
        
        # 应该能够解析为有效的JSON
        parsed_result = json.loads(result)
        assert isinstance(parsed_result, dict)
        assert "timestamp" in parsed_result
        assert "level" in parsed_result
        assert "message" in parsed_result
        assert "data" in parsed_result