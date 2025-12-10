"""
配置系统 - 新架构下的简化配置管理
基于优化分析，采用平衡方案设计
"""

from .config_manager import ConfigManager
from .models import (
    BaseConfig,
    LLMConfig,
    ToolConfig,
    ToolSetConfig,
    GlobalConfig,
)
from .processor import (
    ConfigProcessorChain,
)
from src.infrastructure.config.processor import (
    InheritanceProcessor,
    EnvironmentProcessor,
    ReferenceProcessor,
)
from .validation import (
    ValidationResult,
    ValidationLevel,
    ValidationSeverity,
    BaseConfigValidator,
)
from src.interfaces.configuration import (
    ConfigError,
    ConfigurationLoadError as ConfigNotFoundError,
    ConfigurationValidationError as ConfigValidationError,
)

__all__ = [
    "ConfigManager",
    "BaseConfig",
    "LLMConfig",
    "ToolConfig",
    "ToolSetConfig",
    "GlobalConfig",
    "ConfigProcessorChain",
    "InheritanceProcessor",
    "EnvironmentProcessor",
    "ReferenceProcessor",
    "ValidationResult",
    "ValidationLevel",
    "ValidationSeverity",
    "BaseConfigValidator",
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigValidationError",
]