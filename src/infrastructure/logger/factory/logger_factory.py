"""日志工厂 - 基础设施层实现"""

import threading
from typing import Any, Dict, List, Optional, Type, Union

from ....interfaces.logger import ILogger, IBaseHandler, ILogRedactor, ILoggerFactory, LogLevel
from ..core.log_level import LogLevel
from ..core.redactor import LogRedactor, CustomLogRedactor
from ..handlers.base_handler import BaseHandler
from ..handlers.console_handler import ConsoleHandler
from ..handlers.file_handler import FileHandler
from ..handlers.json_handler import JsonHandler
from ..formatters.text_formatter import TextFormatter
from ..formatters.color_formatter import ColorFormatter
from ..formatters.json_formatter import JsonFormatter


class LoggerFactory(ILoggerFactory):
    """日志工厂 - 基础设施层实现
    
    负责创建和配置日志系统的各种组件，包括：
    - 日志记录器
    - 处理器
    - 格式化器
    - 脱敏器
    """
    
    def __init__(self):
        """初始化日志工厂"""
        self._loggers: Dict[str, ILogger] = {}
        self._handlers: Dict[str, IBaseHandler] = {}
        self._formatters: Dict[str, Any] = {}
        self._redactors: Dict[str, ILogRedactor] = {}
        self._lock = threading.RLock()
        
        # 注册默认组件
        self._register_default_components()
    
    def _register_default_components(self) -> None:
        """注册默认组件"""
        # 注册默认格式化器
        self.register_formatter("text", TextFormatter())
        self.register_formatter("color", ColorFormatter())
        self.register_formatter("json", JsonFormatter())
        
        # 注册默认脱敏器
        self.register_redactor("default", LogRedactor())
    
    def create_logger(self, name: str, **kwargs: Any) -> ILogger:
        """创建日志记录器实例
        
        Args:
            name: 日志记录器名称
            **kwargs: 额外参数，包括：
                - handlers: 日志处理器列表
                - level: 日志级别
                - redactor: 日志脱敏器
                - config: 配置字典
            
        Returns:
            日志记录器实例
        """
        # 提取参数
        handlers: Optional[List[IBaseHandler]] = kwargs.get("handlers")
        level = kwargs.get("level", LogLevel.INFO)
        redactor = kwargs.get("redactor")
        config = kwargs.get("config")
        
        # 从配置创建处理器
        if handlers is None and config:
            handlers = self._create_handlers_from_config(config)
        
        # 使用默认处理器
        if handlers is None:
            handlers = [self.create_console_handler()]
        
        # 使用默认脱敏器
        if redactor is None:
            redactor = self.get_redactor("default") or LogRedactor()
        
        # 创建日志记录器
        # 注意：这里返回的是基础设施层的日志记录器实现
        # 在实际使用中，服务层会包装这个基础设施层实现
        logger = self._create_infrastructure_logger(
            name=name,
            handlers=handlers,
            level=level,
            redactor=redactor,
            config=config
        )
        
        return logger
    
    def _create_infrastructure_logger(
        self,
        name: str,
        handlers: List[IBaseHandler],
        level: LogLevel,
        redactor: ILogRedactor,
        config: Optional[Dict[str, Any]],
    ) -> ILogger:
        """创建基础设施层日志记录器
        
        Args:
            name: 日志记录器名称
            handlers: 处理器列表
            level: 日志级别
            redactor: 脱敏器
            config: 配置
            
        Returns:
            基础设施层日志记录器
        """
        # 这里创建一个简单的基础设施层日志记录器
        # 实际的ILogger实现会在服务层提供
        class InfrastructureLogger(ILogger):
            def __init__(self, name, handlers, level, redactor, config):
                self.name = name
                self.handlers = handlers
                self.level = level
                self.redactor = redactor
                self.config = config or {}
                self._lock = threading.RLock()
            
            def debug(self, message: str, **kwargs: Any) -> None:
                self._log(LogLevel.DEBUG, message, **kwargs)
            
            def info(self, message: str, **kwargs: Any) -> None:
                self._log(LogLevel.INFO, message, **kwargs)
            
            def warning(self, message: str, **kwargs: Any) -> None:
                self._log(LogLevel.WARNING, message, **kwargs)
            
            def error(self, message: str, **kwargs: Any) -> None:
                self._log(LogLevel.ERROR, message, **kwargs)
            
            def critical(self, message: str, **kwargs: Any) -> None:
                self._log(LogLevel.CRITICAL, message, **kwargs)
            
            def set_level(self, level: LogLevel) -> None:
                with self._lock:
                    self.level = level
            
            def add_handler(self, handler: IBaseHandler) -> None:
                with self._lock:
                    if handler not in self.handlers:
                        self.handlers.append(handler)
            
            def remove_handler(self, handler: IBaseHandler) -> None:
                with self._lock:
                    if handler in self.handlers:
                        self.handlers.remove(handler)
            
            def set_redactor(self, redactor: ILogRedactor) -> None:
                with self._lock:
                    self.redactor = redactor
            
            def _log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
                if level.value < self.level.value:
                    return
                
                import os
                from datetime import datetime
                
                record = {
                    "name": self.name,
                    "level": level,
                    "message": message,
                    "timestamp": datetime.now(),
                    "thread_id": threading.get_ident(),
                    "process_id": os.getpid(),
                    **kwargs,
                }
                
                # 脱敏处理
                if isinstance(record["message"], str):
                    record["message"] = self.redactor.redact(record["message"], level)
                
                # 发送到处理器
                with self._lock:
                    for handler in self.handlers:
                        try:
                            handler.handle(record)
                        except Exception as e:
                            print(f"日志处理器错误: {e}")
        
        return InfrastructureLogger(name, handlers, level, redactor, config)
    
    def get_logger(
        self,
        name: str,
        handlers: Optional[List[IBaseHandler]] = None,
        level: LogLevel = LogLevel.INFO,
        redactor: Optional[ILogRedactor] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> ILogger:
        """获取或创建日志记录器实例（单例）
        
        Args:
            name: 日志记录器名称
            handlers: 日志处理器列表
            level: 日志级别
            redactor: 日志脱敏器
            config: 配置
            
        Returns:
            日志记录器实例
        """
        with self._lock:
            if name not in self._loggers:
                self._loggers[name] = self.create_logger(
                    name, handlers=handlers, level=level, redactor=redactor, config=config
                )
            return self._loggers[name]
    
    def create_console_handler(
        self,
        level: LogLevel | None = None,
        formatter_name: str = "color",
        use_colors: Optional[bool] = None,
    ) -> ConsoleHandler:
        """创建控制台处理器
        
        Args:
             level: 日志级别
            formatter_name: 格式化器名称
            use_colors: 是否使用颜色
            
        Returns:
            控制台处理器
        """
        if level is None:
            level = LogLevel.INFO
        formatter = self.get_formatter(formatter_name)
        if formatter_name == "color" and isinstance(formatter, ColorFormatter):
            return ConsoleHandler(level, formatter, use_colors=use_colors)
        else:
            return ConsoleHandler(level, formatter)
    
    def create_file_handler(
        self,
        filename: str,
        level: LogLevel | None = None,
        formatter_name: str = "text",
        encoding: str = "utf-8",
        max_bytes: Optional[int] = None,
        backup_count: int = 0,
    ) -> FileHandler:
        """创建文件处理器
        
        Args:
            filename: 日志文件名
            level: 日志级别
            formatter_name: 格式化器名称
            encoding: 文件编码
            max_bytes: 最大文件字节数
            backup_count: 备份文件数量
            
        Returns:
            文件处理器
        """
        if level is None:
            level = LogLevel.INFO
        formatter = self.get_formatter(formatter_name)
        return FileHandler(
            filename=filename,
            level=level,
            formatter=formatter,
            encoding=encoding,
            max_bytes=max_bytes,
            backup_count=backup_count,
        )
    
    def create_json_handler(
        self,
        filename: str,
        level: LogLevel | None = None,
        encoding: str = "utf-8",
        max_bytes: Optional[int] = None,
        backup_count: int = 0,
        ensure_ascii: bool = False,
        indent: Optional[int] = None,
        sort_keys: bool = False,
    ) -> JsonHandler:
        """创建JSON处理器
        
        Args:
            filename: 日志文件名
            level: 日志级别
            encoding: 文件编码
            max_bytes: 最大文件字节数
            backup_count: 备份文件数量
            ensure_ascii: 是否确保ASCII编码
            indent: 缩进空格数
            sort_keys: 是否排序键
            
        Returns:
            JSON处理器
        """
        if level is None:
            level = LogLevel.INFO
        return JsonHandler(
            filename=filename,
            level=level,
            encoding=encoding,
            max_bytes=max_bytes,
            backup_count=backup_count,
            ensure_ascii=ensure_ascii,
            indent=indent,
            sort_keys=sort_keys,
        )
    
    def create_redactor(
        self,
        redactor_type: str = "default",
        config: Optional[Dict[str, Any]] = None,
    ) -> ILogRedactor:
        """创建脱敏器
        
        Args:
            redactor_type: 脱敏器类型
            config: 配置
            
        Returns:
            脱敏器实例
        """
        if redactor_type == "default":
            return LogRedactor()
        elif redactor_type == "custom":
            return CustomLogRedactor(config)
        else:
            raise ValueError(f"未知的脱敏器类型: {redactor_type}")
    
    def _create_handlers_from_config(self, config: Dict[str, Any]) -> List[IBaseHandler]:
        """从配置创建处理器
        
        Args:
            config: 配置字典
            
        Returns:
            处理器列表
        """
        handlers = []
        log_outputs = config.get("log_outputs", [])
        
        for output_config in log_outputs:
            handler_type = output_config.get("type", "console")
            level_str = output_config.get("level", "INFO")
            level = LogLevel[level_str.upper()]
            
            if handler_type == "console":
                formatter_name = output_config.get("formatter", "color")
                use_colors = output_config.get("use_colors")
                handlers.append(self.create_console_handler(level, formatter_name, use_colors))
            
            elif handler_type == "file":
                filename = output_config.get("filename", "app.log")
                formatter_name = output_config.get("formatter", "text")
                encoding = output_config.get("encoding", "utf-8")
                max_bytes = output_config.get("max_bytes")
                backup_count = output_config.get("backup_count", 0)
                handlers.append(self.create_file_handler(
                    filename, level, formatter_name, encoding, max_bytes, backup_count
                ))
            
            elif handler_type == "json":
                filename = output_config.get("filename", "app.json")
                encoding = output_config.get("encoding", "utf-8")
                max_bytes = output_config.get("max_bytes")
                backup_count = output_config.get("backup_count", 0)
                ensure_ascii = output_config.get("ensure_ascii", False)
                indent = output_config.get("indent")
                sort_keys = output_config.get("sort_keys", False)
                handlers.append(self.create_json_handler(
                    filename, level, encoding, max_bytes, backup_count,
                    ensure_ascii, indent, sort_keys
                ))
        
        return handlers
    
    def register_formatter(self, name: str, formatter: Any) -> None:
        """注册格式化器
        
        Args:
            name: 格式化器名称
            formatter: 格式化器实例
        """
        with self._lock:
            self._formatters[name] = formatter
    
    def register_redactor(self, name: str, redactor: ILogRedactor) -> None:
        """注册脱敏器
        
        Args:
            name: 脱敏器名称
            redactor: 脱敏器实例
        """
        with self._lock:
            self._redactors[name] = redactor
    
    def get_formatter(self, name: str) -> Any:
        """获取格式化器
        
        Args:
            name: 格式化器名称
            
        Returns:
            格式化器实例
        """
        return self._formatters.get(name)
    
    def get_redactor(self, name: str) -> Optional[ILogRedactor]:
        """获取脱敏器
        
        Args:
            name: 脱敏器名称
            
        Returns:
            脱敏器实例
        """
        return self._redactors.get(name)
    
    def clear_cache(self) -> None:
        """清除缓存的日志记录器"""
        with self._lock:
            self._loggers.clear()


# 注意：已移除全局便利函数，推荐通过依赖注入容器获取ILoggerFactory和ILogger实例
# 这样可以避免循环依赖并提高架构清晰度