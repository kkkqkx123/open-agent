"""文本日志格式化器"""

from typing import Any, Dict

from .base_formatter import BaseFormatter
from ..logger import LogLevel


class TextFormatter(BaseFormatter):
    """文本日志格式化器"""
    
    def __init__(
        self, 
        datefmt: str = "%Y-%m-%d %H:%M:%S",
        fmt: str = "{timestamp} [{level}] {name}: {message}"
    ):
        """初始化文本格式化器
        
        Args:
            datefmt: 日期时间格式
            fmt: 日志格式模板
        """
        super().__init__(datefmt)
        self.fmt = fmt
    
    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录
        
        Args:
            record: 日志记录
            
        Returns:
            格式化后的日志字符串
        """
        # 获取基本字段
        timestamp = self.format_time(record['timestamp'])
        level = self.format_level(record['level'])
        name = self._get_record_value(record, 'name', 'unknown')
        message = self._get_record_value(record, 'message', '')
        
        # 格式化基本日志
        formatted = self.fmt.format(
            timestamp=timestamp,
            level=level,
            name=name,
            message=message
        )
        
        # 添加额外字段
        extra_fields = self._get_extra_fields(record)
        if extra_fields:
            extra_str = " ".join([f"{k}={v}" for k, v in extra_fields.items()])
            formatted += f" {extra_str}"
        
        return formatted
    
    def _get_extra_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """获取额外字段
        
        Args:
            record: 日志记录
            
        Returns:
            额外字段字典
        """
        # 排除基本字段
        basic_fields = {'name', 'level', 'message', 'timestamp', 'thread_id', 'process_id'}
        extra_fields = {}
        
        for key, value in record.items():
            if key not in basic_fields:
                extra_fields[key] = value
        
        return extra_fields
    
    def set_format(self, fmt: str) -> None:
        """设置日志格式
        
        Args:
            fmt: 日志格式模板
        """
        self.fmt = fmt


class DetailedTextFormatter(TextFormatter):
    """详细文本日志格式化器"""
    
    def __init__(self, datefmt: str = "%Y-%m-%d %H:%M:%S"):
        """初始化详细文本格式化器
        
        Args:
            datefmt: 日期时间格式
        """
        fmt = "{timestamp} [{level}] {name} (T:{thread_id} P:{process_id}): {message}"
        super().__init__(datefmt, fmt)
    
    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录
        
        Args:
            record: 日志记录
            
        Returns:
            格式化后的日志字符串
        """
        # 获取基本字段
        timestamp = self.format_time(record['timestamp'])
        level = self.format_level(record['level'])
        name = self._get_record_value(record, 'name', 'unknown')
        message = self._get_record_value(record, 'message', '')
        thread_id = self._get_record_value(record, 'thread_id', 0)
        process_id = self._get_record_value(record, 'process_id', 0)
        
        # 格式化基本日志
        formatted = self.fmt.format(
            timestamp=timestamp,
            level=level,
            name=name,
            message=message,
            thread_id=thread_id,
            process_id=process_id
        )
        
        # 添加额外字段
        extra_fields = self._get_extra_fields(record)
        if extra_fields:
            extra_str = " ".join([f"{k}={v}" for k, v in extra_fields.items()])
            formatted += f" | {extra_str}"
        
        return formatted


class SimpleTextFormatter(TextFormatter):
    """简单文本日志格式化器"""
    
    def __init__(self, datefmt: str = "%H:%M:%S"):
        """初始化简单文本格式化器
        
        Args:
            datefmt: 日期时间格式
        """
        fmt = "{timestamp} [{level}] {message}"
        super().__init__(datefmt, fmt)
    
    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录
        
        Args:
            record: 日志记录
            
        Returns:
            格式化后的日志字符串
        """
        # 获取基本字段
        timestamp = self.format_time(record['timestamp'])
        level = self.format_level(record['level'])
        message = self._get_record_value(record, 'message', '')
        
        # 格式化基本日志
        formatted = self.fmt.format(
            timestamp=timestamp,
            level=level,
            message=message
        )
        
        return formatted