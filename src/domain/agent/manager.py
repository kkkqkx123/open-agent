"""Agent管理器实现"""

from typing import Any, Dict, Type, Optional
from .interfaces import IAgent, IAgentManager, IAgentEventManager
from .config import AgentConfig
from .events import AgentEventManager, AgentEvent


class AgentManager(IAgentManager):
    def __init__(self, llm_client: 'ILLMClient', tool_executor: 'IToolExecutor', event_manager: Optional[IAgentEventManager] = None):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.event_manager = event_manager or AgentEventManager()
        self.agents: Dict[str, IAgent] = {}
        self.agent_types: Dict[str, Type[IAgent]] = {}
    
    def create_agent(self, config: AgentConfig) -> IAgent:
        if config.agent_type not in self.agent_types:
            raise ValueError(f"Unknown agent type: {config.agent_type}")
        
        agent_class = self.agent_types[config.agent_type]
        agent = agent_class(config, self.llm_client, self.tool_executor, self.event_manager)
        
        # 注册事件处理器
        self._setup_agent_events(agent, config.name)
        
        return agent
    
    def register_agent_type(self, agent_type: str, agent_class: Type[IAgent]) -> None:
        self.agent_types[agent_type] = agent_class
    
    async def execute_agent(self, agent_id: str, input_state: 'AgentState') -> 'AgentState':
        if agent_id not in self.agents:
            raise ValueError(f"Agent not found: {agent_id}")
        
        # 发布执行开始事件
        self.event_manager.publish(AgentEvent.EXECUTION_STARTED, {
            "agent_id": agent_id,
            "state": input_state
        })
        
        agent = self.agents[agent_id]
        try:
            result = await agent.execute(input_state)
            
            # 发布执行完成事件
            self.event_manager.publish(AgentEvent.EXECUTION_COMPLETED, {
                "agent_id": agent_id,
                "input_state": input_state,
                "output_state": result
            })
            
            return result
        except Exception as e:
            # 发布错误事件
            self.event_manager.publish(AgentEvent.ERROR_OCCURRED, {
                "agent_id": agent_id,
                "error": str(e),
                "state": input_state
            })
            
            # 重新抛出异常
            raise e
    
    def register_agent(self, agent_id: str, agent: IAgent) -> None:
        """注册Agent实例"""
        self.agents[agent_id] = agent
        
        # 注册事件处理器
        self._setup_agent_events(agent, agent_id)
    
    def _setup_agent_events(self, agent: IAgent, agent_id: str) -> None:
        """为Agent设置事件处理器"""
        # 这里可以为特定Agent设置事件处理器
        pass