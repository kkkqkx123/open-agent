"""路由函数注册表

管理所有可用的路由函数，提供注册、获取和查询功能。
"""

from typing import Dict, Any, Callable, Optional, List

from src.interfaces.workflow.graph import IRouteFunctionConfig


class RouteFunctionConfig(IRouteFunctionConfig):
    """路由函数配置"""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        return_values: Optional[List[str]] = None,
        category: str = "general",
        implementation: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化路由函数配置
        
        Args:
            name: 路由函数名称
            description: 路由函数描述
            parameters: 参数配置
            return_values: 可能的返回值列表
            category: 路由函数分类
            implementation: 实现方式：builtin, config, custom
            metadata: 元数据
        """
        self._name = name  # 路由函数名称
        self._description = description  # 路由函数描述
        self._parameters = parameters if parameters is not None else {}  # 参数配置
        self._return_values = return_values if return_values is not None else []  # 可能的返回值列表
        self._category = category  # 路由函数分类
        self.implementation = implementation  # 实现方式：builtin, config, custom
        self._metadata = metadata if metadata is not None else {}  # 元数据
    
    @property
    def name(self) -> str:
        """路由函数名称"""
        return self._name
    
    @property
    def description(self) -> str:
        """路由函数描述"""
        return self._description
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """参数配置"""
        return self._parameters
    
    @property
    def return_values(self) -> List[str]:
        """可能的返回值列表"""
        return self._return_values
    
    @property
    def category(self) -> str:
        """路由函数分类"""
        return self._category
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        return self._metadata


class RouteFunctionRegistry:
    """路由函数注册表
    
    管理所有可用的路由函数，支持分类管理和查询。
    """
    
    def __init__(self) -> None:
        # 使用基础设施层的日志服务
        from src.services.logger.injection import get_logger
        self.logger = get_logger(self.__class__.__name__)
        
        self._route_functions: Dict[str, Callable] = {}
        self._route_configs: Dict[str, RouteFunctionConfig] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register_route_function(
        self, 
        name: str, 
        function: Callable, 
        config: RouteFunctionConfig
    ) -> None:
        """注册路由函数
        
        Args:
            name: 路由函数名称
            function: 路由函数
            config: 路由函数配置
        """
        self._route_functions[name] = function
        self._route_configs[name] = config
        
        # 更新分类索引
        if config.category not in self._categories:
            self._categories[config.category] = []
        if name not in self._categories[config.category]:
            self._categories[config.category].append(name)
        
        self.logger.debug(f"注册路由函数: {name} (分类: {config.category})")
    
    def get_route_function(self, name: str) -> Optional[Callable]:
        """获取路由函数
        
        Args:
            name: 路由函数名称
            
        Returns:
            Optional[Callable]: 路由函数，如果不存在返回None
        """
        return self._route_functions.get(name)
    
    def get_route_config(self, name: str) -> Optional[RouteFunctionConfig]:
        """获取路由函数配置
        
        Args:
            name: 路由函数名称
            
        Returns:
            Optional[RouteFunctionConfig]: 路由函数配置，如果不存在返回None
        """
        return self._route_configs.get(name)
    
    def list_route_functions(self, category: Optional[str] = None) -> List[str]:
        """列出路由函数
        
        Args:
            category: 分类过滤器，如果为None则返回所有函数
            
        Returns:
            List[str]: 路由函数名称列表
        """
        if category:
            return self._categories.get(category, [])
        return list(self._route_functions.keys())
    
    def list_categories(self) -> List[str]:
        """列出所有分类
        
        Returns:
            List[str]: 分类列表
        """
        return list(self._categories.keys())
    
    def unregister(self, name: str) -> bool:
        """注销路由函数
        
        Args:
            name: 路由函数名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._route_functions:
            config = self._route_configs[name]
            
            # 从分类中移除
            if config.category in self._categories:
                if name in self._categories[config.category]:
                    self._categories[config.category].remove(name)
                
                # 如果分类为空，移除分类
                if not self._categories[config.category]:
                    del self._categories[config.category]
            
            del self._route_functions[name]
            del self._route_configs[name]
            
            self.logger.debug(f"注销路由函数: {name}")
            return True
        return False
    
    def validate_route_function(self, name: str) -> List[str]:
        """验证路由函数
        
        Args:
            name: 路由函数名称
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if name not in self._route_functions:
            errors.append(f"路由函数不存在: {name}")
            return errors
        
        config = self._route_configs[name]
        
        # 验证配置
        if not config.name:
            errors.append("路由函数名称不能为空")
        
        if not config.description:
            errors.append("路由函数描述不能为空")
        
        if not config.return_values:
            errors.append("路由函数返回值列表不能为空")
        
        return errors
    
    def get_route_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取路由函数信息
        
        Args:
            name: 路由函数名称
            
        Returns:
            Optional[Dict[str, Any]]: 路由函数信息，如果不存在返回None
        """
        config = self._route_configs.get(name)
        if not config:
            return None
        
        return {
            "name": config.name,
            "description": config.description,
            "category": config.category,
            "parameters": config.parameters,
            "return_values": config.return_values,
            "implementation": config.implementation,
            "metadata": config.metadata
        }
    
    def clear(self) -> None:
        """清除所有注册的路由函数"""
        self._route_functions.clear()
        self._route_configs.clear()
        self._categories.clear()
        self.logger.debug("清除所有路由函数")
    
    def size(self) -> int:
        """获取注册的路由函数数量
        
        Returns:
            int: 路由函数数量
        """
        return len(self._route_functions)