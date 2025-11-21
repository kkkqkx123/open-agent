"""注册表管理器

统一管理工作流、节点和函数注册表。
"""

from typing import Dict, Any, List, Optional, Type, Union
import logging
from abc import ABC, abstractmethod

from ...graph.nodes.registry import BaseNode, NodeRegistry
from ..registry import WorkflowRegistry
from ..function_registry import FunctionRegistry

logger = logging.getLogger(__name__)


class IRegistryManager(ABC):
    """注册表管理器接口"""
    
    @abstractmethod
    def get_workflow_registry(self) -> WorkflowRegistry:
        """获取工作流注册表"""
        pass
    
    @abstractmethod
    def get_node_registry(self) -> NodeRegistry:
        """获取节点注册表"""
        pass
    
    @abstractmethod
    def get_function_registry(self) -> FunctionRegistry:
        """获取函数注册表"""
        pass
    
    @abstractmethod
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取所有注册表的统计信息"""
        pass
    
    @abstractmethod
    def clear_all(self) -> None:
        """清除所有注册表"""
        pass


class RegistryManager(IRegistryManager):
    """注册表管理器实现
    
    统一管理工作流、节点和函数注册表。
    """
    
    def __init__(self) -> None:
        """初始化注册表管理器"""
        self._workflow_registry = WorkflowRegistry()
        self._node_registry = NodeRegistry()
        self._function_registry = FunctionRegistry()
        
        logger.info("注册表管理器初始化完成")
    
    def get_workflow_registry(self) -> WorkflowRegistry:
        """获取工作流注册表
        
        Returns:
            WorkflowRegistry: 工作流注册表
        """
        return self._workflow_registry
    
    def get_node_registry(self) -> NodeRegistry:
        """获取节点注册表
        
        Returns:
            NodeRegistry: 节点注册表
        """
        return self._node_registry
    
    def get_function_registry(self) -> FunctionRegistry:
        """获取函数注册表
        
        Returns:
            FunctionRegistry: 函数注册表
        """
        return self._function_registry
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取所有注册表的统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "workflow_registry": self._workflow_registry.get_registry_stats(),
            "node_registry": {
                "registered_nodes": len(self._node_registry._nodes),
                "registered_instances": len(self._node_registry._node_instances),
                "node_types": self._node_registry.list_nodes()
            },
            "function_registry": {
                "registered_functions": len(self._function_registry._node_functions),
                "function_names": list(self._function_registry._node_functions.keys())
            }
        }
    
    def clear_all(self) -> None:
        """清除所有注册表"""
        self._workflow_registry.clear()
        self._node_registry.clear()
        self._function_registry.clear()
        logger.info("所有注册表已清除")
    
    def register_workflow_node(self, node_class: Type[BaseNode]) -> None:
        """注册工作流节点
        
        Args:
            node_class: 节点类
        """
        self._node_registry.register_node(node_class)
        logger.info(f"注册工作流节点: {node_class.__name__}")
    
    def register_workflow_node_instance(self, node: BaseNode) -> None:
        """注册工作流节点实例
        
        Args:
            node: 节点实例
        """
        self._node_registry.register_node_instance(node)
        logger.info(f"注册工作流节点实例: {node.node_type}")
    
    def get_workflow_node(self, node_type: str) -> BaseNode:
        """获取工作流节点
        
        Args:
            node_type: 节点类型
            
        Returns:
            BaseNode: 节点实例
        """
        return self._node_registry.get_node_instance(node_type)
    
    def list_workflow_nodes(self) -> List[str]:
        """列出所有工作流节点
        
        Returns:
            List[str]: 节点类型列表
        """
        return self._node_registry.list_nodes()
    
    def validate_workflow_node_config(self, node_type: str, config: Dict[str, Any]) -> List[str]:
        """验证工作流节点配置
        
        Args:
            node_type: 节点类型
            config: 配置
            
        Returns:
            List[str]: 验证错误列表
        """
        return self._node_registry.validate_node_config(node_type, config)
    
    def register_function(self, name: str, func: Any) -> None:
        """注册函数
        
        Args:
            name: 函数名
            func: 函数对象
        """
        self._function_registry.register_node_function(name, func)
        logger.info(f"注册函数: {name}")
    
    def get_function(self, name: str) -> Any:
        """获取函数
        
        Args:
            name: 函数名
            
        Returns:
            函数对象
        """
        return self._function_registry.get_node_function(name)
    
    def list_functions(self) -> List[str]:
        """列出所有函数
        
        Returns:
            List[str]: 函数名列表
        """
        return list(self._function_registry._node_functions.keys())
    
    def register_workflow(self, workflow_id: str, workflow: Any) -> None:
        """注册工作流
        
        Args:
            workflow_id: 工作流ID
            workflow: 工作流实例
        """
        self._workflow_registry.register_workflow(workflow_id, workflow)
        logger.info(f"注册工作流: {workflow_id}")
    
    def get_workflow(self, workflow_id: str) -> Any:
        """获取工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流实例
        """
        return self._workflow_registry.get_workflow(workflow_id)
    
    def list_workflows(self) -> List[str]:
        """列出所有工作流
        
        Returns:
            List[str]: 工作流ID列表
        """
        return self._workflow_registry.list_workflows()
    
    def unregister_workflow(self, workflow_id: str) -> bool:
        """注销工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否成功注销
        """
        result = self._workflow_registry.unregister_workflow(workflow_id)
        if result:
            logger.info(f"注销工作流: {workflow_id}")
        return result


# 全局注册表管理器实例
_global_registry_manager: Optional[RegistryManager] = None


def get_global_registry_manager() -> RegistryManager:
    """获取全局注册表管理器
    
    Returns:
        RegistryManager: 全局注册表管理器
    """
    global _global_registry_manager
    if _global_registry_manager is None:
        _global_registry_manager = RegistryManager()
    return _global_registry_manager


def register_workflow_node(node_class: Type[BaseNode]) -> None:
    """注册工作流节点到全局注册表
    
    Args:
        node_class: 节点类
    """
    get_global_registry_manager().register_workflow_node(node_class)


def register_workflow_node_instance(node: BaseNode) -> None:
    """注册工作流节点实例到全局注册表
    
    Args:
        node: 节点实例
    """
    get_global_registry_manager().register_workflow_node_instance(node)


def get_workflow_node(node_type: str) -> BaseNode:
    """从全局注册表获取工作流节点
    
    Args:
        node_type: 节点类型
        
    Returns:
        BaseNode: 节点实例
    """
    return get_global_registry_manager().get_workflow_node(node_type)


def register_function(name: str, func: Any) -> None:
    """注册函数到全局注册表
    
    Args:
        name: 函数名
        func: 函数对象
    """
    get_global_registry_manager().register_function(name, func)


def get_function(name: str) -> Any:
    """从全局注册表获取函数
    
    Args:
        name: 函数名
        
    Returns:
        函数对象
    """
    return get_global_registry_manager().get_function(name)


def register_workflow(workflow_id: str, workflow: Any) -> None:
    """注册工作流到全局注册表
    
    Args:
        workflow_id: 工作流ID
        workflow: 工作流实例
    """
    get_global_registry_manager().register_workflow(workflow_id, workflow)


def get_workflow(workflow_id: str) -> Any:
    """从全局注册表获取工作流
    
    Args:
        workflow_id: 工作流ID
        
    Returns:
        工作流实例
    """
    return get_global_registry_manager().get_workflow(workflow_id)