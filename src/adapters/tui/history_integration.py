"""TUI历史管理集成模块

提供历史管理服务与TUI状态管理器的集成功能。
"""

from typing import Dict, Any, Optional
from src.interfaces.history import IHistoryManager
from src.services.history.manager import HistoryManager
from .state_manager import StateManager


class TUIHistoryIntegration:
    """TUI历史管理集成类
    
    负责将历史管理服务与TUI状态管理器集成。
    """
    
    def __init__(self, history_manager: IHistoryManager):
        self.history_manager = history_manager
    
    def integrate_with_state_manager(self, state_manager: StateManager) -> None:
        """与状态管理器集成
        
        Args:
            state_manager: 状态管理器
        """
        # 添加消息钩子
        if hasattr(state_manager, 'add_user_message_hook'):
            state_manager.add_user_message_hook(self._on_user_message)
        if hasattr(state_manager, 'add_assistant_message_hook'):
            state_manager.add_assistant_message_hook(self._on_assistant_message)
        if hasattr(state_manager, 'add_tool_call_hook'):
            state_manager.add_tool_call_hook(lambda tool_name, args, context=None: self._on_tool_call(tool_name, args))
    
    def _on_user_message(self, message: str) -> None:
        """处理用户消息"""
        # 这里可以添加历史记录逻辑
        pass
    
    def _on_assistant_message(self, message: str) -> None:
        """处理助手消息"""
        # 这里可以添加历史记录逻辑
        pass
    
    def _on_tool_call(self, tool_name: str, args: Dict[str, Any]) -> None:
        """处理工具调用"""
        # 这里可以添加历史记录逻辑
        pass
    
    def on_session_created(self, state_manager: StateManager, workflow_config: str, agent_config: Optional[str] = None) -> None:
        """处理会话创建事件
        
        Args:
            state_manager: 状态管理器
            workflow_config: 工作流配置
            agent_config: 代理配置
        """
        # 会话创建逻辑
        pass
    
    def on_session_ended(self, state_manager: StateManager, reason: str = "normal") -> None:
        """处理会话结束事件
        
        Args:
            state_manager: 状态管理器
            reason: 结束原因
        """
        # 会话结束逻辑
        pass
    
    def on_error_occurred(self, state_manager: StateManager, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """处理错误事件
        
        Args:
            state_manager: 状态管理器
            error: 错误对象
            context: 错误上下文
        """
        # 错误处理逻辑
        pass
    
    def get_session_summary_for_display(self, state_manager: StateManager) -> Optional[Dict[str, Any]]:
        """获取用于显示的会话摘要
        
        Args:
            state_manager: 状态管理器
            
        Returns:
            Optional[Dict[str, Any]]: 会话摘要，如果没有会话则返回None
        """
        if not state_manager.session_id:
            return None
        
        return {"session_id": state_manager.session_id}
    
    def export_session_data_for_display(self, state_manager: StateManager, format: str = "json") -> Optional[Dict[str, Any]]:
        """导出用于显示的会话数据
        
        Args:
            state_manager: 状态管理器
            format: 导出格式
            
        Returns:
            Optional[Dict[str, Any]]: 导出的数据，如果没有会话则返回None
        """
        if not state_manager.session_id:
            return None
        
        return {"session_id": state_manager.session_id, "format": format}