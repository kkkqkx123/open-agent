"""基础设施层DI配置

提供基础设施层服务的统一配置入口。
"""

import logging
from typing import Dict, Any, Type

from src.infrastructure.container_interfaces import IDependencyContainer
from .infrastructure_module import InfrastructureModule

logger = logging.getLogger(__name__)


class InfrastructureConfig:
    """基础设施层DI配置
    
    负责配置基础设施层服务，包括配置系统、日志系统、存储系统等。
    """
    
    @staticmethod
    def configure(container: IDependencyContainer, environment: str = "default") -> None:
        """配置基础设施服务
        
        Args:
            container: 依赖注入容器
            environment: 环境名称
        """
        logger.info(f"开始配置基础设施层服务，环境: {environment}")
        
        # 创建并配置基础设施模块
        infrastructure_module = InfrastructureModule()
        
        # 注册基础服务
        infrastructure_module.register_services(container)
        
        # 注册环境特定服务
        infrastructure_module.register_environment_services(container, environment)
        
        logger.info("基础设施层服务配置完成")
    
    @staticmethod
    def validate_configuration(container: IDependencyContainer) -> Dict[str, Any]:
        """验证基础设施层配置
        
        Args:
            container: 依赖注入容器
            
        Returns:
            验证结果
        """
        logger.info("验证基础设施层配置")
        
        infrastructure_module = InfrastructureModule()
        validation_result = infrastructure_module.validate_configuration(container)
        
        if validation_result["valid"]:
            logger.info("基础设施层配置验证通过")
        else:
            logger.error(f"基础设施层配置验证失败: {validation_result['errors']}")
        
        return validation_result
    
    @staticmethod
    def get_required_services() -> Dict[str, Type]:
        """获取必需的服务列表
        
        Returns:
            必需的服务类型字典
        """
        infrastructure_module = InfrastructureModule()
        return infrastructure_module.get_registered_services()
    
    @staticmethod
    def get_service_dependencies() -> Dict[str, list]:
        """获取服务依赖关系
        
        Returns:
            服务依赖关系字典
        """
        # 这里可以返回基础设施层服务之间的依赖关系
        return {
            "config_system": ["config_loader", "config_merger", "config_validator"],
            "logger": ["config_system"],
            "storage_services": ["config_system"],
            "llm_client": ["config_system"],
            "tool_manager": ["config_system", "logger"],
            "performance_monitor": ["config_system"],
            "graph_builder": ["node_registry", "state_factory"],
        }