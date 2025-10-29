"""工作流工厂

负责工作流实例的创建和初始化。
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import logging

from src.infrastructure.graph.states import (
    BaseGraphState, WorkflowState,
    ReActState, PlanExecuteState, StateFactory
)
from src.domain.agent.state import AgentState as DomainAgentState
from src.infrastructure.graph.config import WorkflowConfig
from src.infrastructure.graph.registry import NodeRegistry
from src.infrastructure.graph.builder import GraphBuilder
from src.infrastructure.container import IDependencyContainer

logger = logging.getLogger(__name__)


class IWorkflowFactory(ABC):
    """工作流工厂接口"""

    @abstractmethod
    def create_workflow(
        self,
        config: WorkflowConfig,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Any:
        """创建工作流实例

        Args:
            config: 工作流配置
            initial_state: 初始状态

        Returns:
            工作流实例
        """
        pass

    @abstractmethod
    def create_state(
        self,
        state_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """创建状态

        Args:
            state_type: 状态类型
            **kwargs: 状态参数

        Returns:
            状态实例
        """
        pass

    @abstractmethod
    def create_workflow_state(
        self,
        workflow_id: str,
        workflow_name: str,
        input_text: str,
        workflow_config: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10
    ) -> WorkflowState:
        """创建工作流状态

        Args:
            workflow_id: 工作流ID
            workflow_name: 工作流名称
            input_text: 输入文本
            workflow_config: 工作流配置
            max_iterations: 最大迭代次数

        Returns:
            工作流状态
        """
        pass

    @abstractmethod
    def create_workflow_from_config(
        self,
        config_path: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Any:
        """从配置文件创建工作流

        Args:
            config_path: 配置文件路径
            initial_state: 初始状态

        Returns:
            工作流实例
        """
        pass

    @abstractmethod
    def clone_workflow(self, workflow: Any) -> Any:
        """克隆工作流

        Args:
            workflow: 原工作流实例

        Returns:
            克隆的工作流实例
        """
        pass

    @property
    @abstractmethod
    def graph_builder(self) -> GraphBuilder:
        """获取图构建器"""
        pass


class WorkflowFactory(IWorkflowFactory):
    """工作流工厂实现
    
    负责根据配置创建工作流实例和状态。
    """
    
    def __init__(
        self,
        container: Optional[IDependencyContainer] = None,
        node_registry: Optional[NodeRegistry] = None
    ):
        """初始化工作流工厂
        
        Args:
            container: 依赖注入容器
            node_registry: 节点注册表
        """
        self.container = container
        self.node_registry = node_registry
        self._graph_builder = None
    
    @property
    def graph_builder(self) -> GraphBuilder:
        """获取图构建器（延迟初始化）"""
        if self._graph_builder is None:
            self._graph_builder = GraphBuilder(
                node_registry=self.node_registry or NodeRegistry()
            )
        return self._graph_builder
    
    def create_workflow(
        self,
        config: WorkflowConfig,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Any:
        """创建工作流实例
        
        Args:
            config: 工作流配置
            initial_state: 初始状态
            
        Returns:
            工作流实例
        """
        logger.info(f"创建工作流: {config.name}")
        
        # 使用图构建器创建工作流
        workflow = self.graph_builder.build_graph(config)
        
        # 如果提供了初始状态，进行状态初始化
        if initial_state:
            workflow = self._initialize_workflow_with_state(
                workflow, initial_state, config
            )
        
        return workflow
    
    def create_state(
        self,
        state_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """创建状态
        
        Args:
            state_type: 状态类型
            **kwargs: 状态参数
            
        Returns:
            状态实例
        """
        state = StateFactory.create_state_by_type(state_type, **kwargs)
        return dict(state)
    
    def create_workflow_state(
        self,
        workflow_id: str,
        workflow_name: str,
        input_text: str,
        workflow_config: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10
    ) -> WorkflowState:
        """创建工作流状态
        
        Args:
            workflow_id: 工作流ID
            workflow_name: 工作流名称
            input_text: 输入文本
            workflow_config: 工作流配置
            max_iterations: 最大迭代次数
            
        Returns:
            工作流状态
        """
        return StateFactory.create_workflow_state(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            input_text=input_text,
            workflow_config=workflow_config,
            max_iterations=max_iterations
        )
    
    def create_agent_state(
        self,
        input_text: str,
        agent_id: str,
        agent_config: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10
    ) -> DomainAgentState:
        """创建Agent状态

        Args:
            input_text: 输入文本
            agent_id: Agent ID
            agent_config: Agent配置
            max_iterations: 最大迭代次数

        Returns:
            Agent状态
        """
        # 创建域层Agent状态
        domain_state = DomainAgentState()
        domain_state.agent_id = agent_id
        domain_state.agent_type = agent_config.get("agent_type", "") if agent_config else ""
        domain_state.current_task = input_text
        domain_state.max_iterations = max_iterations
        domain_state.context = agent_config or {}
        
        return domain_state
    
    def create_react_state(
        self,
        workflow_id: str,
        workflow_name: str,
        input_text: str,
        max_iterations: int = 10,
        max_steps: int = 10
    ) -> ReActState:
        """创建ReAct状态
        
        Args:
            workflow_id: 工作流ID
            workflow_name: 工作流名称
            input_text: 输入文本
            max_iterations: 最大迭代次数
            max_steps: 最大步骤数
            
        Returns:
            ReAct状态
        """
        return StateFactory.create_react_state(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            input_text=input_text,
            max_iterations=max_iterations,
            max_steps=max_steps
        )
    
    def create_plan_execute_state(
        self,
        workflow_id: str,
        workflow_name: str,
        input_text: str,
        max_iterations: int = 10,
        max_steps: int = 10
    ) -> PlanExecuteState:
        """创建计划执行状态
        
        Args:
            workflow_id: 工作流ID
            workflow_name: 工作流名称
            input_text: 输入文本
            max_iterations: 最大迭代次数
            max_steps: 最大步骤数
            
        Returns:
            计划执行状态
        """
        return StateFactory.create_plan_execute_state(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            input_text=input_text,
            max_iterations=max_iterations,
            max_steps=max_steps
        )
    
    def create_workflow_from_config(
        self,
        config_path: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Any:
        """从配置文件创建工作流
        
        Args:
            config_path: 配置文件路径
            initial_state: 初始状态
            
        Returns:
            工作流实例
        """
        # 加载配置
        config = self.graph_builder.load_workflow_config(config_path)
        
        # 创建工作流
        return self.create_workflow(config, initial_state)
    
    def validate_workflow_config(self, config: WorkflowConfig) -> List[str]:
        """验证工作流配置
        
        Args:
            config: 工作流配置
            
        Returns:
            验证错误列表
        """
        return self.graph_builder.validate_config(config)
    
    def _initialize_workflow_with_state(
        self,
        workflow: Any,
        initial_state: Dict[str, Any],
        config: WorkflowConfig
    ) -> Any:
        """使用初始状态初始化工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            config: 工作流配置
            
        Returns:
            初始化后的工作流
        """
        # 这里可以根据工作流类型进行特定的初始化
        # 目前直接返回工作流实例
        return workflow
    
    def get_supported_state_types(self) -> List[str]:
        """获取支持的状态类型
        
        Returns:
            支持的状态类型列表
        """
        return [
            "base",
            "agent", 
            "workflow",
            "react",
            "plan_execute"
        ]
    
    def clone_workflow(self, workflow: Any) -> Any:
        """克隆工作流
        
        Args:
            workflow: 原作流实例
            
        Returns:
            克隆的工作流实例
        """
        # 这里可以实现工作流的克隆逻辑
        # 目前直接返回原实例（实际实现中可能需要深拷贝）
        return workflow
    
    def get_workflow_info(self, workflow: Any) -> Dict[str, Any]:
        """获取工作流信息
        
        Args:
            workflow: 工作流实例
            
        Returns:
            工作流信息
        """
        info = {
            "type": type(workflow).__name__,
            "module": type(workflow).__module__
        }
        
        # 尝试获取更多工作流特定信息
        if hasattr(workflow, 'get_graph'):
            try:
                graph = workflow.get_graph()
                info["node_count"] = str(len(graph.nodes) if hasattr(graph, 'nodes') else 0)
                info["edge_count"] = str(len(graph.edges) if hasattr(graph, 'edges') else 0)
            except Exception:
                pass
        
        return info