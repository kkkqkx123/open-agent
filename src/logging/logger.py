"""日志记录器实现"""

import os
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from ..config.models.global_config import GlobalConfig
from .handlers.base_handler import BaseHandler
from .redactor import LogRedactor


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    @classmethod
    def from_string(cls, level_str: str) -> 'LogLevel':
        """从字符串创建日志级别"""
        level_map = {
            'DEBUG': cls.DEBUG,
            'INFO': cls.INFO,
            'WARNING': cls.WARNING,
            'WARN': cls.WARNING,
            'ERROR': cls.ERROR,
            'CRITICAL': cls.CRITICAL,
            'FATAL': cls.CRITICAL
        }
        
        upper_level = level_str.upper()
        if upper_level not in level_map:
            raise ValueError(f"无效的日志级别: {level_str}")
        
        return level_map[upper_level]

    def __str__(self) -> str:
        """返回日志级别的字符串表示"""
        return self.name


class ILogger(ABC):
    """日志记录器接口"""
    
    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志"""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志"""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志"""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志"""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        """记录严重错误日志"""
        pass
    
    @abstractmethod
    def set_level(self, level: LogLevel) -> None:
        """设置日志级别"""
        pass
    
    @abstractmethod
    def add_handler(self, handler: BaseHandler) -> None:
        """添加日志处理器"""
        pass
    
    @abstractmethod
    def remove_handler(self, handler: BaseHandler) -> None:
        """移除日志处理器"""
        pass
    
    @abstractmethod
    def set_redactor(self, redactor: LogRedactor) -> None:
        """设置日志脱敏器"""
        pass


