"""触发器函数注册表

管理触发器函数的注册和查找。
"""

from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
import logging

from .config import TriggerFunctionConfig, TriggerCompositionConfig

logger = logging.getLogger(__name__)


@dataclass
class RegisteredTriggerFunction:
    """已注册的触发器函数"""
    name: str
    function: Callable
    config: TriggerFunctionConfig
    is_rest: bool = False


class TriggerFunctionRegistry:
    """触发器函数注册表"""
    
    def __init__(self) -> None:
        self._functions: Dict[str, RegisteredTriggerFunction] = {}
        self._compositions: Dict[str, TriggerCompositionConfig] = {}
        self._categories: Dict[str, List[str]] = {
            "evaluate": [],
            "execute": [],
            "condition": [],
            "time": [],
            "state": [],
            "event": [],
            "custom": []
        }
    
    def register_function(
        self, 
        name: str, 
        function: Callable, 
        config: TriggerFunctionConfig,
        is_rest: bool = False
    ) -> None:
        """注册触发器函数
        
        Args:
            name: 函数名称
            function: 函数对象
            config: 函数配置
            is_rest: 是否为内置函数
        """
        registered_func = RegisteredTriggerFunction(
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
        
        logger.debug(f"注册触发器函数: {name} (类型: {func_type})")
    
    def get_function(self, name: str) -> Optional[Callable]:
        """获取触发器函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 函数对象，如果不存在返回None
        """
        registered_func = self._functions.get(name)
        return registered_func.function if registered_func else None
    
    def get_function_config(self, name: str) -> Optional[TriggerFunctionConfig]:
        """获取触发器函数配置
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[TriggerFunctionConfig]: 函数配置，如果不存在返回None
        """
        registered_func = self._functions.get(name)
        return registered_func.config if registered_func else None
    
    def register_composition(self, config: TriggerCompositionConfig) -> None:
        """注册触发器组合配置
        
        Args:
            config: 触发器组合配置
        """
        self._compositions[config.name] = config
        logger.debug(f"注册触发器组合: {config.name}")
    
    def get_composition(self, name: str) -> Optional[TriggerCompositionConfig]:
        """获取触发器组合配置
        
        Args:
            name: 组合名称
            
        Returns:
            Optional[TriggerCompositionConfig]: 触发器组合配置，如果不存在返回None
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
        """列出所有触发器组合
        
        Returns:
            List[str]: 触发器组合名称列表
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
        """检查是否存在指定名称的触发器组合
        
        Args:
            name: 组合名称
            
        Returns:
            bool: 是否存在
        """
        return name in self._compositions
    
    def unregister_function(self, name: str) -> bool:
        """注销触发器函数
        
        Args:
            name: 函数名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._functions:
            registered_func = self._functions[name]
            func_type = registered_func.config.function_type
            
            # 从分类中移除
            if func_type in self._categories and name in self._categories[func_type]:
                self._categories[func_type].remove(name)
            
            del self._functions[name]
            logger.debug(f"注销触发器函数: {name}")
            return True
        return False
    
    def unregister_composition(self, name: str) -> bool:
        """注销触发器组合
        
        Args:
            name: 组合名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._compositions:
            del self._compositions[name]
            logger.debug(f"注销触发器组合: {name}")
            return True
        return False
    
    def get_categories(self) -> List[str]:
        """获取所有分类
        
        Returns:
            List[str]: 分类列表
        """
        return list(self._categories.keys())
    
    def clear(self) -> None:
        """清除所有注册的函数和组合"""
        self._functions.clear()
        self._compositions.clear()
        for category in self._categories:
            self._categories[category].clear()
        logger.debug("清除所有触发器函数和组合")
    
    def size(self) -> int:
        """获取注册的函数数量
        
        Returns:
            int: 函数数量
        """
        return len(self._functions)
    
    def composition_size(self) -> int:
        """获取注册的组合数量
        
        Returns:
            int: 组合数量
        """
        return len(self._compositions)


# 全局触发器函数注册表实例
_global_trigger_function_registry: Optional[TriggerFunctionRegistry] = None


def get_global_trigger_function_registry() -> TriggerFunctionRegistry:
    """获取全局触发器函数注册表
    
    Returns:
        TriggerFunctionRegistry: 全局触发器函数注册表
    """
    global _global_trigger_function_registry
    if _global_trigger_function_registry is None:
        _global_trigger_function_registry = TriggerFunctionRegistry()
    return _global_trigger_function_registry


def reset_global_trigger_function_registry() -> None:
    """重置全局触发器函数注册表（用于测试）"""
    global _global_trigger_function_registry
    _global_trigger_function_registry = None