"""验证器注册模块

提供配置验证器的注册和发现机制。
"""

from typing import Dict, List, Optional, Type, Any, Callable
import logging
from dataclasses import dataclass

from src.interfaces.config import (
    IConfigValidator,
    IEnhancedConfigValidator,
    IValidationRule,
    IBusinessValidator
)
from src.interfaces.dependency_injection import get_logger
from .factory import ValidatorFactory


logger = get_logger(__name__)


@dataclass
class ValidatorRegistration:
    """验证器注册信息"""
    
    validator_class: Type[IConfigValidator]
    config_types: List[str]
    priority: int = 100
    enabled: bool = True
    factory: Optional[Callable[[], IConfigValidator]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ValidatorRegistry:
    """验证器注册表
    
    管理所有配置验证器的注册、发现和创建。
    """
    
    def __init__(self):
        """初始化验证器注册表"""
        self._validators: Dict[str, List[ValidatorRegistration]] = {}
        self._global_validators: List[ValidatorRegistration] = []
        self._rule_registrations: Dict[str, List[Type[IValidationRule]]] = {}
        self._business_validator_registrations: Dict[str, Type[IBusinessValidator]] = {}
        self._factory: Optional[ValidatorFactory] = None
        
        logger.info("验证器注册表初始化完成")
    
    def set_factory(self, factory: ValidatorFactory) -> None:
        """设置验证器工厂
        
        Args:
            factory: 验证器工厂
        """
        self._factory = factory
        logger.info("验证器工厂已设置")
    
    def register_validator(self,
                         validator_class: Type[IConfigValidator],
                         config_types: List[str],
                         priority: int = 100,
                         enabled: bool = True,
                         factory: Optional[Callable[[], IConfigValidator]] = None,
                         **metadata) -> None:
        """注册验证器
        
        Args:
            validator_class: 验证器类
            config_types: 支持的配置类型列表
            priority: 优先级
            enabled: 是否启用
            factory: 工厂函数
            **metadata: 元数据
        """
        registration = ValidatorRegistration(
            validator_class=validator_class,
            config_types=config_types,
            priority=priority,
            enabled=enabled,
            factory=factory,
            metadata=metadata
        )
        
        # 如果支持所有类型，注册为全局验证器
        if "all" in config_types:
            self._global_validators.append(registration)
        else:
            # 按类型注册
            for config_type in config_types:
                if config_type not in self._validators:
                    self._validators[config_type] = []
                self._validators[config_type].append(registration)
        
        # 按优先级排序
        if "all" in config_types:
            self._global_validators.sort(key=lambda r: r.priority)
        else:
            for config_type in config_types:
                if config_type in self._validators:
                    self._validators[config_type].sort(key=lambda r: r.priority)
        
        logger.info(f"已注册验证器: {validator_class.__name__} for {config_types}")
    
    def register_validation_rule(self,
                                rule_class: Type[IValidationRule],
                                config_type: str) -> None:
        """注册验证规则
        
        Args:
            rule_class: 验证规则类
            config_type: 配置类型
        """
        if config_type not in self._rule_registrations:
            self._rule_registrations[config_type] = []
        
        self._rule_registrations[config_type].append(rule_class)
        logger.info(f"已注册验证规则: {rule_class.__name__} for {config_type}")
    
    def register_business_validator(self,
                                   validator_class: Type[IBusinessValidator],
                                   config_type: str) -> None:
        """注册业务验证器
        
        Args:
            validator_class: 业务验证器类
            config_type: 配置类型
        """
        self._business_validator_registrations[config_type] = validator_class
        logger.info(f"已注册业务验证器: {validator_class.__name__} for {config_type}")
    
    def get_validators(self, config_type: str) -> List[ValidatorRegistration]:
        """获取指定配置类型的验证器
        
        Args:
            config_type: 配置类型
            
        Returns:
            验证器注册信息列表
        """
        validators = []
        
        # 添加全局验证器
        validators.extend([r for r in self._global_validators if r.enabled])
        
        # 添加特定类型的验证器
        if config_type in self._validators:
            validators.extend([r for r in self._validators[config_type] if r.enabled])
        
        return validators
    
    def get_validation_rules(self, config_type: str) -> List[Type[IValidationRule]]:
        """获取指定配置类型的验证规则
        
        Args:
            config_type: 配置类型
            
        Returns:
            验证规则类列表
        """
        return self._rule_registrations.get(config_type, []).copy()
    
    def get_business_validator(self, config_type: str) -> Optional[Type[IBusinessValidator]]:
        """获取指定配置类型的业务验证器
        
        Args:
            config_type: 配置类型
            
        Returns:
            业务验证器类或None
        """
        return self._business_validator_registrations.get(config_type)
    
    def create_validator(self, config_type: str, **kwargs) -> Optional[IConfigValidator]:
        """创建验证器实例
        
        Args:
            config_type: 配置类型
            **kwargs: 创建参数
            
        Returns:
            验证器实例或None
        """
        # 优先使用工厂创建
        if self._factory:
            try:
                return self._factory.create_config_validator(config_type, **kwargs)
            except Exception as e:
                logger.warning(f"使用工厂创建验证器失败: {e}")
        
        # 使用注册的验证器
        validators = self.get_validators(config_type)
        if not validators:
            logger.warning(f"没有找到配置类型 {config_type} 的验证器")
            return None
        
        # 使用优先级最高的验证器
        registration = validators[0]
        
        try:
            if registration.factory:
                return registration.factory()
            else:
                return registration.validator_class()
        except Exception as e:
            logger.error(f"创建验证器失败: {e}")
            return None
    
    def get_supported_config_types(self) -> List[str]:
        """获取支持的配置类型
        
        Returns:
            配置类型列表
        """
        types = set()
        
        # 从验证器注册中获取
        types.update(self._validators.keys())
        
        # 从规则注册中获取
        types.update(self._rule_registrations.keys())
        
        # 从业务验证器注册中获取
        types.update(self._business_validator_registrations.keys())
        
        return list(types)
    
    def enable_validator(self, validator_class: Type[IConfigValidator]) -> bool:
        """启用验证器
        
        Args:
            validator_class: 验证器类
            
        Returns:
            是否成功启用
        """
        found = False
        
        # 检查全局验证器
        for registration in self._global_validators:
            if registration.validator_class == validator_class:
                registration.enabled = True
                found = True
        
        # 检查特定类型验证器
        for validators in self._validators.values():
            for registration in validators:
                if registration.validator_class == validator_class:
                    registration.enabled = True
                    found = True
        
        if found:
            logger.info(f"已启用验证器: {validator_class.__name__}")
        
        return found
    
    def disable_validator(self, validator_class: Type[IConfigValidator]) -> bool:
        """禁用验证器
        
        Args:
            validator_class: 验证器类
            
        Returns:
            是否成功禁用
        """
        found = False
        
        # 检查全局验证器
        for registration in self._global_validators:
            if registration.validator_class == validator_class:
                registration.enabled = False
                found = True
        
        # 检查特定类型验证器
        for validators in self._validators.values():
            for registration in validators:
                if registration.validator_class == validator_class:
                    registration.enabled = False
                    found = True
        
        if found:
            logger.info(f"已禁用验证器: {validator_class.__name__}")
        
        return found
    
    def unregister_validator(self, validator_class: Type[IConfigValidator]) -> bool:
        """注销验证器
        
        Args:
            validator_class: 验证器类
            
        Returns:
            是否成功注销
        """
        found = False
        
        # 从全局验证器中移除
        original_length = len(self._global_validators)
        self._global_validators = [r for r in self._global_validators if r.validator_class != validator_class]
        if len(self._global_validators) < original_length:
            found = True
        
        # 从特定类型验证器中移除
        for config_type, validators in self._validators.items():
            original_length = len(validators)
            self._validators[config_type] = [r for r in validators if r.validator_class != validator_class]
            if len(self._validators[config_type]) < original_length:
                found = True
        
        if found:
            logger.info(f"已注销验证器: {validator_class.__name__}")
        
        return found
    
    def get_registry_info(self) -> Dict[str, Any]:
        """获取注册表信息
        
        Returns:
            注册表信息
        """
        info = {
            "supported_config_types": self.get_supported_config_types(),
            "validator_count": sum(len(validators) for validators in self._validators.values()) + len(self._global_validators),
            "rule_count": sum(len(rules) for rules in self._rule_registrations.values()),
            "business_validator_count": len(self._business_validator_registrations),
            "validators_by_type": {},
            "rules_by_type": {},
            "business_validators_by_type": {}
        }
        
        # 按类型统计验证器
        for config_type, validators in self._validators.items():
            info["validators_by_type"][config_type] = [
                {
                    "class": reg.validator_class.__name__,
                    "priority": reg.priority,
                    "enabled": reg.enabled,
                    "metadata": reg.metadata
                }
                for reg in validators
            ]
        
        # 按类型统计规则
        for config_type, rules in self._rule_registrations.items():
            info["rules_by_type"][config_type] = [rule.__name__ for rule in rules]
        
        # 按类型统计业务验证器
        for config_type, validator_class in self._business_validator_registrations.items():
            info["business_validators_by_type"][config_type] = validator_class.__name__
        
        return info
    
    def clear_registrations(self, config_type: Optional[str] = None) -> None:
        """清除注册信息
        
        Args:
            config_type: 配置类型，None表示清除所有
        """
        if config_type:
            # 清除特定类型的注册
            if config_type in self._validators:
                del self._validators[config_type]
            if config_type in self._rule_registrations:
                del self._rule_registrations[config_type]
            if config_type in self._business_validator_registrations:
                del self._business_validator_registrations[config_type]
            
            logger.info(f"已清除配置类型 {config_type} 的注册信息")
        else:
            # 清除所有注册
            self._validators.clear()
            self._global_validators.clear()
            self._rule_registrations.clear()
            self._business_validator_registrations.clear()
            
            logger.info("已清除所有注册信息")


# 全局注册表实例
_global_registry: Optional[ValidatorRegistry] = None


def get_validator_registry() -> ValidatorRegistry:
    """获取全局验证器注册表
    
    Returns:
        验证器注册表实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ValidatorRegistry()
    return _global_registry


def register_validator(validator_class: Type[IConfigValidator],
                      config_types: List[str],
                      priority: int = 100,
                      enabled: bool = True,
                      **metadata) -> None:
    """注册验证器的便捷函数
    
    Args:
        validator_class: 验证器类
        config_types: 支持的配置类型列表
        priority: 优先级
        enabled: 是否启用
        **metadata: 元数据
    """
    registry = get_validator_registry()
    registry.register_validator(validator_class, config_types, priority, enabled, **metadata)