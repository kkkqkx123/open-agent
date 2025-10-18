"""控制台日志处理器"""

import sys
from typing import Any, Dict, Optional

from .base_handler import BaseHandler
from ..log_level import LogLevel
from ..formatters.text_formatter import TextFormatter
from ..formatters.color_formatter import ColorFormatter


class ConsoleHandler(BaseHandler):
    """控制台日志处理器"""
    
    def __init__(self, level: LogLevel = LogLevel.INFO, config: Optional[Dict[str, Any]] = None):
        """初始化控制台处理器
        
        Args:
            level: 日志级别
            config: 处理器配置
        """
        super().__init__(level, config)
        
        # 获取配置
        self.use_colors = config.get('use_colors', True) if config else True
        self.format_type = config.get('format', 'text') if config else 'text'
        
        # 设置输出流
        if config and config.get('stream') == 'stderr':
            self.stream = sys.stderr
        else:
            self.stream = sys.stdout
        
        # 设置格式化器
        self._setup_formatter()
    
    def emit(self, record: Dict[str, Any]) -> None:
        """输出日志记录到控制台
        
        Args:
            record: 日志记录
        """
        try:
            # 获取格式化后的消息
            formatted_record = self.format(record)
            msg = formatted_record.get('formatted_message', str(record))
            
            self.stream.write(msg + '\n')
            self.stream.flush()
        except Exception:
            self.handleError(record)
    
    def _setup_formatter(self) -> None:
        """设置格式化器"""
        if self.format_type == 'color' and self.use_colors:
            self.set_formatter(ColorFormatter())
        else:
            self.set_formatter(TextFormatter())
    
    def set_use_colors(self, use_colors: bool) -> None:
        """设置是否使用彩色输出
        
        Args:
            use_colors: 是否使用彩色输出
        """
        self.use_colors = use_colors
        self._setup_formatter()
    
    def set_stream(self, stream: Any) -> None:
        """设置输出流
        
        Args:
            stream: 输出流
        """
        self.stream = stream