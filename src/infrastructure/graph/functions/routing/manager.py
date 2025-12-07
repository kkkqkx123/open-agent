"""路由函数管理器

提供统一的路由函数管理接口。
"""

from typing import Dict, Any, Callable, Optional, List

from .registry import RouteFunctionRegistry, RouteFunctionConfig
from .builtin import BuiltinRouteFunctions


class RouteFunctionManager:
    """路由函数管理器
    
    提供统一的路由函数管理接口，是系统的入口点。
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """初始化路由函数管理器
        
        Args:
            config_dir: 配置目录路径
        """
        # 使用基础设施层的日志服务
        from src.services.logger.injection import get_logger
        self.logger = get_logger(self.__class__.__name__)
        
        self.registry = RouteFunctionRegistry()
        
        # 注册内置函数
        self._register_builtin_functions()
        
        # 从配置目录加载
        if config_dir:
            self._load_from_config_directory(config_dir)
    
    def _register_builtin_functions(self) -> None:
        """注册内置函数"""
        builtin_functions = BuiltinRouteFunctions.get_all_functions()
        
        for name, func in builtin_functions.items():
            # 创建配置
            config = RouteFunctionConfig(
                name=name,
                description=f"内置路由函数: {name}",
                parameters={},
                return_values=["continue", "end"],
                category="builtin",
                implementation="builtin"
            )
            
            self.registry.register_route_function(name, func, config)
    
    def _load_from_config_directory(self, config_dir: str) -> None:
        """从配置目录加载路由函数
        
        Args:
            config_dir: 配置目录路径
        """
        # 这里可以实现从配置文件加载路由函数的逻辑
        # 暂时留空，可以根据需要实现
        self.logger.debug(f"从配置目录加载路由函数: {config_dir}")
    
    def get_route_function(self, name: str) -> Optional[Callable]:
        """获取路由函数
        
        Args:
            name: 路由函数名称
            
        Returns:
            Optional[Callable]: 路由函数，如果不存在返回None
        """
        return self.registry.get_route_function(name)
    
    def list_route_functions(self, category: Optional[str] = None) -> List[str]:
        """列出路由函数
        
        Args:
            category: 分类过滤器，如果为None则返回所有函数
            
        Returns:
            List[str]: 路由函数名称列表
        """
        return self.registry.list_route_functions(category)
    
    def get_route_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取路由函数信息
        
        Args:
            name: 路由函数名称
            
        Returns:
            Optional[Dict[str, Any]]: 路由函数信息，如果不存在返回None
        """
        return self.registry.get_route_info(name)
    
    def validate_route_function(self, name: str, parameters: Dict[str, Any]) -> List[str]:
        """验证路由函数参数
        
        Args:
            name: 路由函数名称
            parameters: 参数字典
            
        Returns:
            List[str]: 验证错误列表
        """
        config = self.registry.get_route_config(name)
        if not config:
            return [f"路由函数不存在: {name}"]
        
        errors = []
        param_config = config.parameters
        
        # 检查必需参数
        if isinstance(param_config, dict) and "type" in param_config:
            # JSON Schema 风格的参数验证
            required = param_config.get("required", [])
            properties = param_config.get("properties", {})
            
            for req_param in required:
                if req_param not in parameters:
                    errors.append(f"缺少必需参数: {req_param}")
            
            # 检查参数类型
            for param_name, param_value in parameters.items():
                if param_name in properties:
                    expected_type = properties[param_name].get("type")
                    if expected_type and not self._check_type(param_value, expected_type):
                        errors.append(f"参数 {param_name} 类型错误，期望 {expected_type}")
        
        return errors
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查参数类型
        
        Args:
            value: 参数值
            expected_type: 期望类型
            
        Returns:
            bool: 类型是否匹配
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True
    
    def register_custom_function(
        self, 
        name: str, 
        function: Callable, 
        config: Optional[RouteFunctionConfig] = None
    ) -> None:
        """注册自定义路由函数
        
        Args:
            name: 路由函数名称
            function: 路由函数
            config: 路由函数配置，如果为None则创建默认配置
        """
        if config is None:
            config = RouteFunctionConfig(
                name=name,
                description=f"自定义路由函数: {name}",
                parameters={},
                return_values=["continue", "end"],
                category="custom",
                implementation="custom"
            )
        
        self.registry.register_route_function(name, function, config)
    
    def unregister_function(self, name: str) -> bool:
        """注销路由函数
        
        Args:
            name: 路由函数名称
            
        Returns:
            bool: 是否成功注销
        """
        return self.registry.unregister(name)
    
    def get_categories(self) -> List[str]:
        """获取所有分类
        
        Returns:
            List[str]: 分类列表
        """
        return self.registry.list_categories()
    
    def get_functions_by_category(self, category: str) -> List[str]:
        """获取指定分类的路由函数
        
        Args:
            category: 分类名称
            
        Returns:
            List[str]: 路由函数名称列表
        """
        return self.registry.list_route_functions(category)
    
    def reload_from_config(self, config_dir: str) -> None:
        """从配置目录重新加载路由函数
        
        Args:
            config_dir: 配置目录路径
        """
        # 清除现有的配置函数（保留内置函数）
        builtin_functions = self.registry.list_route_functions("builtin")
        custom_functions = [name for name in self.registry.list_route_functions() 
                          if name not in builtin_functions]
        
        for func_name in custom_functions:
            self.registry.unregister(func_name)
        
        # 重新加载配置
        self._load_from_config_directory(config_dir)
    
    def validate_all_functions(self) -> Dict[str, List[str]]:
        """验证所有注册的路由函数
        
        Returns:
            Dict[str, List[str]]: 验证结果，键为函数名称，值为错误列表
        """
        results = {}
        
        for func_name in self.registry.list_route_functions():
            errors = self.registry.validate_route_function(func_name)
            if errors:
                results[func_name] = errors
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            "total_functions": self.registry.size(),
            "categories": {},
            "implementations": {}
        }
        
        # 按分类统计
        for category in self.registry.list_categories():
            functions = self.registry.list_route_functions(category)
            stats["categories"][category] = len(functions)
        
        # 按实现方式统计
        for func_name in self.registry.list_route_functions():
            config = self.registry.get_route_config(func_name)
            if config:
                impl = config.implementation
                stats["implementations"][impl] = stats["implementations"].get(impl, 0) + 1
        
        return stats


# 全局路由函数管理器实例
_global_manager: Optional[RouteFunctionManager] = None


def get_route_function_manager(config_dir: Optional[str] = None) -> RouteFunctionManager:
    """获取全局路由函数管理器实例
    
    Args:
        config_dir: 配置目录路径，只在第一次调用时有效
        
    Returns:
        RouteFunctionManager: 路由函数管理器实例
    """
    global _global_manager
    
    if _global_manager is None:
        _global_manager = RouteFunctionManager(config_dir)
    
    return _global_manager


def reset_route_function_manager() -> None:
    """重置全局路由函数管理器实例"""
    global _global_manager
    _global_manager = None