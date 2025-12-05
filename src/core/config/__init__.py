"""
配置系统 - 新架构下的简化配置管理
基于优化分析，采用平衡方案设计
"""

from .config_manager import ConfigManager, ConfigRegistry
from .models import (
    BaseConfig,
    LLMConfig,
    ToolConfig,
    ToolSetConfig,
    GlobalConfig,
    ConfigType,
    ConfigMetadata,
    ConfigInheritance,
    ValidationRule,
)
from src.interfaces.configuration import (
    ConfigError,
    ConfigurationLoadError as ConfigNotFoundError,
    ConfigurationValidationError as ConfigValidationError,
    ConfigurationInheritanceError as ConfigInheritanceError
)

__all__ = [
    "ConfigManager",
    "ConfigRegistry",
    "BaseConfig",
    "LLMConfig", 
    "ToolConfig",
    "ToolSetConfig",
    "GlobalConfig",
    "ConfigType",
    "ConfigMetadata",
    "ConfigInheritance",
    "ValidationRule",
    "ConfigError",
    "ConfigNotFoundError", 
    "ConfigValidationError",
    "ConfigInheritanceError"
]