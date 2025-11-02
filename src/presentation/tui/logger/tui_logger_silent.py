"""TUI静默日志记录器，专门用于TUI环境避免终端输出"""

from typing import Any, Dict, Optional
from pathlib import Path

from .tui_logger_base import TUILoggerBase
from .tui_logger_manager import TUILoggerFactory


class TUISilentLogger:
    """TUI静默日志记录器，统一输出到TUI主日志文件，不输出到终端"""
    
    def __init__(self, name: str = "main"):
        """初始化TUI静默日志记录器
        
        Args:
            name: 日志记录器名称
        """
        self.name = name
        self._logger = TUILoggerFactory.create_silent_logger(name)
    
    def debug_component_event(self, component: str, event: str, **kwargs: Any) -> None:
        """记录组件事件调试信息"""
        self._logger.debug_component_event(component, event, **kwargs)
    
    def debug_input_handling(self, input_type: str, content: str, **kwargs: Any) -> None:
        """记录输入处理调试信息"""
        self._logger.debug_input_handling(input_type, content, **kwargs)
    
    def debug_ui_state_change(self, component: str, old_state: Any, new_state: Any, **kwargs: Any) -> None:
        """记录UI状态变更调试信息"""
        self._logger.debug_ui_state_change(component, old_state, new_state, **kwargs)
    
    def debug_workflow_operation(self, operation: str, **kwargs: Any) -> None:
        """记录工作流操作调试信息"""
        self._logger.debug_workflow_operation(operation, **kwargs)
    
    def debug_session_operation(self, operation: str, session_id: Optional[str] = None, **kwargs: Any) -> None:
        """记录会话操作调试信息"""
        self._logger.debug_session_operation(operation, session_id, **kwargs)
    
    def debug_key_event(self, key: str, handled: bool, context: str = "", **kwargs: Any) -> None:
        """记录按键事件调试信息"""
        self._logger.debug_key_event(key, handled, context, **kwargs)
    
    def debug_subview_navigation(self, from_view: str, to_view: str, **kwargs: Any) -> None:
        """记录子界面导航调试信息"""
        self._logger.debug_subview_navigation(from_view, to_view, **kwargs)
    
    def debug_render_operation(self, component: str, operation: str, **kwargs: Any) -> None:
        """记录渲染操作调试信息"""
        self._logger.debug_render_operation(component, operation, **kwargs)
    
    def debug_error_handling(self, error_type: str, error_message: str, **kwargs: Any) -> None:
        """记录错误处理调试信息"""
        self._logger.debug_error_handling(error_type, error_message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志"""
        self._logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志"""
        self._logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志"""
        self._logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志"""
        self._logger.debug(message, **kwargs)
    
    def set_debug_mode(self, enabled: bool) -> None:
        """设置调试模式"""
        self._logger.set_debug_mode(enabled)


def get_tui_silent_logger(name: str = "main") -> TUISilentLogger:
    """获取TUI静默日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        TUI静默日志记录器实例
    """
    return TUISilentLogger(name)