"""配置工厂，负责创建配置系统组件"""

from typing import Optional
from .config_system import IConfigSystem, ConfigSystem
from .config_service_factory import ConfigServiceFactory
from .loader.yaml_loader import YamlConfigLoader
from .processor.inheritance import ConfigInheritanceHandler
from .processor.merger import ConfigMerger
from .processor.validator import ConfigValidator
from .processor.env_resolver import EnvResolver
from .service.callback_manager import ConfigCallbackManager
from .service.error_recovery import ConfigErrorRecovery


class ConfigFactory:
    """配置工厂"""
    
    @staticmethod
    def create_config_system(base_path: str = "configs") -> IConfigSystem:
        """创建配置系统"""
        return ConfigServiceFactory.create_config_system(base_path)
    
    @staticmethod
    def create_minimal_config_system(base_path: str = "configs") -> IConfigSystem:
        """创建最小配置系统（仅核心功能）"""
        return ConfigServiceFactory.create_config_system(
            base_path=base_path,
            enable_inheritance=False,
            enable_error_recovery=False,
            enable_callback_manager=False
        )


# 为了兼容性，保留便捷函数
def create_config_system(base_path: str = "configs") -> IConfigSystem:
    """创建配置系统的便捷函数"""
    return ConfigFactory.create_config_system(base_path)