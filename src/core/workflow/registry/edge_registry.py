"""边注册器

提供边的类型注册、实例管理和配置验证功能。
"""

from typing import Dict, Type, List, Optional, Any, Union
from abc import ABC, abstractmethod

from src.interfaces.workflow.graph import IEdge
from src.interfaces.workflow.registry import IEdgeRegistry
from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


class EdgeRegistry(IEdgeRegistry):
    """边注册器实现
    
    核心层的边注册器，提供边的类型注册、实例管理和配置验证功能。
    支持边类型的动态注册和实例化，以及配置验证。
    
    特点：
    - 支持边类型注册和查询
    - 支持边实例管理
    - 提供配置验证功能
    - 支持边类型元数据管理
    - 提供边类型统计信息
    """
    
    def __init__(self) -> None:
        """初始化边注册器"""
        self._edge_classes: Dict[str, Type[IEdge]] = {}
        self._edge_instances: Dict[str, IEdge] = {}
        self._edge_metadata: Dict[str, Dict[str, Any]] = {}
        
        logger.debug("初始化边注册器")
    
    def register_edge(self, edge_type: str, edge_class: Type[IEdge]) -> None:
        """注册边类型
        
        Args:
            edge_type: 边类型
            edge_class: 边类
            
        Raises:
            ValueError: 边类型已存在或边类无效
        """
        if edge_type in self._edge_classes:
            raise ValueError(f"边类型 '{edge_type}' 已存在")
        
        if not issubclass(edge_class, IEdge):
            raise ValueError(f"边类必须实现 IEdge 接口: {edge_class}")
        
        self._edge_classes[edge_type] = edge_class
        logger.debug(f"注册边类型: {edge_type} -> {edge_class.__name__}")
    
    def register_edge_instance(self, edge: IEdge) -> None:
        """注册边实例
        
        Args:
            edge: 边实例
            
        Raises:
            ValueError: 边实例已存在或无效
        """
        edge_id = edge.edge_id
        if edge_id in self._edge_instances:
            raise ValueError(f"边实例 '{edge_id}' 已存在")
        
        if not isinstance(edge, IEdge):
            raise ValueError(f"边实例必须实现 IEdge 接口: {type(edge)}")
        
        # 验证实例
        validation_errors = edge.validate()
        if validation_errors:
            raise ValueError(f"边实例验证失败: {', '.join(validation_errors)}")
        
        self._edge_instances[edge_id] = edge
        logger.debug(f"注册边实例: {edge_id}")
    
    def get_edge_class(self, edge_type: str) -> Optional[Type[IEdge]]:
        """获取边类型
        
        Args:
            edge_type: 边类型
            
        Returns:
            Optional[Type[IEdge]]: 边类，如果不存在则返回None
        """
        return self._edge_classes.get(edge_type)
    
    def get_edge_instance(self, edge_id: str) -> Optional[IEdge]:
        """获取边实例
        
        Args:
            edge_id: 边ID
            
        Returns:
            Optional[IEdge]: 边实例，如果不存在则返回None
        """
        return self._edge_instances.get(edge_id)
    
    def create_edge(self, edge_type: str, **kwargs) -> IEdge:
        """创建边实例
        
        Args:
            edge_type: 边类型
            **kwargs: 边构造参数
            
        Returns:
            IEdge: 边实例
            
        Raises:
            ValueError: 边类型不存在或创建失败
        """
        edge_class = self.get_edge_class(edge_type)
        if edge_class is None:
            raise ValueError(f"边类型 '{edge_type}' 不存在")
        
        try:
            edge = edge_class(**kwargs)
            
            # 验证创建的实例
            validation_errors = edge.validate()
            if validation_errors:
                raise ValueError(f"创建的边实例验证失败: {', '.join(validation_errors)}")
            
            logger.debug(f"创建边实例: {edge.edge_id} (类型: {edge_type})")
            return edge
            
        except Exception as e:
            logger.error(f"创建边实例失败: {e}")
            raise ValueError(f"创建边实例失败: {e}")
    
    def list_edge_types(self) -> List[str]:
        """列出所有注册的边类型
        
        Returns:
            List[str]: 边类型列表
        """
        return list(self._edge_classes.keys())
    
    def list_edge_instances(self) -> List[str]:
        """列出所有注册的边实例
        
        Returns:
            List[str]: 边ID列表
        """
        return list(self._edge_instances.keys())
    
    def unregister_edge(self, edge_type: str) -> bool:
        """注销边类型
        
        Args:
            edge_type: 边类型
            
        Returns:
            bool: 是否成功注销
        """
        if edge_type in self._edge_classes:
            del self._edge_classes[edge_type]
            
            # 清除相关元数据
            if edge_type in self._edge_metadata:
                del self._edge_metadata[edge_type]
            
            logger.debug(f"注销边类型: {edge_type}")
            return True
        
        return False
    
    def unregister_edge_instance(self, edge_id: str) -> bool:
        """注销边实例
        
        Args:
            edge_id: 边ID
            
        Returns:
            bool: 是否成功注销
        """
        if edge_id in self._edge_instances:
            del self._edge_instances[edge_id]
            logger.debug(f"注销边实例: {edge_id}")
            return True
        
        return False
    
    def validate_edge_config(self, edge_type: str, config: Dict[str, Any]) -> List[str]:
        """验证边配置
        
        Args:
            edge_type: 边类型
            config: 边配置
            
        Returns:
            List[str]: 验证错误列表
        """
        edge_class = self.get_edge_class(edge_type)
        if edge_class is None:
            return [f"边类型 '{edge_type}' 不存在"]
        
        try:
            # 创建临时实例进行验证
            temp_instance = edge_class()
            return temp_instance.validate_config(config)
            
        except Exception as e:
            return [f"配置验证失败: {e}"]
    
    def get_edge_schema(self, edge_type: str) -> Optional[Dict[str, Any]]:
        """获取边配置Schema
        
        Args:
            edge_type: 边类型
            
        Returns:
            Optional[Dict[str, Any]]: 配置Schema，如果边类型不存在则返回None
        """
        edge_class = self.get_edge_class(edge_type)
        if edge_class is None:
            return None
        
        try:
            # 创建临时实例获取Schema
            temp_instance = edge_class()
            return temp_instance.get_config_schema()
            
        except Exception as e:
            logger.error(f"获取边Schema失败: {e}")
            return None
    
    def set_edge_metadata(self, edge_type: str, metadata: Dict[str, Any]) -> None:
        """设置边类型元数据
        
        Args:
            edge_type: 边类型
            metadata: 元数据
        """
        if edge_type not in self._edge_classes:
            raise ValueError(f"边类型 '{edge_type}' 不存在")
        
        if not isinstance(metadata, dict):
            raise ValueError("元数据必须是字典类型")
        
        self._edge_metadata[edge_type] = metadata
        logger.debug(f"设置边类型元数据: {edge_type}")
    
    def get_edge_metadata(self, edge_type: str) -> Optional[Dict[str, Any]]:
        """获取边类型元数据
        
        Args:
            edge_type: 边类型
            
        Returns:
            Optional[Dict[str, Any]]: 元数据，如果不存在则返回None
        """
        return self._edge_metadata.get(edge_type)
    
    def get_edge_info(self, edge_type: str) -> Optional[Dict[str, Any]]:
        """获取边类型信息
        
        Args:
            edge_type: 边类型
            
        Returns:
            Optional[Dict[str, Any]]: 边类型信息
        """
        edge_class = self.get_edge_class(edge_type)
        if edge_class is None:
            return None
        
        return {
            "type": edge_type,
            "class_name": edge_class.__name__,
            "module": edge_class.__module__,
            "schema": self.get_edge_schema(edge_type),
            "metadata": self.get_edge_metadata(edge_type),
            "instance_count": len([e for e in self._edge_instances.values() if e.edge_type == edge_type])
        }
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        # 统计各类型的实例数量
        instance_counts = {}
        for edge in self._edge_instances.values():
            edge_type = edge.edge_type
            instance_counts[edge_type] = instance_counts.get(edge_type, 0) + 1
        
        return {
            "registered_types": len(self._edge_classes),
            "registered_instances": len(self._edge_instances),
            "type_list": self.list_edge_types(),
            "instance_list": self.list_edge_instances(),
            "instance_counts": instance_counts,
            "metadata_count": len(self._edge_metadata)
        }
    
    def clear(self) -> None:
        """清除所有注册的边类型和实例"""
        self._edge_classes.clear()
        self._edge_instances.clear()
        self._edge_metadata.clear()
        logger.debug("清除所有边注册信息")
    
    def validate_registry(self) -> List[str]:
        """验证注册器状态
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证边类型
        for edge_type, edge_class in self._edge_classes.items():
            if not issubclass(edge_class, IEdge):
                errors.append(f"边类型 '{edge_type}' 的类未实现 IEdge 接口")
        
        # 验证实例
        for edge_id, edge in self._edge_instances.items():
            if not isinstance(edge, IEdge):
                errors.append(f"边实例 '{edge_id}' 未实现 IEdge 接口")
            else:
                validation_errors = edge.validate()
                if validation_errors:
                    errors.extend([f"边实例 '{edge_id}': {err}" for err in validation_errors])
        
        # 验证实例对应的类型是否存在
        for edge in self._edge_instances.values():
            if edge.edge_type not in self._edge_classes:
                errors.append(f"边实例 '{edge.edge_id}' 的类型 '{edge.edge_type}' 未注册")
        
        return errors
    
    def export_registry(self) -> Dict[str, Any]:
        """导出注册器数据
        
        Returns:
            Dict[str, Any]: 注册器数据
        """
        return {
            "edge_types": {
                edge_type: {
                    "class_name": edge_class.__name__,
                    "module": edge_class.__module__,
                    "metadata": self._edge_metadata.get(edge_type, {})
                }
                for edge_type, edge_class in self._edge_classes.items()
            },
            "edge_instances": {
                edge_id: {
                    "type": edge.edge_type,
                    "from_node": edge.from_node,
                    "to_node": edge.to_node,
                    "class_name": edge.__class__.__name__
                }
                for edge_id, edge in self._edge_instances.items()
            },
            "stats": self.get_registry_stats()
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"EdgeRegistry(types={len(self._edge_classes)}, instances={len(self._edge_instances)})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"EdgeRegistry(edge_types={list(self._edge_classes.keys())}, edge_instances={list(self._edge_instances.keys())})"


# 装饰器版本，用于自动注册边类型
def edge(edge_type: str, metadata: Optional[Dict[str, Any]] = None):
    """边类型注册装饰器
    
    Args:
        edge_type: 边类型
        metadata: 边类型元数据
        
    Returns:
        装饰器函数
    """
    def decorator(edge_class: Type[IEdge]) -> Type[IEdge]:
        # 注意：全局注册表已被移除，请使用依赖注入方式注册
        # 这里保留装饰器功能但不再自动注册到全局注册表
        logger.warning(f"边类型 {edge_type} 装饰器已使用，但全局注册表已被移除。请使用依赖注入方式注册。")
        
        # 为类添加边类型属性
        setattr(edge_class, '_decorator_edge_type', edge_type)
        setattr(edge_class, '_decorator_metadata', metadata or {})
        
        return edge_class
    
    return decorator