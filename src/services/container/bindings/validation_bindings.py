"""验证模块依赖注入绑定

配置验证相关服务的依赖注入绑定。
"""

from typing import Optional

from src.interfaces.config import (
    IConfigValidator,
    IEnhancedConfigValidator,
    IConfigValidationService
)
from src.interfaces.dependency_injection import (
    container,
    Lifecycle,
    get_logger
)
from src.core.config.validation import (
    ValidationRuleRegistry,
    GlobalConfigBusinessValidator,
    LLMConfigBusinessValidator,
    ToolConfigBusinessValidator,
    TokenCounterConfigBusinessValidator
)
from src.infrastructure.config.validation import ConfigValidator
from src.infrastructure.cache.core.cache_manager import CacheManager
from src.services.config.validation import (
    ConfigValidationService,
    ValidationOrchestrator,
    ValidatorFactory,
    ValidatorRegistry
)


logger = get_logger(__name__)


def register_validation_services(cache_manager: Optional[CacheManager] = None) -> None:
    """注册验证相关服务
    
    Args:
        cache_manager: 缓存管理器
    """
    try:
        # 注册验证规则注册表
        container.register(
            ValidationRuleRegistry,
            ValidationRuleRegistry,
            lifecycle=Lifecycle.SINGLETON
        )
        
        # 注册业务验证器
        container.register(
            GlobalConfigBusinessValidator,
            GlobalConfigBusinessValidator,
            lifecycle=Lifecycle.SINGLETON
        )
        
        container.register(
            LLMConfigBusinessValidator,
            LLMConfigBusinessValidator,
            lifecycle=Lifecycle.SINGLETON
        )
        
        container.register(
            ToolConfigBusinessValidator,
            ToolConfigBusinessValidator,
            lifecycle=Lifecycle.SINGLETON
        )
        
        container.register(
            TokenCounterConfigBusinessValidator,
            TokenCounterConfigBusinessValidator,
            lifecycle=Lifecycle.SINGLETON
        )
        
        # 注册基础验证器
        container.register(
            ConfigValidator,
            ConfigValidator,
            dependencies=[cache_manager] if cache_manager else [],
            lifecycle=Lifecycle.SINGLETON
        )
        
        # 注册验证器工厂
        container.register(
            ValidatorFactory,
            ValidatorFactory,
            dependencies=[cache_manager] if cache_manager else [],
            lifecycle=Lifecycle.SINGLETON
        )
        
        # 注册验证器注册表
        container.register(
            ValidatorRegistry,
            ValidatorRegistry,
            lifecycle=Lifecycle.SINGLETON
        )
        
        # 注册验证编排器
        container.register(
            ValidationOrchestrator,
            ValidationOrchestrator,
            dependencies=[
                ValidationRuleRegistry,
                ConfigValidator,
                "business_validators"  # 将通过工厂方法提供
            ],
            lifecycle=Lifecycle.SINGLETON,
            factory=create_validation_orchestrator
        )
        
        # 注册配置验证服务
        container.register(
            ConfigValidationService,
            ConfigValidationService,
            factory=create_config_validation_service,
            lifecycle=Lifecycle.SINGLETON
        )
        
        # 注册为接口
        container.register(
            IConfigValidator,
            ConfigValidationService,
            lifecycle=Lifecycle.SINGLETON
        )
        
        container.register(
            IEnhancedConfigValidator,
            ConfigValidationService,
            lifecycle=Lifecycle.SINGLETON
        )
        
        container.register(
            IConfigValidationService,
            ValidationOrchestrator,
            lifecycle=Lifecycle.SINGLETON
        )
        
        logger.info("验证服务依赖注入绑定完成")
        
    except Exception as e:
        logger.error(f"注册验证服务失败: {e}")
        raise


