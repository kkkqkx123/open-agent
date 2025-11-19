"""简单边实现，用于工作流模板

提供一个简单的边实现，用于在工作流模板中创建边。
"""

from typing import Dict, Any, List, Optional
from .interfaces import IEdge
from src.state.interfaces import IState


class SimpleEdge(IEdge):
    """简单边实现"""
    
    def __init__(self, edge_id: str, from_node: str, to_node: str,
                 edge_type: str = "simple", condition: Optional[str] = None):
        """初始化边
        
        Args:
            edge_id: 边ID
            from_node: 起始节点ID
            to_node: 目标节点ID
            edge_type: 边类型
            condition: 条件表达式
        """
        self._edge_id = edge_id
        self._from_node = from_node
        self._to_node = to_node
        self._edge_type = edge_type
        self.condition = condition or ""
    
    @property
    def edge_id(self) -> str:
        """边ID"""
        return self._edge_id
    
    @property
    def from_node(self) -> str:
        """起始节点ID"""
        return self._from_node
    
    @property
    def to_node(self) -> str:
        """目标节点ID"""
        return self._to_node
    
    @property
    def edge_type(self) -> str:
        """边类型"""
        return self._edge_type
    
    def can_traverse(self, state: IState, config: Dict[str, Any]) -> bool:
        """判断是否可以遍历此边"""
        # 简单实现：总是可以遍历
        return True
    
    def get_next_nodes(self, state: IState, config: Dict[str, Any]) -> List[str]:
        """获取下一个节点列表"""
        # 简单实现：返回目标节点
        return [self._to_node]