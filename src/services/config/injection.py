"""配置服务依赖注入便利层

使用通用依赖注入框架提供简洁的配置服务获取方式。
"""

from typing import Optional
from unittest.mock import Mock

from src.interfaces.config.interfaces import IConfigValidator
from ...core.config.config_manager import ConfigManager, DefaultConfigValidator
from ...core.config.config_manager_factory import ConfigManagerFactory
from ...core.config.processor.config_processor_chain import (
    ConfigProcessorChain,
    InheritanceProcessor,
    EnvironmentVariableProcessor,
    ReferenceProcessor
)
from ...core.config.adapter_factory import AdapterFactory
from src.services.container.injection.injection_base import get_global_injection_registry
from src.services.container.injection.injection_decorators import injectable


def _create_fallback_config_manager() -> ConfigManager:
    """创建fallback配置管理器"""
    return Mock(spec=ConfigManager)


def _create_fallback_config_manager_factory() -> ConfigManagerFactory:
    """创建fallback配置管理器工厂"""
    return Mock(spec=ConfigManagerFactory)


def _create_fallback_config_validator() -> IConfigValidator:
    """创建fallback配置验证器"""
    return DefaultConfigValidator()


def _create_fallback_config_processor_chain() -> ConfigProcessorChain:
    """创建fallback配置处理器链"""
    return Mock(spec=ConfigProcessorChain)


def _create_fallback_inheritance_processor() -> InheritanceProcessor:
    """创建fallback继承处理器"""
    return Mock(spec=InheritanceProcessor)


def _create_fallback_environment_variable_processor() -> EnvironmentVariableProcessor:
    """创建fallback环境变量处理器"""
    return Mock(spec=EnvironmentVariableProcessor)


def _create_fallback_reference_processor() -> ReferenceProcessor:
    """创建fallback引用处理器"""
    return Mock(spec=ReferenceProcessor)


def _create_fallback_adapter_factory() -> AdapterFactory:
    """创建fallback适配器工厂"""
    return Mock(spec=AdapterFactory)


# 注册配置服务注入
_config_manager_injection = get_global_injection_registry().register(
    ConfigManager, _create_fallback_config_manager
)

_config_manager_factory_injection = get_global_injection_registry().register(
    ConfigManagerFactory, _create_fallback_config_manager_factory
)

_config_validator_injection = get_global_injection_registry().register(
    IConfigValidator, _create_fallback_config_validator
)

_config_processor_chain_injection = get_global_injection_registry().register(
    ConfigProcessorChain, _create_fallback_config_processor_chain
)

_inheritance_processor_injection = get_global_injection_registry().register(
    InheritanceProcessor, _create_fallback_inheritance_processor
)

_environment_variable_processor_injection = get_global_injection_registry().register(
    EnvironmentVariableProcessor, _create_fallback_environment_variable_processor
)

_reference_processor_injection = get_global_injection_registry().register(
    ReferenceProcessor, _create_fallback_reference_processor
)

_adapter_factory_injection = get_global_injection_registry().register(
    AdapterFactory, _create_fallback_adapter_factory
)


@injectable(ConfigManager, _create_fallback_config_manager)
def get_config_manager() -> ConfigManager:
    """获取配置管理器实例
    
    Returns:
        ConfigManager: 配置管理器实例
    """
    return _config_manager_injection.get_instance()


@injectable(ConfigManagerFactory, _create_fallback_config_manager_factory)
def get_config_manager_factory() -> ConfigManagerFactory:
    """获取配置管理器工厂实例
    
    Returns:
        ConfigManagerFactory: 配置管理器工厂实例
    """
    return _config_manager_factory_injection.get_instance()


@injectable(IConfigValidator, _create_fallback_config_validator)
def get_config_validator() -> IConfigValidator:
    """获取配置验证器实例
    
    Returns:
        IConfigValidator: 配置验证器实例
    """
    return _config_validator_injection.get_instance()


@injectable(ConfigProcessorChain, _create_fallback_config_processor_chain)
def get_config_processor_chain() -> ConfigProcessorChain:
    """获取配置处理器链实例
    
    Returns:
        ConfigProcessorChain: 配置处理器链实例
    """
    return _config_processor_chain_injection.get_instance()


@injectable(InheritanceProcessor, _create_fallback_inheritance_processor)
def get_inheritance_processor() -> InheritanceProcessor:
    """获取继承处理器实例
    
    Returns:
        InheritanceProcessor: 继承处理器实例
    """
    return _inheritance_processor_injection.get_instance()


@injectable(EnvironmentVariableProcessor, _create_fallback_environment_variable_processor)
def get_environment_variable_processor() -> EnvironmentVariableProcessor:
    """获取环境变量处理器实例
    
    Returns:
        EnvironmentVariableProcessor: 环境变量处理器实例
    """
    return _environment_variable_processor_injection.get_instance()


@injectable(ReferenceProcessor, _create_fallback_reference_processor)
def get_reference_processor() -> ReferenceProcessor:
    """获取引用处理器实例
    
    Returns:
        ReferenceProcessor: 引用处理器实例
    """
    return _reference_processor_injection.get_instance()