def create_validation_orchestrator(
    rule_registry: ValidationRuleRegistry,
    base_validator: ConfigValidator
) -> ValidationOrchestrator:
    """创建验证编排器
    
    Args:
        rule_registry: 规则注册表
        base_validator: 基础验证器
        
    Returns:
        验证编排器实例
    """
    # 获取业务验证器
    business_validators = {
        "global": container.resolve(GlobalConfigBusinessValidator),
        "llm": container.resolve(LLMConfigBusinessValidator),
        "tool": container.resolve(ToolConfigBusinessValidator),
        "token_counter": container.resolve(TokenCounterConfigBusinessValidator)
    }
    
    return ValidationOrchestrator(
        rule_registry=rule_registry,
        base_validator=base_validator,
        business_validators=business_validators
    )


def create_config_validation_service() -> ConfigValidationService:
    """创建配置验证服务
    
    Returns:
        配置验证服务实例
    """
    # 获取依赖
    rule_registry = container.resolve(ValidationRuleRegistry)
    base_validator = container.resolve(ConfigValidator)
    
    return ConfigValidationService(
        rule_registry=rule_registry,
        business_validator=None,  # 将根据配置类型动态设置
        base_validator=base_validator,
        config_type="generic"
    )


def register_config_type_validators() -> None:
    """注册特定配置类型的验证器"""
    
    # 注册全局配置验证器
    container.register(
        "global_config_validator",
        ConfigValidationService,
        factory=lambda: create_config_type_validator("global"),
        lifecycle=Lifecycle.SINGLETON
    )
    
    # 注册LLM配置验证器
    container.register(
        "llm_config_validator",
        ConfigValidationService,
        factory=lambda: create_config_type_validator("llm"),
        lifecycle=Lifecycle.SINGLETON
    )
    
    # 注册工具配置验证器
    container.register(
        "tool_config_validator",
        ConfigValidationService,
        factory=lambda: create_config_type_validator("tool"),
        lifecycle=Lifecycle.SINGLETON
    )
    
    # 注册Token计数器配置验证器
    container.register(
        "token_counter_config_validator",
        ConfigValidationService,
        factory=lambda: create_config_type_validator("token_counter"),
        lifecycle=Lifecycle.SINGLETON
    )
    
    logger.info("配置类型验证器注册完成")


def create_config_type_validator(config_type: str) -> ConfigValidationService:
    """创建特定配置类型的验证器
    
    Args:
        config_type: 配置类型
        
    Returns:
        配置验证服务实例
    """
    # 获取依赖
    rule_registry = container.resolve(ValidationRuleRegistry)
    base_validator = container.resolve(ConfigValidator)
    
    # 获取对应的业务验证器
    business_validator = None
    if config_type == "global":
        business_validator = container.resolve(GlobalConfigBusinessValidator)
    elif config_type == "llm":
        business_validator = container.resolve(LLMConfigBusinessValidator)
    elif config_type == "tool":
        business_validator = container.resolve(ToolConfigBusinessValidator)
    elif config_type == "token_counter":
        business_validator = container.resolve(TokenCounterConfigBusinessValidator)
    
    return ConfigValidationService(
        rule_registry=rule_registry,
        business_validator=business_validator,
        base_validator=base_validator,
        config_type=config_type
    )


def get_config_validator(config_type: str) -> IConfigValidator:
    """获取配置验证器
    
    Args:
        config_type: 配置类型
        
    Returns:
        配置验证器实例
    """
    validator_key = f"{config_type}_config_validator"
    
    try:
        return container.resolve(validator_key)
    except KeyError:
        # 如果没有注册特定类型的验证器，返回通用验证器
        logger.warning(f"没有找到配置类型 {config_type} 的验证器，使用通用验证器")
        return container.resolve(ConfigValidationService)


def setup_validation_bindings(cache_manager: Optional[CacheManager] = None) -> None:
    """设置验证模块的完整依赖注入绑定
    
    Args:
        cache_manager: 缓存管理器
    """
    register_validation_services(cache_manager)
    register_config_type_validators()
    
    logger.info("验证模块依赖注入绑定设置完成")