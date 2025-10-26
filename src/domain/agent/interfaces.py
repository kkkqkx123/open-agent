"""Agent接口定义"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Callable, Union, Union
from .state import AgentState
from .config import AgentConfig
from .events import AgentEvent
from ...application.workflow.state import WorkflowState

# 导入WorkflowState用于类型兼容性
from src.application.workflow.state import WorkflowState


class IAgent(ABC):
    """Agent接口定义"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Agent描述"""
        pass
    
    @abstractmethod
    async def execute(self, state: Union[AgentState, WorkflowState], config: Dict[str, Any]) -> Union[AgentState, WorkflowState]:
        """执行Agent逻辑，返回更新后的状态

        Args:
            state: 当前Agent状态
            config: 执行配置

        Returns:
            AgentState或WorkflowState: 更新后的状态
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """获取Agent能力描述
        
        Returns:
            Dict[str, Any]: 能力描述字典
        """
        pass
    
    @abstractmethod
    def validate_state(self, state: AgentState) -> bool:
        """验证状态是否适合此Agent
        
        Args:
            state: Agent状态
            
        Returns:
            bool: 是否适合
        """
        pass
    
    @abstractmethod
    def can_handle(self, state: AgentState) -> bool:
        """判断Agent是否能处理当前状态
        
        Args:
            state: Agent状态
            
        Returns:
            bool: 是否能处理
        """
        pass
    
    @abstractmethod
    def get_available_tools(self) -> List[str]:
        """获取可用工具列表
        
        Returns:
            List[str]: 工具名称列表
        """
        pass


class IAgentFactory(ABC):
    """Agent工厂接口"""
    
    @abstractmethod
    def create_agent(self, agent_config: Dict[str, Any]) -> IAgent:
        """根据配置创建Agent实例
        
        Args:
            agent_config: Agent配置字典
            
        Returns:
            IAgent: Agent实例
        """
        pass
    
    @abstractmethod
    def create_agent_from_config(self, config: AgentConfig) -> IAgent:
        """从AgentConfig对象创建Agent实例
        
        Args:
            config: Agent配置对象
            
        Returns:
            IAgent: Agent实例
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """获取支持的Agent类型列表
        
        Returns:
            List[str]: 支持的Agent类型列表
        """
        pass
    
    @abstractmethod
    def register_agent_type(self, agent_type: str, agent_class: Type[IAgent]) -> None:
        """注册新的Agent类型
        
        Args:
            agent_type: Agent类型名称
            agent_class: Agent类
        """
        pass


class IAgentManager(ABC):
    """Agent管理器接口"""
    
    @abstractmethod
    def create_agent(self, config: AgentConfig) -> IAgent:
        """根据配置创建Agent
        
        Args:
            config: Agent配置
            
        Returns:
            IAgent: Agent实例
        """
        pass
    
    @abstractmethod
    async def execute_agent(self, agent_id: str, input_state: AgentState) -> AgentState:
        """执行指定Agent
        
        Args:
            agent_id: Agent ID
            input_state: 输入状态
            
        Returns:
            AgentState: 输出状态
        """
        pass
    
    @abstractmethod
    def register_agent_type(self, agent_type: str, agent_class: Type[IAgent]) -> None:
        """注册Agent类型
        
        Args:
            agent_type: Agent类型名称
            agent_class: Agent类
        """
        pass
    
    @abstractmethod
    def register_agent(self, agent_id: str, agent: IAgent) -> None:
        """注册Agent实例
        
        Args:
            agent_id: Agent ID
            agent: Agent实例
        """
        pass


class IAgentEventManager(ABC):
    """Agent事件管理器接口"""
    
    @abstractmethod
    def subscribe(self, event_type: AgentEvent, handler: Callable) -> None:
        """订阅Agent事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        pass
    
    @abstractmethod
    def publish(self, event: AgentEvent, data: Dict[str, Any]) -> None:
        """发布Agent事件
        
        Args:
            event: 事件对象
            data: 事件数据
        """
        pass


class IAgentRegistry(ABC):
    """Agent注册表接口"""
    
    @abstractmethod
    def register(self, agent_id: str, agent: IAgent) -> None:
        """注册Agent
        
        Args:
            agent_id: Agent ID
            agent: Agent实例
        """
        pass
    
    @abstractmethod
    def get(self, agent_id: str) -> Optional[IAgent]:
        """获取Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Optional[IAgent]: Agent实例，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def list_agents(self) -> List[str]:
        """列出所有Agent ID
        
        Returns:
            List[str]: Agent ID列表
        """
        pass
    
    @abstractmethod
    def unregister(self, agent_id: str) -> bool:
        """注销Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            bool: 是否成功注销
        """
        pass