"""TUI日志管理器"""

import os
import threading
from typing import Optional, Dict, Any
from pathlib import Path

from src.infrastructure.logger.logger import get_logger, Logger
from src.infrastructure.config.models.global_config import GlobalConfig, LogOutputConfig


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
            self._loggers: Dict[str, Logger] = {}
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
    
    def _add_tui_file_handler_to_logger(self, logger: Logger, log_output_config: LogOutputConfig) -> None:
        """为TUI日志记录器添加TUI文件处理器
        
        Args:
            logger: 日志记录器
            log_output_config: 日志输出配置
        """
        try:
            from pathlib import Path
            from src.infrastructure.logger.handlers.file_handler import FileHandler
            from src.infrastructure.logger.log_level import LogLevel
            
            # 对于所有TUI日志记录器，统一使用tui.log配置的路径
            # 这样可以确保所有TUI模块的日志都输出到同一个文件中
            original_path = Path(log_output_config.path)  # type: ignore[arg-type]
            
            # 检查是否是TUI专用的日志配置
            if "tui.log" in original_path.name:
                tui_log_path = original_path
            else:
                # 如果不是tui.log配置，我们仍然使用tui.log作为目标文件
                # 这样所有TUI相关的日志都输出到同一个文件中
                tui_log_path = original_path.parent / "tui.log"
            
            # 创建文件处理器配置
            file_handler_config = {
                "type": "file",
                "level": log_output_config.level or "INFO",
                "path": str(tui_log_path),  # 使用"path"而不是"file_path"
                "format": log_output_config.format or "text",
                "rotation": log_output_config.rotation,
                "max_size": log_output_config.max_size,
                "backup_count": 5
            }
            
            # 检查是否已经存在相同路径的处理器，避免重复添加
            existing_handlers = logger.get_handlers()
            target_path_str = str(tui_log_path)
            for existing_handler in existing_handlers:
                # 检查处理器是否为FileHandler且路径相同
                if (hasattr(existing_handler, 'config') and
                    existing_handler.config.get('path') == target_path_str):
                    # 如果已存在相同路径的处理器，跳过添加
                    return
            
            file_handler = FileHandler(
                level=LogLevel.from_string(log_output_config.level or "INFO"),
                config=file_handler_config
            )
            
            # 为日志记录器添加文件处理器
            logger.add_handler(file_handler)
                
        except Exception as e:
            print(f"TUI日志管理器添加文件处理器失败: {e}")
    
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
    
    def get_logger(self, name: str) -> Logger:
        """获取或创建日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            日志记录器实例
        """
        if name not in self._loggers:
            # 创建带前缀的logger名称以区分TUI日志
            full_name = f"tui.{name}"
            
            # 为TUI日志记录器创建一个新的Logger实例，不使用全局配置中的处理器
            # 这样可以确保TUI日志只输出到TUI专用的日志文件中
            from src.infrastructure.logger.logger import Logger
            logger = Logger(full_name, None)  # 不传递全局配置，避免继承全局处理器
            
            # 如果启用了TUI调试模式，将日志级别设置为DEBUG
            if self._debug_enabled:
                from src.infrastructure.logger.log_level import LogLevel
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
            from src.infrastructure.logger.log_level import LogLevel
            for logger in self._loggers.values():
                logger.set_level(LogLevel.DEBUG)
    
    def is_debug_enabled(self) -> bool:
        """检查是否启用了调试模式
        
        Returns:
            是否启用调试模式
        """
        return self._debug_enabled
    
    def create_file_logger(self, name: str, log_file_path: Path) -> Logger:
        """创建文件日志记录器
        
        Args:
            name: 日志记录器名称
            log_file_path: 日志文件路径
            
        Returns:
            日志记录器实例
        """
        from src.infrastructure.logger.handlers.file_handler import FileHandler
        from src.infrastructure.logger.log_level import LogLevel
        
        # 确保日志目录存在
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建文件处理器
        file_handler = FileHandler(
            level=LogLevel.DEBUG if self._debug_enabled else LogLevel.INFO,
            config={
                "type": "file",
                "level": "DEBUG" if self._debug_enabled else "INFO",
                "file_path": str(log_file_path),
                "max_size": "10MB",
                "backup_count": 5
            }
        )
        
        # 获取logger并添加文件处理器
        logger = self.get_logger(name)
        logger.add_handler(file_handler)
        
        return logger


# 全局TUI日志管理器实例
tui_logger_manager = TUILoggerManager()


def get_tui_logger(name: str) -> Logger:
    """获取TUI日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
    """
    return tui_logger_manager.get_logger(name)


TUI_LOGGER_NAME = "tui"