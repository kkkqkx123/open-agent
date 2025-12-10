"""验证模块统一导出

提供完整的验证功能，包括验证框架、规则和具体验证器。
"""

# 导入验证框架核心类
from .framework import (
    ValidationLevel,
    ValidationSeverity,
    ValidationResult,
    EnhancedValidationResult,
    ValidationReport
)

# 导入验证规则
from .rules import (
    ValidationRule,
    RequiredFieldRule,
    ValueRangeRule,
    RegexPatternRule
)

# 导入基础验证器
from .base_validator import BaseConfigValidator

# 导入具体配置验证器
from .config_validator import ConfigValidator, generate_cache_key

# 导入兼容性类型
from .config_validator import UtilsConfigValidationResult

# 注意：FixSuggestion 和 ConfigFixer 现在在基础设施层
# 需要通过依赖注入使用，不应在core层直接导入

__all__ = [
    # 验证框架
    "ValidationLevel",
    "ValidationSeverity", 
    "ValidationResult",
    "EnhancedValidationResult",
    "ValidationReport",
    
    # 验证规则
    "ValidationRule",
    "RequiredFieldRule",
    "ValueRangeRule", 
    "RegexPatternRule",
    
    # 验证器
    "BaseConfigValidator",
    "ConfigValidator",
    
    # 工具函数
    "generate_cache_key",
    
    # 兼容性类型
    "UtilsConfigValidationResult"
]