"""
统一配置系统 - 支持所有模块的配置管理
基于统一配置系统设计，提供模块化、可扩展的配置管理解决方案。
"""

from .config_manager import (
    ConfigManager,
    ConfigManager,  # 向后兼容
    ModuleConfigRegistry,
    ConfigMapperRegistry,
    CrossModuleResolver,
)
from .config_manager_factory import (
    CoreConfigManagerFactory,
    set_global_factory,
    get_global_factory,
    get_module_manager,
    register_module_decorator,
)
from .models import (
    BaseConfig,
    LLMConfig,
    GlobalConfig,
)
from src.infrastructure.config.impl.base_impl import ConfigProcessorChain
from src.infrastructure.config.processor import (
    InheritanceProcessor,
    ReferenceProcessor,
)
from src.infrastructure.config.validation import (
    ValidationLevel,
    ValidationSeverity,
    BaseConfigValidator,
)
from src.interfaces.config import (
    ConfigError,
    ConfigurationLoadError as ConfigNotFoundError,
    ConfigurationValidationError as ConfigValidationError,
    ModuleConfig,
    IModuleConfigRegistry,
    IConfigMapperRegistry,
    ICrossModuleResolver,
)

__all__ = [
    # 统一配置管理器
    "ConfigManager",
    "ConfigManager",  # 向后兼容
    "ModuleConfigRegistry",
    "ConfigMapperRegistry",
    "CrossModuleResolver",
    
    # 工厂和全局管理
    "CoreConfigManagerFactory",
    "set_global_factory",
    "get_global_factory",
    "get_module_manager",
    "register_module_decorator",
    
    # 配置模型
    "BaseConfig",
    "LLMConfig",
    "GlobalConfig",
    
    # 基础设施组件
    "ConfigProcessorChain",
    "InheritanceProcessor",
    "ReferenceProcessor",
    "ValidationLevel",
    "ValidationSeverity",
    "BaseConfigValidator",
    
    # 异常定义
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    
    # 接口定义
    "ModuleConfig",
    "IModuleConfigRegistry",
    "IConfigMapperRegistry",
    "ICrossModuleResolver",
]