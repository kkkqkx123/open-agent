"""图服务

提供统一的图操作接口，集成节点、边、触发器、插件等所有组件。
"""

from typing import Dict, Any, List, Optional, Type, Union, TYPE_CHECKING, cast
from abc import ABC, abstractmethod

from src.interfaces.workflow.graph import IGraph, INode, IEdge, NodeExecutionResult
from src.interfaces.state.interfaces import IState
from src.interfaces.state.workflow import IWorkflowState
from .registry.global_registry import get_global_registry

if TYPE_CHECKING:
    from .extensions.triggers.base import ITrigger
    from .extensions.plugins.base import IPlugin


class IGraphService(ABC):
    """图服务接口"""
    
    @abstractmethod
    def register_node_type(self, node_type: str, node_class: Type[INode]) -> None:
        """注册节点类型"""
        pass
    
    @abstractmethod
    def register_edge_type(self, edge_type: str, edge_class: Type[IEdge]) -> None:
        """注册边类型"""
        pass
    
    @abstractmethod
    def register_trigger(self, trigger: "ITrigger") -> None:
        """注册触发器"""
        pass
    
    @abstractmethod
    def register_plugin(self, plugin: "IPlugin") -> None:
        """注册插件"""
        pass
    
    @abstractmethod
    def build_graph(self, config: Dict[str, Any]) -> IGraph:
        """构建图"""
        pass
    
    @abstractmethod
    def execute_graph(self, graph: IGraph, initial_state: IWorkflowState) -> NodeExecutionResult:
        """执行图"""
        pass


