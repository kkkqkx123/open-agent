"""
配置管理接口模块

提供配置系统的统一接口定义，包括配置加载、处理、验证和热重载等功能。
"""

from .interfaces import (
    IConfigLoader,
    IConfigInheritanceHandler,
    IConfigProcessor,
    IHotReloadManager,
    IUnifiedConfigManager,
    IConfigManagerFactory,
    IConfigValidator,
)

__all__ = [
    # 核心配置接口
    "IConfigLoader",
    "IConfigInheritanceHandler",
    
    # 配置处理接口
    "IConfigProcessor",
    "IHotReloadManager",
    
    # 统一配置管理
    "IUnifiedConfigManager",
    "IConfigManagerFactory",
    
    # 配置验证
    "IConfigValidator",
]