@injectable(AdapterFactory, _create_fallback_adapter_factory)
def get_adapter_factory() -> AdapterFactory:
    """获取适配器工厂实例
    
    Returns:
        AdapterFactory: 适配器工厂实例
    """
    return _adapter_factory_injection.get_instance()


# 设置实例的便捷函数
def set_config_manager_instance(manager: ConfigManager) -> None:
    """设置配置管理器实例"""
    _config_manager_injection.set_instance(manager)


def set_config_manager_factory_instance(factory: ConfigManagerFactory) -> None:
    """设置配置管理器工厂实例"""
    _config_manager_factory_injection.set_instance(factory)


def set_config_validator_instance(validator: IConfigValidator) -> None:
    """设置配置验证器实例"""
    _config_validator_injection.set_instance(validator)


def set_config_processor_chain_instance(chain: ConfigProcessorChain) -> None:
    """设置配置处理器链实例"""
    _config_processor_chain_injection.set_instance(chain)


def set_inheritance_processor_instance(processor: InheritanceProcessor) -> None:
    """设置继承处理器实例"""
    _inheritance_processor_injection.set_instance(processor)


def set_environment_variable_processor_instance(processor: EnvironmentVariableProcessor) -> None:
    """设置环境变量处理器实例"""
    _environment_variable_processor_injection.set_instance(processor)


def set_reference_processor_instance(processor: ReferenceProcessor) -> None:
    """设置引用处理器实例"""
    _reference_processor_injection.set_instance(processor)


def set_adapter_factory_instance(factory: AdapterFactory) -> None:
    """设置适配器工厂实例"""
    _adapter_factory_injection.set_instance(factory)


# 清除实例的便捷函数（主要用于测试）
def clear_config_manager_instance() -> None:
    """清除配置管理器实例"""
    _config_manager_injection.clear_instance()


def clear_config_manager_factory_instance() -> None:
    """清除配置管理器工厂实例"""
    _config_manager_factory_injection.clear_instance()


def clear_config_validator_instance() -> None:
    """清除配置验证器实例"""
    _config_validator_injection.clear_instance()


def clear_config_processor_chain_instance() -> None:
    """清除配置处理器链实例"""
    _config_processor_chain_injection.clear_instance()


def clear_inheritance_processor_instance() -> None:
    """清除继承处理器实例"""
    _inheritance_processor_injection.clear_instance()


def clear_environment_variable_processor_instance() -> None:
    """清除环境变量处理器实例"""
    _environment_variable_processor_injection.clear_instance()


def clear_reference_processor_instance() -> None:
    """清除引用处理器实例"""
    _reference_processor_injection.clear_instance()


def clear_adapter_factory_instance() -> None:
    """清除适配器工厂实例"""
    _adapter_factory_injection.clear_instance()


# 获取状态的便捷函数
def get_config_manager_status() -> dict:
    """获取配置管理器状态"""
    return _config_manager_injection.get_status()


def get_config_manager_factory_status() -> dict:
    """获取配置管理器工厂状态"""
    return _config_manager_factory_injection.get_status()


def get_config_validator_status() -> dict:
    """获取配置验证器状态"""
    return _config_validator_injection.get_status()


def get_config_processor_chain_status() -> dict:
    """获取配置处理器链状态"""
    return _config_processor_chain_injection.get_status()


def get_inheritance_processor_status() -> dict:
    """获取继承处理器状态"""
    return _inheritance_processor_injection.get_status()


def get_environment_variable_processor_status() -> dict:
    """获取环境变量处理器状态"""
    return _environment_variable_processor_injection.get_status()


def get_reference_processor_status() -> dict:
    """获取引用处理器状态"""
    return _reference_processor_injection.get_status()


def get_adapter_factory_status() -> dict:
    """获取适配器工厂状态"""
    return _adapter_factory_injection.get_status()


# 导出的公共接口
__all__ = [
    # 获取函数
    "get_config_manager",
    "get_config_manager_factory",
    "get_config_validator",
    "get_config_processor_chain",
    "get_inheritance_processor",
    "get_environment_variable_processor",
    "get_reference_processor",
    "get_adapter_factory",
    
    # 设置函数
    "set_config_manager_instance",
    "set_config_manager_factory_instance",
    "set_config_validator_instance",
    "set_config_processor_chain_instance",
    "set_inheritance_processor_instance",
    "set_environment_variable_processor_instance",
    "set_reference_processor_instance",
    "set_adapter_factory_instance",
    
    # 清除函数
    "clear_config_manager_instance",
    "clear_config_manager_factory_instance",
    "clear_config_validator_instance",
    "clear_config_processor_chain_instance",
    "clear_inheritance_processor_instance",
    "clear_environment_variable_processor_instance",
    "clear_reference_processor_instance",
    "clear_adapter_factory_instance",
    
    # 状态函数
    "get_config_manager_status",
    "get_config_manager_factory_status",
    "get_config_validator_status",
    "get_config_processor_chain_status",
    "get_inheritance_processor_status",
    "get_environment_variable_processor_status",
    "get_reference_processor_status",
    "get_adapter_factory_status",
]