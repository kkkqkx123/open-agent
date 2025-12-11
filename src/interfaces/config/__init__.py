"""配置相关接口统一导出

提供完整的配置系统接口定义，包括加载器、处理器、验证器、管理器、映射器和异常定义。
"""

# 导入加载器相关接口
from .loader import IConfigLoader, IConfigInheritanceHandler, IHotReloadManager

# 导入处理器相关接口
from .processor import IConfigProcessor

# 导入验证器相关接口
from .validation import (
    IConfigValidator,
    IConfigValidationService,
    IValidationRule,
    IValidationRuleRegistry,
    IBusinessValidator,
    IValidationReport,
    ValidationContext,
    ValidationLevel,
    ValidationSeverity,
    IFixSuggestion
)

# 导入模式相关接口
from .schema import IConfigSchema, ISchemaRegistry, ISchemaGenerator

# 导入实现相关接口
from .impl import IConfigImpl

# 导入管理器相关接口
from .manager import IConfigManager, IConfigManager, IConfigManagerFactory

# 导入映射器相关接口
from .mapper import (
    IConfigMapper,
    IModuleConfigService,
    IModuleConfigRegistry,
    IConfigMapperRegistry,
    ICrossModuleResolver,
    IModuleConfigLoader,
    IUnifiedConfigService,
    IConfigChangeListener,
    IConfigWatcher,
    IConfigMonitor,
    IConfigVersionManager,
    IConfigStorage,
    ModuleConfig,
    ModuleDependency,
    ConfigChangeEvent,
    ConfigVersion
)

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
from ...infrastructure.validation.result import ValidationResult

__all__ = [
    # 加载器接口
    "IConfigLoader",
    "IConfigInheritanceHandler",
    "IHotReloadManager",
    
    # 处理器接口
    "IConfigProcessor",
    
    # 验证器接口
    "IConfigValidator",
    "IConfigValidationService",
    "IValidationRule",
    "IValidationRuleRegistry",
    "IBusinessValidator",
    "IValidationReport",
    "ValidationContext",
    "ValidationLevel",
    "ValidationSeverity",
    "IFixSuggestion",
    
    # 模式接口
    "IConfigSchema",
    "ISchemaRegistry",
    "ISchemaGenerator",
    
    # 实现接口
    "IConfigImpl",
    
    # 管理器接口
    "IConfigManager",
    "IConfigManager",
    "IConfigManagerFactory",
    
    # 映射器接口
    "IConfigMapper",
    "IModuleConfigService",
    "IModuleConfigRegistry",
    "IConfigMapperRegistry",
    "ICrossModuleResolver",
    "IModuleConfigLoader",
    "IUnifiedConfigService",
    "IConfigChangeListener",
    "IConfigWatcher",
    "IConfigMonitor",
    "IConfigVersionManager",
    "IConfigStorage",
    
    # 数据类
    "ModuleConfig",
    "ModuleDependency",
    "ConfigChangeEvent",
    "ConfigVersion",
    
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