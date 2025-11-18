"""路由函数注册表

管理所有可用的路由函数，提供注册、获取和查询功能。
"""

from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class RouteFunctionConfig:
    """路由函数配置"""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)  # 参数配置
    return_values: List[str] = field(default_factory=list)   # 可能的返回值列表
    category: str = "general"   # 路由函数分类
    implementation: str = ""    # 实现方式：rest, config, custom
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


class RouteFunctionRegistry:
    """路由函数注册表
    
    管理所有可用的路由函数，支持分类管理和查询。
    """
    
    def __init__(self):
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
        
        logger.debug(f"注册路由函数: {name} (分类: {config.category})")
    
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
            
            logger.debug(f"注销路由函数: {name}")
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
        logger.debug("清除所有路由函数")
    
    def size(self) -> int:
        """获取注册的路由函数数量
        
        Returns:
            int: 路由函数数量
        """
        return len(self._route_functions)