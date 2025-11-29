"""工作流数据模型 - 纯数据容器

基于新架构原则，Workflow 仅作为数据容器，实现 IWorkflow 接口，
不包含任何执行逻辑、验证逻辑或其他业务逻辑。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.workflow.config.config import GraphConfig
from src.interfaces.workflow.core import IWorkflow


class Workflow(IWorkflow):
    """工作流数据模型 - 纯数据容器
    
    只包含数据和基本访问器，不包含任何业务逻辑。
    所有执行、验证、管理等功能都由专门的服务类负责。
    """
    
    def __init__(
        self,
        config: GraphConfig,
        compiled_graph: Optional[Any] = None
    ):
        """初始化工作流数据模型
        
        Args:
            config: 工作流配置
            compiled_graph: 编译后的图
        """
        self._config = config
        self._compiled_graph = compiled_graph
        self._created_at = datetime.now()
        self._metadata = {}  # 内部元数据存储
    
    # 基本属性访问器（IWorkflow 接口要求）
    @property
    def workflow_id(self) -> str:
        """工作流ID"""
        return self._config.name
    
    @property
    def name(self) -> str:
        """工作流名称"""
        return self._config.name
    
    @property
    def description(self) -> Optional[str]:
        """工作流描述"""
        return self._config.description
    
    @property
    def version(self) -> str:
        """工作流版本"""
        return getattr(self._config, 'version', '1.0.0')
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """工作流元数据"""
        return getattr(self._config, 'metadata', {}) or self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]) -> None:
        """设置工作流元数据"""
        self._metadata = value
        if hasattr(self._config, 'metadata'):
            setattr(self._config, 'metadata', value)
    
    @property
    def entry_point(self) -> Optional[str]:
        """入口点"""
        return self._config.entry_point
    
    @property
    def graph(self) -> Optional[Any]:
        """编译后的图"""
        return self._compiled_graph
    
    @property
    def compiled_graph(self) -> Optional[Any]:
        """编译后的图"""
        return self._compiled_graph
    
    @property
    def config(self) -> GraphConfig:
        """工作流配置"""
        return self._config
    
    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at
    
    # 节点和边访问器（IWorkflow接口要求）
    @property
    def _nodes(self) -> Dict[str, Any]:
        """工作流节点字典（IWorkflow接口要求）"""
        return self._config.nodes if hasattr(self._config, 'nodes') else {}
    
    @property
    def _edges(self) -> Dict[str, Any]:
        """工作流边字典（IWorkflow接口要求）"""
        if hasattr(self._config, 'edges') and self._config.edges:
            # 将List转换为Dict以满足接口要求
            return {f"edge_{i}": edge for i, edge in enumerate(self._config.edges)}
        return {}
    
    # 便捷访问器
    @property
    def nodes(self) -> Dict[str, Any]:
        """节点字典"""
        return self._nodes
    
    @property
    def edges(self) -> List[Any]:
        """边列表"""
        return self._config.edges if hasattr(self._config, 'edges') else []
    
    # 数据操作方法
    def add_node(self, node: Any) -> None:
        """添加节点（仅数据操作）"""
        if hasattr(self._config, 'nodes') and node:
            node_id = getattr(node, 'id', getattr(node, 'name', None))
            if node_id:
                self._config.nodes[node_id] = node
    
    def add_edge(self, edge: Any) -> None:
        """添加边（仅数据操作）"""
        if hasattr(self._config, 'edges') and edge:
            self._config.edges.append(edge)
    
    def get_node(self, node_id: str) -> Optional[Any]:
        """获取节点"""
        return self.nodes.get(node_id)
    
    def get_edge(self, edge_id: str) -> Optional[Any]:
        """获取边"""
        edges_dict = {}
        for i, edge in enumerate(self.edges):
            edge_key = f"{getattr(edge, 'from_node', '')}-{getattr(edge, 'to_node', '')}-{i}"
            edges_dict[edge_key] = edge
        return edges_dict.get(edge_id)
    
    def add_step(self, step: Any) -> None:
        """添加步骤（委托给add_node）"""
        self.add_node(step)
    
    def add_transition(self, transition: Any) -> None:
        """添加转换（委托给add_edge）"""
        self.add_edge(transition)
    
    def get_step(self, step_id: str) -> Optional[Any]:
        """获取步骤（委托给get_node）"""
        return self.get_node(step_id)
    
    # 配置操作
    def set_entry_point(self, entry_point: str) -> None:
        """设置入口点"""
        self._config.entry_point = entry_point
    
    def set_graph(self, graph: Any) -> None:
        """设置编译后的图"""
        self._compiled_graph = graph
    
    def get_config(self) -> GraphConfig:
        """获取工作流配置"""
        return self._config
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"Workflow(name={self.name}, nodes={len(self.nodes)}, edges={len(self.edges)})"
    
    def __str__(self) -> str:
        """字符串表示"""
        return self.__repr__()
    
    # IWorkflow接口要求的抽象方法实现
    def validate(self) -> List[str]:
        """验证工作流（IWorkflow接口要求）
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        if not self.workflow_id:
            errors.append("工作流ID不能为空")
        if not self._nodes:
            errors.append("工作流必须包含至少一个节点")
        return errors
    
    def execute(self, initial_state: Any, context: Any) -> Any:
        """执行工作流（IWorkflow接口要求）
        
        Args:
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            执行结果状态
            
        Raises:
            NotImplementedError: Workflow是纯数据模型，执行由WorkflowExecutor处理
        """
        raise NotImplementedError("Workflow是纯数据模型，执行逻辑由WorkflowExecutor处理")
    
    async def execute_async(self, initial_state: Any, context: Any) -> Any:
        """异步执行工作流（IWorkflow接口要求）
        
        Args:
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            执行结果状态
            
        Raises:
            NotImplementedError: Workflow是纯数据模型，执行由WorkflowExecutor处理
        """
        raise NotImplementedError("Workflow是纯数据模型，执行逻辑由WorkflowExecutor处理")