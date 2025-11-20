"""边基类

提供边的基础实现。
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from ..interfaces import IEdge
from src.interfaces.state_core import IState

class BaseEdge(IEdge):
    """边基类"""

    def __init__(self, edge_id: str, from_node: str, to_node: str):
        """初始化边

        Args:
            edge_id: 边ID
            from_node: 起始节点ID
            to_node: 目标节点ID
        """
        self._edge_id = edge_id
        self._from_node = from_node
        self._to_node = to_node

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

    def can_traverse(self, state: 'IState', config: Dict[str, Any]) -> bool:
        """判断是否可以遍历此边

        Args:
            state: 当前工作流状态
            config: 边配置

        Returns:
            bool: 是否可以遍历
        """
        # 默认实现：总是可以遍历
        return True

    def get_next_nodes(self, state: 'IState', config: Dict[str, Any]) -> List[str]:
        """获取下一个节点列表

        Args:
            state: 当前工作流状态
            config: 边配置

        Returns:
            List[str]: 下一个节点ID列表
        """
        # 默认实现：返回目标节点
        return [self._to_node]