class Logger(ILogger):
    """日志记录器实现"""
    
    def __init__(
        self, 
        name: str,
        config: Optional[GlobalConfig] = None,
        redactor: Optional[LogRedactor] = None
    ):
        """初始化日志记录器
        
        Args:
            name: 日志记录器名称
            config: 全局配置
            redactor: 日志脱敏器
        """
        self.name = name
        self._config = config
        self._redactor = redactor or LogRedactor()
        self._handlers: List[BaseHandler] = []
        self._level = LogLevel.INFO
        self._lock = threading.RLock()
        
        # 如果有配置，根据配置设置日志级别和处理器
        if config:
            self._level = LogLevel.from_string(config.log_level)
            self._setup_handlers_from_config(config)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志"""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志"""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志"""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志"""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """记录严重错误日志"""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def set_level(self, level: LogLevel) -> None:
        """设置日志级别"""
        with self._lock:
            self._level = level
    
    def add_handler(self, handler: BaseHandler) -> None:
        """添加日志处理器"""
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)
    
    def remove_handler(self, handler: BaseHandler) -> None:
        """移除日志处理器"""
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)
    
    def set_redactor(self, redactor: LogRedactor) -> None:
        """设置日志脱敏器"""
        with self._lock:
            self._redactor = redactor
    
    def _log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        """内部日志记录方法
        
        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        if not self._should_log(level):
            return
        
        # 创建日志记录
        log_record = self._create_log_record(level, message, **kwargs)
        
        # 脱敏处理
        redacted_record = self._redact_log_record(log_record)
        
        # 发送到所有处理器
        with self._lock:
            for handler in self._handlers:
                try:
                    handler.handle(redacted_record)
                except Exception as e:
                    # 避免日志记录本身出错导致程序崩溃
                    print(f"日志处理器错误: {e}")
    
    def _should_log(self, level: LogLevel) -> bool:
        """检查是否应该记录日志
        
        Args:
            level: 日志级别
            
        Returns:
            是否应该记录
        """
        return level.value >= self._level.value
    
    def _create_log_record(self, level: LogLevel, message: str, **kwargs: Any) -> Dict[str, Any]:
        """创建日志记录
        
        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外的日志数据
            
        Returns:
            日志记录字典
        """
        return {
            'name': self.name,
            'level': level,
            'message': message,
            'timestamp': datetime.now(),
            'thread_id': threading.get_ident(),
            'process_id': os.getpid() if 'os' in globals() else None,
            **kwargs
        }
    
    def _redact_log_record(self, log_record: Dict[str, Any]) -> Dict[str, Any]:
        """对日志记录进行脱敏处理
        
        Args:
            log_record: 原始日志记录
            
        Returns:
            脱敏后的日志记录
        """
        # 脱敏消息
        redacted_record = log_record.copy()
        redacted_record['message'] = self._redactor.redact(
            log_record['message'], 
            log_record['level']
        )
        
        # 脱敏其他字符串字段
        for key, value in log_record.items():
            if isinstance(value, str) and key != 'message':
                redacted_record[key] = self._redactor.redact(value, log_record['level'])
        
        return redacted_record
    
    def _setup_handlers_from_config(self, config: GlobalConfig) -> None:
        """根据配置设置处理器
        
        Args:
            config: 全局配置
        """
        from .handlers.console_handler import ConsoleHandler
        from .handlers.file_handler import FileHandler
        from .handlers.json_handler import JsonHandler
        
        for output_config in config.log_outputs:
            # 处理不同类型的配置对象
            if isinstance(output_config, dict):
                handler_type = output_config.get("type", "console")
                handler_level = LogLevel.from_string(output_config.get("level", "INFO"))
                handler_config = output_config
            else:
                # 假设是对象类型，使用属性访问
                handler_type = getattr(output_config, 'type', 'console')
                handler_level = LogLevel.from_string(getattr(output_config, 'level', 'INFO'))
                handler_config = output_config.__dict__ if hasattr(output_config, '__dict__') else {}
            
            handler: BaseHandler
            if handler_type == "console":
                handler = ConsoleHandler(handler_level, handler_config)
            elif handler_type == "file":
                handler = FileHandler(handler_level, handler_config)
            elif handler_type == "json":
                handler = JsonHandler(handler_level, handler_config)
            else:
                continue  # 跳过未知类型的处理器
            
            self.add_handler(handler)
    
    def get_level(self) -> LogLevel:
        """获取当前日志级别
        
        Returns:
            当前日志级别
        """
        return self._level
    
    def get_handlers(self) -> List[BaseHandler]:
        """获取所有处理器
        
        Returns:
            处理器列表
        """
        with self._lock:
            return self._handlers.copy()
    
    def flush(self) -> None:
        """刷新所有处理器"""
        with self._lock:
            for handler in self._handlers:
                try:
                    handler.flush()
                except Exception as e:
                    print(f"刷新日志处理器错误: {e}")
    
    def close(self) -> None:
        """关闭所有处理器"""
        with self._lock:
            for handler in self._handlers:
                try:
                    handler.close()
                except Exception as e:
                    print(f"关闭日志处理器错误: {e}")
            self._handlers.clear()


# 全局日志记录器注册表
_loggers: Dict[str, Logger] = {}
_loggers_lock = threading.RLock()


def get_logger(name: str, config: Optional[GlobalConfig] = None) -> Logger:
    """获取或创建日志记录器
    
    Args:
        name: 日志记录器名称
        config: 全局配置
        
    Returns:
        日志记录器实例
    """
    with _loggers_lock:
        if name not in _loggers:
            _loggers[name] = Logger(name, config)
        return _loggers[name]


def set_global_config(config: GlobalConfig) -> None:
    """设置全局配置，更新所有已创建的日志记录器
    
    Args:
        config: 全局配置
    """
    with _loggers_lock:
        for logger in _loggers.values():
            logger._config = config
            logger._level = LogLevel.from_string(config.log_level)
            
            # 清除现有处理器
            for handler in logger._handlers:
                handler.close()
            logger._handlers.clear()
            
            # 根据新配置设置处理器
            logger._setup_handlers_from_config(config)