"""JSON日志格式化器"""

import json
from datetime import datetime
from typing import Any, Dict

from .base_formatter import BaseFormatter
from ..logger import LogLevel


class JsonFormatter(BaseFormatter):
    """JSON日志格式化器"""
    
    def __init__(
        self, 
        datefmt: str = "%Y-%m-%dT%H:%M:%S",
        pretty_print: bool = False,
        ensure_ascii: bool = False
    ):
        """初始化JSON格式化器
        
        Args:
            datefmt: 日期时间格式
            pretty_print: 是否美化JSON输出
            ensure_ascii: 是否确保ASCII编码
        """
        super().__init__(datefmt)
        self.pretty_print = pretty_print
        self.ensure_ascii = ensure_ascii
    
    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录
        
        Args:
            record: 日志记录
            
        Returns:
            格式化后的JSON字符串
        """
        # 创建JSON记录
        json_record = self._create_json_record(record)
        
        # 序列化为JSON
        if self.pretty_print:
            return json.dumps(
                json_record,
                ensure_ascii=self.ensure_ascii,
                indent=2,
                default=self._json_serializer
            )
        else:
            return json.dumps(
                json_record,
                ensure_ascii=self.ensure_ascii,
                default=self._json_serializer
            )
    
    def _create_json_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """创建JSON记录
        
        Args:
            record: 原始日志记录
            
        Returns:
            JSON记录字典
        """
        json_record = {
            'timestamp': self.format_time(record['timestamp']),
            'level': self.format_level(record['level']),
            'logger': self._get_record_value(record, 'name', 'unknown'),
            'message': self._get_record_value(record, 'message', ''),
        }
        
        # 添加可选字段
        if 'thread_id' in record:
            json_record['thread_id'] = record['thread_id']
        
        if 'process_id' in record:
            json_record['process_id'] = record['process_id']
        
        # 添加额外字段
        extra_fields = self._get_extra_fields(record)
        if extra_fields:
            json_record['extra'] = extra_fields
        
        return json_record
    
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
    
    def _json_serializer(self, obj: Any) -> Any:
        """JSON序列化器，处理不可序列化的对象
        
        Args:
            obj: 要序列化的对象
            
        Returns:
            序列化后的字符串
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
    
    def set_pretty_print(self, pretty_print: bool) -> None:
        """设置是否美化JSON输出
        
        Args:
            pretty_print: 是否美化JSON输出
        """
        self.pretty_print = pretty_print
    
    def set_ensure_ascii(self, ensure_ascii: bool) -> None:
        """设置是否确保ASCII编码
        
        Args:
            ensure_ascii: 是否确保ASCII编码
        """
        self.ensure_ascii = ensure_ascii


class CompactJsonFormatter(JsonFormatter):
    """紧凑JSON日志格式化器"""
    
    def __init__(self, datefmt: str = "%Y-%m-%dT%H:%M:%S"):
        """初始化紧凑JSON格式化器
        
        Args:
            datefmt: 日期时间格式
        """
        super().__init__(datefmt, pretty_print=False, ensure_ascii=False)
    
    def _create_json_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """创建紧凑JSON记录
        
        Args:
            record: 原始日志记录
            
        Returns:
            JSON记录字典
        """
        json_record = {
            'ts': self.format_time(record['timestamp']),
            'lvl': self.format_level(record['level'])[0],  # 只取首字母
            'log': self._get_record_value(record, 'name', 'unknown'),
            'msg': self._get_record_value(record, 'message', ''),
        }
        
        # 添加可选字段
        if 'thread_id' in record:
            json_record['tid'] = record['thread_id']
        
        if 'process_id' in record:
            json_record['pid'] = record['process_id']
        
        # 添加额外字段
        extra_fields = self._get_extra_fields(record)
        if extra_fields:
            json_record.update(extra_fields)
        
        return json_record


class StructuredJsonFormatter(JsonFormatter):
    """结构化JSON日志格式化器"""
    
    def _create_json_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """创建结构化JSON记录
        
        Args:
            record: 原始日志记录
            
        Returns:
            JSON记录字典
        """
        json_record = {
            '@timestamp': self.format_time(record['timestamp']),
            'level': self.format_level(record['level']),
            'logger_name': self._get_record_value(record, 'name', 'unknown'),
            'message': self._get_record_value(record, 'message', ''),
        }
        
        # 添加系统信息
        system_info = {}
        if 'thread_id' in record:
            system_info['thread_id'] = record['thread_id']
        
        if 'process_id' in record:
            system_info['process_id'] = record['process_id']
        
        if system_info:
            json_record['system'] = system_info
        
        # 添加额外字段
        extra_fields = self._get_extra_fields(record)
        if extra_fields:
            json_record['fields'] = extra_fields
        
        return json_record