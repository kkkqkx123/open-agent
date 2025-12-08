"""时间管理器单元测试

测试基础设施层时间管理器的基本功能。
"""

import pytest
from datetime import datetime, timedelta, timezone
from src.infrastructure.common.utils.temporal import TemporalManager


class TestTemporalManager:
    """测试时间管理器"""

    def test_now(self):
        """测试获取当前时间"""
        now = TemporalManager.now()
        assert isinstance(now, datetime)
        # 应为naive datetime（无时区）
        assert now.tzinfo is None

    def test_utc_now(self):
        """测试获取当前UTC时间"""
        utc_now = TemporalManager.utc_now()
        assert isinstance(utc_now, datetime)
        assert utc_now.tzinfo == timezone.utc

    def test_format_timestamp_iso(self):
        """测试ISO格式时间戳"""
        dt = datetime(2023, 1, 1, 12, 30, 45, 123456)
        formatted = TemporalManager.format_timestamp(dt, "iso")
        assert formatted == "2023-01-01T12:30:45.123456"
        
        # 测试带时区的时间
        dt_tz = datetime(2023, 1, 1, 12, 30, 45, tzinfo=timezone.utc)
        formatted = TemporalManager.format_timestamp(dt_tz, "iso")
        assert "2023-01-01T12:30:45+00:00" in formatted

    def test_format_timestamp_timestamp(self):
        """测试时间戳格式"""
        # naive datetime
        dt = datetime(2023, 1, 1, 12, 30, 45)
        formatted = TemporalManager.format_timestamp(dt, "timestamp")
        # 应为整数时间戳字符串
        assert formatted.isdigit()
        
        # 带时区的datetime
        dt_tz = datetime(2023, 1, 1, 12, 30, 45, tzinfo=timezone.utc)
        formatted = TemporalManager.format_timestamp(dt_tz, "timestamp")
        assert formatted.isdigit()

    def test_format_timestamp_readable(self):
        """测试可读格式"""
        dt = datetime(2023, 1, 1, 12, 30, 45)
        formatted = TemporalManager.format_timestamp(dt, "readable")
        assert formatted == "2023-01-01 12:30:45"

    def test_format_timestamp_unsupported_format(self):
        """测试不支持的格式"""
        dt = datetime.now()
        with pytest.raises(ValueError):
            TemporalManager.format_timestamp(dt, "unsupported")

    def test_parse_timestamp_iso(self):
        """测试解析ISO格式时间戳"""
        # 无时区
        dt = TemporalManager.parse_timestamp("2023-01-01T12:30:45", "iso")
        assert dt == datetime(2023, 1, 1, 12, 30, 45)
        
        # 带时区
        dt = TemporalManager.parse_timestamp("2023-01-01T12:30:45+00:00", "iso")
        assert dt.tzinfo == timezone.utc
        
        # 带微秒
        dt = TemporalManager.parse_timestamp("2023-01-01T12:30:45.123456", "iso")
        assert dt.microsecond == 123456

    def test_parse_timestamp_timestamp(self):
        """测试解析时间戳格式"""
        # 创建时间戳
        dt = datetime(2023, 1, 1, 12, 30, 45)
        import time
        timestamp = str(int(time.mktime(dt.timetuple())))
        
        parsed = TemporalManager.parse_timestamp(timestamp, "timestamp")
        # 解析后应为naive datetime
        assert parsed.tzinfo is None
        # 日期部分应相同
        assert parsed.year == 2023
        assert parsed.month == 1
        assert parsed.day == 1

    def test_parse_timestamp_readable(self):
        """测试解析可读格式"""
        dt = TemporalManager.parse_timestamp("2023-01-01 12:30:45", "readable")
        assert dt == datetime(2023, 1, 1, 12, 30, 45)

    def test_parse_timestamp_unsupported_format(self):
        """测试解析不支持的格式"""
        with pytest.raises(ValueError):
            TemporalManager.parse_timestamp("2023-01-01", "unsupported")

    def test_calculate_duration(self):
        """测试计算时间差"""
        start = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 13, 30, 0)  # 1.5小时后
        
        duration = TemporalManager.calculate_duration(start, end)
        assert duration == 5400.0  # 1.5小时 = 5400秒
        
        # 反向时间差为负
        duration = TemporalManager.calculate_duration(end, start)
        assert duration == -5400.0

    def test_calculate_duration_with_timezone(self):
        """测试带时区的时间差计算"""
        start = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        
        duration = TemporalManager.calculate_duration(start, end)
        assert duration == 3600.0
        
        # 混合时区（应自动调整）
        start = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 13, 0, 0)  # naive
        duration = TemporalManager.calculate_duration(start, end)
        # 结果可能因时区转换而不同，但至少不应出错
        assert isinstance(duration, float)

    def test_add_duration(self):
        """测试添加时间间隔"""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        new_dt = TemporalManager.add_duration(dt, 3600)  # 加1小时
        assert new_dt == datetime(2023, 1, 1, 13, 0, 0)
        
        # 负间隔
        new_dt = TemporalManager.add_duration(dt, -1800)  # 减30分钟
        assert new_dt == datetime(2023, 1, 1, 11, 30, 0)

    def test_is_expired(self):
        """测试检查是否过期"""
        # 未过期
        dt = datetime.now()
        assert TemporalManager.is_expired(dt, 3600) is False
        
        # 已过期
        past = datetime.now() - timedelta(hours=2)
        assert TemporalManager.is_expired(past, 3600) is True
        
        # 刚好过期
        past = datetime.now() - timedelta(seconds=3601)
        assert TemporalManager.is_expired(past, 3600) is True

    def test_is_expired_with_timezone(self):
        """测试带时区的过期检查"""
        # UTC时间
        dt = datetime.now(timezone.utc)
        assert TemporalManager.is_expired(dt, 3600) is False
        
        # naive datetime（假设为本地时间）
        dt = datetime.now()
        # 应能处理
        TemporalManager.is_expired(dt, 3600)

    def test_to_utc(self):
        """测试转换为UTC时间"""
        # naive datetime（假设为本地时间）
        dt = datetime(2023, 1, 1, 12, 0, 0)
        utc = TemporalManager.to_utc(dt)
        assert utc.tzinfo == timezone.utc
        
        # 已经是UTC时间
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        utc = TemporalManager.to_utc(dt)
        assert utc.tzinfo == timezone.utc

    def test_from_utc(self):
        """测试从UTC时间转换"""
        utc_dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # 转换为本地时区
        local = TemporalManager.from_utc(utc_dt)
        assert local.tzinfo is not None
        
        # 转换为指定时区
        target_tz = timezone(timedelta(hours=8))  # UTC+8
        beijing = TemporalManager.from_utc(utc_dt, target_tz)
        assert beijing.tzinfo == target_tz
        assert beijing.hour == 20  # UTC+8，12+8=20

    def test_static_methods(self):
        """测试所有静态方法"""
        # 确保所有方法都可以作为静态方法调用
        assert TemporalManager.now() is not None
        assert TemporalManager.utc_now() is not None
        assert TemporalManager.format_timestamp(datetime.now(), "iso") is not None
        assert TemporalManager.parse_timestamp("2023-01-01T12:00:00", "iso") is not None
        assert TemporalManager.calculate_duration(datetime.now(), datetime.now()) == 0.0
        assert TemporalManager.add_duration(datetime.now(), 0) is not None
        assert isinstance(TemporalManager.is_expired(datetime.now(), 3600), bool)
        assert TemporalManager.to_utc(datetime.now()) is not None
        assert TemporalManager.from_utc(datetime.now(timezone.utc)) is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])