"""Node registry for the graph sub-module.

This module provides node registration and discovery functionality.
"""

from typing import Dict, Type, Optional, List
from .interfaces import INode, INodeRegistry


class NodeRegistry(INodeRegistry):
    """节点注册表实现"""
    
    def __init__(self) -> None:
        """初始化节点注册表"""
        self._node_classes: Dict[str, Type[INode]] = {}
        self._node_instances: Dict[str, INode] = {}
    
    def register_node(self, node_class: Type[INode]) -> None:
        """注册节点类型
        
        Args:
            node_class: 节点类
        """
        # 获取节点类型
        node_type = getattr(node_class, '_decorator_node_type', None)
        if not node_type:
            # 如果没有装饰器设置的节点类型，尝试从类名推断
            node_type = node_class.__name__.lower().replace('node', '_node')
        
        self._node_classes[node_type] = node_class
    
    def register_node_instance(self, node: INode) -> None:
        """注册节点实例
        
        Args:
            node: 节点实例
        """
        node_id = node.node_id
        self._node_instances[node_id] = node
    
    def get_node_class(self, node_type: str) -> Type[INode]:
        """获取节点类型
        
        Args:
            node_type: 节点类型
            
        Returns:
            Type[INode]: 节点类
        """
        if node_type not in self._node_classes:
            raise ValueError(f"Unknown node type: {node_type}")
        return self._node_classes[node_type]
    
    def get_node_instance(self, node_type: str) -> INode:
        """获取节点实例
        
        Args:
            node_type: 节点类型
            
        Returns:
            INode: 节点实例
        """
        node_class = self.get_node_class(node_type)
        return node_class()
    
    def list_nodes(self) -> List[str]:
        """列出所有注册的节点类型
        
        Returns:
            List[str]: 节点类型列表
        """
        return list(self._node_classes.keys())
    
    def get_node_schema(self, node_type: str) -> Dict:
        """获取节点配置Schema
        
        Args:
            node_type: 节点类型
            
        Returns:
            Dict: 配置Schema
        """
        node_class = self.get_node_class(node_type)
        # 创建一个临时实例来获取配置schema
        temp_instance = node_class()
        return temp_instance.get_config_schema()
    
    def validate_node_config(self, node_type: str, config: Dict) -> List[str]:
        """验证节点配置
        
        Args:
            node_type: 节点类型
            config: 节点配置
            
        Returns:
            List[str]: 验证错误列表
        """
        node_class = self.get_node_class(node_type)
        # 创建一个临时实例来验证配置
        temp_instance = node_class()
        return temp_instance.validate_config(config)


# 全局节点注册表实例
_global_registry = NodeRegistry()


def register_node(node_class: Type[INode]) -> None:
    """注册节点到全局注册表
    
    Args:
        node_class: 节点类
    """
    _global_registry.register_node(node_class)


def get_global_registry() -> NodeRegistry:
    """获取全局节点注册表
    
    Returns:
        NodeRegistry: 全局节点注册表
    """
    return _global_registry


def get_node_class(node_type: str) -> Type[INode]:
    """获取节点类型
    
    Args:
        node_type: 节点类型
        
    Returns:
        Type[INode]: 节点类
    """
    return _global_registry.get_node_class(node_type)


def get_node_instance(node_type: str) -> INode:
    """获取节点实例
    
    Args:
        node_type: 节点类型
        
    Returns:
        INode: 节点实例
    """
    return _global_registry.get_node_instance(node_type)


def list_node_types() -> List[str]:
    """列出所有节点类型
    
    Returns:
        List[str]: 节点类型列表
    """
    return _global_registry.list_nodes()