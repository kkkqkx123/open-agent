"""节点函数注册表

管理节点内部函数的注册和查找。
"""

from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
from src.services.logger.injection import get_logger

from .config import NodeFunctionConfig, NodeCompositionConfig

logger = get_logger(__name__)


@dataclass
class RegisteredNodeFunction:
    """已注册的节点函数"""
    name: str
    function: Callable
    config: NodeFunctionConfig
    is_rest: bool = False


class NodeFunctionRegistry:
    """节点函数注册表"""
    
    def __init__(self) -> None:
        self._functions: Dict[str, RegisteredNodeFunction] = {}
        self._compositions: Dict[str, NodeCompositionConfig] = {}
        self._categories: Dict[str, List[str]] = {
            "llm": [],
            "tool": [],
            "analysis": [],
            "condition": [],
            "custom": []
        }
    
    def register_function(
        self, 
        name: str, 
        function: Callable, 
        config: NodeFunctionConfig,
        is_rest: bool = False
    ) -> None:
        """注册节点函数
        
        Args:
            name: 函数名称
            function: 函数对象
            config: 函数配置
            is_rest: 是否为内置函数
        """
        registered_func = RegisteredNodeFunction(
            name=name,
            function=function,
            config=config,
            is_rest=is_rest
        )
        
        self._functions[name] = registered_func
        
        # 按类别分类
        func_type = config.function_type
        if func_type in self._categories:
            self._categories[func_type].append(name)
        else:
            self._categories["custom"].append(name)
        
        logger.debug(f"注册节点函数: {name} (类型: {func_type})")
    
    def get_function(self, name: str) -> Optional[Callable]:
        """获取节点函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 函数对象，如果不存在返回None
        """
        registered_func = self._functions.get(name)
        return registered_func.function if registered_func else None
    
    def get_function_config(self, name: str) -> Optional[NodeFunctionConfig]:
        """获取节点函数配置
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[NodeFunctionConfig]: 函数配置，如果不存在返回None
        """
        registered_func = self._functions.get(name)
        return registered_func.config if registered_func else None
    
    def register_composition(self, config: NodeCompositionConfig) -> None:
        """注册节点组合配置
        
        Args:
            config: 节点组合配置
        """
        self._compositions[config.name] = config
        logger.debug(f"注册节点组合: {config.name}")
    
    def get_composition(self, name: str) -> Optional[NodeCompositionConfig]:
        """获取节点组合配置
        
        Args:
            name: 组合名称
            
        Returns:
            Optional[NodeCompositionConfig]: 节点组合配置，如果不存在返回None
        """
        return self._compositions.get(name)
    
    def list_functions(self) -> List[str]:
        """列出所有函数名称
        
        Returns:
            List[str]: 函数名称列表
        """
        return list(self._functions.keys())
    
    def list_functions_by_type(self, func_type: str) -> List[str]:
        """按类型列出函数
        
        Args:
            func_type: 函数类型
            
        Returns:
            List[str]: 函数名称列表
        """
        return self._categories.get(func_type, [])
    
    def list_compositions(self) -> List[str]:
        """列出所有节点组合
        
        Returns:
            List[str]: 节点组合名称列表
        """
        return list(self._compositions.keys())
    
    def has_function(self, name: str) -> bool:
        """检查是否存在指定名称的函数
        
        Args:
            name: 函数名称
            
        Returns:
            bool: 是否存在
        """
        return name in self._functions
    
    def has_composition(self, name: str) -> bool:
        """检查是否存在指定名称的节点组合
        
        Args:
            name: 组合名称
            
        Returns:
            bool: 是否存在
        """
        return name in self._compositions


# 注意：全局注册表已被移除，请使用依赖注入方式注册节点函数
# 以下函数已被弃用，请使用新的注册表接口

def get_global_node_function_registry() -> NodeFunctionRegistry:
    """获取全局节点函数注册表（已弃用）
    
    Returns:
        NodeFunctionRegistry: 全局节点函数注册表
        
    Raises:
        DeprecationWarning: 此函数已被弃用，请使用依赖注入方式
    """
    import warnings
    warnings.warn(
        "get_global_node_function_registry 已被弃用，请使用依赖注入方式",
        DeprecationWarning,
        stacklevel=2
    )
    raise NotImplementedError("请使用依赖注入方式获取节点函数注册表")


def reset_global_node_function_registry() -> None:
    """重置全局节点函数注册表（已弃用）
    
    Raises:
        DeprecationWarning: 此函数已被弃用，请使用依赖注入方式
    """
    import warnings
    warnings.warn(
        "reset_global_node_function_registry 已被弃用，请使用依赖注入方式",
        DeprecationWarning,
        stacklevel=2
    )
    raise NotImplementedError("请使用依赖注入方式管理节点函数注册表")