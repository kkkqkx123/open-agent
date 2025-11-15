"""提示词管理DI配置

负责注册提示词管理相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.domain.prompts.interfaces import IPromptTemplateManager, IPromptInjector
from src.domain.prompts.template_manager import PromptTemplateManager
from src.domain.prompts.injector import PromptInjector

logger = logging.getLogger(__name__)


class PromptConfigRegistration:
    """提示词管理注册类
    
    负责注册提示词管理相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册提示词管理服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册提示词管理服务")
        
        # 注册提示词模板管理器
        container.register_factory(
            IPromptTemplateManager,
            lambda: PromptTemplateManager(
                config_loader=container.get(
                    "src.infrastructure.config.loader.file_config_loader.IConfigLoader"
                ) if container.has_service(
                    "src.infrastructure.config.loader.file_config_loader.IConfigLoader"
                ) else None
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册提示词注入器
        container.register(
            IPromptInjector,
            PromptInjector,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("提示词管理服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "prompt_template_manager": IPromptTemplateManager,
            "prompt_injector": IPromptInjector,
        }