"""工作流注册表实现

实现工作流相关组件的注册表，支持依赖注入。
"""

from typing import Dict, Any, List, Type, Optional
import logging

from src.interfaces.workflow.registry import (
    IComponentRegistry, 
    IFunctionRegistry,
    IWorkflowRegistry
)
from src.interfaces.workflow.graph import INode, IEdge

logger = logging.getLogger(__name__)


class ComponentRegistry(IComponentRegistry):
    """组件注册表实现"""
    
    def __init__(self):
        """初始化组件注册表"""
        self._node_types: Dict[str, Type[INode]] = {}
        self._edge_types: Dict[str, Type[IEdge]] = {}
        self._logger = logging.getLogger(f"{__name__}.ComponentRegistry")
    
    def register_node(self, node_type: str, node_class: Type[INode]) -> None:
        """注册节点类型"""
        if not issubclass(node_class, INode):
            raise ValueError(f"节点类必须实现 INode 接口: {node_class}")
        
        self._node_types[node_type] = node_class
        self._logger.debug(f"注册节点类型: {node_type} -> {node_class.__name__}")
    
    def register_edge(self, edge_type: str, edge_class: Type[IEdge]) -> None:
        """注册边类型"""
        if not issubclass(edge_class, IEdge):
            raise ValueError(f"边类必须实现 IEdge 接口: {edge_class}")
        
        self._edge_types[edge_type] = edge_class
        self._logger.debug(f"注册边类型: {edge_type} -> {edge_class.__name__}")
    
    def get_node_class(self, node_type: str) -> Optional[Type[INode]]:
        """获取节点类"""
        return self._node_types.get(node_type)
    
    def get_edge_class(self, edge_type: str) -> Optional[Type[IEdge]]:
        """获取边类"""
        return self._edge_types.get(edge_type)
    
    def list_node_types(self) -> List[str]:
        """列出所有注册的节点类型"""
        return list(self._node_types.keys())
    
    def list_edge_types(self) -> List[str]:
        """列出所有注册的边类型"""
        return list(self._edge_types.keys())
    
    def clear(self) -> None:
        """清除所有注册"""
        self._node_types.clear()
        self._edge_types.clear()
        self._logger.debug("组件注册表已清除")


class FunctionRegistry(IFunctionRegistry):
    """函数注册表实现"""
    
    def __init__(self):
        """初始化函数注册表"""
        self._node_functions: Dict[str, Any] = {}
        self._route_functions: Dict[str, Any] = {}
        self._logger = logging.getLogger(f"{__name__}.FunctionRegistry")
    
    def register_node_function(self, name: str, function: Any) -> None:
        """注册节点函数"""
        if not callable(function):
            raise ValueError(f"节点函数必须是可调用对象: {function}")
        
        self._node_functions[name] = function
        self._logger.debug(f"注册节点函数: {name}")
    
    def register_route_function(self, name: str, function: Any) -> None:
        """注册路由函数"""
        if not callable(function):
            raise ValueError(f"路由函数必须是可调用对象: {function}")
        
        self._route_functions[name] = function
        self._logger.debug(f"注册路由函数: {name}")
    
    def get_node_function(self, name: str) -> Optional[Any]:
        """获取节点函数"""
        return self._node_functions.get(name)
    
    def get_route_function(self, name: str) -> Optional[Any]:
        """获取路由函数"""
        return self._route_functions.get(name)
    
    def list_node_functions(self) -> List[str]:
        """列出所有节点函数"""
        return list(self._node_functions.keys())
    
    def list_route_functions(self) -> List[str]:
        """列出所有路由函数"""
        return list(self._route_functions.keys())
    
    def clear(self) -> None:
        """清除所有注册"""
        self._node_functions.clear()
        self._route_functions.clear()
        self._logger.debug("函数注册表已清除")


class WorkflowRegistry(IWorkflowRegistry):
    """工作流注册表实现 - 组合所有注册表"""
    
    def __init__(self):
        """初始化工作流注册表"""
        self._component_registry = ComponentRegistry()
        self._function_registry = FunctionRegistry()
        self._logger = logging.getLogger(f"{__name__}.WorkflowRegistry")
    
    @property
    def component_registry(self) -> IComponentRegistry:
        """组件注册表"""
        return self._component_registry
    
    @property
    def function_registry(self) -> IFunctionRegistry:
        """函数注册表"""
        return self._function_registry
    
    def validate_dependencies(self) -> List[str]:
        """验证依赖完整性"""
        errors = []
        
        # 验证节点类型的依赖
        for node_type in self._component_registry.list_node_types():
            node_class = self._component_registry.get_node_class(node_type)
            if node_class and hasattr(node_class, 'get_required_functions'):
                required_functions = node_class.get_required_functions()
                for func_name in required_functions:
                    if not self._function_registry.get_node_function(func_name):
                        errors.append(f"节点类型 {node_type} 需要函数 {func_name} 但未注册")
        
        # 验证边类型的依赖
        for edge_type in self._component_registry.list_edge_types():
            edge_class = self._component_registry.get_edge_class(edge_type)
            if edge_class and hasattr(edge_class, 'get_required_functions'):
                required_functions = edge_class.get_required_functions()
                for func_name in required_functions:
                    if not self._function_registry.get_route_function(func_name):
                        errors.append(f"边类型 {edge_type} 需要函数 {func_name} 但未注册")
        
        return errors
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        return {
            "node_types": len(self._component_registry.list_node_types()),
            "edge_types": len(self._component_registry.list_edge_types()),
            "node_functions": len(self._function_registry.list_node_functions()),
            "route_functions": len(self._function_registry.list_route_functions()),
            "dependency_errors": len(self.validate_dependencies())
        }
    
    def clear_all(self) -> None:
        """清除所有注册表"""
        self._component_registry.clear()
        self._function_registry.clear()
        self._logger.debug("工作流注册表已清除")


# 便捷函数
def create_workflow_registry() -> WorkflowRegistry:
    """创建工作流注册表实例
    
    Returns:
        WorkflowRegistry: 工作流注册表实例
    """
    return WorkflowRegistry()


# 导出所有实现
__all__ = [
    "ComponentRegistry",
    "FunctionRegistry", 
    "WorkflowRegistry",
    "create_workflow_registry",
]