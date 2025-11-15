"""领域层DI配置

提供领域层服务的统一配置入口。
"""

import logging
from typing import Dict, Any, Type

from src.infrastructure.container_interfaces import IDependencyContainer
from .domain_module import DomainModule

logger = logging.getLogger(__name__)


class DomainConfig:
    """领域层DI配置
    
    负责配置领域层服务，包括状态管理、工作流核心、线程核心等。
    """
    
    @staticmethod
    def configure(container: IDependencyContainer, environment: str = "default") -> None:
        """配置领域服务
        
        Args:
            container: 依赖注入容器
            environment: 环境名称
        """
        logger.info(f"开始配置领域层服务，环境: {environment}")
        
        # 创建并配置领域模块
        domain_module = DomainModule()
        
        # 注册基础服务
        domain_module.register_services(container)
        
        # 注册环境特定服务
        domain_module.register_environment_services(container, environment)
        
        logger.info("领域层服务配置完成")
    
    @staticmethod
    def validate_configuration(container: IDependencyContainer) -> Dict[str, Any]:
        """验证领域层配置
        
        Args:
            container: 依赖注入容器
            
        Returns:
            验证结果
        """
        logger.info("验证领域层配置")
        
        domain_module = DomainModule()
        validation_result = domain_module.validate_configuration(container)
        
        if validation_result["valid"]:
            logger.info("领域层配置验证通过")
        else:
            logger.error(f"领域层配置验证失败: {validation_result['errors']}")
        
        return validation_result
    
    @staticmethod
    def get_required_services() -> Dict[str, Type]:
        """获取必需的服务列表
        
        Returns:
            必需的服务类型字典
        """
        domain_module = DomainModule()
        return domain_module.get_registered_services()
    
    @staticmethod
    def get_service_dependencies() -> Dict[str, list]:
        """获取服务依赖关系
        
        Returns:
            服务依赖关系字典
        """
        # 这里可以返回领域层服务之间的依赖关系
        return {
            "state_collaboration_manager": ["state_manager"],
            "workflow_config_manager": ["config_loader"],
            "thread_manager": ["thread_repository", "checkpoint_manager"],
            "tool_manager": ["tool_registry", "tool_executor"],
            "prompt_template_manager": ["config_loader"],
            "session_repository": ["session_store"],
            "checkpoint_repository": ["checkpoint_store"],
            "history_repository": ["history_store"],
        }