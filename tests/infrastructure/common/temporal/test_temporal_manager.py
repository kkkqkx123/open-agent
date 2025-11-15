"""时间管理器测试"""

import pytest
from datetime import datetime, timedelta, timezone
from src.infrastructure.common.temporal.temporal_manager import TemporalManager


class TestTemporalManager:
    """时间管理器测试类"""
    
    def test_now(self):
        """测试获取当前时间"""
        now = TemporalManager.now()
        assert isinstance(now, datetime)
        assert now <= datetime.now()
    
    def test_utc_now(self):
        """测试获取当前UTC时间"""
        utc_now = TemporalManager.utc_now()
        assert isinstance(utc_now, datetime)
        assert utc_now.tzinfo == timezone.utc
    
    def test_format_timestamp_iso(self):
        """测试ISO格式时间戳"""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = TemporalManager.format_timestamp(dt, "iso")
        assert result == "2023-01-01T12:00:00"
    
    def test_format_timestamp_timestamp(self):
        """测试时间戳格式"""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = TemporalManager.format_timestamp(dt, "timestamp")
        assert isinstance(int(result), int)
    
    def test_format_timestamp_readable(self):
        """测试可读格式"""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = TemporalManager.format_timestamp(dt, "readable")
        assert result == "2023-01-01 12:00:00"
    
    def test_parse_timestamp_iso(self):
        """测试解析ISO时间戳"""
        timestamp = "2023-01-01T12:00:00"
        result = TemporalManager.parse_timestamp(timestamp, "iso")
        assert result == datetime(2023, 1, 1, 12, 0, 0)
    
    def test_parse_timestamp_iso_with_timezone(self):
        """测试解析带时区的ISO时间戳"""
        timestamp = "2023-01-01T12:00:00+08:00"
        result = TemporalManager.parse_timestamp(timestamp, "iso")
        assert result.tzinfo is not None
        # 带时区的时间应该保持原始小时数，而不是转换为UTC
        assert result.hour == 12
    
    def test_parse_timestamp_timestamp(self):
        """测试解析时间戳"""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        timestamp = str(int(dt.timestamp()))
        result = TemporalManager.parse_timestamp(timestamp, "timestamp")
        assert result.year == 2023
    
    def test_parse_timestamp_readable(self):
        """测试解析可读格式"""
        timestamp = "2023-01-01 12:00:00"
        result = TemporalManager.parse_timestamp(timestamp, "readable")
        assert result == datetime(2023, 1, 1, 12, 0, 0)
    
    def test_calculate_duration(self):
        """测试计算时间差"""
        start = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 12, 1, 0)
        result = TemporalManager.calculate_duration(start, end)
        assert result == 60.0
    
    def test_calculate_duration_with_timezone(self):
        """测试计算时区感知的时间差"""
        start = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 12, 1, 0, tzinfo=timezone.utc)
        result = TemporalManager.calculate_duration(start, end)
        assert result == 60.0
    
    def test_calculate_duration_mixed_timezone(self):
        """测试计算混合时区的时间差"""
        start = datetime(2023, 1, 1, 12, 0, 0)  # naive
        end = datetime(2023, 1, 1, 12, 1, 0, tzinfo=timezone.utc)  # aware
        result = TemporalManager.calculate_duration(start, end)
        assert result == 60.0
    
    def test_add_duration(self):
        """测试添加时间间隔"""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = TemporalManager.add_duration(dt, 60)
        assert result == datetime(2023, 1, 1, 12, 1, 0)
    
    def test_is_expired(self):
        """测试过期检查"""
        past = datetime.now() - timedelta(seconds=10)
        assert TemporalManager.is_expired(past, 5) == True
        assert TemporalManager.is_expired(past, 15) == False
    
    def test_is_expired_with_timezone(self):
        """测试时区感知的过期检查"""
        past = datetime.now(timezone.utc) - timedelta(seconds=10)
        assert TemporalManager.is_expired(past, 5) == True
        assert TemporalManager.is_expired(past, 15) == False
    
    def test_to_utc(self):
        """测试转换为UTC时间"""
        # 测试时区感知的时间
        local_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=8)))
        utc_time = TemporalManager.to_utc(local_time)
        assert utc_time.hour == 4
        assert utc_time.tzinfo == timezone.utc
    
    def test_to_utc_naive(self):
        """测试naive时间转换为UTC"""
        naive_time = datetime(2023, 1, 1, 12, 0, 0)
        utc_time = TemporalManager.to_utc(naive_time)
        assert utc_time.tzinfo == timezone.utc
    
    def test_from_utc(self):
        """测试从UTC时间转换"""
        utc_time = datetime(2023, 1, 1, 4, 0, 0, tzinfo=timezone.utc)
        local_tz = timezone(timedelta(hours=8))
        local_time = TemporalManager.from_utc(utc_time, local_tz)
        assert local_time.hour == 12
    
    def test_invalid_format(self):
        """测试无效格式"""
        with pytest.raises(ValueError):
            TemporalManager.format_timestamp(datetime.now(), "invalid")
        
        with pytest.raises(ValueError):
            TemporalManager.parse_timestamp("invalid", "invalid")