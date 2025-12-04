"""TUI 日志记录器包装类
 
为 TUI 模块提供一个轻量级的日志记录器包装，
与新的日志架构兼容。
"""

from typing import Any, Optional, List
from src.interfaces.logger import ILogger


class TUILogger(ILogger):
    """TUI 日志记录器包装类
    
    提供与原有 Logger 接口兼容的包装，但基于新的 ILogger 接口。
    """
    
    def __init__(self, name: str, base_logger: Optional[ILogger] = None):
        """初始化 TUI 日志记录器
        
        Args:
            name: 日志记录器名称
            base_logger: 基础日志记录器（可选）
        """
        self.name = name
        self._base_logger = base_logger
        self._handlers: List[Any] = []
        self._level: str = "INFO"
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志"""
        if self._base_logger:
            self._base_logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志"""
        if self._base_logger:
            self._base_logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志"""
        if self._base_logger:
            self._base_logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志"""
        if self._base_logger:
            self._base_logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """记录严重错误日志"""
        if self._base_logger:
            self._base_logger.critical(message, **kwargs)
    
    def set_level(self, level: Any) -> None:
        """设置日志级别
        
        Args:
            level: 日志级别对象或字符串
        """
        self._level = str(level) if level else "INFO"
        if self._base_logger and hasattr(self._base_logger, 'set_level'):
            self._base_logger.set_level(level)
    
    def add_handler(self, handler: Any) -> None:
        """添加日志处理器
        
        Args:
            handler: 日志处理器
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
        if self._base_logger and hasattr(self._base_logger, 'add_handler'):
            self._base_logger.add_handler(handler)
    
    def remove_handler(self, handler: Any) -> None:
        """移除日志处理器
        
        Args:
            handler: 日志处理器
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
        if self._base_logger and hasattr(self._base_logger, 'remove_handler'):
            self._base_logger.remove_handler(handler)
    
    def set_redactor(self, redactor: Any) -> None:
        """设置日志脱敏器
        
        Args:
            redactor: 日志脱敏器
        """
        if self._base_logger and hasattr(self._base_logger, 'set_redactor'):
            self._base_logger.set_redactor(redactor)
    
    def get_handlers(self) -> List[Any]:
        """获取所有处理器
        
        Returns:
            处理器列表
        """
        return self._handlers.copy()
