"""组件组装器接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from ..container import IDependencyContainer
from ..config.core.loader import IConfigLoader


class IComponentAssembler(ABC):
    """组件组装器接口"""
    
    @abstractmethod
    def assemble(self, config: Dict[str, Any]) -> IDependencyContainer:
        """组装组件
        
        Args:
            config: 组装配置
            
        Returns:
            IDependencyContainer: 组装后的依赖注入容器
            
        Raises:
            AssemblyError: 组装失败时抛出
        """
        pass
    
    @abstractmethod
    def register_services(self, services_config: Dict[str, Any]) -> None:
        """注册服务
        
        Args:
            services_config: 服务配置
        """
        pass
    
    @abstractmethod
    def register_dependencies(self, dependencies_config: Dict[str, Any]) -> None:
        """注册依赖关系
        
        Args:
            dependencies_config: 依赖配置
        """
        pass
    
    @abstractmethod
    def resolve_dependencies(self, service_type: Type) -> Any:
        """解析依赖
        
        Args:
            service_type: 服务类型
            
        Returns:
            Any: 服务实例
        """
        pass
    
    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def get_assembly_plan(self) -> Dict[str, Any]:
        """获取组装计划
        
        Returns:
            Dict[str, Any]: 组装计划
        """
        pass