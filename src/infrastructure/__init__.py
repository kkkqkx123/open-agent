"""基础设施模块

提供依赖注入、配置加载、环境检查等基础功能。
"""

from .container import IDependencyContainer, DependencyContainer, get_global_container
from .config.config_loader import IConfigLoader, YamlConfigLoader
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
    ConfigValidatorTool,
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

# 导入配置接口
from .config.config_interfaces import (
    IConfigLoader,
    IConfigInheritanceHandler,
)

# 导入配置继承和迁移功能
from .config.config_inheritance import (
    IConfigInheritanceHandler,
    ConfigInheritanceHandler,
    InheritanceConfigLoader,
)

from .config.models.config_models import (
    BaseConfigModel,
    WorkflowConfigModel,
    AgentConfigModel,
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

from .config.config_migration import (
    MigrationResult,
    ConfigMigrationTool,
    migrate_workflow_config,
    migrate_agent_config,
    migrate_tool_config,
    migrate_llm_config,
    migrate_graph_config,
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
    "ConfigValidatorTool",
    "ConfigErrorRecovery",
    "ConfigBackupManager",
    "ConfigValidatorWithRecovery",
    "ConfigCallbackManager",
    "ConfigChangeContext",
    "CallbackPriority",
    "register_config_callback",
    "unregister_config_callback",
    "trigger_config_callbacks",
    # 配置接口相关
    "IConfigInheritanceHandler",
]