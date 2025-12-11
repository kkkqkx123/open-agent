"""TUI日志管理器"""

import os
import threading
from typing import Optional, Dict, Any, Type
from pathlib import Path

from src.interfaces.dependency_injection import get_logger
from src.core.config.models.global_config import GlobalConfig, LogOutputConfig
from src.interfaces.logger import LogLevel
from .logger_wrapper import TUILogger


class TUILoggerManager:
    """TUI日志管理器，负责管理TUI界面的调试日志"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'TUILoggerManager':
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # Initialize instance attributes
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """初始化TUI日志管理器"""
        if not self._initialized:
            self._loggers: Dict[str, TUILogger] = {}
            self._config: Optional[GlobalConfig] = None
            self._debug_enabled: bool = os.getenv("TUI_DEBUG", "0").lower() in ("1", "true", "yes")
            self._initialized: bool = True
    
    def initialize(self, config: Optional[GlobalConfig] = None) -> None:
        """初始化日志管理器
        
        Args:
            config: 全局配置
        """
        self._config = config
        if config:
            self._debug_enabled = config.debug or os.getenv("TUI_DEBUG", "0").lower() in ("1", "true", "yes")
            
            # 查找TUI专用的日志配置
            tui_log_config = None
            for log_output in config.log_outputs:
                if log_output.type == "file" and log_output.path and "tui.log" in log_output.path:
                    tui_log_config = log_output
                    break
            
            # 如果找到了TUI专用的日志配置，使用它
            if tui_log_config:
                self._setup_tui_file_logger(tui_log_config)
            else:
                # 否则，为所有文件日志配置创建TUI专用的日志记录器
                for log_output in config.log_outputs:
                    if log_output.type == "file" and log_output.path:
                        # 为TUI创建专门的文件日志记录器
                        self._setup_tui_file_logger(log_output)
    
    def _add_tui_file_handler_to_logger(self, logger: TUILogger, log_output_config: LogOutputConfig) -> None:
        """为TUI日志记录器添加TUI文件处理器
        
        Args:
            logger: 日志记录器
            log_output_config: 日志输出配置
        
        注意：新的日志架构通过容器管理处理器，此方法为兼容性而保留
        """
        # 在新的日志架构中，处理器由容器和工厂管理
        # TUI日志记录器继承自ILogger，已支持日志输出
        pass
    
    def _setup_tui_file_logger(self, log_output_config: LogOutputConfig) -> None:
        """根据配置设置TUI文件日志记录器
        
        Args:
            log_output_config: 日志输出配置
        """
        try:
            # 为所有已存在的TUI日志记录器添加TUI文件处理器
            # 避免重复添加相同的处理器
            for logger in self._loggers.values():
                self._add_tui_file_handler_to_logger(logger, log_output_config)
                
        except Exception as e:
            print(f"TUI日志管理器设置文件处理器失败: {e}")
    
    def get_logger(self, name: str) -> TUILogger:
        """获取或创建日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            日志记录器实例
        """
        if name not in self._loggers:
            # 创建带前缀的logger名称以区分TUI日志
            full_name = f"tui.{name}"
            
            # 为TUI日志记录器创建一个新的TUILogger实例，不使用全局配置中的处理器
            # 这样可以确保TUI日志只输出到TUI专用的日志文件中
            logger = TUILogger(full_name)  # 创建独立的TUI日志记录器
            
            # 如果启用了TUI调试模式，将日志级别设置为DEBUG
            if self._debug_enabled:
                logger.set_level(LogLevel.DEBUG)
            
            # 如果配置已经初始化，直接为新创建的日志记录器添加处理器
            if self._config:
                for log_output in self._config.log_outputs:
                    if log_output.type == "file" and log_output.path:
                        # 为TUI创建专门的文件日志记录器
                        self._add_tui_file_handler_to_logger(logger, log_output)
            
            self._loggers[name] = logger
        
        return self._loggers[name]
    
    def set_debug_mode(self, enabled: bool) -> None:
        """设置调试模式
        
        Args:
            enabled: 是否启用调试模式
        """
        self._debug_enabled = enabled
        
        # 更新所有现有logger的级别
        if self._debug_enabled:
            for logger in self._loggers.values():
                logger.set_level(LogLevel.DEBUG)
    
    def is_debug_enabled(self) -> bool:
        """检查是否启用了调试模式
        
        Returns:
            是否启用调试模式
        """
        return self._debug_enabled
    
    def create_file_logger(self, name: str, log_file_path: Path) -> TUILogger:
        """创建文件日志记录器
        
        Args:
            name: 日志记录器名称
            log_file_path: 日志文件路径
            
        Returns:
            日志记录器实例
        
        注意：新的日志架构通过容器和工厂管理处理器，此方法为兼容性而保留
        """
        # 确保日志目录存在
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 在新的日志架构中，处理器由容器和工厂管理
        # 直接返回日志记录器，日志会通过已注册的处理器输出
        logger = self.get_logger(name)
        return logger


# 全局TUI日志管理器实例
tui_logger_manager = TUILoggerManager()


def get_tui_logger(name: str) -> TUILogger:
    """获取TUI日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
    """
    return tui_logger_manager.get_logger(name)


TUI_LOGGER_NAME = "tui"


class TUILoggerFactory:
    """TUI日志记录器工厂，负责创建不同类型的TUI日志记录器"""
    
    @staticmethod
    def create_silent_logger(name: str = "main"):
        """创建静默日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            静默日志记录器实例
        """
        # 延迟导入避免循环依赖
        from .tui_logger_strategies import SilentLoggingStrategy
        from .tui_logger_base import TUILoggerBase
        
        strategy = SilentLoggingStrategy()
        return TUILoggerBase(name, strategy)
    
    @staticmethod
    def create_debug_logger(name: str = "main"):
        """创建调试日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            调试日志记录器实例
        """
        # 延迟导入避免循环依赖
        from .tui_logger_strategies import DebugLoggingStrategy
        from .tui_logger_base import TUILoggerBase
        
        strategy = DebugLoggingStrategy()
        return TUILoggerBase(name, strategy)
    
    @staticmethod
    def create_logger(logger_type: str, name: str = "main"):
        """根据类型创建日志记录器
        
        Args:
            logger_type: 日志记录器类型 ("silent" 或 "debug")
            name: 日志记录器名称
            
        Returns:
            日志记录器实例
            
        Raises:
            ValueError: 当日志记录器类型不支持时
        """
        if logger_type == "silent":
            return TUILoggerFactory.create_silent_logger(name)
        elif logger_type == "debug":
            return TUILoggerFactory.create_debug_logger(name)
        else:
            raise ValueError(f"不支持的日志记录器类型: {logger_type}")