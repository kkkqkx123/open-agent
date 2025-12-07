"""边注册表

提供边的注册和管理功能。
"""

from typing import Dict, Type, Optional, List, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.workflow.graph import IEdge


class EdgeRegistry:
    """边注册表实现"""
    
    def __init__(self) -> None:
        """初始化边注册表"""
        self._edge_classes: Dict[str, Type['IEdge']] = {}
        self._edge_instances: Dict[str, 'IEdge'] = {}
    
    def register_edge(self, edge_type: str, edge_class: Type['IEdge']) -> None:
        """注册边类型
        
        Args:
            edge_type: 边类型
            edge_class: 边类
            
        Raises:
            ValueError: 边类型已存在
        """
        if edge_type in self._edge_classes:
            raise ValueError(f"边类型 '{edge_type}' 已存在")
        self._edge_classes[edge_type] = edge_class
    
    def register_edge_instance(self, edge: 'IEdge') -> None:
        """注册边实例
        
        Args:
            edge: 边实例
            
        Raises:
            ValueError: 边实例已存在
        """
        edge_id = edge.edge_id
        if edge_id in self._edge_instances:
            raise ValueError(f"边实例 '{edge_id}' 已存在")
        self._edge_instances[edge_id] = edge
    
    def get_edge_class(self, edge_type: str) -> Type['IEdge']:
        """获取边类型
        
        Args:
            edge_type: 边类型
            
        Returns:
            Type[IEdge]: 边类
            
        Raises:
            ValueError: 边类型不存在
        """
        if edge_type not in self._edge_classes:
            raise ValueError(f"未知的边类型: {edge_type}")
        return self._edge_classes[edge_type]
    
    def get_edge_instance(self, edge_type: str) -> 'IEdge':
        """获取边实例
        
        Args:
            edge_type: 边类型
            
        Returns:
            IEdge: 边实例
            
        Raises:
            ValueError: 边类型不存在
        """
        # 优先返回已注册的实例
        if edge_type in self._edge_instances:
            return self._edge_instances[edge_type]
        
        # 如果没有实例，创建新实例
        edge_class = self.get_edge_class(edge_type)
        try:
            return edge_class()  # type: ignore
        except TypeError as e:
            if "missing" in str(e) and "required positional argument" in str(e):
                raise ValueError(f"边类型 '{edge_type}' 需要依赖项，无法直接实例化。请使用 register_edge_instance 注册预配置的实例。")
            else:
                raise
    
    def list_edge_types(self) -> List[str]:
        """列出所有注册的边类型
        
        Returns:
            List[str]: 边类型列表
        """
        # 合并边类和边实例的类型
        all_edges = set(self._edge_classes.keys())
        all_edges.update(self._edge_instances.keys())
        return list(all_edges)
    
    def get_edge_schema(self, edge_type: str) -> Dict[str, Any]:
        """获取边配置Schema
        
        Args:
            edge_type: 边类型
            
        Returns:
            Dict: 配置Schema
            
        Raises:
            ValueError: 边类型不存在
        """
        edge = self.get_edge_instance(edge_type)
        if hasattr(edge, 'get_config_schema'):
            return edge.get_config_schema()
        return {}
    
    def validate_edge_config(self, edge_type: str, config: Dict[str, Any]) -> List[str]:
        """验证边配置
        
        Args:
            edge_type: 边类型
            config: 边配置
            
        Returns:
            List[str]: 验证错误列表
        """
        try:
            edge = self.get_edge_instance(edge_type)
            if hasattr(edge, 'validate_config'):
                return edge.validate_config(config)
            return []
        except ValueError as e:
            return [str(e)]
    
    def clear(self) -> None:
        """清除所有注册的边"""
        self._edge_classes.clear()
        self._edge_instances.clear()


# 装饰器版本，用于自动注册边
def edge(edge_type: str) -> Callable:
    """边注册装饰器

    Args:
        edge_type: 边类型

    Returns:
        装饰器函数
    """
    def decorator(edge_class: Type['IEdge']) -> Type['IEdge']:
        # 为类添加边类型属性
        setattr(edge_class, '_decorator_edge_type', edge_type)
        
        # 注意：基础设施层不依赖服务层，避免使用logger
        # 这里保留装饰器功能但不再自动注册到全局注册表
        print(f"Warning: 边类型 {edge_type} 装饰器已使用，但基础设施层不提供全局注册表。请使用依赖注入方式注册。")
        
        return edge_class
    
    return decorator