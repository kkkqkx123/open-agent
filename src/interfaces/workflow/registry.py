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


class IWorkflowRegistry(ABC):
    """工作流注册表接口 - 组合所有注册表"""
    
    @property
    @abstractmethod
    def component_registry(self) -> IComponentRegistry:
        """组件注册表"""
        pass
    
    @property
    @abstractmethod
    def function_registry(self) -> IFunctionRegistry:
        """函数注册表"""
        pass
    
    @abstractmethod
    def validate_dependencies(self) -> List[str]:
        """验证依赖完整性"""
        pass
    
    @abstractmethod
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        pass
    
    @abstractmethod
    def clear_all(self) -> None:
        """清除所有注册表"""
        pass


# 导出所有接口
__all__ = [
    "IComponentRegistry",
    "IFunctionRegistry", 
    "IWorkflowRegistry",
]