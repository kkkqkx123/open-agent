"""全局注册表

提供统一的注册表管理和访问接口。
"""

from typing import Optional
from .node_registry import NodeRegistry
from .edge_registry import EdgeRegistry
from .function_registry import FunctionRegistry


class GlobalRegistry:
    """全局注册表，管理所有子注册表"""
    
    def __init__(self) -> None:
        """初始化全局注册表"""
        self._node_registry: Optional[NodeRegistry] = None
        self._edge_registry: Optional[EdgeRegistry] = None
        self._function_registry: Optional[FunctionRegistry] = None
    
    @property
    def node_registry(self) -> NodeRegistry:
        """获取节点注册表"""
        if self._node_registry is None:
            self._node_registry = NodeRegistry()
        return self._node_registry
    
    @property
    def edge_registry(self) -> EdgeRegistry:
        """获取边注册表"""
        if self._edge_registry is None:
            self._edge_registry = EdgeRegistry()
        return self._edge_registry
    
    @property
    def function_registry(self) -> FunctionRegistry:
        """获取函数注册表"""
        if self._function_registry is None:
            self._function_registry = FunctionRegistry()
        return self._function_registry
    
    def clear_all(self) -> None:
        """清除所有注册表"""
        if self._node_registry is not None:
            self._node_registry.clear()
        if self._edge_registry is not None:
            self._edge_registry.clear()
        if self._function_registry is not None:
            self._function_registry.clear()
    
    def get_registry_stats(self) -> dict:
        """获取注册表统计信息
        
        Returns:
            dict: 统计信息
        """
        return {
            "node_types": len(self.node_registry.list_types()),
            "edge_types": len(self.edge_registry.list_edge_types()),
            "node_functions": len(self.function_registry.list_node_functions()),
            "route_functions": len(self.function_registry.list_route_functions())
        }


# 全局注册表实例
_global_registry: Optional[GlobalRegistry] = None


def get_global_registry() -> GlobalRegistry:
    """获取全局注册表实例
    
    Returns:
        GlobalRegistry: 全局注册表
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = GlobalRegistry()
    return _global_registry


def reset_global_registry() -> None:
    """重置全局注册表"""
    global _global_registry
    _global_registry = None


# 便捷函数
def register_node(node_type: str, node_class):
    """注册节点类型到全局注册表
    
    Args:
        node_type: 节点类型
        node_class: 节点类
    """
    get_global_registry().node_registry.register(node_type, node_class)


def register_edge(edge_type: str, edge_class):
    """注册边类型到全局注册表
    
    Args:
        edge_type: 边类型
        edge_class: 边类
    """
    get_global_registry().edge_registry.register_edge(edge_type, edge_class)


def register_node_function(name: str, function):
    """注册节点函数到全局注册表
    
    Args:
        name: 函数名称
        function: 函数对象
    """
    get_global_registry().function_registry.register_node_function(name, function)


def register_route_function(name: str, function):
    """注册路由函数到全局注册表
    
    Args:
        name: 函数名称
        function: 函数对象
    """
    get_global_registry().function_registry.register_route_function(name, function)


def get_node_class(node_type: str):
    """从全局注册表获取节点类
    
    Args:
        node_type: 节点类型
        
    Returns:
        节点类
    """
    return get_global_registry().node_registry.get_node_class(node_type)


def get_edge_class(edge_type: str):
    """从全局注册表获取边类
    
    Args:
        edge_type: 边类型
        
    Returns:
        边类
    """
    return get_global_registry().edge_registry.get_edge_class(edge_type)


def get_node_function(name: str):
    """从全局注册表获取节点函数
    
    Args:
        name: 函数名称
        
    Returns:
        函数对象
    """
    return get_global_registry().function_registry.get_node_function(name)


def get_route_function(name: str):
    """从全局注册表获取路由函数
    
    Args:
        name: 函数名称
        
    Returns:
        函数对象
    """
    return get_global_registry().function_registry.get_route_function(name)