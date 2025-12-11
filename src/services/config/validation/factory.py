"""验证器工厂

负责创建和配置各种验证器实例。
"""

from typing import Dict, Any, Optional, Type, List
import logging

from src.interfaces.config import IConfigValidator
from src.interfaces.dependency_injection import get_logger
from src.core.config.validation import (
    ValidationRuleRegistry,
    GlobalConfigValidationRules,
    LLMConfigValidationRules,
    ToolConfigValidationRules,
    TokenCounterConfigValidationRules,
    GlobalConfigBusinessValidator,
    LLMConfigBusinessValidator,
    ToolConfigBusinessValidator,
    TokenCounterConfigBusinessValidator,
    ValidationContext
)
from src.infrastructure.config.validation import ConfigValidator
from src.infrastructure.cache.core.cache_manager import CacheManager
from src.infrastructure.cache.config.cache_config import BaseCacheConfig


logger = get_logger(__name__)


class ValidatorFactory:
    """验证器工厂
    
    负责创建和配置各种验证器实例，管理验证器的生命周期。
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """初始化验证器工厂
        
        Args:
            cache_manager: 缓存管理器
        """
        self.cache_manager = cache_manager
        self._rule_registry: Optional[ValidationRuleRegistry] = None
        self._business_validators: Dict[str, Any] = {}
        self._base_validator: Optional[ConfigValidator] = None
        
        # 初始化组件
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """初始化组件"""
        try:
            # 初始化规则注册表
            self._rule_registry = ValidationRuleRegistry()
            self._register_validation_rules()
            
            # 初始化业务验证器
            self._initialize_business_validators()
            
            # 初始化基础验证器
            self._base_validator = ConfigValidator(
                cache_manager=self.cache_manager,
                logger=logger
            )
            
            logger.info("验证器工厂初始化完成")
            
        except Exception as e:
            logger.error(f"验证器工厂初始化失败: {e}")
            raise
    
    def _register_validation_rules(self) -> None:
        """注册验证规则"""
        if not self._rule_registry:
            return
        
        # 注册全局配置验证规则
        self._rule_registry.register_rule(GlobalConfigValidationRules.LogOutputRule())
        self._rule_registry.register_rule(GlobalConfigValidationRules.SecretPatternRule())
        self._rule_registry.register_rule(GlobalConfigValidationRules.ProductionDebugRule())
        
        # 注册LLM配置验证规则
        self._rule_registry.register_rule(LLMConfigValidationRules.APIKeyRule())
        self._rule_registry.register_rule(LLMConfigValidationRules.BaseURLRule())
        self._rule_registry.register_rule(LLMConfigValidationRules.RetryConfigRule())
        self._rule_registry.register_rule(LLMConfigValidationRules.TimeoutConfigRule())
        
        # 注册工具配置验证规则
        self._rule_registry.register_rule(ToolConfigValidationRules.ToolsExistRule())
        
        # 注册Token计数器配置验证规则
        self._rule_registry.register_rule(TokenCounterConfigValidationRules.EnhancedModeRule())
        self._rule_registry.register_rule(TokenCounterConfigValidationRules.ModelNameRule())
        
        logger.info("验证规则注册完成")
    
    def _initialize_business_validators(self) -> None:
        """初始化业务验证器"""
        self._business_validators = {
            "global": GlobalConfigBusinessValidator(),
            "llm": LLMConfigBusinessValidator(),
            "tool": ToolConfigBusinessValidator(),
            "token_counter": TokenCounterConfigBusinessValidator()
        }
        
        logger.info("业务验证器初始化完成")
    
    def create_validation_context(self, 
                                config_type: str,
                                config_path: Optional[str] = None,
                                environment: str = "development",
                                strict_mode: bool = False,
                                **kwargs) -> ValidationContext:
        """创建验证上下文
        
        Args:
            config_type: 配置类型
            config_path: 配置路径
            environment: 环境
            strict_mode: 严格模式
            **kwargs: 其他参数
            
        Returns:
            验证上下文
        """
        return ValidationContext(
            config_type=config_type,
            config_path=config_path,
            environment=environment,
            strict_mode=strict_mode,
            **kwargs
        )
    
    def get_rule_registry(self) -> ValidationRuleRegistry:
        """获取规则注册表
        
        Returns:
            规则注册表
        """
        if not self._rule_registry:
            raise RuntimeError("规则注册表未初始化")
        return self._rule_registry
    
    def get_business_validator(self, config_type: str) -> Optional[Any]:
        """获取业务验证器
        
        Args:
            config_type: 配置类型
            
        Returns:
            业务验证器或None
        """
        return self._business_validators.get(config_type)
    
    def get_base_validator(self) -> ConfigValidator:
        """获取基础验证器
        
        Returns:
            基础验证器
        """
        if not self._base_validator:
            raise RuntimeError("基础验证器未初始化")
        return self._base_validator
    
    def create_config_validator(self, 
                              config_type: str,
                              enable_business_validation: bool = True,
                              enable_rule_validation: bool = True) -> IConfigValidator:
        """创建配置验证器
        
        Args:
            config_type: 配置类型
            enable_business_validation: 是否启用业务验证
            enable_rule_validation: 是否启用规则验证
            
        Returns:
            配置验证器
        """
        from .validation_service import ConfigValidationService
        
        return ConfigValidationService(
            rule_registry=self._rule_registry if enable_rule_validation else None,
            business_validator=self._business_validators.get(config_type) if enable_business_validation else None,
            base_validator=self._base_validator,
            config_type=config_type
        )
    
    def register_custom_rule(self, rule: Any) -> None:
        """注册自定义验证规则
        
        Args:
            rule: 验证规则
        """
        if self._rule_registry:
            self._rule_registry.register_rule(rule)
            logger.info(f"已注册自定义验证规则: {rule.rule_id}")
    
    def register_custom_business_validator(self, config_type: str, validator: Any) -> None:
        """注册自定义业务验证器
        
        Args:
            config_type: 配置类型
            validator: 业务验证器
        """
        self._business_validators[config_type] = validator
        logger.info(f"已注册自定义业务验证器: {config_type}")
    
    def get_supported_config_types(self) -> List[str]:
        """获取支持的配置类型
        
        Returns:
            配置类型列表
        """
        if self._rule_registry:
            return self._rule_registry.get_supported_config_types()
        return list(self._business_validators.keys())
    
    def validate_factory_health(self) -> Dict[str, Any]:
        """验证工厂健康状态
        
        Returns:
            健康状态信息
        """
        health = {
            "status": "healthy",
            "components": {},
            "issues": []
        }
        
        # 检查规则注册表
        if self._rule_registry:
            health["components"]["rule_registry"] = {
                "status": "healthy",
                "supported_types": self._rule_registry.get_supported_config_types(),
                "rule_count": sum(len(self._rule_registry.get_rules(t)) for t in self._rule_registry.get_supported_config_types())
            }
        else:
            health["components"]["rule_registry"] = {"status": "uninitialized"}
            health["issues"].append("规则注册表未初始化")
        
        # 检查业务验证器
        health["components"]["business_validators"] = {
            "status": "healthy",
            "validators": list(self._business_validators.keys())
        }
        
        # 检查基础验证器
        if self._base_validator:
            health["components"]["base_validator"] = {"status": "healthy"}
        else:
            health["components"]["base_validator"] = {"status": "uninitialized"}
            health["issues"].append("基础验证器未初始化")
        
        # 检查缓存管理器
        if self.cache_manager:
            health["components"]["cache_manager"] = {"status": "healthy"}
        else:
            health["components"]["cache_manager"] = {"status": "disabled"}
        
        # 确定整体状态
        if health["issues"]:
            health["status"] = "degraded"
        
        return health


# 默认工厂实例
_default_factory: Optional[ValidatorFactory] = None


def get_validator_factory(cache_manager: Optional[CacheManager] = None) -> ValidatorFactory:
    """获取默认验证器工厂实例
    
    Args:
        cache_manager: 缓存管理器
        
    Returns:
        验证器工厂实例
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = ValidatorFactory(cache_manager=cache_manager)
    return _default_factory


def create_validator_factory(cache_manager: Optional[CacheManager] = None) -> ValidatorFactory:
    """创建新的验证器工厂实例
    
    Args:
        cache_manager: 缓存管理器
        
    Returns:
        验证器工厂实例
    """
    return ValidatorFactory(cache_manager=cache_manager)