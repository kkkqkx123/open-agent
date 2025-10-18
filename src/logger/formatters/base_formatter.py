"""日志格式化器基础类"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

from ..log_level import LogLevel


class BaseFormatter(ABC):
    """日志格式化器基础类"""
    
    def __init__(self, datefmt: str = "%Y-%m-%d %H:%M:%S"):
        """初始化格式化器
        
        Args:
            datefmt: 日期时间格式
        """
        self.datefmt = datefmt
    
    @abstractmethod
    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录
        
        Args:
            record: 日志记录
            
        Returns:
            格式化后的日志字符串
        """
        pass
    
    def format_time(self, timestamp: datetime) -> str:
        """格式化时间戳
        
        Args:
            timestamp: 时间戳
            
        Returns:
            格式化后的时间字符串
        """
        return timestamp.strftime(self.datefmt)
    
    def format_level(self, level: LogLevel) -> str:
        """格式化日志级别
        
        Args:
            level: 日志级别
            
        Returns:
            格式化后的日志级别字符串
        """
        return level.name
    
    def _get_record_value(self, record: Dict[str, Any], key: str, default: Any = None) -> Any:
        """获取日志记录中的值
        
        Args:
            record: 日志记录
            key: 键名
            default: 默认值
            
        Returns:
            值
        """
        return record.get(key, default)