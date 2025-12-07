"""统一的节点注册表

合并了原有的两个节点注册表实现，提供统一的节点注册和管理功能。
"""

from typing import Dict, Type, Optional, List, Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.workflow.graph import INode

from src.interfaces.workflow.graph import INodeRegistry


class NodeRegistry(INodeRegistry):
    """统一的节点注册表实现"""
    
    def __init__(self) -> None:
        """初始化节点注册表"""
        self._node_classes: Dict[str, Type['INode']] = {}
        self._node_instances: Dict[str, 'INode'] = {}
    
    # 实现 INodeRegistry 接口
    def register(self, node_type: str, node_class: Type['INode']) -> None:
        """注册节点类型（实现接口方法）"""
        if node_type in self._node_classes:
            raise ValueError(f"节点类型 '{node_type}' 已存在")
        self._node_classes[node_type] = node_class
    
    def get(self, node_type: str) -> Optional[Type['INode']]:
        """获取节点类型（实现接口方法）"""
        return self._node_classes.get(node_type)
    
    def list_types(self) -> List[str]:
        """列出所有注册的节点类型（实现接口方法）"""
        return list(self._node_classes.keys())
    
    # 扩展功能
    def register_node(self, node_class: Type['INode']) -> None:
        """注册节点类型（兼容旧方法）
        
        Args:
            node_class: 节点类
        """
        # 获取节点类型
        node_type = getattr(node_class, '_decorator_node_type', None)
        if not node_type:
            # 如果没有装饰器设置的节点类型，尝试从类名推断
            node_type = node_class.__name__.lower().replace('node', '_node')
        
        self.register(node_type, node_class)
    
    def register_node_instance(self, node: 'INode') -> None:
        """注册节点实例
        
        Args:
            node: 节点实例
        """
        node_id = node.node_id
        if node_id in self._node_instances:
            raise ValueError(f"节点实例 '{node_id}' 已存在")
        self._node_instances[node_id] = node
    
    def get_node_class(self, node_type: str) -> Type['INode']:
        """获取节点类型
        
        Args:
            node_type: 节点类型
            
        Returns:
            Type[INode]: 节点类
            
        Raises:
            ValueError: 节点类型不存在
        """
        if node_type not in self._node_classes:
            raise ValueError(f"未知的节点类型: {node_type}")
        return self._node_classes[node_type]
    
    def get_node_instance(self, node_type: str) -> 'INode':
        """获取节点实例
        
        Args:
            node_type: 节点类型
            
        Returns:
            INode: 节点实例
            
        Raises:
            ValueError: 节点类型不存在
        """
        # 优先返回已注册的实例
        if node_type in self._node_instances:
            return self._node_instances[node_type]
        
        # 如果没有实例，创建新实例
        node_class = self.get_node_class(node_type)
        try:
            return node_class()  # type: ignore
        except TypeError as e:
            if "missing" in str(e) and "required positional argument" in str(e):
                raise ValueError(f"节点类型 '{node_type}' 需要依赖项，无法直接实例化。请使用 register_node_instance 注册预配置的实例。")
            else:
                raise
    
    def list_nodes(self) -> List[str]:
        """列出所有注册的节点类型
        
        Returns:
            List[str]: 节点类型列表
        """
        # 合并节点类和节点实例的类型
        all_nodes = set(self._node_classes.keys())
        all_nodes.update(self._node_instances.keys())
        return list(all_nodes)
    
    def get_node_schema(self, node_type: str) -> Dict[str, Any]:
        """获取节点配置Schema
        
        Args:
            node_type: 节点类型
            
        Returns:
            Dict: 配置Schema
            
        Raises:
            ValueError: 节点类型不存在
        """
        node = self.get_node_instance(node_type)
        return node.get_config_schema()
    
    def validate_node_config(self, node_type: str, config: Dict[str, Any]) -> List[str]:
        """验证节点配置
        
        Args:
            node_type: 节点类型
            config: 节点配置
            
        Returns:
            List[str]: 验证错误列表
        """
        try:
            node = self.get_node_instance(node_type)
            return node.validate_config(config)
        except ValueError as e:
            return [str(e)]
    
    def clear(self) -> None:
        """清除所有注册的节点"""
        self._node_classes.clear()
        self._node_instances.clear()


# 装饰器版本，用于自动注册节点
def node(node_type: str) -> Callable:
    """节点注册装饰器

    Args:
        node_type: 节点类型

    Returns:
        Callable: 装饰器函数
    """
    def decorator(node_class: Type['INode']) -> Type['INode']:
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
        
        # 注意：基础设施层不依赖服务层，避免使用logger
        # 这里保留装饰器功能但不再自动注册到全局注册表
        print(f"Warning: 节点类型 {node_type} 装饰器已使用，但基础设施层不提供全局注册表。请使用依赖注入方式注册。")
        
        return WrappedNode
    
    return decorator