"""图的基础实现类

提供图的核心功能实现，包括节点和边的管理。
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from src.interfaces.workflow.graph import INode, IEdge
    from src.infrastructure.graph.engine.state_graph import StateGraphEngine

from src.interfaces.workflow.graph import IGraph


class Graph(IGraph):
    """图实现类"""
    
    def __init__(self, graph_id: Optional[str] = None) -> None:
        """初始化图
        
        Args:
            graph_id: 图ID，如果为None则自动生成
        """
        self._graph_id = graph_id or str(uuid4())
        self._nodes: Dict[str, 'INode'] = {}
        self._edges: Dict[str, 'IEdge'] = {}
        self._engine: Optional['StateGraphEngine'] = None
    
    @property
    def graph_id(self) -> str:
        """图ID"""
        return self._graph_id
    
    def add_node(self, node: 'INode') -> None:
        """添加节点
        
        Args:
            node: 要添加的节点
            
        Raises:
            ValueError: 节点ID已存在
        """
        if node.node_id in self._nodes:
            raise ValueError(f"节点 {node.node_id} 已存在")
        self._nodes[node.node_id] = node
    
    def add_edge(self, edge: 'IEdge') -> None:
        """添加边
        
        Args:
            edge: 要添加的边
            
        Raises:
            ValueError: 边ID已存在或源/目标节点不存在
        """
        if edge.edge_id in self._edges:
            raise ValueError(f"边 {edge.edge_id} 已存在")
        
        # 验证源节点和目标节点存在
        if edge.source_node not in self._nodes:
            raise ValueError(f"源节点 {edge.source_node} 不存在")
        if edge.target_node not in self._nodes:
            raise ValueError(f"目标节点 {edge.target_node} 不存在")
        
        self._edges[edge.edge_id] = edge
    
    def get_node(self, node_id: str) -> Optional['INode']:
        """获取节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            INode: 节点对象，如果不存在则返回None
        """
        return self._nodes.get(node_id)
    
    def get_edge(self, edge_id: str) -> Optional['IEdge']:
        """获取边
        
        Args:
            edge_id: 边ID
            
        Returns:
            IEdge: 边对象，如果不存在则返回None
        """
        return self._edges.get(edge_id)
    
    def get_nodes(self) -> Dict[str, 'INode']:
        """获取所有节点
        
        Returns:
            Dict[str, INode]: 节点ID到节点对象的映射
        """
        return self._nodes.copy()
    
    def get_edges(self) -> Dict[str, 'IEdge']:
        """获取所有边
        
        Returns:
            Dict[str, IEdge]: 边ID到边对象的映射
        """
        return self._edges.copy()
    
    def validate(self) -> List[str]:
        """验证图结构
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors: List[str] = []
        
        # 验证至少有一个节点
        if not self._nodes:
            errors.append("图必须至少有一个节点")
            return errors
        
        # 验证所有节点
        for node in self._nodes.values():
            errors.extend(node.validate())
        
        # 验证所有边
        for edge in self._edges.values():
            errors.extend(edge.validate())
            
            # 验证边的源和目标节点存在
            if edge.source_node not in self._nodes:
                errors.append(f"边 {edge.edge_id} 的源节点 {edge.source_node} 不存在")
            if edge.target_node not in self._nodes:
                errors.append(f"边 {edge.edge_id} 的目标节点 {edge.target_node} 不存在")
        
        return errors
    
    def get_entry_points(self) -> List[str]:
        """获取入口节点列表（没有入站边的节点）
        
        Returns:
            List[str]: 入口节点ID列表
        """
        # 如果没有边，所有节点都是入口点
        if not self._edges:
            return list(self._nodes.keys())
        
        # 找出所有有入站边的节点
        nodes_with_incoming = set()
        for edge in self._edges.values():
            nodes_with_incoming.add(edge.target_node)
        
        # 入口点是没有入站边的节点
        entry_points = [
            node_id for node_id in self._nodes.keys()
            if node_id not in nodes_with_incoming
        ]
        
        # 如果没有找到入口点，返回第一个节点
        return entry_points if entry_points else list(self._nodes.keys())[:1]
    
    def get_exit_points(self) -> List[str]:
        """获取出口节点列表（没有出站边的节点）
        
        Returns:
            List[str]: 出口节点ID列表
        """
        # 如果没有边，所有节点都是出口点
        if not self._edges:
            return list(self._nodes.keys())
        
        # 找出所有有出站边的节点
        nodes_with_outgoing = set()
        for edge in self._edges.values():
            nodes_with_outgoing.add(edge.source_node)
        
        # 出口点是没有出站边的节点
        exit_points = [
            node_id for node_id in self._nodes.keys()
            if node_id not in nodes_with_outgoing
        ]
        
        # 如果没有找到出口点，返回最后一个节点
        return exit_points if exit_points else list(self._nodes.keys())[-1:]
    
    def get_engine(self) -> Optional['StateGraphEngine']:
        """获取图引擎
        
        Returns:
            StateGraphEngine: 图引擎实例
        """
        if self._engine is None:
            # 创建图引擎
            from src.infrastructure.graph.engine.state_graph import StateGraphEngine
            self._engine = StateGraphEngine(dict)  # 使用简单的字典作为状态模式
            
            # 添加节点
            for node_id, node in self._nodes.items():
                self._engine.add_node(node_id, node.execute)
            
            # 添加边
            for edge in self._edges.values():
                self._engine.add_edge(edge.source_node, edge.target_node)
            
            # 设置入口点
            entry_points = self.get_entry_points()
            if entry_points:
                self._engine.set_entry_point(entry_points[0])
        
        return self._engine
    
    async def compile(self, config: Optional[Dict[str, Any]] = None) -> Any:
        """编译图
        
        Args:
            config: 编译配置
            
        Returns:
            编译后的图
        """
        engine = self.get_engine()
        if engine is None:
            raise RuntimeError("无法创建图引擎")
        
        return await engine.compile(config or {})
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行图
        
        Args:
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        engine = self.get_engine()
        if engine is None:
            raise RuntimeError("无法创建图引擎")
        
        return await engine.execute(input_data)