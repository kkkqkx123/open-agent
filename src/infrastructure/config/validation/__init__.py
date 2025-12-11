"""验证模块统一导出

提供基础设施层的验证功能，包括验证框架、基础验证器和工具函数。
不包含业务逻辑，业务逻辑由核心层提供。
"""

# 导入验证框架核心类
from .framework import (
    ValidationReport,
    FrameworkValidationResult
)

# 从接口层导入验证级别和严重性
from src.interfaces.config.validation import (
    ValidationLevel,
    ValidationSeverity,
    IFixSuggestion
)

# 导入验证规则
from .rules import (
    ValidationRule,
    RequiredFieldRule,
    ValueRangeRule,
    RegexPatternRule
)

# 导入基础验证器
from .base_validator import (
    BaseConfigValidator,
    GenericConfigValidator,
    IValidationContext
)

# 导入具体配置验证器
from .config_validator import (
    ConfigValidator,
    generate_cache_key,
    ICacheManager
)

# 导入兼容性类型
from .config_validator import UtilsConfigValidationResult

# 导入基础设施层的验证结果
from src.infrastructure.validation.result import ValidationResult

# 导入配置修复相关类
from src.infrastructure.config.fixer import ConfigFixer, FixSuggestion

__all__ = [
    # 验证框架
    "ValidationLevel",
    "ValidationSeverity",
    "ValidationReport",
    "FrameworkValidationResult",
    "IFixSuggestion",
    
    # 验证规则
    "ValidationRule",
    "RequiredFieldRule",
    "ValueRangeRule",
    "RegexPatternRule",
    
    # 验证器
    "BaseConfigValidator",
    "GenericConfigValidator",
    "ConfigValidator",
    
    # 接口
    "IValidationContext",
    "ICacheManager",
    
    # 工具函数
    "generate_cache_key",
    
    # 兼容性类型
    "UtilsConfigValidationResult",
    
    # 配置修复
    "ConfigFixer",
    "FixSuggestion",
    
    # 接口层类型
    "ValidationResult"
]