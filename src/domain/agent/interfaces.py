"""Agent接口定义"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from ...domain.prompts.agent_state import AgentState


class IAgent(ABC):
    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """执行Agent逻辑，返回更新后的状态"""
    
    @abstractmethod
    def can_handle(self, state: AgentState) -> bool:
        """判断Agent是否能处理当前状态"""
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """获取Agent的能力列表"""


class IAgentManager(ABC):
    @abstractmethod
    def create_agent(self, config: 'AgentConfig') -> IAgent:
        """根据配置创建Agent"""
    
    @abstractmethod
    async def execute_agent(self, agent_id: str, input_state: AgentState) -> AgentState:
        """执行指定Agent"""
    
    @abstractmethod
    def register_agent_type(self, agent_type: str, agent_class: Type[IAgent]) -> None:
        """注册Agent类型"""


class IAgentEventManager(ABC):
    @abstractmethod
    def subscribe(self, event_type: 'AgentEvent', handler: callable) -> None:
        """订阅Agent事件"""
    
    @abstractmethod
    def publish(self, event: 'AgentEvent', data: Dict[str, Any]) -> None:
        """发布Agent事件"""