"""
配置系统 - 新架构下的简化配置管理
基于优化分析，采用平衡方案设计
"""

from .config_manager import ConfigManager
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
    ToolConfig,
    ToolSetConfig,
    GlobalConfig,
)
from src.infrastructure.config.impl.base_impl import ConfigProcessorChain
from src.infrastructure.config.processor import (
    InheritanceProcessor,
    ReferenceProcessor,
)
from src.infrastructure.config.validation import (
    ValidationResult,
    ValidationLevel,
    ValidationSeverity,
    BaseConfigValidator,
)
from src.interfaces.config import (
    ConfigError,
    ConfigurationLoadError as ConfigNotFoundError,
    ConfigurationValidationError as ConfigValidationError,
)

__all__ = [
    "ConfigManager",
    "CoreConfigManagerFactory",
    "set_global_factory",
    "get_global_factory",
    "get_module_manager",
    "register_module_decorator",
    "BaseConfig",
    "LLMConfig",
    "ToolConfig",
    "ToolSetConfig",
    "GlobalConfig",
    "ConfigProcessorChain",
    "InheritanceProcessor",
    "ReferenceProcessor",
    "ValidationResult",
    "ValidationLevel",
    "ValidationSeverity",
    "BaseConfigValidator",
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigValidationError",
]