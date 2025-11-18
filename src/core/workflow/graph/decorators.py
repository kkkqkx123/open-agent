"""Node decorators for the graph sub-module.

This module provides decorators for node registration and other
node-related functionality.
"""

from typing import Callable, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from .interfaces import INode
    from .nodes.base import BaseNode


def node(node_type: str) -> Callable:
    """节点注册装饰器
    
    Args:
        node_type: 节点类型
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(node_class: Type) -> Type:
        # 创建一个新的类，覆盖 node_type 属性
        class WrappedNode(node_class):  # type: ignore
            @property
            def node_type(self) -> str:
                return node_type
            
            # 传递所有构造函数参数到原始类
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
        
        # 保持原始类的名称和文档
        WrappedNode.__name__ = node_class.__name__
        WrappedNode.__qualname__ = node_class.__qualname__
        if hasattr(node_class, '__doc__'):
            WrappedNode.__doc__ = node_class.__doc__
        
        # 为包装类添加 node_type 属性，以便注册系统能够获取
        setattr(WrappedNode, '_decorator_node_type', node_type)
        
        # 注册到全局注册表
        from .registry import register_node
        register_node(WrappedNode)
        
        return WrappedNode
    
    return decorator