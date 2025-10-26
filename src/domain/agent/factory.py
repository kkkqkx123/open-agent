"""Agent工厂实现

提供配置驱动的Agent创建功能，支持多种Agent类型的统一管理。
"""

from typing import Dict, Any, List, Optional, Type, cast
from abc import ABC, abstractmethod
import logging

from .interfaces import IAgent, IAgentFactory
from .config import AgentConfig
from .react_agent import ReActAgent
from .plan_execute_agent import PlanExecuteAgent
from .base import BaseAgent
from ..state.interfaces import IStateManager
from ...infrastructure.llm.interfaces import ILLMClient
from ..tools.interfaces import IToolExecutor
from .events import AgentEventManager

logger = logging.getLogger(__name__)


class AgentFactory(IAgentFactory):
    """Agent工厂实现
    
    负责根据配置创建不同类型的Agent实例，支持配置驱动的Agent管理。
    """
    
    def __init__(
        self,
        llm_factory: Any,  # ILLMFactory
        tool_executor: IToolExecutor,
        state_manager: Optional[IStateManager] = None,
        event_manager: Optional[AgentEventManager] = None
    ):
        """初始化Agent工厂

        Args:
            llm_factory: LLM工厂实例
            tool_executor: 工具执行器实例
            state_manager: 状态管理器实例（可选）
            event_manager: 事件管理器实例（可选）
        """
        self.llm_factory = llm_factory
        self.tool_executor = tool_executor
        self.state_manager = state_manager
        self.event_manager = event_manager or AgentEventManager()
        
        # 注册支持的Agent类型
        self._agent_types: Dict[str, Type[IAgent]] = {
        "react": ReActAgent,
        "plan_execute": PlanExecuteAgent,
        }
        
        # Agent实例缓存（可选，用于性能优化）
        self._agent_cache: Dict[str, IAgent] = {}
        
        logger.info("AgentFactory初始化完成")
    
    def create_agent(self, agent_config: Dict[str, Any]) -> IAgent:
        """根据配置创建Agent实例
        
        Args:
            agent_config: Agent配置字典
            
        Returns:
            IAgent: 创建的Agent实例
            
        Raises:
            ValueError: 当Agent类型不支持或配置无效时
        """
        try:
            # 1. 解析和验证配置
            config = self._parse_config(agent_config)
            
            # 2. 检查缓存（如果启用）
            cache_key = self._generate_cache_key(config)
            if cache_key in self._agent_cache:
                logger.debug(f"从缓存获取Agent: {config.name}")
                return self._agent_cache[cache_key]
            
            # 3. 获取LLM客户端
            llm_client = self._get_llm_client(config.llm)
            
            # 4. 获取工具执行器
            tool_executor = self._get_tool_executor(config)
            
            # 5. 创建Agent实例
            agent = self._create_agent_instance(config, llm_client, tool_executor)
            
            # 6. 缓存Agent实例（如果启用）
            if self._should_cache_agent(config):
                self._agent_cache[cache_key] = agent
            
            logger.info(f"成功创建Agent: {config.name} (类型: {config.agent_type})")
            return agent
            
        except Exception as e:
            logger.error(f"创建Agent失败: {e}")
            raise ValueError(f"创建Agent失败: {e}")
    
    def create_agent_from_config(self, config: AgentConfig) -> IAgent:
        """从AgentConfig对象创建Agent实例
        
        Args:
            config: Agent配置对象
            
        Returns:
            IAgent: 创建的Agent实例
        """
        return self.create_agent(config.to_dict())
    
    def get_supported_types(self) -> List[str]:
        """获取支持的Agent类型列表
        
        Returns:
            List[str]: 支持的Agent类型列表
        """
        return list(self._agent_types.keys())
    
    def register_agent_type(self, agent_type: str, agent_class: Type[IAgent]) -> None:
        """注册新的Agent类型
        
        Args:
            agent_type: Agent类型名称
            agent_class: Agent类
            
        Raises:
            ValueError: 当Agent类型已存在时
        """
        if agent_type in self._agent_types:
            raise ValueError(f"Agent类型已存在: {agent_type}")
        
        self._agent_types[agent_type] = agent_class
        logger.info(f"注册Agent类型: {agent_type}")
    
    def unregister_agent_type(self, agent_type: str) -> None:
        """注销Agent类型
        
        Args:
            agent_type: Agent类型名称
        """
        if agent_type in self._agent_types:
            del self._agent_types[agent_type]
            logger.info(f"注销Agent类型: {agent_type}")
    
    def clear_cache(self) -> None:
        """清除Agent实例缓存"""
        self._agent_cache.clear()
        logger.info("清除Agent缓存")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息
        
        Returns:
            Dict[str, Any]: 缓存信息
        """
        return {
            "cache_size": len(self._agent_cache),
            "cached_agents": list(self._agent_cache.keys())
        }
    
    def _parse_config(self, agent_config: Dict[str, Any]) -> AgentConfig:
        """解析和验证Agent配置
        
        Args:
            agent_config: 原始配置字典
            
        Returns:
            AgentConfig: 解析后的配置对象
            
        Raises:
            ValueError: 当配置无效时
        """
        try:
            # 验证必需字段
            if "agent_type" not in agent_config:
                raise ValueError("缺少必需字段: agent_type")
            
            if "name" not in agent_config:
                raise ValueError("缺少必需字段: name")
            
            # 创建配置对象
            config = AgentConfig(**agent_config)
            
            # 验证Agent类型
            if config.agent_type not in self._agent_types:
                raise ValueError(f"不支持的Agent类型: {config.agent_type}")
            
            return config
            
        except Exception as e:
            raise ValueError(f"配置解析失败: {e}")
    
    def _get_llm_client(self, llm_name: str) -> ILLMClient:
        """获取LLM客户端
        
        Args:
            llm_name: LLM名称
            
        Returns:
            ILLMClient: LLM客户端实例
            
        Raises:
            ValueError: 当LLM不存在时
        """
        try:
            # 从LLM工厂获取客户端
            llm_config = {"model_name": llm_name}
            return cast(ILLMClient, self.llm_factory.create_client(llm_config))
        except Exception as e:
            raise ValueError(f"获取LLM客户端失败 ({llm_name}): {e}")
    
    def _get_tool_executor(self, config: AgentConfig) -> IToolExecutor:
        """获取工具执行器

        Args:
            config: Agent配置

        Returns:
            IToolExecutor: 工具执行器实例
        """
        # 这里可以根据配置创建特定的工具执行器
        # 目前使用工具执行器
        return self.tool_executor
    
    def _create_agent_instance(
        self,
        config: AgentConfig,
        llm_client: ILLMClient,
        tool_executor: IToolExecutor
    ) -> IAgent:
        """创建Agent实例

        Args:
        config: Agent配置
        llm_client: LLM客户端
        tool_executor: 工具执行器

        Returns:
        IAgent: Agent实例
        """
        agent_class = cast(Type[BaseAgent], self._agent_types[config.agent_type])

        # 创建Agent实例
        agent = agent_class(
            config=config,
            llm_client=llm_client,
            tool_executor=tool_executor,
            event_manager=self.event_manager
        )

        return agent
    
    def _generate_cache_key(self, config: AgentConfig) -> str:
        """生成缓存键
        
        Args:
            config: Agent配置
            
        Returns:
            str: 缓存键
        """
        # 使用配置的关键字段生成缓存键
        key_parts = [
            config.agent_type,
            config.name,
            config.llm,
            str(sorted(config.tools)),
            str(sorted(config.tool_sets))
        ]
        return "|".join(key_parts)
    
    def _should_cache_agent(self, config: AgentConfig) -> bool:
        """判断是否应该缓存Agent实例
        
        Args:
            config: Agent配置
            
        Returns:
            bool: 是否应该缓存
        """
        # 可以根据配置决定是否缓存
        # 目前默认不缓存，因为Agent可能有状态
        return False


# 全局Agent工厂实例
_global_factory: Optional[AgentFactory] = None


def get_global_factory() -> AgentFactory:
    """获取全局Agent工厂实例
    
    Returns:
        AgentFactory: 全局Agent工厂实例
    """
    global _global_factory
    if _global_factory is None:
        raise RuntimeError("Agent工厂未初始化，请先调用set_global_factory")
    return _global_factory


def set_global_factory(factory: AgentFactory) -> None:
    """设置全局Agent工厂实例
    
    Args:
        factory: 工厂实例
    """
    global _global_factory
    _global_factory = factory


def create_agent(agent_config: Dict[str, Any]) -> IAgent:
    """使用全局工厂创建Agent的便捷函数
    
    Args:
        agent_config: Agent配置
        
    Returns:
        IAgent: Agent实例
    """
    return get_global_factory().create_agent(agent_config)