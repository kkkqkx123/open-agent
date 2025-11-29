"""工作流实例 - 新架构轻量级实现

基于新架构原则，WorkflowInstance 仅作为轻量级容器类，
实现 IWorkflow 接口，不包含执行逻辑。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.workflow.config.config import GraphConfig
from src.core.workflow.graph.nodes.state_machine.templates import StateTemplateManager
from src.interfaces.workflow.core import IWorkflow


class WorkflowInstance(IWorkflow):
    """轻量级工作流实例 - 仅实现IWorkflow接口
    
    不包含执行逻辑，仅持有配置和编译图。
    执行逻辑由 WorkflowInstanceCoordinator 处理。
    """
    
    def __init__(
        self,
        config: GraphConfig,
        compiled_graph: Optional[Any] = None,
        state_template_manager: Optional[StateTemplateManager] = None
    ):
        """初始化工作流实例
        
        Args:
            config: 工作流配置
            compiled_graph: 编译后的图
            state_template_manager: 状态模板管理器
        """
        self.config = config
        self.compiled_graph = compiled_graph
        self.state_template_manager = state_template_manager or StateTemplateManager()
        self._created_at = datetime.now()
        
        if self.compiled_graph is None:
            from src.adapters.workflow.langgraph_adapter import LangGraphAdapter
            adapter = LangGraphAdapter()
            self.compiled_graph = adapter.create_graph_sync(config)
    
    # 基本属性（IWorkflow 接口要求）
    @property
    def workflow_id(self) -> str:
        return self.config.name
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def description(self) -> Optional[str]:
        return self.config.description
    
    @property
    def version(self) -> str:
        return getattr(self.config, 'version', '1.0.0')
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return getattr(self.config, 'metadata', {})
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]) -> None:
        if hasattr(self.config, 'metadata'):
            setattr(self.config, 'metadata', value)
    
    @property
    def entry_point(self) -> Optional[str]:
        return self.config.entry_point
    
    @property
    def graph(self) -> Optional[Any]:
        return self.compiled_graph
    
    @property
    def _nodes(self) -> Dict[str, Any]:
        return self.config.nodes if hasattr(self.config, 'nodes') else {}
    
    @property
    def _edges(self) -> Dict[str, Any]:
        edges_dict = {}
        if hasattr(self.config, 'edges'):
            for i, edge in enumerate(self.config.edges):
                edge_id = f"{edge.from_node}-{edge.to_node}-{i}" if hasattr(edge, 'from_node') else str(i)
                edges_dict[edge_id] = edge
        return edges_dict
    
    def set_entry_point(self, entry_point: str) -> None:
        self.config.entry_point = entry_point
    
    def set_graph(self, graph: Any) -> None:
        self.compiled_graph = graph
    
    # IWorkflow 接口要求的方法（简单实现）
    def add_node(self, node: Any) -> None:
        if hasattr(self.config, 'nodes') and node:
            node_id = getattr(node, 'id', getattr(node, 'name', None))
            if node_id:
                self.config.nodes[node_id] = node
    
    def add_edge(self, edge: Any) -> None:
        if hasattr(self.config, 'edges') and edge:
            self.config.edges.append(edge)
    
    def get_node(self, node_id: str) -> Optional[Any]:
        return self._nodes.get(node_id)
    
    def get_edge(self, edge_id: str) -> Optional[Any]:
        return self._edges.get(edge_id)
    
    def add_step(self, step: Any) -> None:
        self.add_node(step)
    
    def add_transition(self, transition: Any) -> None:
        self.add_edge(transition)
    
    def get_step(self, step_id: str) -> Optional[Any]:
        return self.get_node(step_id)
    
    def validate(self) -> List[str]:
        """基础验证 - 详细验证由 WorkflowInstanceCoordinator 处理"""
        errors = []
        
        if not self.config.name:
            errors.append("工作流名称不能为空")
        
        if not self.config.nodes:
            errors.append("工作流必须至少包含一个节点")
        
        if not self.config.entry_point:
            errors.append("工作流必须指定入口点")
        
        return errors
    
    # 执行相关方法（抛出异常，引导使用协调器）
    def execute(self, initial_state: Any, context: Any) -> Any:
        """执行工作流 - 应该通过 WorkflowInstanceCoordinator 调用"""
        raise NotImplementedError(
            "直接调用 execute() 已废弃。请使用 WorkflowInstanceCoordinator 进行执行"
        )
    
    async def execute_async(self, initial_state: Any, context: Any) -> Any:
        """异步执行工作流 - 应该通过 WorkflowInstanceCoordinator 调用"""
        raise NotImplementedError(
            "直接调用 execute_async() 已废弃。请使用 WorkflowInstanceCoordinator 进行执行"
        )
    
    def get_config(self) -> GraphConfig:
        """获取工作流配置"""
        return self.config
    
    def __repr__(self) -> str:
        return f"WorkflowInstance(name={self.config.name}, nodes={len(self.config.nodes)}, edges={len(self.config.edges)})"