class GraphService(IGraphService):
    """图服务实现"""
    
    def __init__(self) -> None:
        """初始化图服务"""
        self._global_registry = get_global_registry()
        self._triggers: List["ITrigger"] = []
        self._plugins: List["IPlugin"] = []
    
    def register_node_type(self, node_type: str, node_class: Type[INode]) -> None:
        """注册节点类型"""
        self._global_registry.node_registry.register(node_type, node_class)
    
    def register_edge_type(self, edge_type: str, edge_class: Type[IEdge]) -> None:
        """注册边类型"""
        self._global_registry.edge_registry.register_edge(edge_type, edge_class)
    
    def register_trigger(self, trigger: ITrigger) -> None:
        """注册触发器"""
        self._triggers.append(trigger)
    
    def register_plugin(self, plugin: IPlugin) -> None:
        """注册插件"""
        self._plugins.append(plugin)
    
    def build_graph(self, config: Dict[str, Any]) -> IGraph:
        """从配置构建图
        
        Args:
            config: 图配置，格式为:
                {
                    "graph_id": "graph_1",  # 可选
                    "nodes": [
                        {
                            "id": "node_1",
                            "type": "simple_node",
                            "name": "Start Node",
                            "description": "Entry point",
                            "config": {}
                        },
                        ...
                    ],
                    "edges": [
                        {
                            "id": "edge_1",
                            "from": "node_1",
                            "to": "node_2",
                            "type": "simple",
                            "config": {}
                        },
                        ...
                    ]
                }
            
        Returns:
            IGraph: 构建的图
            
        Raises:
            ValueError: 配置无效或图构建失败
        """
        from .graph import Graph
        
        # 创建图
        graph_id = config.get("graph_id")
        graph = Graph(graph_id)
        
        # 添加节点
        nodes_config = config.get("nodes", [])
        created_nodes: Dict[str, INode] = {}
        
        for node_config in nodes_config:
            node_id = node_config.get("id")
            node_type = node_config.get("type")
            
            if not node_id:
                raise ValueError("节点必须有ID")
            
            if not node_type:
                raise ValueError(f"节点 {node_id} 必须指定type")
            
            try:
                # 从注册表获取节点类
                node_class = self._global_registry.node_registry.get_node_class(node_type)
                if not node_class:
                    raise ValueError(f"未注册的节点类型: {node_type}")
                
                node = node_class()
                graph.add_node(node)
                created_nodes[node_id] = node
                
            except ValueError as ve:
                # 直接重新抛出ValueError
                raise ve
            except Exception as e:
                raise ValueError(f"创建节点 {node_id} (type={node_type}) 失败: {str(e)}")
        
        # 添加边
        edges_config = config.get("edges", [])
        
        for edge_config in edges_config:
            edge_id = edge_config.get("id")
            source_node = edge_config.get("from")
            target_node = edge_config.get("to")
            edge_type = edge_config.get("type")
            
            if not all([edge_id, source_node, target_node]):
                raise ValueError("边必须有id、from和to")
            
            if not edge_type:
                raise ValueError(f"边 {edge_id} 必须指定type")
            
            if source_node not in created_nodes:
                raise ValueError(f"源节点 {source_node} 不存在")
            if target_node not in created_nodes:
                raise ValueError(f"目标节点 {target_node} 不存在")
            
            try:
                # 从注册表获取边类
                edge_class = self._global_registry.edge_registry.get_edge_class(edge_type)
                if not edge_class:
                    raise ValueError(f"未注册的边类型: {edge_type}")
                
                # 创建边实例（使用 type: ignore 处理动态类型）
                edge: IEdge = edge_class(edge_id, source_node, target_node)  # type: ignore[call-arg]
                graph.add_edge(edge)
                
            except ValueError as ve:
                # 直接重新抛出ValueError
                raise ve
            except Exception as e:
                raise ValueError(f"创建边 {edge_id} (type={edge_type}) 失败: {str(e)}")
        
        # 验证图
        validation_errors = graph.validate()
        if validation_errors:
            raise ValueError(f"图验证失败: {', '.join(validation_errors)}")
        
        return graph
    
    def execute_graph(self, graph: IGraph, initial_state: IWorkflowState) -> NodeExecutionResult:
        """执行图
        
        Args:
            graph: 要执行的图
            initial_state: 初始状态
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        # 执行开始插件
        self._execute_start_plugins(initial_state)
        
        try:
            # 获取入口节点
            entry_points = graph.get_entry_points()
            if not entry_points:
                raise ValueError("图没有入口节点")
            
            current_node_id = entry_points[0]
            current_state: IWorkflowState = initial_state
            
            # 执行图
            while current_node_id:
                # 获取当前节点
                current_node = graph.get_node(current_node_id)
                if current_node is None:
                    break
                
                # 执行前触发器检查
                if not self._check_triggers_before_execution(current_node, current_state):
                    break
                
                # 执行节点
                result = current_node.execute(current_state, {})
                current_state = cast(IWorkflowState, result.state)
                
                # 执行后触发器检查
                self._check_triggers_after_execution(current_node, result)
                
                # 获取下一个节点
                next_nodes = self._get_next_nodes(graph, current_node_id, current_state)
                if not next_nodes:
                    break
                
                # 简单选择第一个下一个节点（可以根据路由逻辑改进）
                current_node_id = next_nodes[0]
            
            # 执行结束插件
            self._execute_end_plugins(current_state)
            
            return NodeExecutionResult(state=current_state)
            
        except Exception as e:
            # 错误处理插件
            self._execute_error_plugins(e, initial_state)
            raise
    
    def _execute_start_plugins(self, state: IWorkflowState) -> None:
        """执行开始插件"""
        for plugin in self._plugins:
            callback = getattr(plugin, 'on_start', None)
            if callback is not None:
                callback(state)
    
    def _execute_end_plugins(self, state: IWorkflowState) -> None:
        """执行结束插件"""
        for plugin in self._plugins:
            callback = getattr(plugin, 'on_end', None)
            if callback is not None:
                callback(state)
    
    def _execute_error_plugins(self, error: Exception, state: IWorkflowState) -> None:
        """执行错误处理插件"""
        for plugin in self._plugins:
            callback = getattr(plugin, 'on_error', None)
            if callback is not None:
                callback(error, state)
    
    def _check_triggers_before_execution(self, node: INode, state: IWorkflowState) -> bool:
        """执行前触发器检查"""
        for trigger in self._triggers:
            callback = getattr(trigger, 'before_node_execution', None)
            if callback is not None:
                if not callback(node, state):
                    return False
        return True
    
    def _check_triggers_after_execution(self, node: INode, result: NodeExecutionResult) -> None:
        """执行后触发器检查"""
        for trigger in self._triggers:
            callback = getattr(trigger, 'after_node_execution', None)
            if callback is not None:
                callback(node, result)
    
    def _get_next_nodes(self, graph: IGraph, current_node_id: str, state: IWorkflowState) -> List[str]:
        """获取下一个节点列表"""
        next_nodes = []
        edges = graph.get_edges()
        
        for edge in edges.values():
            if edge.source_node == current_node_id:
                if edge.can_traverse(state):
                    next_nodes.append(edge.target_node)
        
        return next_nodes
    
    def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        registry_stats = self._global_registry.get_registry_stats()
        
        return {
            **registry_stats,
            "triggers": len(self._triggers),
            "plugins": len(self._plugins)
        }


# 全局图服务实例
_global_graph_service: Optional[GraphService] = None


def get_graph_service() -> GraphService:
    """获取全局图服务实例
    
    Returns:
        GraphService: 图服务实例
    """
    global _global_graph_service
    if _global_graph_service is None:
        _global_graph_service = GraphService()
    return _global_graph_service


def reset_graph_service() -> None:
    """重置全局图服务"""
    global _global_graph_service
    _global_graph_service = None