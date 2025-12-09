"""图服务

提供统一的图操作接口，集成节点、边、触发器、插件等所有组件。
"""

from typing import Dict, Any, List, Optional, Type, Union, TYPE_CHECKING, cast
from abc import ABC, abstractmethod

from src.interfaces.workflow.graph import IGraph, INode, IEdge, NodeExecutionResult
from src.interfaces.state.base import IState
from src.interfaces.state.workflow import IWorkflowState
from src.core.workflow.registry.registry import UnifiedRegistry

if TYPE_CHECKING:
    from .extensions.triggers.base import ITrigger
    from .extensions.plugins.base import IPlugin


class IGraphService(ABC):
    """图服务接口"""
    
    @abstractmethod
    def build_graph(self, config: Dict[str, Any]) -> IGraph:
        """构建图"""
        pass
    
    @abstractmethod
    async def execute_graph(self, graph: IGraph, initial_state: IWorkflowState) -> NodeExecutionResult:
        """执行图"""
        pass


class GraphService(IGraphService):
    """图服务实现"""
    
    def __init__(self,
                 workflow_registry: UnifiedRegistry,
                 triggers: Optional[List["ITrigger"]] = None,
                 plugins: Optional[List["IPlugin"]] = None) -> None:
        """初始化图服务
        
        Args:
            workflow_registry: 工作流注册表
            triggers: 触发器列表
            plugins: 插件列表
        """
        self._workflow_registry = workflow_registry
        self._triggers: List["ITrigger"] = triggers or []
        self._plugins: List["IPlugin"] = plugins or []
    
    def register_trigger(self, trigger: "ITrigger") -> None:
        """注册触发器"""
        self._triggers.append(trigger)
    
    def register_plugin(self, plugin: "IPlugin") -> None:
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
        from src.infrastructure.graph.core import Graph
        
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
                node_class = self._workflow_registry.nodes.get_node_class(node_type)
                if not node_class:
                    raise ValueError(f"未注册的节点类型: {node_type}")
                
                node = node_class()
                # 确保节点符合INode接口（使用类型检查来满足类型检查器）
                node_interface: INode = cast(INode, node)
                graph.add_node(node_interface)
                created_nodes[node_id] = node_interface
                
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
                edge_class = self._workflow_registry.nodes.get_node_class(edge_type)
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
    
    async def execute_graph(self, graph: IGraph, initial_state: IWorkflowState) -> NodeExecutionResult:
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
            # 检查图是否有引擎
            engine = graph.get_engine()
            if engine:
                # 使用基础设施层的图引擎执行
                input_data = initial_state.to_dict() if hasattr(initial_state, 'to_dict') else {}
                result = await engine.execute(input_data)
                
                # 将结果转换回状态对象
                final_state: IWorkflowState
                if hasattr(initial_state, 'from_dict'):
                    final_state = cast(IWorkflowState, initial_state.__class__.from_dict(result))
                else:
                    final_state = initial_state
                
                # 执行结束插件
                self._execute_end_plugins(final_state)
                
                return NodeExecutionResult(state=final_state)
            
            # 回退到原有的执行逻辑
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
        registry_stats = self._workflow_registry.get_registry_stats()
        
        return {
            **registry_stats,
            "triggers": len(self._triggers),
            "plugins": len(self._plugins)
        }


# 全局图服务实例
_global_graph_service: Optional[GraphService] = None


def create_graph_service(workflow_registry: UnifiedRegistry) -> GraphService:
    """创建图服务实例
    
    Args:
        workflow_registry: 工作流注册表
        
    Returns:
        GraphService: 图服务实例
    """
    return GraphService(workflow_registry)