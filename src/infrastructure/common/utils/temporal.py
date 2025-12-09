"""统一时间管理器"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import re


class TemporalManager:
    """统一时间管理器"""
    
    @staticmethod
    def now() -> datetime:
        """获取当前时间（本地时区）"""
        return datetime.now()
    
    @staticmethod
    def utc_now() -> datetime:
        """获取当前UTC时间（时区感知）"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def format_timestamp(dt: datetime, format: str = "iso") -> str:
        """格式化时间戳
        
        Args:
            dt: 时间对象
            format: 格式类型 ("iso", "timestamp", "readable")
            
        Returns:
            格式化的时间字符串
        """
        if format == "iso":
            return dt.isoformat()
        elif format == "timestamp":
            # 统一使用datetime.timestamp()方法，简化代码逻辑
            return str(int(dt.timestamp()))
        elif format == "readable":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def parse_timestamp(timestamp: str, format: str = "iso") -> datetime:
        """解析时间戳
        
        Args:
            timestamp: 时间字符串
            format: 格式类型 ("iso", "timestamp", "readable")
            
        Returns:
            解析后的时间对象
        """
        if format == "iso":
            try:
                # 尝试解析ISO格式，支持时区信息
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                # 尝试更宽松的ISO格式解析
                iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
                if re.match(iso_pattern, timestamp):
                    # 移除时区信息，创建naive datetime
                    naive_part = timestamp.split('+')[0].split('Z')[0]
                    if '.' in naive_part:
                        return datetime.strptime(naive_part, "%Y-%m-%dT%H:%M:%S.%f")
                    else:
                        return datetime.strptime(naive_part, "%Y-%m-%dT%H:%M:%S")
                else:
                    raise ValueError(f"Invalid ISO timestamp format: {timestamp}")
        elif format == "timestamp":
            # 返回naive datetime，与测试期望一致
            dt_with_tz = datetime.fromtimestamp(float(timestamp), tz=timezone.utc)
            # 移除时区信息，返回naive datetime
            return dt_with_tz.replace(tzinfo=None)
        elif format == "readable":
            return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def calculate_duration(start: datetime, end: datetime) -> float:
        """计算时间差（秒）
        
        Args:
            start: 开始时间
            end: 结束时间
            
        Returns:
            时间差（秒）
        """
        # 处理时区感知和naive datetime的混合情况
        if start.tzinfo is not None and end.tzinfo is None:
            end = end.replace(tzinfo=start.tzinfo)
        elif start.tzinfo is None and end.tzinfo is not None:
            start = start.replace(tzinfo=end.tzinfo)
        
        return (end - start).total_seconds()
    
    @staticmethod
    def add_duration(dt: datetime, seconds: float) -> datetime:
        """添加时间间隔
        
        Args:
            dt: 原始时间
            seconds: 秒数
            
        Returns:
            新的时间
        """
        return dt + timedelta(seconds=seconds)
    
    @staticmethod
    def is_expired(dt: datetime, ttl_seconds: float) -> bool:
        """检查是否过期
        
        Args:
            dt: 时间戳
            ttl_seconds: TTL秒数
            
        Returns:
            是否过期
        """
        # 使用与dt相同类型的时间进行比较
        if dt.tzinfo is not None:
            # 时区感知时间，使用UTC时间比较
            now = TemporalManager.utc_now()
            # 如果dt是naive的，假设它是UTC时间
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            # naive时间，使用本地时间比较
            now = TemporalManager.now()
        
        return TemporalManager.calculate_duration(dt, now) > ttl_seconds
    
    @staticmethod
    def to_utc(dt: datetime) -> datetime:
        """转换为UTC时间
        
        Args:
            dt: 原始时间
            
        Returns:
            UTC时间
        """
        if dt.tzinfo is None:
            # 假设naive datetime是本地时间
            return dt.replace(tzinfo=timezone.utc)
        else:
            return dt.astimezone(timezone.utc)
    
    @staticmethod
    def from_utc(dt: datetime, tz: Optional[timezone] = None) -> datetime:
        """从UTC时间转换为指定时区
        
        Args:
            dt: UTC时间
            tz: 目标时区，如果为None则使用本地时区
            
        Returns:
            转换后的时间
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        if tz is None:
            return dt.astimezone()
        else:
            return dt.astimezone(tz)