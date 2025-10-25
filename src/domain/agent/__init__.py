"""Agent模块接口"""

from .interfaces import IAgent, IAgentManager, IAgentEventManager, IAgentFactory, IAgentRegistry
from .config import AgentConfig, MemoryConfig
from .base import BaseAgent
from .manager import AgentManager
from .factory import AgentFactory, get_global_factory, set_global_factory, create_agent  # type: ignore
from .config_loader import AgentConfigLoader
from .events import AgentEvent, AgentEventManager
from .react_agent import ReActAgent
from .plan_execute_agent import PlanExecuteAgent
from .state_manager import AgentStateManager

__all__ = [
    # 接口
    "IAgent",
    "IAgentManager", 
    "IAgentEventManager",
    "IAgentFactory",
    "IAgentRegistry",
    
    # 配置
    "AgentConfig",
    "MemoryConfig",
    
    # 基础类
    "BaseAgent",
    
    # 管理器和工厂
    "AgentManager",
    "AgentFactory",
    "get_global_factory",
    "set_global_factory", 
    "create_agent",
    
    # 配置加载器
    "AgentConfigLoader",
    
    # 事件
    "AgentEvent",
    "AgentEventManager",
    
    # 具体Agent实现
    "ReActAgent",
    "PlanExecuteAgent",
    
    # 状态管理
    "AgentStateManager"
]