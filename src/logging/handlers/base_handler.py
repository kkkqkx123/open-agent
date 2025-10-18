"""日志处理器基础类"""

import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..logger import LogLevel


class BaseHandler(ABC):
    """日志处理器基础类"""
    
    def __init__(self, level: LogLevel = LogLevel.INFO, config: Optional[Dict[str, Any]] = None):
        """初始化日志处理器
        
        Args:
            level: 日志级别
            config: 处理器配置
        """
        self.level = level
        self.config = config or {}
        self._formatter = None
    
    @abstractmethod
    def emit(self, record: Dict[str, Any]) -> None:
        """输出日志记录
        
        Args:
            record: 日志记录
        """
        pass
    
    def handle(self, record: Dict[str, Any]) -> None:
        """处理日志记录
        
        Args:
            record: 日志记录
        """
        # 检查日志级别
        if record['level'].value < self.level.value:
            return
        
        # 输出日志记录
        try:
            self.emit(record)
        except Exception:
            # 避免日志处理器出错导致程序崩溃
            self.handleError(record)
    
    def format(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """格式化日志记录
        
        Args:
            record: 原始日志记录
            
        Returns:
            格式化后的日志记录
        """
        if self._formatter:
            # 如果有格式化器，将格式化后的字符串添加到记录中
            formatted_msg = self._formatter.format(record)
            formatted_record = record.copy()
            formatted_record['formatted_message'] = formatted_msg
            return formatted_record
        return record
    
    def set_formatter(self, formatter: Any) -> None:
        """设置格式化器
        
        Args:
            formatter: 格式化器
        """
        self._formatter = formatter
    
    def set_level(self, level: LogLevel) -> None:
        """设置日志级别
        
        Args:
            level: 日志级别
        """
        self.level = level
    
    def flush(self) -> None:
        """刷新缓冲区"""
        pass
    
    def close(self) -> None:
        """关闭处理器"""
        self.flush()
    
    def handleError(self, record: Dict[str, Any]) -> None:
        """处理错误
        
        Args:
            record: 日志记录
        """
        try:
            sys.stderr.write(f"日志处理器错误: {self.__class__.__name__}\n")
            sys.stderr.write(f"日志记录: {record}\n")
            sys.stderr.write("异常信息: 请检查日志处理器配置\n")
        except Exception:
            # 避免错误处理本身出错
            pass