"""节点函数管理器

提供统一的节点函数管理接口。
"""

from typing import Dict, Any, Callable, Optional, List
from pathlib import Path
import logging

from .registry import NodeFunctionRegistry, get_global_node_function_registry
from .loader import NodeFunctionLoader
from .config import NodeFunctionConfig, NodeCompositionConfig
from .executor import NodeFunctionExecutor

logger = logging.getLogger(__name__)


class NodeFunctionManager:
    """节点函数管理器
    
    提供统一的节点函数管理接口，包括加载、注册、执行等功能。
    """
    
    def __init__(
        self, 
        registry: Optional[NodeFunctionRegistry] = None,
        config_dir: Optional[str] = None
    ):
        """初始化节点函数管理器
        
        Args:
            registry: 节点函数注册表
            config_dir: 配置目录路径
        """
        self.registry = registry or get_global_node_function_registry()
        self.loader = NodeFunctionLoader(self.registry)
        self.executor = NodeFunctionExecutor(self.registry)
        
        # 如果提供了配置目录，加载配置
        if config_dir:
            self.load_configurations(config_dir)
    
    def load_configurations(self, config_dir: str) -> None:
        """加载配置
        
        Args:
            config_dir: 配置目录路径
        """
        self.loader.load_from_config_directory(config_dir)
        logger.info(f"从目录加载节点函数配置: {config_dir}")
    
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
        self.registry.register_function(name, function, config, is_rest)
    
    def get_function(self, name: str) -> Optional[Callable]:
        """获取节点函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 函数对象，如果不存在返回None
        """
        return self.registry.get_function(name)
    
    def get_function_config(self, name: str) -> Optional[NodeFunctionConfig]:
        """获取节点函数配置
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[NodeFunctionConfig]: 函数配置，如果不存在返回None
        """
        return self.registry.get_function_config(name)
    
    def register_composition(self, config: NodeCompositionConfig) -> None:
        """注册节点组合配置
        
        Args:
            config: 节点组合配置
        """
        self.registry.register_composition(config)
    
    def get_composition(self, name: str) -> Optional[NodeCompositionConfig]:
        """获取节点组合配置
        
        Args:
            name: 组合名称
            
        Returns:
            Optional[NodeCompositionConfig]: 节点组合配置，如果不存在返回None
        """
        return self.registry.get_composition(name)
    
    def execute_function(
        self, 
        name: str, 
        state: Dict[str, Any], 
        **kwargs
    ) -> Dict[str, Any]:
        """执行节点函数
        
        Args:
            name: 函数名称
            state: 工作流状态
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        return self.executor.execute_function(name, state, **kwargs)
    
    def execute_composition(
        self, 
        name: str, 
        state: Dict[str, Any], 
        **kwargs
    ) -> Dict[str, Any]:
        """执行节点组合
        
        Args:
            name: 组合名称
            state: 工作流状态
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        return self.executor.execute_composition(name, state, **kwargs)
    
    def list_functions(self) -> List[str]:
        """列出所有函数名称
        
        Returns:
            List[str]: 函数名称列表
        """
        return self.registry.list_functions()
    
    def list_functions_by_type(self, func_type: str) -> List[str]:
        """按类型列出函数
        
        Args:
            func_type: 函数类型
            
        Returns:
            List[str]: 函数名称列表
        """
        return self.registry.list_functions_by_type(func_type)
    
    def list_compositions(self) -> List[str]:
        """列出所有节点组合
        
        Returns:
            List[str]: 节点组合名称列表
        """
        return self.registry.list_compositions()
    
    def has_function(self, name: str) -> bool:
        """检查是否存在指定名称的函数
        
        Args:
            name: 函数名称
            
        Returns:
            bool: 是否存在
        """
        return self.registry.has_function(name)
    
    def has_composition(self, name: str) -> bool:
        """检查是否存在指定名称的节点组合
        
        Args:
            name: 组合名称
            
        Returns:
            bool: 是否存在
        """
        return self.registry.has_composition(name)


# 全局节点函数管理器实例
_global_node_function_manager: Optional[NodeFunctionManager] = None


def get_node_function_manager(config_dir: Optional[str] = None) -> NodeFunctionManager:
    """获取全局节点函数管理器
    
    Args:
        config_dir: 配置目录路径（可选）
        
    Returns:
        NodeFunctionManager: 全局节点函数管理器
    """
    global _global_node_function_manager
    if _global_node_function_manager is None:
        _global_node_function_manager = NodeFunctionManager(config_dir=config_dir)
    return _global_node_function_manager


def reset_global_node_function_manager() -> None:
    """重置全局节点函数管理器（用于测试）"""
    global _global_node_function_manager
    _global_node_function_manager = None