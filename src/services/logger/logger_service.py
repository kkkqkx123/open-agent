"""日志服务实现"""

import os
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...interfaces.common_infra import ILogger, IBaseHandler, ILogRedactor, LogLevel
from ...core.logger.log_level import LogLevel as CoreLogLevel
from ...core.logger.redactor import LogRedactor


def _log_level_from_string(level_str: str) -> LogLevel:
    """从字符串创建日志级别"""
    level_map = {
        "DEBUG": LogLevel.DEBUG,
        "INFO": LogLevel.INFO,
        "WARNING": LogLevel.WARNING,
        "WARN": LogLevel.WARNING,
        "ERROR": LogLevel.ERROR,
        "CRITICAL": LogLevel.CRITICAL,
        "FATAL": LogLevel.CRITICAL,
    }

    upper_level = level_str.upper()
    if upper_level not in level_map:
        raise ValueError(f"无效的日志级别: {level_str}")

    return level_map[upper_level]


def _to_core_log_level(interface_level: LogLevel) -> CoreLogLevel:
    """将接口层LogLevel转换为核心层LogLevel"""
    mapping = {
        LogLevel.DEBUG: CoreLogLevel.DEBUG,
        LogLevel.INFO: CoreLogLevel.INFO,
        LogLevel.WARNING: CoreLogLevel.WARNING,
        LogLevel.ERROR: CoreLogLevel.ERROR,
        LogLevel.CRITICAL: CoreLogLevel.CRITICAL,
    }
    return mapping[interface_level]


class LoggerService(ILogger):
    """日志服务实现 - 纯业务逻辑"""

    def __init__(
        self,
        name: str,
        redactor: ILogRedactor,
        handlers: List[IBaseHandler],
        config: Optional[Dict[str, Any]] = None,
    ):
        """初始化日志服务

        Args:
            name: 日志记录器名称
            redactor: 日志脱敏器
            handlers: 日志处理器列表
            config: 配置
        """
        self.name = name
        self._redactor = redactor
        self._handlers = handlers
        self._config = config or {}
        self._level = LogLevel.INFO
        self._lock = threading.RLock()

        # 从配置设置日志级别
        if config:
            level_str = config.get("log_level", "INFO")
            self._level = _log_level_from_string(level_str)

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

    def add_handler(self, handler: IBaseHandler) -> None:
        """添加日志处理器"""
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)

    def remove_handler(self, handler: IBaseHandler) -> None:
        """移除日志处理器"""
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)

    def set_redactor(self, redactor: ILogRedactor) -> None:
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
        # 创建级别映射用于比较
        level_values = {
            LogLevel.DEBUG: 10,
            LogLevel.INFO: 20,
            LogLevel.WARNING: 30,
            LogLevel.ERROR: 40,
            LogLevel.CRITICAL: 50,
        }
        return level_values[level] >= level_values[self._level]

    def _create_log_record(
        self, level: LogLevel, message: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """创建日志记录

        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外的日志数据

        Returns:
            日志记录字典
        """
        return {
            "name": self.name,
            "level": level,
            "message": message,
            "timestamp": datetime.now(),
            "thread_id": threading.get_ident(),
            "process_id": os.getpid() if "os" in globals() else None,
            **kwargs,
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
        redacted_record["message"] = self._redactor.redact(
            log_record["message"], log_record["level"]
        )

        # 脱敏其他字符串字段
        for key, value in log_record.items():
            if isinstance(value, str) and key != "message":
                redacted_record[key] = self._redactor.redact(value, log_record["level"])

        return redacted_record

    def get_level(self) -> LogLevel:
        """获取当前日志级别

        Returns:
            当前日志级别
        """
        return self._level

    def get_handlers(self) -> List[IBaseHandler]:
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


class LoggerFactory:
    """日志工厂 - 用于依赖注入容器"""
    
    def __init__(self):
        """初始化日志工厂"""
        self._loggers: Dict[str, LoggerService] = {}
        self._lock = threading.RLock()
    
    def create_logger(
        self,
        name: str,
        redactor: ILogRedactor,
        handlers: List[IBaseHandler],
        config: Optional[Dict[str, Any]] = None,
    ) -> LoggerService:
        """创建日志服务实例
        
        Args:
            name: 日志记录器名称
            redactor: 日志脱敏器
            handlers: 日志处理器列表
            config: 配置
            
        Returns:
            日志服务实例
        """
        return LoggerService(name, redactor, handlers, config)
    
    def get_logger(
        self,
        name: str,
        redactor: ILogRedactor,
        handlers: List[IBaseHandler],
        config: Optional[Dict[str, Any]] = None,
    ) -> LoggerService:
        """获取或创建日志服务实例（单例）
        
        Args:
            name: 日志记录器名称
            redactor: 日志脱敏器
            handlers: 日志处理器列表
            config: 配置
            
        Returns:
            日志服务实例
        """
        with self._lock:
            if name not in self._loggers:
                self._loggers[name] = self.create_logger(name, redactor, handlers, config)
            return self._loggers[name]


# 全局工厂实例（临时，将被依赖注入替代）
_global_factory: Optional[LoggerFactory] = None


def get_logger_factory() -> LoggerFactory:
    """获取全局日志工厂
    
    Returns:
        日志工厂实例
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = LoggerFactory()
    return _global_factory


def get_logger(name: str, config: Optional[Dict[str, Any]] = None) -> LoggerService:
    """获取日志记录器（临时函数，将被依赖注入替代）
    
    Args:
        name: 日志记录器名称
        config: 配置
        
    Returns:
        日志服务实例
    """
    # 临时实现，创建默认的redactor和handlers
    redactor = LogRedactor()
    handlers = []
    
    factory = get_logger_factory()
    return factory.get_logger(name, redactor, handlers, config)


def set_global_config(config: Dict[str, Any]) -> None:
    """设置全局配置（临时函数，将被依赖注入替代）
    
    Args:
        config: 全局配置
    """
    # 临时实现，这里应该通过依赖注入容器重新配置服务
    pass