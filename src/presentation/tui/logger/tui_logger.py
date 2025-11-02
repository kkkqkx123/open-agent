"""TUI调试日志记录器"""

from typing import Any, Dict, Optional
from pathlib import Path

from .tui_logger_base import TUILoggerBase
from .tui_logger_manager import TUILoggerFactory


class TUIDebugLogger:
    """TUI调试日志记录器，提供专门的TUI调试功能"""
    
    def __init__(self, name: str = "main"):
        """初始化TUI调试日志记录器
        
        Args:
            name: 日志记录器名称
        """
        self.name = name
        self._logger = TUILoggerFactory.create_debug_logger(name)
    
    def debug_component_event(self, component: str, event: str, **kwargs: Any) -> None:
        """记录组件事件调试信息
        
        Args:
            component: 组件名称
            event: 事件类型
            **kwargs: 附加信息
        """
        self._logger.debug_component_event(component, event, **kwargs)
    
    def debug_input_handling(self, input_type: str, content: str, **kwargs: Any) -> None:
        """记录输入处理调试信息
        
        Args:
            input_type: 输入类型
            content: 输入内容
            **kwargs: 附加信息
        """
        self._logger.debug_input_handling(input_type, content, **kwargs)
    
    def debug_ui_state_change(self, component: str, old_state: Any, new_state: Any, **kwargs: Any) -> None:
        """记录UI状态变更调试信息
        
        Args:
            component: 组件名称
            old_state: 旧状态
            new_state: 新状态
            **kwargs: 附加信息
        """
        self._logger.debug_ui_state_change(component, old_state, new_state, **kwargs)
    
    def debug_workflow_operation(self, operation: str, **kwargs: Any) -> None:
        """记录工作流操作调试信息
        
        Args:
            operation: 操作类型
            **kwargs: 附加信息
        """
        self._logger.debug_workflow_operation(operation, **kwargs)
    
    def debug_session_operation(self, operation: str, session_id: Optional[str] = None, **kwargs: Any) -> None:
        """记录会话操作调试信息
        
        Args:
            operation: 操作类型
            session_id: 会话ID
            **kwargs: 附加信息
        """
        self._logger.debug_session_operation(operation, session_id, **kwargs)
    
    def debug_key_event(self, key: str, handled: bool, context: str = "", **kwargs: Any) -> None:
        """记录按键事件调试信息
        
        Args:
            key: 按键
            handled: 是否已处理
            context: 上下文信息
            **kwargs: 附加信息
        """
        self._logger.debug_key_event(key, handled, context, **kwargs)
    
    def debug_subview_navigation(self, from_view: str, to_view: str, **kwargs: Any) -> None:
        """记录子界面导航调试信息
        
        Args:
            from_view: 源界面
            to_view: 目标界面
            **kwargs: 附加信息
        """
        self._logger.debug_subview_navigation(from_view, to_view, **kwargs)
    
    def debug_render_operation(self, component: str, operation: str, **kwargs: Any) -> None:
        """记录渲染操作调试信息
        
        Args:
            component: 组件名称
            operation: 操作类型
            **kwargs: 附加信息
        """
        self._logger.debug_render_operation(component, operation, **kwargs)
    
    def debug_error_handling(self, error_type: str, error_message: str, **kwargs: Any) -> None:
        """记录错误处理调试信息
        
        Args:
            error_type: 错误类型
            error_message: 错误消息
            **kwargs: 附加信息
        """
        self._logger.debug_error_handling(error_type, error_message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志
        
        Args:
            message: 日志消息
            **kwargs: 附加信息
        """
        self._logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志
        
        Args:
            message: 日志消息
            **kwargs: 附加信息
        """
        self._logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志
        
        Args:
            message: 日志消息
            **kwargs: 附加信息
        """
        self._logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志
        
        Args:
            message: 日志消息
            **kwargs: 附加信息
        """
        self._logger.debug(message, **kwargs)
    
    def set_debug_mode(self, enabled: bool) -> None:
        """设置调试模式
        
        Args:
            enabled: 是否启用调试模式
        """
        self._logger.set_debug_mode(enabled)


# 全局TUI调试日志记录器实例
tui_debug_logger = TUIDebugLogger()


def get_tui_debug_logger(name: str = "main") -> TUIDebugLogger:
    """获取TUI调试日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        TUI调试日志记录器实例
    """
    return TUIDebugLogger(name)