"""ColorFormatter 类的单元测试"""

import pytest
from datetime import datetime
from typing import Any, Dict

from src.core.logger.formatters.color_formatter import ColorFormatter
from src.core.logger.log_level import LogLevel


class TestColorFormatter:
    """ColorFormatter 测试类"""

    def test_init_default_values(self):
        """测试默认值初始化"""
        formatter = ColorFormatter()
        
        assert formatter.fmt == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert formatter.datefmt == "%Y-%m-%d %H:%M:%S"

    def test_init_custom_values(self):
        """测试自定义值初始化"""
        custom_fmt = "%(levelname)s: %(message)s"
        custom_datefmt = "%Y/%m/%d %H:%M:%S"
        
        formatter = ColorFormatter(fmt=custom_fmt, datefmt=custom_datefmt)
        
        assert formatter.fmt == custom_fmt
        assert formatter.datefmt == custom_datefmt

    def test_colors_mapping(self):
        """测试颜色映射"""
        assert ColorFormatter.COLORS[LogLevel.DEBUG] == "\033[36m"  # 青色
        assert ColorFormatter.COLORS[LogLevel.INFO] == "\033[32m"   # 绿色
        assert ColorFormatter.COLORS[LogLevel.WARNING] == "\033[33m"  # 黄色
        assert ColorFormatter.COLORS[LogLevel.ERROR] == "\033[31m"   # 红色
        assert ColorFormatter.COLORS[LogLevel.CRITICAL] == "\033[35m" # 紫色

    def test_reset_code(self):
        """测试重置代码"""
        assert ColorFormatter.RESET == "\033[0m"

    def test_format_debug_level(self):
        """测试DEBUG级别格式化"""
        formatter = ColorFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.DEBUG,
            "message": "Debug message"
        }
        
        result = formatter.format(record)
        expected_base = "2023-01-15 10:30:45 - test_logger - DEBUG - Debug message"
        expected_colored = f"\033[36m{expected_base}\033[0m"
        
        assert result == expected_colored

    def test_format_info_level(self):
        """测试INFO级别格式化"""
        formatter = ColorFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.INFO,
            "message": "Info message"
        }
        
        result = formatter.format(record)
        expected_base = "2023-01-15 10:30:45 - test_logger - INFO - Info message"
        expected_colored = f"\033[32m{expected_base}\033[0m"
        
        assert result == expected_colored

    def test_format_warning_level(self):
        """测试WARNING级别格式化"""
        formatter = ColorFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.WARNING,
            "message": "Warning message"
        }
        
        result = formatter.format(record)
        expected_base = "2023-01-15 10:30:45 - test_logger - WARNING - Warning message"
        expected_colored = f"\033[33m{expected_base}\033[0m"
        
        assert result == expected_colored

    def test_format_error_level(self):
        """测试ERROR级别格式化"""
        formatter = ColorFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.ERROR,
            "message": "Error message"
        }
        
        result = formatter.format(record)
        expected_base = "2023-01-15 10:30:45 - test_logger - ERROR - Error message"
        expected_colored = f"\033[31m{expected_base}\033[0m"
        
        assert result == expected_colored

    def test_format_critical_level(self):
        """测试CRITICAL级别格式化"""
        formatter = ColorFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.CRITICAL,
            "message": "Critical message"
        }
        
        result = formatter.format(record)
        expected_base = "2023-01-15 10:30:45 - test_logger - CRITICAL - Critical message"
        expected_colored = f"\033[35m{expected_base}\033[0m"
        
        assert result == expected_colored

    def test_format_unknown_level(self):
        """测试未知日志级别格式化"""
        formatter = ColorFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.INFO,  # 使用已知级别但测试未知级别处理
            "message": "Test message"
        }
        
        # 模拟未知级别
        record["level"] = "UNKNOWN_LEVEL"
        
        result = formatter.format(record)
        expected_base = "2023-01-15 10:30:45 - test_logger - INFO - Test message"
        
        # 未知级别应该没有颜色
        assert result == expected_base

    def test_format_missing_level(self):
        """测试缺少日志级别的记录格式化"""
        formatter = ColorFormatter()
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "message": "Test message"
        }
        
        result = formatter.format(record)
        expected_base = "2023-01-15 10:30:45 - test_logger - INFO - Test message"
        expected_colored = f"\033[32m{expected_base}\033[0m"  # 默认INFO级别，绿色
        
        assert result == expected_colored

    def test_format_custom_format(self):
        """测试自定义格式"""
        custom_fmt = "%(levelname)s: %(message)s"
        formatter = ColorFormatter(fmt=custom_fmt)
        
        record = {
            "level": LogLevel.ERROR,
            "message": "Error occurred"
        }
        
        result = formatter.format(record)
        expected_base = "ERROR: Error occurred"
        expected_colored = f"\033[31m{expected_base}\033[0m"
        
        assert result == expected_colored

    def test_format_custom_date_format(self):
        """测试自定义日期格式"""
        custom_datefmt = "%Y/%m/%d %H:%M:%S"
        formatter = ColorFormatter(datefmt=custom_datefmt)
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.WARNING,
            "message": "Warning message"
        }
        
        result = formatter.format(record)
        expected_base = "2023/01/15 10:30:45 - test_logger - WARNING - Warning message"
        expected_colored = f"\033[33m{expected_base}\033[0m"
        
        assert result == expected_colored

    def test_format_additional_fields(self):
        """测试格式化额外字段"""
        custom_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(module)s:%(line)d]"
        formatter = ColorFormatter(fmt=custom_fmt)
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.DEBUG,
            "message": "Debug message",
            "module": "test_module",
            "line": 123
        }
        
        result = formatter.format(record)
        expected_base = "2023-01-15 10:30:45 - test_logger - DEBUG - Debug message [test_module:123]"
        expected_colored = f"\033[36m{expected_base}\033[0m"
        
        assert result == expected_colored

    def test_format_empty_record(self):
        """测试空记录格式化"""
        formatter = ColorFormatter()
        
        record = {}
        
        result = formatter.format(record)
        expected_base = " - unknown - INFO - "
        expected_colored = f"\033[32m{expected_base}\033[0m"  # 默认INFO级别，绿色
        
        assert result == expected_colored

    def test_inheritance_from_text_formatter(self):
        """测试继承自TextFormatter"""
        formatter = ColorFormatter()
        
        # 应该有TextFormatter的所有属性和方法
        assert hasattr(formatter, 'fmt')
        assert hasattr(formatter, 'datefmt')
        assert hasattr(formatter, 'format')
        assert hasattr(formatter, '_format_additional_fields')

    def test_color_codes_are_applied(self):
        """测试颜色代码是否正确应用"""
        formatter = ColorFormatter()
        
        record = {
            "level": LogLevel.ERROR,
            "message": "Error message"
        }
        
        result = formatter.format(record)
        
        # 检查是否包含颜色代码
        assert result.startswith("\033[31m")  # 红色开始
        assert result.endswith("\033[0m")     # 重置颜色
        
        # 检查中间部分是否包含原始消息
        assert "Error message" in result

    def test_different_levels_different_colors(self):
        """测试不同级别使用不同颜色"""
        formatter = ColorFormatter()
        
        base_record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "message": "Test message"
        }
        
        # 测试每个级别的颜色
        debug_record = {**base_record, "level": LogLevel.DEBUG}
        info_record = {**base_record, "level": LogLevel.INFO}
        warning_record = {**base_record, "level": LogLevel.WARNING}
        error_record = {**base_record, "level": LogLevel.ERROR}
        critical_record = {**base_record, "level": LogLevel.CRITICAL}
        
        debug_result = formatter.format(debug_record)
        info_result = formatter.format(info_record)
        warning_result = formatter.format(warning_record)
        error_result = formatter.format(error_record)
        critical_result = formatter.format(critical_record)
        
        # 检查每个结果都有不同的颜色代码
        assert debug_result.startswith("\033[36m")  # 青色
        assert info_result.startswith("\033[32m")   # 绿色
        assert warning_result.startswith("\033[33m") # 黄色
        assert error_result.startswith("\033[31m")   # 红色
        assert critical_result.startswith("\033[35m") # 紫色
        
        # 所有结果都应该以重置代码结束
        assert all(result.endswith("\033[0m") for result in [
            debug_result, info_result, warning_result, error_result, critical_result
        ])