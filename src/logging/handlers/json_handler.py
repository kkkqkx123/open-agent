"""JSON日志处理器"""

import json
import sys
import logging
from typing import Any, Dict, Optional

from .file_handler import FileHandler
from ..logger import LogLevel
from ..formatters.json_formatter import JsonFormatter


class JsonHandler(FileHandler):
    """JSON日志处理器"""
    
    def __init__(self, level: LogLevel = LogLevel.INFO, config: Optional[Dict[str, Any]] = None):
        """初始化JSON处理器
        
        Args:
            level: 日志级别
            config: 处理器配置
        """
        # 强制设置格式类型为JSON
        if config is None:
            config = {}
        config['format'] = 'json'
        
        super().__init__(level, config)
        
        # 获取JSON特定配置
        self.pretty_print = config.get('pretty_print', False)
        self.ensure_ascii = config.get('ensure_ascii', False)
        
        # 重新设置JSON格式化器
        self._setup_json_formatter()
    
    def _setup_json_formatter(self) -> None:
        """设置JSON格式化器"""
        self.set_formatter(JsonFormatter(
            pretty_print=self.pretty_print,
            ensure_ascii=self.ensure_ascii
        ))
    
    def emit(self, record: Dict[str, Any]) -> None:
        """输出日志记录到文件
        
        Args:
            record: 日志记录
        """
        try:
            # 格式化为JSON
            formatted_record = self.format(record)
            
            # 创建一个标准logging记录来使用内置处理器
            log_record = logging.LogRecord(
                name=record.get('name', ''),
                level=record['level'].value,
                pathname='',
                lineno=0,
                msg=formatted_record,
                args=(),
                exc_info=None
            )
            self._file_handler.emit(log_record)
        except Exception:
            self.handleError(record)
    
    def set_pretty_print(self, pretty_print: bool) -> None:
        """设置是否美化JSON输出
        
        Args:
            pretty_print: 是否美化JSON输出
        """
        self.pretty_print = pretty_print
        self._setup_json_formatter()
    
    def set_ensure_ascii(self, ensure_ascii: bool) -> None:
        """设置是否确保ASCII编码
        
        Args:
            ensure_ascii: 是否确保ASCII编码
        """
        self.ensure_ascii = ensure_ascii
        self._setup_json_formatter()


class JsonConsoleHandler(JsonHandler):
    """JSON控制台日志处理器"""
    
    def __init__(self, level: LogLevel = LogLevel.INFO, config: Optional[Dict[str, Any]] = None):
        """初始化JSON控制台处理器
        
        Args:
            level: 日志级别
            config: 处理器配置
        """
        # 强制设置输出到控制台
        if config is None:
            config = {}
        config['path'] = 'console'
        
        super().__init__(level, config)
        
        # 设置输出流
        self.stream = config.get('stream', 'stdout') if config else 'stdout'
        if self.stream == 'stderr':
            self.stream = sys.stderr
        else:
            self.stream = sys.stdout
    
    def emit(self, record: Dict[str, Any]) -> None:
        """输出日志记录到控制台
        
        Args:
            record: 日志记录
        """
        try:
            # 格式化为JSON
            formatted_record = self.format(record)
            
            # 写入控制台
            self.stream.write(formatted_record + '\n')
            self.stream.flush()
        except Exception:
            self.handleError(record)