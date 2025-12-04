"""TUI日志记录器基础类，提供共同的日志记录功能"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path

from .logger_wrapper import TUILogger
from src.interfaces.logger import LogLevel


class TUILoggingStrategy(ABC):
    """TUI日志记录策略抽象基类"""
    
    @abstractmethod
    def should_log(self, level: LogLevel) -> bool:
        """判断是否应该记录指定级别的日志
        
        Args:
            level: 日志级别
            
        Returns:
            是否应该记录日志
        """
        pass
    
    @abstractmethod
    def get_logger_prefix(self) -> str:
        """获取日志记录器前缀
        
        Returns:
            日志记录器前缀
        """
        pass
    
    @abstractmethod
    def handle_log_error(self, error: Exception) -> None:
        """处理日志记录错误
        
        Args:
            error: 异常对象
        """
        pass
    
    def format_key_event(self, key: str) -> str:
        """格式化按键事件显示
        
        Args:
            key: 按键字符串
            
        Returns:
            格式化后的按键字符串
        """
        # 默认简单实现，子类可以重写
        return key


class TUILoggerBase:
    """TUI日志记录器基础类，提供共同的日志记录功能"""
    
    def __init__(self, name: str, strategy: TUILoggingStrategy):
        """初始化TUI日志记录器基础类
        
        Args:
            name: 日志记录器名称
            strategy: 日志记录策略
        """
        self.name = name
        self.strategy = strategy
        # 延迟导入避免循环依赖
        from .tui_logger_manager import TUILoggerManager
        self.tui_manager = TUILoggerManager()
        self._logger: Optional[TUILogger] = None
        self._initialized = False
        
    def _ensure_initialized(self) -> None:
        """确保日志记录器已初始化"""
        if not self._initialized:
            self._initialize_logger()
            self._initialized = True
    
    def _initialize_logger(self) -> None:
        """初始化日志记录器"""
        try:
            # 延迟导入避免循环依赖
            from .tui_logger_manager import get_tui_logger
            
            # 使用策略获取前缀
            prefix = self.strategy.get_logger_prefix()
            full_name = f"{prefix}.{self.name}"
            
            # 获取日志记录器
            self._logger = get_tui_logger(full_name)
            
            # 设置日志级别
            if self.tui_manager.is_debug_enabled():
                self._logger.set_level(LogLevel.DEBUG)
                
        except Exception as e:
            # 使用策略处理错误
            self.strategy.handle_log_error(e)
            self._logger = None
    
    def _log_if_enabled(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        """如果启用了日志记录，则记录日志
        
        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 附加信息
        """
        # 使用策略判断是否应该记录日志
        if not self.strategy.should_log(level):
            return
            
        self._ensure_initialized()
        
        if self._logger:
            try:
                getattr(self._logger, level.name.lower())(message, **kwargs)
            except Exception as e:
                # 使用策略处理错误
                self.strategy.handle_log_error(e)
    
    def debug_component_event(self, component: str, event: str, **kwargs: Any) -> None:
        """记录组件事件调试信息"""
        self._log_if_enabled(
            LogLevel.DEBUG,
            f"TUI组件事件: {component} -> {event}",
            component=component,
            event=event,
            **kwargs
        )
    
    def debug_input_handling(self, input_type: str, content: str, **kwargs: Any) -> None:
        """记录输入处理调试信息"""
        self._log_if_enabled(
            LogLevel.DEBUG,
            f"TUI输入处理: {input_type} -> {content}",
            input_type=input_type,
            content=content,
            **kwargs
        )
    
    def debug_ui_state_change(self, component: str, old_state: Any, new_state: Any, **kwargs: Any) -> None:
        """记录UI状态变更调试信息"""
        self._log_if_enabled(
            LogLevel.DEBUG,
            f"TUI状态变更: {component} -> {old_state} to {new_state}",
            component=component,
            old_state=old_state,
            new_state=new_state,
            **kwargs
        )
    
    def debug_workflow_operation(self, operation: str, **kwargs: Any) -> None:
        """记录工作流操作调试信息"""
        self._log_if_enabled(
            LogLevel.DEBUG,
            f"TUI工作流操作: {operation}",
            operation=operation,
            **kwargs
        )
    
    def debug_session_operation(self, operation: str, session_id: Optional[str] = None, **kwargs: Any) -> None:
        """记录会话操作调试信息"""
        message = f"TUI会话操作: {operation}"
        if session_id:
            message += f" (Session: {session_id})"
        
        self._log_if_enabled(
            LogLevel.DEBUG,
            message,
            operation=operation,
            session_id=session_id,
            **kwargs
        )
    
    def debug_key_event(self, key: str, handled: bool, context: str = "", **kwargs: Any) -> None:
        """记录按键事件调试信息"""
        # 使用策略格式化按键事件
        display_key = self.strategy.format_key_event(key)
        
        self._log_if_enabled(
            LogLevel.DEBUG,
            f"TUI按键事件: {display_key}, handled: {handled}, context: {context}",
            key=key,
            handled=handled,
            context=context,
            **kwargs
        )
    
    def debug_subview_navigation(self, from_view: str, to_view: str, **kwargs: Any) -> None:
        """记录子界面导航调试信息"""
        self._log_if_enabled(
            LogLevel.DEBUG,
            f"TUI子界面导航: {from_view} -> {to_view}",
            from_view=from_view,
            to_view=to_view,
            **kwargs
        )
    
    def debug_render_operation(self, component: str, operation: str, **kwargs: Any) -> None:
        """记录渲染操作调试信息"""
        self._log_if_enabled(
            LogLevel.DEBUG,
            f"TUI渲染操作: {component} -> {operation}",
            component=component,
            operation=operation,
            **kwargs
        )
    
    def debug_error_handling(self, error_type: str, error_message: str, **kwargs: Any) -> None:
        """记录错误处理调试信息"""
        self._log_if_enabled(
            LogLevel.DEBUG,
            f"TUI错误处理: {error_type} -> {error_message}",
            error_type=error_type,
            error_message=error_message,
            **kwargs
        )
    
    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志"""
        self._log_if_enabled(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志"""
        self._log_if_enabled(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志"""
        self._log_if_enabled(LogLevel.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志"""
        self._log_if_enabled(LogLevel.DEBUG, message, **kwargs)
    
    def set_debug_mode(self, enabled: bool) -> None:
        """设置调试模式"""
        self.tui_manager.set_debug_mode(enabled)
        # 重新初始化日志记录器以应用新的设置
        self._initialized = False