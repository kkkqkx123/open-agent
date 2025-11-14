"""基础设施模块

提供依赖注入、配置加载、环境检查等基础功能。
"""

from .container import IDependencyContainer, DependencyContainer, get_global_container
from .config.loader.yaml_loader import IConfigLoader, YamlConfigLoader
from .environment import IEnvironmentChecker, EnvironmentChecker
from .env_check_command import EnvironmentCheckCommand
from .architecture_check import ArchitectureChecker
from .test_container import TestContainer
from .exceptions import (
    InfrastructureError,
    ServiceNotRegisteredError,
    ServiceCreationError,
    CircularDependencyError,
    ConfigurationError,
    EnvironmentCheckError,
    ArchitectureViolationError,
)
from .infrastructure_types import CheckResult, ServiceLifetime

# 导入配置系统相关服务
from .config import (
    IConfigSystem,
    ConfigSystem,
    IConfigMerger,
    ConfigMerger,
    IConfigValidator,
    ConfigValidator,
    ValidationResult,
    ConfigErrorRecovery,
    ConfigBackupManager,
    ConfigValidatorWithRecovery,
    ConfigCallbackManager,
    ConfigChangeContext,
    CallbackPriority,
    register_config_callback,
    unregister_config_callback,
    trigger_config_callbacks,
)

# 导入配置模型
from .config.models.config import (
    BaseConfigModel,
    WorkflowConfigModel,
    ToolConfigModel,
    LLMConfigModel,
    GraphConfigModel,
    ConfigType,
    ConfigMetadata,
    ConfigInheritance,
    ValidationRule,
    create_config_model,
    validate_config_with_model,
)

__all__ = [
    "IDependencyContainer",
    "DependencyContainer",
    "get_global_container",
    "IConfigLoader",
    "YamlConfigLoader",
    "IEnvironmentChecker",
    "EnvironmentChecker",
    "EnvironmentCheckCommand",
    "ArchitectureChecker",
    "TestContainer",
    "InfrastructureError",
    "ServiceNotRegisteredError",
    "ServiceCreationError",
    "CircularDependencyError",
    "ConfigurationError",
    "EnvironmentCheckError",
    "ArchitectureViolationError",
    "CheckResult",
    "ServiceLifetime",
    # 配置系统相关
    "IConfigSystem",
    "ConfigSystem",
    "IConfigMerger",
    "ConfigMerger",
    "IConfigValidator",
    "ConfigValidator",
    "ValidationResult",
    "ConfigErrorRecovery",
    "ConfigBackupManager",
    "ConfigValidatorWithRecovery",
    "ConfigCallbackManager",
    "ConfigChangeContext",
    "CallbackPriority",
    "register_config_callback",
    "unregister_config_callback",
    "trigger_config_callbacks",
    # 配置模型相关
    "BaseConfigModel",
    "WorkflowConfigModel",
    
    "ToolConfigModel",
    "LLMConfigModel",
    "GraphConfigModel",
    "ConfigType",
    "ConfigMetadata",
    "ConfigInheritance",
    "ValidationRule",
    "create_config_model",
    "validate_config_with_model",
]