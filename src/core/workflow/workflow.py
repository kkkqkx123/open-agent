"""工作流核心实现

基于图的工作流实现。
"""

from typing import Dict, Any, List, Optional
from .interfaces import IWorkflow, IWorkflowState, ExecutionContext
from src.state.interfaces import IState
from .graph import IGraph, INode, IEdge
from .entities import WorkflowState, ExecutionResult
from .value_objects import WorkflowStep, WorkflowTransition, StepType, TransitionType


class Workflow(IWorkflow):
    """工作流实现
    
    基于图的工作流实现，将图的概念封装在工作流内部。
    """
    
    def __init__(self, workflow_id: str, name: str, description: Optional[str] = None):
        """初始化工作流
        
        Args:
            workflow_id: 工作流ID
            name: 工作流名称
        """
        self._workflow_id = workflow_id
        self._name = name
        self._description = description
        self._metadata: Dict[str, Any] = {}
        self._graph: Optional[IGraph] = None
        self._internal_entry_point: Optional[str] = None
        self._internal_nodes: Dict[str, INode] = {}
        self._internal_edges: Dict[str, IEdge] = {}

    @property
    def workflow_id(self) -> str:
        """工作流ID"""
        return self._workflow_id

    @property
    def name(self) -> str:
        """工作流名称"""
        return self._name

    @property
    def description(self) -> Optional[str]:
        """工作流描述"""
        return self._description

    @property
    def metadata(self) -> Dict[str, Any]:
        """工作流元数据"""
        return self._metadata

    @metadata.setter
    def metadata(self, value: Dict[str, Any]) -> None:
        """设置工作流元数据"""
        self._metadata = value

    @property
    def _nodes(self) -> Dict[str, INode]:
        """工作流节点字典"""
        return self._internal_nodes
    
    @property
    def _edges(self) -> Dict[str, IEdge]:
        """工作流边字典"""
        return self._internal_edges
    
    @property
    def _entry_point(self) -> Optional[str]:
        """工作流入口点"""
        return self._internal_entry_point

    def set_graph(self, graph: IGraph) -> None:
        """设置图
        
        Args:
            graph: 图实例
        """
        self._graph = graph

    def set_entry_point(self, entry_point: str) -> None:
        """设置入口点
        
        Args:
            entry_point: 入口点节点ID
        """
        self._internal_entry_point = entry_point

    def add_step(self, step: 'WorkflowStep') -> None:
        """添加步骤
        """
        # 将WorkflowStep转换为INode并添加到工作流中
        from .value_objects import WorkflowStep as WorkflowStepType
        if isinstance(step, WorkflowStepType):
            # 创建一个简单的INode实现来表示步骤
            from .graph.simple_node import SimpleNode
            node = SimpleNode(
                node_id=step.id,
                name=step.name,
                node_type=step.type.value,
                description=step.description,
                config=step.config
            )
            self.add_node(node)

    def add_transition(self, transition: 'WorkflowTransition') -> None:
        """添加转换
        """
        # 将WorkflowTransition转换为IEdge并添加到工作流中
        from .graph.simple_edge import SimpleEdge
        edge = SimpleEdge(
            edge_id=transition.id,
            from_node=transition.from_step,
            to_node=transition.to_step,
            edge_type=transition.type.value,
            condition=transition.condition
        )
        self.add_edge(edge)

    def get_step(self, step_id: str):
        """获取步骤
        """
        node = self.get_node(step_id)
        if node:
            # 返回一个WorkflowStep对象
            from .value_objects import WorkflowStep, StepType
            # 由于INode接口没有name等属性，我们使用getattr来安全访问
            return WorkflowStep(
                id=node.node_id,
                name=getattr(node, 'name', ''),
                type=StepType(getattr(node, 'node_type', 'analysis')),
                description=getattr(node, 'description', ''),
                config=getattr(node, 'config', {})
            )
        return None

    def add_node(self, node: INode) -> None:
        """添加节点
        
        Args:
            node: 节点实例
        """
        self._internal_nodes[node.node_id] = node
        if self._graph:
            self._graph.add_node(node)

    def add_edge(self, edge: IEdge) -> None:
        """添加边
        
        Args:
            edge: 边实例
        """
        self._internal_edges[edge.edge_id] = edge
        if self._graph:
            self._graph.add_edge(edge)

    def get_node(self, node_id: str) -> Optional[INode]:
        """获取节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            Optional[INode]: 节点实例，如果不存在则返回None
        """
        return self._internal_nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[IEdge]:
        """获取边
        
        Args:
            edge_id: 边ID
            
        Returns:
            Optional[IEdge]: 边实例，如果不存在则返回None
        """
        return self._internal_edges.get(edge_id)

    def validate(self) -> List[str]:
        """验证工作流
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 检查是否有入口点
        if not self._internal_entry_point:
            errors.append("工作流缺少入口点")
        
        # 检查入口点是否存在
        if self._internal_entry_point and self._internal_entry_point not in self._internal_nodes:
            errors.append(f"入口点节点不存在: {self._internal_entry_point}")
        
        # 检查边的有效性
        for edge in self._internal_edges.values():
            if edge.from_node not in self._internal_nodes:
                errors.append(f"边的起始节点不存在: {edge.from_node}")
            if edge.to_node not in self._internal_nodes:
                errors.append(f"边的目标节点不存在: {edge.to_node}")
        
        # 如果有图，使用图的验证
        if self._graph:
            graph_errors = self._graph.validate()
            errors.extend(graph_errors)
        
        return errors

    def execute(self, initial_state: IWorkflowState, context: ExecutionContext) -> IWorkflowState:
        """执行工作流
        
        Args:
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        from .execution.executor import WorkflowExecutor
        
        if not self._graph:
            raise ValueError("工作流未设置图，无法执行")
        
        executor = WorkflowExecutor()
        return executor.execute(self, initial_state, context)

    async def execute_async(self, initial_state: IWorkflowState,
                           context: ExecutionContext) -> IWorkflowState:
        """异步执行工作流
        
        Args:
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        from .execution.executor import WorkflowExecutor
        
        if not self._graph:
            raise ValueError("工作流未设置图，无法执行")
        
        executor = WorkflowExecutor()
        return await executor.execute_async(self, initial_state, context)