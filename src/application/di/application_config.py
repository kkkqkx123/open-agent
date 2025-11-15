"""应用层DI配置

提供应用层服务的统一配置入口。
"""

import logging
from typing import Dict, Any, Type

from src.infrastructure.container_interfaces import IDependencyContainer
from .application_module import ApplicationModule

logger = logging.getLogger(__name__)


class ApplicationConfig:
    """应用层DI配置
    
    负责配置应用层服务，包括会话管理、工作流管理、线程服务等。
    """
    
    @staticmethod
    def configure(container: IDependencyContainer, environment: str = "default") -> None:
        """配置应用服务
        
        Args:
            container: 依赖注入容器
            environment: 环境名称
        """
        logger.info(f"开始配置应用层服务，环境: {environment}")
        
        # 创建并配置应用模块
        application_module = ApplicationModule()
        
        # 注册基础服务
        application_module.register_services(container)
        
        # 注册环境特定服务
        application_module.register_environment_services(container, environment)
        
        logger.info("应用层服务配置完成")
    
    @staticmethod
    def validate_configuration(container: IDependencyContainer) -> Dict[str, Any]:
        """验证应用层配置
        
        Args:
            container: 依赖注入容器
            
        Returns:
            验证结果
        """
        logger.info("验证应用层配置")
        
        application_module = ApplicationModule()
        validation_result = application_module.validate_configuration(container)
        
        if validation_result["valid"]:
            logger.info("应用层配置验证通过")
        else:
            logger.error(f"应用层配置验证失败: {validation_result['errors']}")
        
        return validation_result
    
    @staticmethod
    def get_required_services() -> Dict[str, Type]:
        """获取必需的服务列表
        
        Returns:
            必需的服务类型字典
        """
        application_module = ApplicationModule()
        return application_module.get_registered_services()
    
    @staticmethod
    def get_service_dependencies() -> Dict[str, list]:
        """获取服务依赖关系
        
        Returns:
            服务依赖关系字典
        """
        # 这里可以返回应用层服务之间的依赖关系
        return {
            "session_manager": ["thread_service", "session_store", "git_manager"],
            "workflow_manager": ["workflow_factory", "workflow_config_manager"],
            "thread_service": ["thread_repository", "thread_domain_service", "checkpoint_manager"],
            "replay_manager": ["history_manager", "session_manager"],
            "checkpoint_manager": ["checkpoint_repository"],
            "history_manager": ["history_repository"],
        }