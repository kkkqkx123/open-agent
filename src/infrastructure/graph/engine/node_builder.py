"""节点构建器实现

负责构建和管理图节点。
"""

from typing import Any, Callable, Dict, List, Optional

__all__ = ("NodeBuilder",)


class NodeBuilder:
    """节点构建器，负责构建和管理图节点。"""
    
    def __init__(self):
        """初始化节点构建器。"""
        self.nodes: Dict[str, Dict[str, Any]] = {}
    
    def build_node(
        self,
        name: str,
        func: Callable,
        **kwargs
    ) -> Dict[str, Any]:
        """构建节点。
        
        Args:
            name: 节点名称
            func: 节点函数
            **kwargs: 额外参数
            
        Returns:
            节点配置字典
        """
        node_config = {
            "name": name,
            "func": func,
            "type": kwargs.get("type", "simple"),
            "config": kwargs.get("config", {}),
            "metadata": kwargs.get("metadata", {})
        }
        
        self.nodes[name] = node_config
        return node_config
    
    def get_node(self, name: str) -> Optional[Dict[str, Any]]:
        """获取节点配置。
        
        Args:
            name: 节点名称
            
        Returns:
            节点配置字典（如果存在）
        """
        return self.nodes.get(name)
    
    def list_nodes(self) -> Dict[str, Dict[str, Any]]:
        """列出所有节点。
        
        Returns:
            节点配置字典
        """
        return self.nodes.copy()
    
    def remove_node(self, name: str) -> bool:
        """移除节点。
        
        Args:
            name: 节点名称
            
        Returns:
            是否成功移除
        """
        if name in self.nodes:
            del self.nodes[name]
            return True
        return False
    
    def validate_node(self, name: str) -> List[str]:
        """验证节点配置。
        
        Args:
            name: 节点名称
            
        Returns:
            错误列表
        """
        errors = []
        
        if name not in self.nodes:
            errors.append(f"节点 '{name}' 不存在")
            return errors
        
        node = self.nodes[name]
        
        if not node.get("func"):
            errors.append(f"节点 '{name}' 缺少函数")
        
        if not node.get("type"):
            errors.append(f"节点 '{name}' 缺少类型")
        
        return errors