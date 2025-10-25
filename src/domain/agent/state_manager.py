"""Agent状态管理器"""

from typing import Dict, Optional, Any
from ..prompts.agent_state import AgentState
from .config import AgentConfig


class AgentStateManager:
    """Agent状态管理器"""
    
    def __init__(self) -> None:
        self._states: Dict[str, AgentState] = {}
        self._default_state = AgentState()
    
    def create_state(self, agent_id: str, config: AgentConfig, initial_context: Optional[Dict[str, Any]] = None) -> AgentState:
        """创建新的Agent状态"""
        state = AgentState()
        state.agent_id = agent_id
        state.agent_config = config
        state.context = initial_context or {}
        
        self._states[agent_id] = state
        return state
    
    def get_state(self, agent_id: str) -> Optional[AgentState]:
        """获取指定Agent的状态"""
        return self._states.get(agent_id)
    
    def update_state(self, agent_id: str, new_state: AgentState) -> None:
        """更新指定Agent的状态"""
        self._states[agent_id] = new_state
    
    def delete_state(self, agent_id: str) -> None:
        """删除指定Agent的状态"""
        if agent_id in self._states:
            del self._states[agent_id]
    
    def update_context(self, agent_id: str, context_updates: Dict[str, Any]) -> None:
        """更新Agent状态中的上下文"""
        state = self.get_state(agent_id)
        if state:
            state.context.update(context_updates)
    
    def add_message(self, agent_id: str, message: Any) -> None:
        """向Agent状态添加消息"""
        state = self.get_state(agent_id)
        if state:
            state.add_message(message)
    
    def add_memory(self, agent_id: str, memory: Any) -> None:
        """向Agent状态添加记忆"""
        state = self.get_state(agent_id)
        if state:
            state.add_memory(memory)
    
    def add_log(self, agent_id: str, log: Dict[str, Any]) -> None:
        """向Agent状态添加日志"""
        state = self.get_state(agent_id)
        if state:
            state.add_log(log)
    
    def add_error(self, agent_id: str, error: Dict[str, Any]) -> None:
        """向Agent状态添加错误"""
        state = self.get_state(agent_id)
        if state:
            state.add_error(error)
    
    def clear_states(self) -> None:
        """清除所有状态"""
        self._states.clear()
    
    def get_all_states(self) -> Dict[str, AgentState]:
        """获取所有状态"""
        return self._states.copy()
    
    def has_state(self, agent_id: str) -> bool:
        """检查是否存在指定Agent的状态"""
        return agent_id in self._states