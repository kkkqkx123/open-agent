"""简单边实现

表示节点之间的直接连接，无条件判断。
"""

from typing import Dict, Any, List, TYPE_CHECKING

from src.infrastructure.graph.edges.base import BaseEdge

if TYPE_CHECKING:
    from src.interfaces.state import IState


class SimpleEdge(BaseEdge):
    """简单边实现
    
    表示从一个节点到另一个节点的直接连接，没有条件判断。
    """
    
    def __init__(self, edge_id: str = "", from_node: str = "", to_node: str = "", 
                 description: str = ""):
        """初始化简单边
        
        Args:
            edge_id: 边ID
            from_node: 起始节点ID
            to_node: 目标节点ID
            description: 边描述
        """
        super().__init__(edge_id, from_node, to_node)
        self.description = description
    
    @property
    def edge_type(self) -> str:
        """边类型"""
        return "simple"
    
    def can_traverse(self, state: 'IState') -> bool:
        """判断是否可以遍历此边
        
        Args:
            state: 当前工作流状态
            
        Returns:
            bool: 总是返回True，简单边无条件限制
        """
        return True
    
    def can_traverse_with_config(self, state: 'IState', config: Dict[str, Any]) -> bool:
        """判断是否可以遍历此边（带配置）
        
        Args:
            state: 当前工作流状态
            config: 边配置
            
        Returns:
            bool: 总是返回True，简单边无条件限制
        """
        return True
    
    def get_next_nodes(self, state: 'IState', config: Dict[str, Any]) -> List[str]:
        """获取下一个节点列表
        
        Args:
            state: 当前工作流状态
            config: 边配置
            
        Returns:
            List[str]: 返回目标节点
        """
        return [self._to_node]
    
    def validate(self) -> List[str]:
        """验证边配置
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = super().validate()
        
        # 检查是否自循环
        if self._from_node == self._to_node:
            errors.append("不允许节点自循环")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 边的字典表示
        """
        return {
            "edge_id": self._edge_id,
            "edge_type": self.edge_type,
            "from_node": self._from_node,
            "to_node": self._to_node,
            "description": self.description
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"SimpleEdge({self._from_node} -> {self._to_node})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        desc = f" ({self.description})" if self.description else ""
        return f"SimpleEdge(edge_id='{self._edge_id}', from_node='{self._from_node}', to_node='{self._to_node}'{desc})"