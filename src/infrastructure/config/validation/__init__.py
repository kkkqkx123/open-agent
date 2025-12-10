"""验证模块统一导出

提供完整的验证功能，包括验证框架、规则和具体验证器。
"""

# 导入验证框架核心类
from .framework import (
    ValidationLevel,
    ValidationSeverity,
    ValidationResult,
    ValidationReport,
    EnhancedValidationResult
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

# 导入修复相关类
from ..fixer import FixSuggestion, ConfigFixer

__all__ = [
    # 验证框架
    "ValidationLevel",
    "ValidationSeverity",
    "ValidationResult",
    "ValidationReport",
    "EnhancedValidationResult",
    
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
    "UtilsConfigValidationResult",
    
    # 修复相关
    "FixSuggestion",
    "ConfigFixer"
]