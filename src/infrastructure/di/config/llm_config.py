"""LLM服务DI配置

负责注册LLM客户端相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.config.loader.file_config_loader import IConfigLoader
from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.infrastructure.llm.config_manager import LLMConfigManager

logger = logging.getLogger(__name__)


class LLMConfigRegistration:
    """LLM服务注册类
    
    负责注册LLM客户端相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册LLM服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册LLM系统服务")
        
        # 注册LLM配置管理器
        def create_llm_config_manager() -> LLMConfigManager:
            config_loader = None
            if container.has_service(IConfigLoader):
                config_loader = container.get(IConfigLoader)
            return LLMConfigManager(config_loader=config_loader)
        
        container.register_factory(
            LLMConfigManager,
            create_llm_config_manager,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("LLM系统服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "llm_config_manager": LLMConfigManager,
        }