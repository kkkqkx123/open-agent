"""配置加载器DI配置

负责注册配置系统相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.infrastructure.config.interfaces import IConfigLoader, IConfigSystem
from src.infrastructure.config.loader.file_config_loader import FileConfigLoader
from src.infrastructure.utils.dict_merger import IDictMerger as IConfigMerger, DictMerger
from src.infrastructure.config.processor.validator import IConfigValidator, ConfigValidator
from src.infrastructure.config.config_system import ConfigSystem

logger = logging.getLogger(__name__)


class ConfigLoaderRegistration:
    """配置加载器注册类
    
    负责注册配置系统相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册配置服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册配置系统服务")
        
        # 注册配置加载器
        container.register_factory(
            IConfigLoader,
            lambda: FileConfigLoader(),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册配置合并器
        container.register_factory(
            IConfigMerger,
            lambda: DictMerger(),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册配置验证器
        container.register_factory(
            IConfigValidator,
            lambda: ConfigValidator(),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册配置系统
        container.register_factory(
            IConfigSystem,
            lambda: ConfigSystem(
                config_loader=container.get(IConfigLoader),
                config_merger=container.get(IConfigMerger),
                config_validator=container.get(IConfigValidator)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("配置系统服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "config_loader": IConfigLoader,
            "config_merger": IConfigMerger,
            "config_validator": IConfigValidator,
            "config_system": IConfigSystem,
        }