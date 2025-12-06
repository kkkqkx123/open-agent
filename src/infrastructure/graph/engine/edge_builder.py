"""边构建器实现

负责构建和管理图边。
"""

from typing import Any, Callable, Dict, List, Optional

__all__ = ("EdgeBuilder",)


class EdgeBuilder:
    """边构建器，负责构建和管理图边。"""
    
    def __init__(self):
        """初始化边构建器。"""
        self.edges: Dict[str, Dict[str, Any]] = {}
    
    def build_edge(
        self,
        edge_id: str,
        start: str,
        end: str,
        edge_type: str = "simple",
        **kwargs
    ) -> Dict[str, Any]:
        """构建边。
        
        Args:
            edge_id: 边ID
            start: 起始节点
            end: 目标节点
            edge_type: 边类型
            **kwargs: 额外参数
            
        Returns:
            边配置字典
        """
        edge_config = {
            "id": edge_id,
            "start": start,
            "end": end,
            "type": edge_type,
            "config": kwargs.get("config", {}),
            "metadata": kwargs.get("metadata", {})
        }
        
        # 处理条件边的特殊参数
        if edge_type == "conditional":
            edge_config["condition"] = kwargs.get("condition")
            edge_config["path_map"] = kwargs.get("path_map", {})
        
        self.edges[edge_id] = edge_config
        return edge_config
    
    def get_edge(self, edge_id: str) -> Optional[Dict[str, Any]]:
        """获取边配置。
        
        Args:
            edge_id: 边ID
            
        Returns:
            边配置字典（如果存在）
        """
        return self.edges.get(edge_id)
    
    def list_edges(self) -> Dict[str, Dict[str, Any]]:
        """列出所有边。
        
        Returns:
            边配置字典
        """
        return self.edges.copy()
    
    def remove_edge(self, edge_id: str) -> bool:
        """移除边。
        
        Args:
            edge_id: 边ID
            
        Returns:
            是否成功移除
        """
        if edge_id in self.edges:
            del self.edges[edge_id]
            return True
        return False
    
    def validate_edge(self, edge_id: str) -> List[str]:
        """验证边配置。
        
        Args:
            edge_id: 边ID
            
        Returns:
            错误列表
        """
        errors = []
        
        if edge_id not in self.edges:
            errors.append(f"边 '{edge_id}' 不存在")
            return errors
        
        edge = self.edges[edge_id]
        
        if not edge.get("start"):
            errors.append(f"边 '{edge_id}' 缺少起始节点")
        
        if not edge.get("end"):
            errors.append(f"边 '{edge_id}' 缺少目标节点")
        
        if not edge.get("type"):
            errors.append(f"边 '{edge_id}' 缺少类型")
        
        # 验证条件边的特殊要求
        if edge.get("type") == "conditional":
            if not edge.get("condition"):
                errors.append(f"条件边 '{edge_id}' 缺少条件函数")
        
        return errors
    
    def get_edges_from_node(self, node_id: str) -> List[Dict[str, Any]]:
        """获取从指定节点出发的所有边。
        
        Args:
            node_id: 节点ID
            
        Returns:
            边列表
        """
        return [
            edge for edge in self.edges.values()
            if edge.get("start") == node_id
        ]
    
    def get_edges_to_node(self, node_id: str) -> List[Dict[str, Any]]:
        """获取到达指定节点的所有边。
        
        Args:
            node_id: 节点ID
            
        Returns:
            边列表
        """
        return [
            edge for edge in self.edges.values()
            if edge.get("end") == node_id
        ]