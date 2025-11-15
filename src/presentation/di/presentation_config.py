"""表示层DI配置

提供表示层服务的统一配置入口。
"""

import logging
from typing import Dict, Any, Type

from src.infrastructure.container_interfaces import IDependencyContainer
from .presentation_module import PresentationModule

logger = logging.getLogger(__name__)


class PresentationConfig:
    """表示层DI配置
    
    负责配置表示层服务，包括API服务、UI服务、CLI命令等。
    """
    
    @staticmethod
    def configure(container: IDependencyContainer, environment: str = "default") -> None:
        """配置表示服务
        
        Args:
            container: 依赖注入容器
            environment: 环境名称
        """
        logger.info(f"开始配置表示层服务，环境: {environment}")
        
        # 创建并配置表示模块
        presentation_module = PresentationModule()
        
        # 注册基础服务
        presentation_module.register_services(container)
        
        # 注册环境特定服务
        presentation_module.register_environment_services(container, environment)
        
        logger.info("表示层服务配置完成")
    
    @staticmethod
    def validate_configuration(container: IDependencyContainer) -> Dict[str, Any]:
        """验证表示层配置
        
        Args:
            container: 依赖注入容器
            
        Returns:
            验证结果
        """
        logger.info("验证表示层配置")
        
        presentation_module = PresentationModule()
        validation_result = presentation_module.validate_configuration(container)
        
        if validation_result["valid"]:
            logger.info("表示层配置验证通过")
        else:
            logger.error(f"表示层配置验证失败: {validation_result['errors']}")
        
        return validation_result
    
    @staticmethod
    def get_required_services() -> Dict[str, Type]:
        """获取必需的服务列表
        
        Returns:
            必需的服务类型字典
        """
        presentation_module = PresentationModule()
        return presentation_module.get_registered_services()
    
    @staticmethod
    def get_service_dependencies() -> Dict[str, list]:
        """获取服务依赖关系
        
        Returns:
            服务依赖关系字典
        """
        # 这里可以返回表示层服务之间的依赖关系
        return {
            "session_router": ["session_manager"],
            "thread_router": ["thread_service"],
            "workflow_router": ["workflow_manager"],
            "session_component": ["session_manager"],
            "thread_component": ["thread_service"],
            "workflow_component": ["workflow_manager"],
            "run_command": ["session_manager", "workflow_manager"],
            "config_command": ["config_system"],
        }