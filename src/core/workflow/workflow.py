"""工作流数据模型 - 纯数据容器

基于新架构原则，Workflow 仅作为数据容器，实现 IWorkflow 接口，
不包含任何执行逻辑、验证逻辑或其他业务逻辑。
"""

from typing import Dict, Any, Optional
from datetime import datetime

from src.core.workflow.graph_entities import Graph
from src.interfaces.workflow.core import IWorkflow


class Workflow(IWorkflow):
    """工作流数据模型 - 纯数据容器
    
    只包含数据和基本访问器，不包含任何业务逻辑。
    所有执行、验证、管理等功能都由专门的服务类负责。
    """
    
    def __init__(
        self,
        graph: Graph,
        compiled_graph: Optional[Any] = None,
        config: Optional[Any] = None
    ):
        """初始化工作流数据模型
        
        Args:
            graph: 工作流图实体
            compiled_graph: 编译后的图
            config: 图配置
        """
        self._graph = graph
        self._compiled_graph = compiled_graph
        self._config = config or graph  # 如果没有提供config，使用graph作为config
        self._created_at = datetime.now()
        self._metadata = {}  # 内部元数据存储
    
    # 基本属性访问器（IWorkflow 接口要求）
    @property
    def workflow_id(self) -> str:
        """工作流ID"""
        return self._graph.graph_id
    
    @property
    def name(self) -> str:
        """工作流名称"""
        return self._graph.name
    
    @property
    def description(self) -> Optional[str]:
        """工作流描述"""
        return self._graph.description
    
    @property
    def version(self) -> str:
        """工作流版本"""
        return self._graph.version
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """工作流元数据"""
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]) -> None:
        """设置工作流元数据"""
        self._metadata = value
    
    @property
    def entry_point(self) -> Optional[str]:
        """入口点"""
        return self._graph.entry_point
    
    @property
    def compiled_graph(self) -> Optional[Any]:
        """编译后的图"""
        return self._compiled_graph
    
    @property
    def graph(self) -> Graph:
        """工作流图"""
        return self._graph
    
    @property
    def config(self) -> Any:
        """工作流配置"""
        return self._config
    
    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at
    
    # 数据访问方法（IWorkflow接口要求）
    def get_node(self, node_id: str) -> Optional[Any]:
        """获取节点"""
        return self._graph.get_node(node_id)
    
    def get_edge(self, edge_id: str) -> Optional[Any]:
        """获取边"""
        # 尝试通过索引获取边
        try:
            index = int(edge_id.split('_')[-1])
            if 0 <= index < len(self._graph.edges):
                return self._graph.edges[index]
        except (ValueError, IndexError):
            pass
        
        # 尝试通过边属性匹配
        for edge in self._graph.edges:
            edge_key = f"{edge.from_node_id}-{edge.to_node_id}"
            if edge_key == edge_id:
                return edge
        return None
    
    def get_nodes(self) -> Dict[str, Any]:
        """获取所有节点"""
        return self._graph.nodes
    
    def get_edges(self) -> Dict[str, Any]:
        """获取所有边"""
        return {f"edge_{i}": edge for i, edge in enumerate(self._graph.edges)}
    
    # 配置操作
    def set_entry_point(self, entry_point: str) -> None:
        """设置入口点"""
        self._graph.entry_point = entry_point
    
    def set_graph(self, graph: Any) -> None:
        """设置编译后的图"""
        self._compiled_graph = graph
    
    def add_node(self, node_config: Any) -> None:
        """添加节点
        
        Args:
            node_config: 节点配置
        """
        if hasattr(node_config, 'node_id'):
            self._graph.add_node(node_config)
    
    def add_edge(self, edge_config: Any) -> None:
        """添加边
        
        Args:
            edge_config: 边配置
        """
        self._graph.edges.append(edge_config)
    
    def __repr__(self) -> str:
        """字符串表示"""
        node_count = len(self.get_nodes())
        edge_count = len(self.get_edges())
        return f"Workflow(name={self.name}, nodes={node_count}, edges={edge_count})"
    
    def __str__(self) -> str:
        """字符串表示"""
        return self.__repr__()