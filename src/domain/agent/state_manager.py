"""Agent状态管理器"""

from typing import Dict, Optional, Any, List
from .state import AgentState
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

    def create_initial_state(self, agent_id: str, config: Dict[str, Any], workflow_name: str) -> AgentState:
        """创建初始状态"""
        state = AgentState()
        state.agent_id = agent_id
        state.agent_config = config  # type: ignore
        state.workflow_name = workflow_name
        state.max_iterations = config.get('max_iterations', 10)
        self._states[agent_id] = state
        return state

    def update_state_with_memory(self, state: AgentState, messages: List[Any]) -> AgentState:
        """更新状态的记忆部分"""
        for message in messages:
            if hasattr(message, 'to_dict'):
                state.add_memory(message)
            else:
                # 如果不是BaseMessage类型，创建HumanMessage
                from ...infrastructure.graph.state import HumanMessage
                human_msg = HumanMessage(content=str(message))
                state.add_memory(human_msg)
        return state

    def update_state_with_tool_result(self, state: AgentState, tool_result: Any) -> AgentState:
        """更新状态的工具结果"""
        state.add_tool_result(tool_result)
        return state

    def update_state_with_error(self, state: AgentState, error_info: Dict[str, Any]) -> AgentState:
        """更新状态的错误信息"""
        state.add_error(error_info)
        return state

    def update_iteration_count(self, state: AgentState) -> AgentState:
        """更新迭代计数"""
        state.increment_iteration()
        return state

    def is_max_iterations_reached(self, state: AgentState) -> bool:
        """检查是否达到最大迭代次数"""
        return state.is_max_iterations_reached()

    def reset_state_for_new_task(self, state: AgentState) -> AgentState:
        """为新任务重置状态"""
        state.current_task = None
        state.memory.clear()
        state.tool_results.clear()
        state.errors.clear()
        state.iteration_count = 0
        return state