"""BaseHandler 类的单元测试"""

import sys
import pytest
from typing import Any, Dict
from unittest.mock import Mock, patch, MagicMock

from src.core.logger.handlers.base_handler import BaseHandler
from src.core.logger.log_level import LogLevel


class ConcreteHandler(BaseHandler):
    """用于测试的具体处理器实现"""

    def emit(self, record: Dict[str, Any]) -> None:
        """实现抽象方法"""
        pass


class TestBaseHandler:
    """BaseHandler 测试类"""

    def test_init_default_values(self):
        """测试默认值初始化"""
        handler = ConcreteHandler()
        
        assert handler.level == LogLevel.INFO
        assert handler.config == {}
        assert handler._formatter is None

    def test_init_custom_values(self):
        """测试自定义值初始化"""
        custom_level = LogLevel.ERROR
        custom_config = {"key1": "value1", "key2": "value2"}
        
        handler = ConcreteHandler(level=custom_level, config=custom_config)
        
        assert handler.level == custom_level
        assert handler.config == custom_config
        assert handler._formatter is None

    def test_init_none_config(self):
        """测试None配置初始化"""
        handler = ConcreteHandler(config=None)
        
        assert handler.config == {}

    def test_set_level(self):
        """测试设置日志级别"""
        handler = ConcreteHandler()
        
        # 测试设置不同级别
        handler.set_level(LogLevel.DEBUG)
        assert handler.level == LogLevel.DEBUG
        
        handler.set_level(LogLevel.WARNING)
        assert handler.level == LogLevel.WARNING
        
        handler.set_level(LogLevel.CRITICAL)
        assert handler.level == LogLevel.CRITICAL

    def test_set_formatter(self):
        """测试设置格式化器"""
        handler = ConcreteHandler()
        mock_formatter = Mock()
        
        handler.set_formatter(mock_formatter)
        
        assert handler._formatter == mock_formatter

    def test_format_without_formatter(self):
        """测试没有格式化器时的格式化"""
        handler = ConcreteHandler()
        record = {"message": "test message", "level": LogLevel.INFO}
        
        result = handler.format(record)
        
        # 应该返回原始记录
        assert result == record

    def test_format_with_formatter(self):
        """测试有格式化器时的格式化"""
        handler = ConcreteHandler()
        mock_formatter = Mock()
        mock_formatter.format.return_value = "formatted message"
        
        handler.set_formatter(mock_formatter)
        record = {"message": "test message", "level": LogLevel.INFO}
        
        result = handler.format(record)
        
        # 应该返回包含格式化消息的记录
        assert result["formatted_message"] == "formatted message"
        assert result["message"] == "test message"  # 原始字段应该保留

    def test_handle_level_filtering(self):
        """测试日志级别过滤"""
        handler = ConcreteHandler(level=LogLevel.WARNING)
        
        # 创建模拟的emit方法
        handler.emit = Mock()
        
        # 测试低于设置级别的记录（应该被过滤）
        debug_record = {"message": "debug", "level": LogLevel.DEBUG}
        info_record = {"message": "info", "level": LogLevel.INFO}
        
        handler.handle(debug_record)
        handler.handle(info_record)
        
        # emit方法不应该被调用
        handler.emit.assert_not_called()
        
        # 测试等于或高于设置级别的记录（应该被处理）
        warning_record = {"message": "warning", "level": LogLevel.WARNING}
        error_record = {"message": "error", "level": LogLevel.ERROR}
        critical_record = {"message": "critical", "level": LogLevel.CRITICAL}
        
        handler.handle(warning_record)
        handler.handle(error_record)
        handler.handle(critical_record)
        
        # emit方法应该被调用3次
        assert handler.emit.call_count == 3

    def test_handle_emit_exception(self):
        """测试emit方法异常处理"""
        handler = ConcreteHandler()
        
        # 模拟emit方法抛出异常
        handler.emit = Mock(side_effect=Exception("Test exception"))
        
        # 模拟handleError方法
        handler.handleError = Mock()
        
        record = {"message": "test", "level": LogLevel.INFO}
        
        # 应该不会抛出异常
        handler.handle(record)
        
        # handleError应该被调用
        handler.handleError.assert_called_once_with(record)

    def test_flush(self):
        """测试刷新方法"""
        handler = ConcreteHandler()
        
        # 默认的flush方法应该什么都不做（不抛出异常）
        handler.flush()

    def test_close(self):
        """测试关闭方法"""
        handler = ConcreteHandler()
        
        # 模拟flush方法
        handler.flush = Mock()
        
        handler.close()
        
        # flush应该被调用
        handler.flush.assert_called_once()

    def test_handle_error(self):
        """测试错误处理方法"""
        handler = ConcreteHandler()
        record = {"message": "test", "level": LogLevel.INFO}
        
        # 测试正常情况（不应该抛出异常）
        handler.handleError(record)

    @patch('sys.stderr.write')
    def test_handle_error_stderr_write(self, mock_stderr_write):
        """测试错误处理写入stderr"""
        handler = ConcreteHandler()
        record = {"message": "test", "level": LogLevel.INFO}
        
        handler.handleError(record)
        
        # 应该调用stderr.write
        assert mock_stderr_write.call_count == 3  # 三次调用：错误信息、记录、提示

    @patch('sys.stderr.write')
    def test_handle_error_stderr_exception(self, mock_stderr_write):
        """测试错误处理本身异常"""
        # 模拟stderr.write抛出异常
        mock_stderr_write.side_effect = Exception("stderr error")
        
        handler = ConcreteHandler()
        record = {"message": "test", "level": LogLevel.INFO}
        
        # 应该不会抛出异常
        handler.handleError(record)

    def test_handle_missing_level(self):
        """测试处理缺少级别的记录"""
        handler = ConcreteHandler()
        handler.emit = Mock()
        
        # 缺少level字段的记录
        record = {"message": "test"}
        
        # 应该抛出KeyError
        with pytest.raises(KeyError):
            handler.handle(record)

    def test_handle_invalid_level_type(self):
        """测试处理无效级别类型的记录"""
        handler = ConcreteHandler()
        handler.emit = Mock()
        
        # level字段不是LogLevel类型的记录
        record = {"message": "test", "level": "invalid"}
        
        # 应该抛出AttributeError
        with pytest.raises(AttributeError):
            handler.handle(record)

    def test_format_record_copy(self):
        """测试格式化记录时创建副本"""
        handler = ConcreteHandler()
        mock_formatter = Mock()
        mock_formatter.format.return_value = "formatted message"
        
        handler.set_formatter(mock_formatter)
        original_record = {"message": "test", "level": LogLevel.INFO}
        
        result = handler.format(original_record)
        
        # 结果应该是原始记录的副本，加上格式化消息
        assert result is not original_record  # 不是同一个对象
        assert result["message"] == "test"
        assert result["level"] == LogLevel.INFO
        assert result["formatted_message"] == "formatted message"
        
        # 原始记录不应该被修改
        assert "formatted_message" not in original_record

    def test_abstract_class(self):
        """测试抽象类不能直接实例化"""
        with pytest.raises(TypeError):
            BaseHandler()  # 不能直接实例化抽象类

    def test_level_comparison(self):
        """测试级别比较逻辑"""
        handler = ConcreteHandler(level=LogLevel.WARNING)
        handler.emit = Mock()
        
        # 测试各种级别组合
        test_cases = [
            (LogLevel.DEBUG, False),    # 低于WARNING，应该被过滤
            (LogLevel.INFO, False),     # 低于WARNING，应该被过滤
            (LogLevel.WARNING, True),   # 等于WARNING，应该被处理
            (LogLevel.ERROR, True),     # 高于WARNING，应该被处理
            (LogLevel.CRITICAL, True),  # 高于WARNING，应该被处理
        ]
        
        for level, should_emit in test_cases:
            handler.emit.reset_mock()
            record = {"message": "test", "level": level}
            
            handler.handle(record)
            
            if should_emit:
                handler.emit.assert_called_once_with(record)
            else:
                handler.emit.assert_not_called()

    def test_config_access(self):
        """测试配置访问"""
        custom_config = {"filename": "test.log", "mode": "w"}
        handler = ConcreteHandler(config=custom_config)
        
        assert handler.config["filename"] == "test.log"
        assert handler.config["mode"] == "w"