"""ConsoleHandler 类的单元测试"""

import sys
import pytest
from datetime import datetime
from typing import Any, Dict
from unittest.mock import Mock, patch, MagicMock

from src.core.logger.handlers.console_handler import ConsoleHandler
from src.core.logger.log_level import LogLevel
from src.core.logger.formatters.text_formatter import TextFormatter
from src.core.logger.formatters.color_formatter import ColorFormatter


class TestConsoleHandler:
    """ConsoleHandler 测试类"""

    def test_init_default_values(self):
        """测试默认值初始化"""
        handler = ConsoleHandler()
        
        assert handler.level == LogLevel.INFO
        assert handler.config == {}
        assert isinstance(handler._formatter, TextFormatter) # 默认格式化器
        assert handler.stream == sys.stdout
        assert handler.use_color is False

    def test_init_custom_values(self):
        """测试自定义值初始化"""
        custom_level = LogLevel.DEBUG
        custom_config = {"stream": sys.stderr, "use_color": True}
        
        handler = ConsoleHandler(level=custom_level, config=custom_config)
        
        assert handler.level == custom_level
        assert handler.config == custom_config
        assert handler.stream == sys.stderr
        assert handler.use_color is True
        assert isinstance(handler._formatter, ColorFormatter)  # 使用颜色格式化器

    def test_init_with_color_config(self):
        """测试使用颜色配置初始化"""
        config = {"use_color": True}
        handler = ConsoleHandler(config=config)
        
        assert handler.use_color is True
        assert isinstance(handler._formatter, ColorFormatter)

    def test_init_with_non_color_config(self):
        """测试使用非颜色配置初始化"""
        config = {"use_color": False}
        handler = ConsoleHandler(config=config)
        
        assert handler.use_color is False
        assert isinstance(handler._formatter, TextFormatter)

    def test_init_with_no_config(self):
        """测试无配置初始化"""
        handler = ConsoleHandler()
        
        assert handler.stream == sys.stdout
        assert handler.use_color is False

    def test_emit_basic_record(self):
        """测试基本记录输出"""
        handler = ConsoleHandler()
        mock_stream = Mock()
        handler.stream = mock_stream
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.INFO,
            "message": "Test message"
        }
        
        handler.emit(record)
        
        # 检查是否写入了格式化消息
        mock_stream.write.assert_called_once()
        mock_stream.flush.assert_called_once()

    def test_emit_with_formatter(self):
        """测试使用格式化器输出"""
        handler = ConsoleHandler()
        mock_stream = Mock()
        handler.stream = mock_stream
        
        # 设置自定义格式化器
        mock_formatter = Mock()
        mock_formatter.format.return_value = "Formatted test message"
        handler.set_formatter(mock_formatter)
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.INFO,
            "message": "Test message"
        }
        
        handler.emit(record)
        
        # 验证格式化器被调用
        mock_formatter.format.assert_called_once_with(record)
        # 验证写入格式化后的消息
        mock_stream.write.assert_called_once()
        assert "Formatted test message" in str(mock_stream.write.call_args[0][0])

    def test_emit_level_filtering(self):
        """测试日志级别过滤"""
        handler = ConsoleHandler(level=LogLevel.WARNING)
        mock_stream = Mock()
        handler.stream = mock_stream
        
        # 测试低于设置级别的记录（应该被过滤）
        debug_record = {"message": "debug", "level": LogLevel.DEBUG}
        info_record = {"message": "info", "level": LogLevel.INFO}
        
        handler.handle(debug_record)
        handler.handle(info_record)
        
        # stream.write不应该被调用
        mock_stream.write.assert_not_called()
        
        # 测试等于或高于设置级别的记录（应该被处理）
        warning_record = {"message": "warning", "level": LogLevel.WARNING}
        error_record = {"message": "error", "level": LogLevel.ERROR}
        critical_record = {"message": "critical", "level": LogLevel.CRITICAL}
        
        handler.handle(warning_record)
        handler.handle(error_record)
        handler.handle(critical_record)
        
        # stream.write应该被调用3次
        assert mock_stream.write.call_count == 3

    def test_flush_method(self):
        """测试刷新方法"""
        handler = ConsoleHandler()
        mock_stream = Mock()
        handler.stream = mock_stream
        
        handler.flush()
        
        mock_stream.flush.assert_called_once()

    def test_flush_method_with_non_flushable_stream(self):
        """测试不可刷新流的刷新方法"""
        handler = ConsoleHandler()
        # 创建一个没有flush方法的对象
        class NoFlushStream:
            def write(self, data):
                pass
        
        handler.stream = NoFlushStream()
        
        # 这不应该抛出异常
        handler.flush()

    def test_emit_with_color_formatter(self):
        """测试使用颜色格式化器输出"""
        config = {"use_color": True}
        handler = ConsoleHandler(config=config)
        mock_stream = Mock()
        handler.stream = mock_stream
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "test_logger",
            "level": LogLevel.ERROR,
            "message": "Error message"
        }
        
        handler.emit(record)
        
        # 检查是否写入了包含颜色代码的消息
        mock_stream.write.assert_called_once()
        written_message = mock_stream.write.call_args[0][0]
        # 错误级别应该使用红色ANSI代码
        assert written_message.startswith("\033[31m")

    def test_emit_to_stderr(self):
        """测试输出到stderr"""
        config = {"stream": sys.stderr}
        handler = ConsoleHandler(config=config)
        mock_stderr = Mock()
        handler.stream = mock_stderr
        
        record = {
            "message": "Test to stderr",
            "level": LogLevel.INFO
        }
        
        handler.emit(record)
        
        mock_stderr.write.assert_called_once()
        mock_stderr.flush.assert_called_once()

    def test_handle_error(self):
        """测试错误处理"""
        handler = ConsoleHandler()
        mock_stream = Mock()
        mock_stream.write.side_effect = Exception("Write error")
        handler.stream = mock_stream
        
        record = {
            "message": "Test message",
            "level": LogLevel.INFO
        }
        
        # 应该不会抛出异常，因为错误被处理了
        handler.emit(record)

    def test_init_with_empty_config(self):
        """测试空配置初始化"""
        handler = ConsoleHandler(config={})
        
        assert handler.stream == sys.stdout
        assert handler.use_color is False
        assert isinstance(handler._formatter, TextFormatter)

    def test_set_formatter(self):
        """测试设置格式化器"""
        handler = ConsoleHandler()
        mock_formatter = Mock()
        
        handler.set_formatter(mock_formatter)
        
        assert handler._formatter == mock_formatter

    def test_emit_with_none_message(self):
        """测试None消息输出"""
        handler = ConsoleHandler()
        mock_stream = Mock()
        handler.stream = mock_stream
        
        record = {
            "message": None,
            "level": LogLevel.INFO
        }
        
        handler.emit(record)
        
        mock_stream.write.assert_called_once()

    def test_emit_with_complex_record(self):
        """测试复杂记录输出"""
        handler = ConsoleHandler()
        mock_stream = Mock()
        handler.stream = mock_stream
        
        record = {
            "timestamp": datetime(2023, 1, 15, 10, 30, 45),
            "name": "complex_logger",
            "level": LogLevel.DEBUG,
            "message": "Debug message",
            "data": {"key": "value"},
            "number": 42
        }
        
        handler.emit(record)
        
        mock_stream.write.assert_called_once()
        mock_stream.flush.assert_called_once()

    def test_multiple_emits(self):
        """测试多次输出"""
        handler = ConsoleHandler()
        mock_stream = Mock()
        handler.stream = mock_stream
        
        records = [
            {"message": "Message 1", "level": LogLevel.INFO},
            {"message": "Message 2", "level": LogLevel.WARNING},
            {"message": "Message 3", "level": LogLevel.ERROR},
        ]
        
        for record in records:
            handler.emit(record)
        
        assert mock_stream.write.call_count == len(records)
        assert mock_stream.flush.call_count == len(records)

    def test_set_level(self):
        """测试设置日志级别"""
        handler = ConsoleHandler()
        
        handler.set_level(LogLevel.DEBUG)
        assert handler.level == LogLevel.DEBUG
        
        handler.set_level(LogLevel.CRITICAL)
        assert handler.level == LogLevel.CRITICAL