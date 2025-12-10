"""配置相关接口统一导出

提供完整的配置系统接口定义，包括加载器、处理器、验证器、管理器和异常定义。
"""

# 导入加载器相关接口
from .loader import IConfigLoader, IConfigInheritanceHandler, IHotReloadManager

# 导入处理器相关接口
from .processor import IConfigProcessor

# 导入验证器相关接口
from .validator import IConfigValidator, ConfigValidationResult, ValidationSeverity

# 导入模式相关接口
from .schema import IConfigSchema, ISchemaRegistry, ISchemaGenerator

# 导入提供者相关接口
from .provider import IConfigProvider

# 导入管理器相关接口
from .manager import IConfigManager, IUnifiedConfigManager, IConfigManagerFactory

# 导入异常定义
from .exceptions import (
    ConfigError,
    ConfigurationValidationError,
    ConfigurationLoadError,
    ConfigurationEnvironmentError,
    ConfigurationParseError,
    ConfigurationMergeError,
    ConfigurationSchemaError,
    ConfigurationInheritanceError
)

# 为了向后兼容，保留原有的导入路径
from ..common_domain import ValidationResult

__all__ = [
    # 加载器接口
    "IConfigLoader",
    "IConfigInheritanceHandler", 
    "IHotReloadManager",
    
    # 处理器接口
    "IConfigProcessor",
    
    # 验证器接口
    "IConfigValidator",
    "ConfigValidationResult",
    "ValidationSeverity",
    
    # 模式接口
    "IConfigSchema",
    "ISchemaRegistry",
    "ISchemaGenerator",
    
    # 提供者接口
    "IConfigProvider",
    
    # 管理器接口
    "IConfigManager",
    "IUnifiedConfigManager",
    "IConfigManagerFactory",
    
    # 异常定义
    "ConfigError",
    "ConfigurationValidationError",
    "ConfigurationLoadError",
    "ConfigurationEnvironmentError",
    "ConfigurationParseError",
    "ConfigurationMergeError",
    "ConfigurationSchemaError",
    "ConfigurationInheritanceError",
    
    # 向后兼容
    "ValidationResult"
]