"""日志记录器单元测试"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from src.logger.logger import Logger, LogLevel, get_logger, set_global_config
from src.logger.redactor import LogRedactor
from src.config.models.global_config import GlobalConfig, LogOutputConfig


class TestLogger:
    """日志记录器测试类"""

    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return GlobalConfig(
            log_level="INFO",
            log_outputs=[
                LogOutputConfig(
                    type="console",
                    level="INFO",
                    format="text",
                    path=None,
                    rotation=None,
                    max_size=None,
                )
            ],
            secret_patterns=["sk-.*"],
            env="testing",
            debug=False,
            env_prefix="AGENT_",
            hot_reload=False,
            watch_interval=5,
        )

    @pytest.fixture
    def logger(self, mock_config):
        """创建日志记录器实例"""
        return Logger("test_logger", mock_config)

    def test_log_level_filtering(self, logger):
        """测试日志级别过滤"""
        mock_handler = Mock()
        logger._handlers = [mock_handler]

        # DEBUG 级别不应记录（配置为 INFO）
        logger.debug("Debug message")
        mock_handler.handle.assert_not_called()

        # INFO 级别应该记录
        logger.info("Info message")
        mock_handler.handle.assert_called_once()

        # 验证调用参数
        call_args = mock_handler.handle.call_args[0][0]
        assert call_args["level"] == LogLevel.INFO
        assert call_args["message"] == "Info message"

    def test_log_redaction(self, mock_config):
        """测试日志脱敏"""
        mock_handler = Mock()
        mock_redactor = Mock()
        mock_redactor.redact.return_value = "Redacted message"

        logger = Logger("test_logger", mock_config, mock_redactor)
        logger._handlers = [mock_handler]

        logger.info("Original message with sk-abc123")

        # 验证脱敏器被调用（消息和日志记录器名称都会被脱敏）
        assert mock_redactor.redact.call_count >= 1
        # 验证消息被脱敏
        mock_redactor.redact.assert_any_call(
            "Original message with sk-abc123", LogLevel.INFO
        )

        # 验证处理器接收到脱敏后的消息
        call_args = mock_handler.handle.call_args[0][0]
        assert call_args["message"] == "Redacted message"

    def test_set_level(self, logger):
        """测试设置日志级别"""
        logger.set_level(LogLevel.ERROR)
        assert logger.get_level() == LogLevel.ERROR

        mock_handler = Mock()
        logger._handlers = [mock_handler]

        # WARNING 级别不应记录（设置为 ERROR）
        logger.warning("Warning message")
        mock_handler.handle.assert_not_called()

        # ERROR 级别应该记录
        logger.error("Error message")
        mock_handler.handle.assert_called_once()

    def test_add_remove_handler(self, logger):
        """测试添加和移除处理器"""
        mock_handler1 = Mock()
        mock_handler2 = Mock()

        # 添加处理器
        logger.add_handler(mock_handler1)
        assert mock_handler1 in logger.get_handlers()

        logger.add_handler(mock_handler2)
        assert mock_handler2 in logger.get_handlers()

        # 移除处理器
        logger.remove_handler(mock_handler1)
        assert mock_handler1 not in logger.get_handlers()
        assert mock_handler2 in logger.get_handlers()

    def test_log_record_creation(self, logger):
        """测试日志记录创建"""
        record = logger._create_log_record(
            LogLevel.INFO, "Test message", extra_field="extra_value"
        )

        assert record["name"] == "test_logger"
        assert record["level"] == LogLevel.INFO
        assert record["message"] == "Test message"
        assert record["extra_field"] == "extra_value"
        assert "timestamp" in record
        assert "thread_id" in record

    def test_should_log(self, logger):
        """测试日志级别检查"""
        # 设置为 INFO 级别
        logger.set_level(LogLevel.INFO)

        # DEBUG 不应该记录
        assert not logger._should_log(LogLevel.DEBUG)

        # INFO 应该记录
        assert logger._should_log(LogLevel.INFO)

        # WARNING 应该记录
        assert logger._should_log(LogLevel.WARNING)

        # ERROR 应该记录
        assert logger._should_log(LogLevel.ERROR)

        # CRITICAL 应该记录
        assert logger._should_log(LogLevel.CRITICAL)

    def test_flush_and_close(self, logger):
        """测试刷新和关闭"""
        mock_handler1 = Mock()
        mock_handler2 = Mock()

        logger._handlers = [mock_handler1, mock_handler2]

        # 测试刷新
        logger.flush()
        mock_handler1.flush.assert_called_once()
        mock_handler2.flush.assert_called_once()

        # 测试关闭
        logger.close()
        mock_handler1.close.assert_called_once()
        mock_handler2.close.assert_called_once()
        assert len(logger._handlers) == 0


class TestGlobalLogger:
    """全局日志记录器测试类"""

    def test_get_logger(self):
        """测试获取日志记录器"""
        logger1 = get_logger("test")
        logger2 = get_logger("test")

        # 相同名称应该返回同一实例
        assert logger1 is logger2

        # 不同名称应该返回不同实例
        logger3 = get_logger("another_test")
        assert logger1 is not logger3

    @patch("src.logger.logger._loggers")
    def test_set_global_config(self, mock_loggers):
        """测试设置全局配置"""
        mock_logger = Mock()
        mock_logger._handlers = []  # 添加空的处理器列表
        mock_loggers.values.return_value = [mock_logger]

        config = GlobalConfig(
            log_level="DEBUG",
            log_outputs=[
                LogOutputConfig(
                    type="console",
                    level="DEBUG",
                    format="text",
                    path=None,
                    rotation=None,
                    max_size=None,
                )
            ],
            secret_patterns=["sk-.*"],
            env="testing",
            debug=True,
            env_prefix="AGENT_",
            hot_reload=False,
            watch_interval=5,
        )

        set_global_config(config)

        # 验证配置被设置
        assert mock_logger._config == config
        assert mock_logger._level == LogLevel.DEBUG

        # 验证处理器被重新设置（直接调用处理器的close方法，不调用logger的close方法）
        mock_logger._setup_handlers_from_config.assert_called_once()


class TestLogLevel:
    """日志级别测试类"""

    def test_from_string(self):
        """测试从字符串创建日志级别"""
        assert LogLevel.from_string("DEBUG") == LogLevel.DEBUG
        assert LogLevel.from_string("INFO") == LogLevel.INFO
        assert LogLevel.from_string("WARNING") == LogLevel.WARNING
        assert LogLevel.from_string("WARN") == LogLevel.WARNING
        assert LogLevel.from_string("ERROR") == LogLevel.ERROR
        assert LogLevel.from_string("CRITICAL") == LogLevel.CRITICAL
        assert LogLevel.from_string("FATAL") == LogLevel.CRITICAL

        # 测试大小写不敏感
        assert LogLevel.from_string("debug") == LogLevel.DEBUG
        assert LogLevel.from_string("Info") == LogLevel.INFO

        # 测试无效级别
        with pytest.raises(ValueError):
            LogLevel.from_string("INVALID")

    def test_str_representation(self):
        """测试字符串表示"""
        assert str(LogLevel.DEBUG) == "DEBUG"
        assert str(LogLevel.INFO) == "INFO"
        assert str(LogLevel.WARNING) == "WARNING"
        assert str(LogLevel.ERROR) == "ERROR"
        assert str(LogLevel.CRITICAL) == "CRITICAL"
