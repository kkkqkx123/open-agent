"""LogLevel 类的单元测试"""

import pytest

from src.core.logger.log_level import LogLevel


class TestLogLevel:
    """LogLevel 测试类"""

    def test_log_level_values(self) -> None:
        """测试日志级别值"""
        assert LogLevel.DEBUG.value == 10
        assert LogLevel.INFO.value == 20
        assert LogLevel.WARNING.value == 30
        assert LogLevel.ERROR.value == 40
        assert LogLevel.CRITICAL.value == 50

    def test_from_string_valid_levels(self) -> None:
        """测试从字符串创建有效的日志级别"""
        assert LogLevel.from_string("DEBUG") == LogLevel.DEBUG
        assert LogLevel.from_string("INFO") == LogLevel.INFO
        assert LogLevel.from_string("WARNING") == LogLevel.WARNING
        assert LogLevel.from_string("WARN") == LogLevel.WARNING  # 别名测试
        assert LogLevel.from_string("ERROR") == LogLevel.ERROR
        assert LogLevel.from_string("CRITICAL") == LogLevel.CRITICAL
        assert LogLevel.from_string("FATAL") == LogLevel.CRITICAL  # 别名测试

    def test_from_string_case_insensitive(self) -> None:
        """测试 from_string 方法不区分大小写"""
        assert LogLevel.from_string("debug") == LogLevel.DEBUG
        assert LogLevel.from_string("Info") == LogLevel.INFO
        assert LogLevel.from_string("warning") == LogLevel.WARNING
        assert LogLevel.from_string("ERROR") == LogLevel.ERROR
        assert LogLevel.from_string("critical") == LogLevel.CRITICAL

    def test_from_string_invalid_level(self) -> None:
        """测试从无效字符串创建日志级别"""
        with pytest.raises(ValueError, match="无效的日志级别"):
            LogLevel.from_string("INVALID")
        
        with pytest.raises(ValueError, match="无效的日志级别"):
            LogLevel.from_string("")
        
        with pytest.raises(ValueError, match="无效的日志级别"):
            LogLevel.from_string("123")

    def test_str_representation(self) -> None:
        """测试日志级别的字符串表示"""
        assert str(LogLevel.DEBUG) == "DEBUG"
        assert str(LogLevel.INFO) == "INFO"
        assert str(LogLevel.WARNING) == "WARNING"
        assert str(LogLevel.ERROR) == "ERROR"
        assert str(LogLevel.CRITICAL) == "CRITICAL"

    def test_log_level_comparison(self) -> None:
        """测试日志级别比较"""
        assert LogLevel.DEBUG < LogLevel.INFO
        assert LogLevel.INFO < LogLevel.WARNING
        assert LogLevel.WARNING < LogLevel.ERROR
        assert LogLevel.ERROR < LogLevel.CRITICAL
        
        assert LogLevel.CRITICAL > LogLevel.ERROR
        assert LogLevel.ERROR > LogLevel.WARNING
        assert LogLevel.WARNING > LogLevel.INFO
        assert LogLevel.INFO > LogLevel.DEBUG

    def test_log_level_equality(self) -> None:
        """测试日志级别相等性"""
        assert LogLevel.DEBUG == LogLevel.DEBUG
        assert LogLevel.INFO == LogLevel.INFO
        assert LogLevel.WARNING == LogLevel.WARNING
        assert LogLevel.ERROR == LogLevel.ERROR
        assert LogLevel.CRITICAL == LogLevel.CRITICAL
        
        # 测试别名相等性
        assert LogLevel.WARNING == LogLevel.from_string("WARN")
        assert LogLevel.CRITICAL == LogLevel.from_string("FATAL")