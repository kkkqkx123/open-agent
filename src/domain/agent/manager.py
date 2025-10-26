"""Agent管理器实现"""

from typing import Any, Dict, Type, Optional, List, TYPE_CHECKING
from .interfaces import IAgent, IAgentManager, IAgentEventManager
from .config import AgentConfig
from .events import AgentEventManager, AgentEvent
from .state import AgentState

if TYPE_CHECKING:
    from src.infrastructure.llm.interfaces import ILLMClient
    from src.infrastructure.tools.executor import IToolExecutor


class AgentManager(IAgentManager):
    """Agent管理器实现
    
    负责Agent的创建、注册和执行管理。
    """
    
    def __init__(
        self, 
        llm_client: 'ILLMClient', 
        tool_executor: 'IToolExecutor', 
        event_manager: Optional[IAgentEventManager] = None
    ):
        """初始化Agent管理器
        
        Args:
            llm_client: LLM客户端
            tool_executor: 工具执行器
            event_manager: 事件管理器（可选）
        """
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.event_manager = event_manager or AgentEventManager()
        self.agents: Dict[str, IAgent] = {}
        self.agent_types: Dict[str, Type[IAgent]] = {}
    
    def create_agent(self, config: AgentConfig) -> IAgent:
        """根据配置创建Agent
        
        Args:
            config: Agent配置
            
        Returns:
            IAgent: Agent实例
        """
        if config.agent_type not in self.agent_types:
            raise ValueError(f"Unknown agent type: {config.agent_type}")
        
        agent_class = self.agent_types[config.agent_type]
        agent = agent_class(config, self.llm_client, self.tool_executor, self.event_manager)  # type: ignore
        
        # 注册事件处理器
        self._setup_agent_events(agent, config.name)
        
        return agent
    
    async def execute_agent(self, agent_id: str, input_state: AgentState) -> AgentState:
        """执行指定Agent
        
        Args:
            agent_id: Agent ID
            input_state: 输入状态
            
        Returns:
            WorkflowState: 输出状态
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent not found: {agent_id}")
        
        # 发布执行开始事件
        self.event_manager.publish(AgentEvent.EXECUTION_STARTED, {
            "agent_id": agent_id,
            "state": input_state
        })
        
        agent = self.agents[agent_id]
        try:
            # 使用默认配置执行Agent
            config = {}
            result = await agent.execute(input_state, config)
            
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
    
    def register_agent_type(self, agent_type: str, agent_class: Type[IAgent]) -> None:
        """注册Agent类型
        
        Args:
            agent_type: Agent类型名称
            agent_class: Agent类
        """
        self.agent_types[agent_type] = agent_class
    
    def register_agent(self, agent_id: str, agent: IAgent) -> None:
        """注册Agent实例
        
        Args:
            agent_id: Agent ID
            agent: Agent实例
        """
        self.agents[agent_id] = agent
        
        # 注册事件处理器
        self._setup_agent_events(agent, agent_id)
    
    def get_agent(self, agent_id: str) -> Optional[IAgent]:
        """获取Agent实例
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Optional[IAgent]: Agent实例，如果不存在则返回None
        """
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """列出所有Agent ID
        
        Returns:
            List[str]: Agent ID列表
        """
        return list(self.agents.keys())
    
    def unregister_agent(self, agent_id: str) -> bool:
        """注销Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            bool: 是否成功注销
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False
    
    def get_agent_types(self) -> List[str]:
        """获取支持的Agent类型列表
        
        Returns:
            List[str]: Agent类型列表
        """
        return list(self.agent_types.keys())
    
    def _setup_agent_events(self, agent: IAgent, agent_id: str) -> None:
        """为Agent设置事件处理器
        
        Args:
            agent: Agent实例
            agent_id: Agent ID
        """
        # 这里可以为特定Agent设置事件处理器
        # 例如：记录Agent执行日志、监控性能等
        pass