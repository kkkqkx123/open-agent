"""配置系统模块"""

from .config_system import IConfigSystem, ConfigSystem
from .config_merger import IConfigMerger, ConfigMerger
from .config_validator import IConfigValidator, ConfigValidator, ValidationResult
from .config_validator_tool import ConfigValidatorTool
from .enhanced_validator import (
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
from .error_recovery import (
    ConfigErrorRecovery,
    ConfigBackupManager,
    ConfigValidatorWithRecovery,
)
from .config_callback_manager import (
    ConfigCallbackManager,
    ConfigChangeContext,
    CallbackPriority,
    register_config_callback,
    unregister_config_callback,
    trigger_config_callbacks,
)

__all__ = [
    "IConfigSystem",
    "ConfigSystem",
    "IConfigMerger",
    "ConfigMerger",
    "IConfigValidator",
    "ConfigValidator",
    "ValidationResult",
    "ConfigValidatorTool",
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
]
