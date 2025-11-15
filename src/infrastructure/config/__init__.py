"""配置系统模块"""

from .config_system import IConfigSystem, ConfigSystem
from .config_factory import ConfigFactory
from .config_service_factory import create_config_system, create_minimal_config_system
from .config_cache import ConfigCache
from .config_loader import ConfigLoader
from .utils.config_operations import ConfigOperations
from ..utils.dict_merger import IDictMerger as IConfigMerger, DictMerger as ConfigMerger
from .processor.validator import IConfigValidator, ConfigValidator, ValidationResult
from .processor.enhanced_validator import (
    EnhancedConfigValidator,
    create_enhanced_config_validator,
    ValidationLevel,
    ValidationSeverity,
    ValidationRule,
    EnhancedValidationResult,
    ValidationReport,
    FixSuggestion,
    ConfigFixer
)
from .service.error_recovery import (
    ConfigErrorRecovery,
    ConfigBackupManager,
    ConfigValidatorWithRecovery,
)
from .service.callback_manager import (
    ConfigCallbackManager,
    ConfigChangeContext,
    CallbackPriority,
    register_config_callback,
    unregister_config_callback,
    trigger_config_callbacks,
)
from .interfaces import IConfigLoader, IConfigInheritanceHandler
from .utils.inheritance_handler import ConfigInheritanceHandler
from .utils.inheritance_handler import IConfigInheritanceHandler
from .utils.inheritance_handler import InheritanceConfigLoader
from .loader.yaml_loader import YamlConfigLoader
from ..utils.file_watcher import FileWatcher
from .migration.migration import (
    MigrationResult,
    ConfigMigrationTool,
    migrate_workflow_config,
    migrate_tool_config,
    migrate_llm_config,
    migrate_graph_config,
)

__all__ = [
    "IConfigSystem",
    "ConfigSystem",
    "ConfigFactory",
    "create_config_system",
    "create_minimal_config_system",
    "ConfigCache",
    "ConfigLoader",
    "ConfigOperations",
    "IConfigMerger",
    "ConfigMerger",
    "IConfigValidator",
    "ConfigValidator",
    "ValidationResult",
    "EnhancedConfigValidator",
    "create_enhanced_config_validator",
    "ValidationLevel",
    "ValidationSeverity",
    "ValidationRule",
    "EnhancedValidationResult",
    "ValidationReport",
    "FixSuggestion",
    "ConfigFixer",
    "ConfigErrorRecovery",
    "ConfigBackupManager",
    "ConfigValidatorWithRecovery",
    "ConfigCallbackManager",
    "ConfigChangeContext",
    "CallbackPriority",
    "register_config_callback",
    "unregister_config_callback",
    "trigger_config_callbacks",
    # 新增的配置相关
    "IConfigLoader",
    "IConfigInheritanceHandler",
    "ConfigInheritanceHandler",
    "InheritanceConfigLoader",
    "YamlConfigLoader",
    "FileWatcher",
    "MigrationResult",
    "ConfigMigrationTool",
    "migrate_workflow_config",
    "migrate_tool_config",
    "migrate_llm_config",
    "migrate_graph_config",
]