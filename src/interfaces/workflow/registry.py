"""工作流注册表接口

定义工作流相关组件的注册表接口，支持依赖注入。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.workflow.graph import INode, IEdge


class IComponentRegistry(ABC):
    """组件注册表接口"""
    
    @abstractmethod
    def register_node(self, node_type: str, node_class: Type['INode']) -> None:
        """注册节点类型"""
        pass
    
    @abstractmethod
    def register_edge(self, edge_type: str, edge_class: Type['IEdge']) -> None:
        """注册边类型"""
        pass
    
    @abstractmethod
    def get_node_class(self, node_type: str) -> Optional[Type['INode']]:
        """获取节点类"""
        pass
    
    @abstractmethod
    def get_edge_class(self, edge_type: str) -> Optional[Type['IEdge']]:
        """获取边类"""
        pass
    
    @abstractmethod
    def list_node_types(self) -> List[str]:
        """列出所有注册的节点类型"""
        pass
    
    @abstractmethod
    def list_edge_types(self) -> List[str]:
        """列出所有注册的边类型"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清除所有注册"""
        pass


class IFunctionRegistry(ABC):
    """函数注册表接口"""
    
    @abstractmethod
    def register_node_function(self, name: str, function: Any) -> None:
        """注册节点函数"""
        pass
    
    @abstractmethod
    def register_route_function(self, name: str, function: Any) -> None:
        """注册路由函数"""
        pass
    
    @abstractmethod
    def get_node_function(self, name: str) -> Optional[Any]:
        """获取节点函数"""
        pass
    
    @abstractmethod
    def get_route_function(self, name: str) -> Optional[Any]:
        """获取路由函数"""
        pass
    
    @abstractmethod
    def list_node_functions(self) -> List[str]:
        """列出所有节点函数"""
        pass
    
    @abstractmethod
    def list_route_functions(self) -> List[str]:
        """列出所有路由函数"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清除所有注册"""
        pass


class IEdgeRegistry(ABC):
    """边注册表接口"""
    
    @abstractmethod
    def register_edge(self, edge_type: str, edge_class: Type['IEdge']) -> None:
        """注册边类型"""
        pass
    
    @abstractmethod
    def register_edge_instance(self, edge: 'IEdge') -> None:
        """注册边实例"""
        pass
    
    @abstractmethod
    def get_edge_class(self, edge_type: str) -> Optional[Type['IEdge']]:
        """获取边类"""
        pass
    
    @abstractmethod
    def get_edge_instance(self, edge_id: str) -> Optional['IEdge']:
        """获取边实例"""
        pass
    
    @abstractmethod
    def create_edge(self, edge_type: str, **kwargs) -> 'IEdge':
        """创建边实例"""
        pass
    
    @abstractmethod
    def list_edge_types(self) -> List[str]:
        """列出所有注册的边类型"""
        pass
    
    @abstractmethod
    def list_edge_instances(self) -> List[str]:
        """列出所有注册的边实例"""
        pass
    
    @abstractmethod
    def unregister_edge(self, edge_type: str) -> bool:
        """注销边类型"""
        pass
    
    @abstractmethod
    def unregister_edge_instance(self, edge_id: str) -> bool:
        """注销边实例"""
        pass
    
    @abstractmethod
    def validate_edge_config(self, edge_type: str, config: Dict[str, Any]) -> List[str]:
        """验证边配置"""
        pass
    
    @abstractmethod
    def get_edge_schema(self, edge_type: str) -> Optional[Dict[str, Any]]:
        """获取边配置Schema"""
        pass
    
    @abstractmethod
    def set_edge_metadata(self, edge_type: str, metadata: Dict[str, Any]) -> None:
        """设置边类型元数据"""
        pass
    
    @abstractmethod
    def get_edge_metadata(self, edge_type: str) -> Optional[Dict[str, Any]]:
        """获取边类型元数据"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清除所有注册"""
        pass


# 导出所有接口
__all__ = [
    "IComponentRegistry",
    "IFunctionRegistry",
    "IEdgeRegistry",
]