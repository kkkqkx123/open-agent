"""配置工厂，负责创建配置系统组件"""

from typing import Optional
from .config_service_factory import (
    ConfigServiceFactory,
    create_config_system,
    create_minimal_config_system
)
from .config_system import IConfigSystem, ConfigSystem


# 为了兼容性，保留ConfigFactory类
class ConfigFactory:
    """配置工厂 - 保持向后兼容性"""
    
    @staticmethod
    def create_config_system(base_path: str = "configs") -> IConfigSystem:
        """创建配置系统"""
        return create_config_system(base_path)
    
    @staticmethod
    def create_minimal_config_system(base_path: str = "configs") -> IConfigSystem:
        """创建最小配置系统（仅核心功能）"""
        return create_minimal_config_system(base_path)


# 为了兼容性，保留便捷函数
def create_config_system_legacy(base_path: str = "configs") -> IConfigSystem:
    """创建配置系统的便捷函数（已弃用，请使用config_service_factory中的版本）"""
    return ConfigFactory.create_config_system(base_path)