"""LangGraph适配器

提供与LangGraph框架的适配。
"""

from typing import Dict, Any, Optional, List, Callable
import logging

from langgraph.graph import StateGraph, START, END
from src.core.workflow.interfaces import IWorkflow, IWorkflowState, IWorkflowBuilder
from src.core.workflow.graph.interfaces import IGraph, INode, IEdge
from src.core.workflow.entities import Workflow, WorkflowState


logger = logging.getLogger(__name__)


class LangGraphAdapter:
    """LangGraph适配器
    
    提供与LangGraph框架的适配，支持图构建和编译。
    """
    
    def __init__(self):
        """初始化适配器"""
        self._compiled_graphs: Dict[str, Any] = {}

    def build_langgraph(self, workflow: IWorkflow) -> Any:
        """构建LangGraph图
        
        Args:
            workflow: 工作流实例
            
        Returns:
            Any: 编译后的LangGraph图
        """
        
        # 获取状态类
        state_class = self._get_state_class(workflow)
        
        # 创建StateGraph
        builder = StateGraph(state_class)
        
        # 添加节点
        for node in workflow._nodes.values():
            node_function = self._create_node_function(node)
            builder.add_node(node.node_id, node_function)
            logger.debug(f"添加节点: {node.node_id}")
        
        # 添加边
        for edge in workflow._edges.values():
            self._add_edge_to_builder(builder, edge)
            logger.debug(f"添加边: {edge.edge_id}")
        
        # 设置入口点
        if workflow._entry_point:
            builder.add_edge(START, workflow._entry_point)
        
        # 编译图
        compiled_graph = builder.compile()
        
        # 缓存编译后的图
        self._compiled_graphs[workflow.workflow_id] = compiled_graph
        
        logger.info(f"LangGraph图构建完成: {workflow.workflow_id}")
        return compiled_graph

    def _get_state_class(self, workflow: IWorkflow) -> type:
        """获取状态类
        
        Args:
            workflow: 工作流实例
            
        Returns:
            type: 状态类
        """
        # 创建动态状态类
        class DynamicState:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        return DynamicState

    def _create_node_function(self, node: INode) -> Callable:
        """创建节点函数
        
        Args:
            node: 节点实例
            
        Returns:
            Callable: 节点函数
        """
        def node_function(state):
            """节点函数"""
            try:
                # 执行节点
                result = node.execute(state, {})
                
                # 返回更新后的状态
                if hasattr(result, 'state'):
                    return result.state
                else:
                    return state
            except Exception as e:
                logger.error(f"节点执行失败 {node.node_id}: {e}")
                # 返回原始状态
                return state
        
        return node_function

    def _add_edge_to_builder(self, builder: Any, edge: IEdge) -> None:
        """添加边到构建器
        
        Args:
            builder: LangGraph构建器
            edge: 边实例
        """
        # 添加简单边
        if edge.edge_type == "simple":
            if edge.to_node == "__end__":
                builder.add_edge(edge.from_node, END)
            else:
                builder.add_edge(edge.from_node, edge.to_node)
        
        # 添加条件边
        elif edge.edge_type == "conditional":
            def condition_function(state):
                """条件函数"""
                return edge.can_traverse(state, {})
            
            if edge.to_node == "__end__":
                builder.add_conditional_edges(edge.from_node, condition_function, {"__end__": END})
            else:
                builder.add_conditional_edges(edge.from_node, condition_function, {edge.to_node: END})
        
        # 添加灵活条件边
        elif edge.edge_type == "flexible":
            def route_function(state):
                """路由函数"""
                next_nodes = edge.get_next_nodes(state, {})
                return next_nodes[0] if next_nodes else "__end__"
            
            if edge.to_node == "__end__":
                builder.add_conditional_edges(edge.from_node, route_function, {"__end__": END})
            else:
                builder.add_conditional_edges(edge.from_node, route_function, {edge.to_node: END})

    def get_compiled_graph(self, workflow_id: str) -> Optional[Any]:
        """获取编译后的图
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[Any]: 编译后的图，如果不存在则返回None
        """
        return self._compiled_graphs.get(workflow_id)

    def clear_cache(self) -> None:
        """清除缓存"""
        self._compiled_graphs.clear()
        logger.info("清除LangGraph图缓存")