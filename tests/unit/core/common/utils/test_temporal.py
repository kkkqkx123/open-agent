"""TemporalManager单元测试"""

from datetime import datetime, timedelta, timezone
import time
from src.core.common.utils.temporal import TemporalManager


class TestTemporalManager:
    """TemporalManager测试类"""

    def test_now(self):
        """测试获取当前时间"""
        dt = TemporalManager.now()
        assert isinstance(dt, datetime)
        
        # 验证时间接近当前时间（误差在1秒内）
        current_time = datetime.now()
        time_diff = abs((current_time - dt).total_seconds())
        assert time_diff < 1

    def test_utc_now(self):
        """测试获取当前UTC时间"""
        dt = TemporalManager.utc_now()
        assert isinstance(dt, datetime)
        assert dt.tzinfo is not None  # 应该是时区感知的

        # 验证是UTC时区
        assert dt.tzinfo == timezone.utc

    def test_format_timestamp_iso(self):
        """测试ISO格式化时间戳"""
        dt = datetime(2023, 12, 1, 10, 30, 45)
        formatted = TemporalManager.format_timestamp(dt, "iso")
        
        assert formatted == "2023-12-01T10:30:45"

    def test_format_timestamp_iso_with_timezone(self):
        """测试带时区的ISO格式化"""
        dt = datetime(2023, 12, 1, 10, 30, 45, tzinfo=timezone.utc)
        formatted = TemporalManager.format_timestamp(dt, "iso")
        
        assert "2023-12-01T10:30:45" in formatted  # 基本格式应该匹配

    def test_format_timestamp_timestamp(self):
        """测试时间戳格式化"""
        # 使用特定时间点进行测试
        dt = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        # 手动计算该时间的UTC时间戳
        expected_timestamp = "1672531200"  # 2023-01-01T00:00:00Z的时间戳
        
        formatted = TemporalManager.format_timestamp(dt, "timestamp")
        assert formatted == expected_timestamp

    def test_format_timestamp_readable(self):
        """测试可读格式化"""
        dt = datetime(2023, 12, 1, 10, 30, 45)
        formatted = TemporalManager.format_timestamp(dt, "readable")
        
        assert formatted == "2023-12-01 10:30:45"

    def test_format_timestamp_invalid_format(self):
        """测试无效格式"""
        dt = datetime(2023, 12, 1, 10, 30, 45)
        
        try:
            TemporalManager.format_timestamp(dt, "invalid_format")
            assert False, "应该抛出ValueError异常"
        except ValueError:
            pass  # 期望抛出异常

    def test_parse_timestamp_iso(self):
        """测试解析ISO时间戳"""
        iso_str = "2023-12-01T10:30:45"
        dt = TemporalManager.parse_timestamp(iso_str, "iso")
        
        assert dt.year == 2023
        assert dt.month == 12
        assert dt.day == 1
        assert dt.hour == 10
        assert dt.minute == 30
        assert dt.second == 45

    def test_parse_timestamp_iso_with_fraction(self):
        """测试解析带小数秒的ISO时间戳"""
        iso_str = "2023-12-01T10:30:45.123456"
        dt = TemporalManager.parse_timestamp(iso_str, "iso")
        
        assert dt.year == 2023
        assert dt.microsecond == 123456

    def test_parse_timestamp_iso_with_timezone(self):
        """测试解析带时区的ISO时间戳"""
        iso_str = "2023-12-01T10:30:45+00:00"
        dt = TemporalManager.parse_timestamp(iso_str, "iso")
        
        assert dt.year == 2023
        assert dt.hour == 10

    def test_parse_timestamp_timestamp(self):
        """测试解析时间戳"""
        timestamp_str = "1672531200"  # 2023-01-01T00:00:00 UTC
        dt = TemporalManager.parse_timestamp(timestamp_str, "timestamp")
        
        expected_dt = datetime(2023, 1, 1, 0, 0, 0)
        assert abs((dt - expected_dt).total_seconds()) < 1  # 允许一秒的误差

    def test_parse_timestamp_float_timestamp(self):
        """测试解析浮点时间戳"""
        timestamp_str = "1672531200.5"  # 带小数的时间戳
        dt = TemporalManager.parse_timestamp(timestamp_str, "timestamp")
        
        # 验证解析成功且时间合理
        assert isinstance(dt, datetime)

    def test_parse_timestamp_readable(self):
        """测试解析可读时间戳"""
        readable_str = "2023-12-01 10:30:45"
        dt = TemporalManager.parse_timestamp(readable_str, "readable")
        
        assert dt.year == 2023
        assert dt.month == 12
        assert dt.day == 1
        assert dt.hour == 10
        assert dt.minute == 30
        assert dt.second == 45

    def test_parse_timestamp_invalid_format(self):
        """测试解析无效格式"""
        try:
            TemporalManager.parse_timestamp("invalid", "invalid_format")
            assert False, "应该抛出ValueError异常"
        except ValueError:
            pass  # 期望抛出异常

    def test_calculate_duration(self):
        """测试计算时间差"""
        start = datetime(2023, 1, 1, 10, 0, 0)
        end = datetime(2023, 1, 1, 10, 5, 30)  # 5分30秒后
        
        duration = TemporalManager.calculate_duration(start, end)
        assert duration == 330  # 5分30秒 = 330秒

    def test_calculate_duration_with_timezone(self):
        """测试带时区的时间差计算"""
        start = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)  # 2小时后
        
        duration = TemporalManager.calculate_duration(start, end)
        assert duration == 7200  # 2小时 = 7200秒

    def test_calculate_duration_mixed_timezone(self):
        """测试混合时区的时间差计算"""
        start = datetime(2023, 1, 1, 10, 0, 0)  # naive
        end = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)  # aware
        
        duration = TemporalManager.calculate_duration(start, end)
        # 实现应该处理时区不匹配的情况

    def test_add_duration(self):
        """测试添加时间间隔"""
        dt = datetime(2023, 1, 1, 10, 0, 0)
        new_dt = TemporalManager.add_duration(dt, 3665)  # 添加1小时1分5秒
        
        expected = datetime(2023, 1, 1, 11, 1, 5)
        assert new_dt == expected

    def test_add_duration_negative(self):
        """测试添加负时间间隔"""
        dt = datetime(2023, 1, 1, 10, 0, 0)
        new_dt = TemporalManager.add_duration(dt, -3665)  # 减去1小时1分5秒
        
        expected = datetime(2023, 1, 1, 8, 58, 55)
        assert new_dt == expected

    def test_is_expired_true(self):
        """测试已过期时间"""
        # 创建一个过去的时间
        past_dt = datetime.now() - timedelta(seconds=120)  # 2分钟前
        ttl_seconds = 60  # 1分钟TTL
        
        result = TemporalManager.is_expired(past_dt, ttl_seconds)
        assert result is True

    def test_is_expired_false(self):
        """测试未过期时间"""
        # 创建一个较近的时间
        recent_dt = datetime.now() - timedelta(seconds=30)  # 30秒前
        ttl_seconds = 60  # 1分钟TTL
        
        result = TemporalManager.is_expired(recent_dt, ttl_seconds)
        assert result is False

    def test_is_expired_future(self):
        """测试未来时间"""
        # 创建一个未来的时间
        future_dt = datetime.now() + timedelta(hours=1) # 1小时后
        ttl_seconds = 60  # 1分钟TTL
        
        result = TemporalManager.is_expired(future_dt, ttl_seconds)
        assert result is False

    def test_to_utc_naive_datetime(self):
        """测试转换naive datetime到UTC"""
        # 创建一个naive datetime
        naive_dt = datetime(2023, 1, 12, 0, 0)
        utc_dt = TemporalManager.to_utc(naive_dt)
        
        assert utc_dt.tzinfo == timezone.utc

    def test_to_utc_aware_datetime(self):
        """测试转换aware datetime到UTC"""
        # 创建一个带时区的datetime
        aware_dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        utc_dt = TemporalManager.to_utc(aware_dt)
        
        assert utc_dt.tzinfo == timezone.utc

    def test_from_utc_to_local(self):
        """测试从UTC转换到本地时区"""
        utc_dt = datetime(2023, 1, 12, 0, 0, tzinfo=timezone.utc)
        local_dt = TemporalManager.from_utc(utc_dt)
        
        assert local_dt.tzinfo is not None

    def test_from_utc_to_specific_timezone(self):
        """测试从UTC转换到特定时区"""
        utc_dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        tz = timezone(timedelta(hours=8))  # UTC+8
        specific_dt = TemporalManager.from_utc(utc_dt, tz)
        
        assert specific_dt.tzinfo == tz

    def test_format_and_parse_roundtrip(self):
        """测试格式化和解析往返"""
        original_dt = datetime(2023, 12, 1, 15, 30, 45)
        
        # 格式化为ISO
        iso_str = TemporalManager.format_timestamp(original_dt, "iso")
        
        # 解析回来
        parsed_dt = TemporalManager.parse_timestamp(iso_str, "iso")
        
        # 验证时间值相同（对于naive datetime）
        assert parsed_dt.year == original_dt.year
        assert parsed_dt.month == original_dt.month
        assert parsed_dt.day == original_dt.day
        assert parsed_dt.hour == original_dt.hour
        assert parsed_dt.minute == original_dt.minute
        assert parsed_dt.second == original_dt.second

    def test_timestamp_format_and_parse_roundtrip(self):
        """测试时间戳格式的往返"""
        original_dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # 格式化为时间戳
        timestamp_str = TemporalManager.format_timestamp(original_dt, "timestamp")
        
        # 解析回来
        parsed_dt = TemporalManager.parse_timestamp(timestamp_str, "timestamp")
        
        # 验证时间接近（由于转换过程中的精度可能略有差异）
        time_diff = abs((original_dt.replace(tzinfo=None) - parsed_dt).total_seconds())
        assert time_diff < 1

    def test_calculate_duration_edge_cases(self):
        """测试时间差计算边界情况"""
        # 相同时间
        dt = datetime(2023, 1, 1, 12, 0, 0)
        duration = TemporalManager.calculate_duration(dt, dt)
        assert duration == 0

        # 负时间差（结束时间早于开始时间）
        start = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 11, 0, 0)
        duration = TemporalManager.calculate_duration(start, end)
        assert duration == -3600  # -1小时