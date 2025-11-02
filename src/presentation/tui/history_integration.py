"""TUI历史管理集成模块

提供历史管理服务与TUI状态管理器的集成功能。
"""

from typing import Dict, Any, Optional
from src.domain.history.interfaces import IHistoryManager
from src.domain.history.models import MessageType
from src.application.history.service_integration import HistoryServiceIntegration
from src.application.history.session_context import set_current_session
from src.presentation.tui.state_manager import StateManager


class TUIHistoryIntegration:
    """TUI历史管理集成类
    
    负责将历史管理服务与TUI状态管理器集成。
    """
    
    def __init__(self, history_manager: IHistoryManager):
        self.history_service = HistoryServiceIntegration(history_manager)
    
    def integrate_with_state_manager(self, state_manager: StateManager) -> None:
        """与状态管理器集成
        
        Args:
            state_manager: 状态管理器
        """
        # 设置会话上下文
        if state_manager.session_id:
            set_current_session(state_manager.session_id)
        
        # 添加消息钩子
        from src.application.history.adapters.tui_adapter import TUIHistoryAdapter
        adapter = TUIHistoryAdapter(self.history_service.history_manager, state_manager)
        
        state_manager.add_user_message_hook(adapter.on_user_message)
        state_manager.add_assistant_message_hook(adapter.on_assistant_message)
        state_manager.add_tool_call_hook(adapter.on_tool_call)
    
    def on_session_created(self, state_manager: StateManager, workflow_config: str, agent_config: Optional[str] = None) -> None:
        """处理会话创建事件
        
        Args:
            state_manager: 状态管理器
            workflow_config: 工作流配置
            agent_config: 代理配置
        """
        if state_manager.session_id:
            self.history_service.record_session_start(
                state_manager.session_id, 
                workflow_config, 
                agent_config
            )
    
    def on_session_ended(self, state_manager: StateManager, reason: str = "normal") -> None:
        """处理会话结束事件
        
        Args:
            state_manager: 状态管理器
            reason: 结束原因
        """
        if state_manager.session_id:
            self.history_service.record_session_end(state_manager.session_id, reason)
    
    def on_error_occurred(self, state_manager: StateManager, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """处理错误事件
        
        Args:
            state_manager: 状态管理器
            error: 错误对象
            context: 错误上下文
        """
        if state_manager.session_id:
            self.history_service.record_error(state_manager.session_id, error, context)
    
    def get_session_summary_for_display(self, state_manager: StateManager) -> Optional[Dict[str, Any]]:
        """获取用于显示的会话摘要
        
        Args:
            state_manager: 状态管理器
            
        Returns:
            Optional[Dict[str, Any]]: 会话摘要，如果没有会话则返回None
        """
        if not state_manager.session_id:
            return None
        
        return self.history_service.get_session_summary(state_manager.session_id)
    
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
        
        return self.history_service.export_session_data(state_manager.session_id, format)