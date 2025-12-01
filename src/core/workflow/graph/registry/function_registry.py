"""函数注册表

统一管理节点函数和路由函数的注册。
"""

from typing import Dict, Callable, Any, List, Optional, Union
from abc import ABC, abstractmethod


class IFunction(ABC):
    """函数接口"""
    
    @property
    @abstractmethod
    def function_name(self) -> str:
        """函数名称"""
        pass
    
    @property
    @abstractmethod
    def function_type(self) -> str:
        """函数类型（node_function, route_function）"""
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置Schema"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置"""
        pass


class FunctionRegistry:
    """统一的函数注册表"""
    
    def __init__(self) -> None:
        """初始化函数注册表"""
        self._node_functions: Dict[str, Union[Callable, IFunction]] = {}
        self._route_functions: Dict[str, Union[Callable, IFunction]] = {}
    
    def register_node_function(self, name: str, function: Union[Callable, IFunction]) -> None:
        """注册节点函数
        
        Args:
            name: 函数名称
            function: 函数对象
            
        Raises:
            ValueError: 函数已存在
        """
        if name in self._node_functions:
            raise ValueError(f"节点函数 '{name}' 已存在")
        self._node_functions[name] = function
    
    def register_route_function(self, name: str, function: Union[Callable, IFunction]) -> None:
        """注册路由函数
        
        Args:
            name: 函数名称
            function: 函数对象
            
        Raises:
            ValueError: 函数已存在
        """
        if name in self._route_functions:
            raise ValueError(f"路由函数 '{name}' 已存在")
        self._route_functions[name] = function
    
    def get_node_function(self, name: str) -> Optional[Union[Callable, IFunction]]:
        """获取节点函数
        
        Args:
            name: 函数名称
            
        Returns:
            函数对象或None
        """
        return self._node_functions.get(name)
    
    def get_route_function(self, name: str) -> Optional[Union[Callable, IFunction]]:
        """获取路由函数
        
        Args:
            name: 函数名称
            
        Returns:
            函数对象或None
        """
        return self._route_functions.get(name)
    
    def list_node_functions(self) -> List[str]:
        """列出所有节点函数
        
        Returns:
            List[str]: 函数名称列表
        """
        return list(self._node_functions.keys())
    
    def list_route_functions(self) -> List[str]:
        """列出所有路由函数
        
        Returns:
            List[str]: 函数名称列表
        """
        return list(self._route_functions.keys())
    
    def get_function_schema(self, function_type: str, name: str) -> Dict[str, Any]:
        """获取函数配置Schema
        
        Args:
            function_type: 函数类型（node_function, route_function）
            name: 函数名称
            
        Returns:
            Dict: 配置Schema
            
        Raises:
            ValueError: 函数不存在
        """
        if function_type == "node_function":
            function = self.get_node_function(name)
        elif function_type == "route_function":
            function = self.get_route_function(name)
        else:
            raise ValueError(f"未知的函数类型: {function_type}")
        
        if function is None:
            raise ValueError(f"函数 '{name}' 不存在")
        
        if isinstance(function, IFunction):
            return function.get_config_schema()
        else:
            # 对于普通函数，返回基本Schema
            return {
                "type": "object",
                "properties": {},
                "required": []
            }
    
    def validate_function_config(self, function_type: str, name: str, config: Dict[str, Any]) -> List[str]:
        """验证函数配置
        
        Args:
            function_type: 函数类型（node_function, route_function）
            name: 函数名称
            config: 函数配置
            
        Returns:
            List[str]: 验证错误列表
        """
        try:
            if function_type == "node_function":
                function = self.get_node_function(name)
            elif function_type == "route_function":
                function = self.get_route_function(name)
            else:
                return [f"未知的函数类型: {function_type}"]
            
            if function is None:
                return [f"函数 '{name}' 不存在"]
            
            if isinstance(function, IFunction):
                return function.validate_config(config)
            else:
                # 对于普通函数，不进行配置验证
                return []
        except Exception as e:
            return [str(e)]
    
    def clear(self) -> None:
        """清除所有注册的函数"""
        self._node_functions.clear()
        self._route_functions.clear()


# 装饰器版本，用于自动注册函数
def node_function(name: str):
    """节点函数注册装饰器

    Args:
        name: 函数名称

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        # 注意：全局注册表已被移除，请使用依赖注入方式注册
        # 这里保留装饰器功能但不再自动注册到全局注册表
        from src.services.logger import get_logger
        logger = get_logger(__name__)
        logger.warning(f"节点函数 {name} 装饰器已使用，但全局注册表已被移除。请使用依赖注入方式注册。")
        
        return func
    
    return decorator


def route_function(name: str):
    """路由函数注册装饰器

    Args:
        name: 函数名称

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        # 注意：全局注册表已被移除，请使用依赖注入方式注册
        # 这里保留装饰器功能但不再自动注册到全局注册表
        from src.services.logger import get_logger
        logger = get_logger(__name__)
        logger.warning(f"路由函数 {name} 装饰器已使用，但全局注册表已被移除。请使用依赖注入方式注册。")
        
        return func
    
    return decorator