"""DI模块接口定义

定义标准化的服务模块接口，确保各层DI配置的一致性。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Type

from src.infrastructure.container_interfaces import IDependencyContainer


class IServiceModule(ABC):
    """服务模块接口
    
    定义标准化的服务注册接口，确保各层DI配置的一致性。
    """
    
    @abstractmethod
    def register_services(self, container: IDependencyContainer) -> None:
        """注册基础服务
        
        Args:
            container: 依赖注入容器
        """
        pass
    
    @abstractmethod
    def register_environment_services(self, 
                                    container: IDependencyContainer, 
                                    environment: str) -> None:
        """注册环境特定服务
        
        Args:
            container: 依赖注入容器
            environment: 环境名称
        """
        pass
    
    @abstractmethod
    def get_module_name(self) -> str:
        """获取模块名称
        
        Returns:
            模块名称
        """
        pass
    
    @abstractmethod
    def get_registered_services(self) -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        pass
    
    def get_dependencies(self) -> list:
        """获取模块依赖
        
        Returns:
            依赖的模块名称列表
        """
        return []
    
    def validate_configuration(self, container: IDependencyContainer) -> Dict[str, Any]:
        """验证配置
        
        Args:
            container: 依赖注入容器
            
        Returns:
            验证结果
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 检查必需服务是否已注册
        required_services = self.get_registered_services()
        for service_name, service_type in required_services.items():
            if not container.has_service(service_type):
                result["errors"].append(f"缺少必需服务: {service_name}")
                result["valid"] = False
        
        return result