"""TUI静默日志记录器，专门用于TUI环境避免终端输出"""

import os
from typing import Any, Dict, Optional
from pathlib import Path

from src.infrastructure.logger.logger import Logger
from src.infrastructure.logger.log_level import LogLevel
from .tui_logger_manager import TUILoggerManager, get_tui_logger


class TUISilentLogger:
    """TUI静默日志记录器，统一输出到TUI主日志文件，不输出到终端"""
    
    def __init__(self, name: str = "main"):
        """初始化TUI静默日志记录器
        
        Args:
            name: 日志记录器名称
        """
        self.name = name
        self.tui_manager = TUILoggerManager()
        self._logger: Optional[Logger] = None
        self._initialized = False
        
    def _ensure_initialized(self) -> None:
        """确保日志记录器已初始化"""
        if not self._initialized:
            self._initialize_logger()
            self._initialized = True
    
    def _initialize_logger(self) -> None:
        """初始化日志记录器，使用TUILoggerManager提供的统一日志记录器"""
        try:
            # 使用TUILoggerManager获取统一的日志记录器
            # 将模块名称作为日志记录器的前缀，以便在统一日志中区分来源
            self._logger = get_tui_logger(f"silent.{self.name}")
            
            # 设置日志级别
            if self.tui_manager.is_debug_enabled():
                from src.infrastructure.logger.log_level import LogLevel
                self._logger.set_level(LogLevel.DEBUG)
            
        except Exception as e:
            # 如果初始化失败，创建一个空的日志记录器
            self._logger = None
    
    def _log_if_enabled(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        """如果启用了日志记录，则记录日志"""
        if not self.tui_manager.is_debug_enabled():
            return
            
        self._ensure_initialized()
        
        if self._logger:
            try:
                getattr(self._logger, level.name.lower())(message, **kwargs)
            except Exception:
                # 忽略日志记录错误，避免影响TUI运行
                pass
    
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
        self._log_if_enabled(
            LogLevel.DEBUG,
            f"TUI按键事件: {key}, handled: {handled}, context: {context}",
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


def get_tui_silent_logger(name: str = "main") -> TUISilentLogger:
    """获取TUI静默日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        TUI静默日志记录器实例
    """
    return TUISilentLogger(name)