"""Config依赖注入便利层

使用通用依赖注入框架提供简洁的Config服务获取方式。
"""

from typing import Optional

from src.core.config.config_manager import ConfigManager
from src.core.config.config_manager_factory import ConfigManagerFactory
from src.core.config.processor.config_processor_chain import (
    ConfigProcessorChain,
    InheritanceProcessor,
    EnvironmentVariableProcessor,
    ReferenceProcessor,
)
from src.core.config.adapter_factory import AdapterFactory
from src.interfaces.config.interfaces import IConfigValidator
from src.interfaces.configuration import ValidationResult
from src.services.container.injection.injection_base import get_global_injection_registry
from src.services.container.injection.injection_decorators import injectable


class _StubConfigManager(ConfigManager):
    """临时 ConfigManager 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def get(self, key: str, default=None):
        """获取配置值"""
        return default
    
    def set(self, key: str, value):
        """设置配置值"""
        pass
    
    def has(self, key: str) -> bool:
        """检查配置是否存在"""
        return False


class _StubConfigManagerFactory(ConfigManagerFactory):
    """临时 ConfigManagerFactory 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def create_manager(self, config_path: str) -> ConfigManager:
        """创建配置管理器"""
        return _StubConfigManager()


class _StubConfigValidator(IConfigValidator):
    """临时 ConfigValidator 实现（用于极端情况）"""
    
    def validate(self, config: dict) -> ValidationResult:
        """验证配置"""
        return ValidationResult(is_valid=True)
    
    def supports_module_type(self, module_type: str) -> bool:
        """检查是否支持指定模块类型"""
        return True


class _StubConfigProcessorChain(ConfigProcessorChain):
    """临时 ConfigProcessorChain 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def process(self, config: dict, config_path: str = "") -> dict:
        """处理配置"""
        return config


class _StubInheritanceProcessor(InheritanceProcessor):
    """临时 InheritanceProcessor 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def process(self, config: dict, config_path: str = "") -> dict:
        """处理继承"""
        return config


class _StubEnvironmentVariableProcessor(EnvironmentVariableProcessor):
    """临时 EnvironmentVariableProcessor 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def process(self, config: dict, config_path: str = "") -> dict:
        """处理环境变量"""
        return config


class _StubReferenceProcessor(ReferenceProcessor):
    """临时 ReferenceProcessor 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def process(self, config: dict, config_path: str = "") -> dict:
        """处理引用"""
        return config


class _StubAdapterFactory(AdapterFactory):
    """临时 AdapterFactory 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def create_adapter(self, module_type: str):
        """创建适配器"""
        # 返回一个虚拟的适配器对象
        from src.core.config.adapters import BaseConfigAdapter
        
        class _StubAdapter(BaseConfigAdapter):
            def __init__(self, base_manager=None):
                self.base_manager = base_manager
            
            def load_config(self, config_path: str, **kwargs) -> dict:
                """加载配置"""
                return {}
            
            def validate_config(self, config: dict) -> bool:
                """验证配置"""
                return True
        
        return _StubAdapter(None)


def _create_fallback_config_manager() -> ConfigManager:
    """创建fallback config manager"""
    return _StubConfigManager()


def _create_fallback_config_manager_factory() -> ConfigManagerFactory:
    """创建fallback config manager factory"""
    return _StubConfigManagerFactory()


def _create_fallback_config_validator() -> IConfigValidator:
    """创建fallback config validator"""
    return _StubConfigValidator()


def _create_fallback_config_processor_chain() -> ConfigProcessorChain:
    """创建fallback config processor chain"""
    return _StubConfigProcessorChain()


def _create_fallback_inheritance_processor() -> InheritanceProcessor:
    """创建fallback inheritance processor"""
    return _StubInheritanceProcessor()


def _create_fallback_environment_variable_processor() -> EnvironmentVariableProcessor:
    """创建fallback environment variable processor"""
    return _StubEnvironmentVariableProcessor()


def _create_fallback_reference_processor() -> ReferenceProcessor:
    """创建fallback reference processor"""
    return _StubReferenceProcessor()


def _create_fallback_adapter_factory() -> AdapterFactory:
    """创建fallback adapter factory"""
    return _StubAdapterFactory()


# 注册Config注入
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


# 设置实例的函数
def set_config_manager_instance(config_manager: ConfigManager) -> None:
    """在应用启动时设置全局 ConfigManager 实例
    
    Args:
        config_manager: ConfigManager 实例
    """
    _config_manager_injection.set_instance(config_manager)


def set_config_manager_factory_instance(config_manager_factory: ConfigManagerFactory) -> None:
    """在应用启动时设置全局 ConfigManagerFactory 实例
    
    Args:
        config_manager_factory: ConfigManagerFactory 实例
    """
    _config_manager_factory_injection.set_instance(config_manager_factory)


def set_config_validator_instance(config_validator: IConfigValidator) -> None:
    """在应用启动时设置全局 ConfigValidator 实例
    
    Args:
        config_validator: IConfigValidator 实例
    """
    _config_validator_injection.set_instance(config_validator)


def set_config_processor_chain_instance(config_processor_chain: ConfigProcessorChain) -> None:
    """在应用启动时设置全局 ConfigProcessorChain 实例
    
    Args:
        config_processor_chain: ConfigProcessorChain 实例
    """
    _config_processor_chain_injection.set_instance(config_processor_chain)


def set_inheritance_processor_instance(inheritance_processor: InheritanceProcessor) -> None:
    """在应用启动时设置全局 InheritanceProcessor 实例
    
    Args:
        inheritance_processor: InheritanceProcessor 实例
    """
    _inheritance_processor_injection.set_instance(inheritance_processor)


def set_environment_variable_processor_instance(environment_variable_processor: EnvironmentVariableProcessor) -> None:
    """在应用启动时设置全局 EnvironmentVariableProcessor 实例
    
    Args:
        environment_variable_processor: EnvironmentVariableProcessor 实例
    """
    _environment_variable_processor_injection.set_instance(environment_variable_processor)


def set_reference_processor_instance(reference_processor: ReferenceProcessor) -> None:
    """在应用启动时设置全局 ReferenceProcessor 实例
    
    Args:
        reference_processor: ReferenceProcessor 实例
    """
    _reference_processor_injection.set_instance(reference_processor)


def set_adapter_factory_instance(adapter_factory: AdapterFactory) -> None:
    """在应用启动时设置全局 AdapterFactory 实例
    
    Args:
        adapter_factory: AdapterFactory 实例
    """
    _adapter_factory_injection.set_instance(adapter_factory)


# 清除实例的函数
def clear_config_manager_instance() -> None:
    """清除全局 ConfigManager 实例"""
    _config_manager_injection.clear_instance()


def clear_config_manager_factory_instance() -> None:
    """清除全局 ConfigManagerFactory 实例"""
    _config_manager_factory_injection.clear_instance()


def clear_config_validator_instance() -> None:
    """清除全局 ConfigValidator 实例"""
    _config_validator_injection.clear_instance()


def clear_config_processor_chain_instance() -> None:
    """清除全局 ConfigProcessorChain 实例"""
    _config_processor_chain_injection.clear_instance()


def clear_inheritance_processor_instance() -> None:
    """清除全局 InheritanceProcessor 实例"""
    _inheritance_processor_injection.clear_instance()


def clear_environment_variable_processor_instance() -> None:
    """清除全局 EnvironmentVariableProcessor 实例"""
    _environment_variable_processor_injection.clear_instance()


def clear_reference_processor_instance() -> None:
    """清除全局 ReferenceProcessor 实例"""
    _reference_processor_injection.clear_instance()


def clear_adapter_factory_instance() -> None:
    """清除全局 AdapterFactory 实例"""
    _adapter_factory_injection.clear_instance()


# 获取状态的函数
def get_config_manager_status() -> dict:
    """获取配置管理器注入状态"""
    return _config_manager_injection.get_status()


def get_config_manager_factory_status() -> dict:
    """获取配置管理器工厂注入状态"""
    return _config_manager_factory_injection.get_status()


def get_config_validator_status() -> dict:
    """获取配置验证器注入状态"""
    return _config_validator_injection.get_status()


def get_config_processor_chain_status() -> dict:
    """获取配置处理器链注入状态"""
    return _config_processor_chain_injection.get_status()


def get_inheritance_processor_status() -> dict:
    """获取继承处理器注入状态"""
    return _inheritance_processor_injection.get_status()


def get_environment_variable_processor_status() -> dict:
    """获取环境变量处理器注入状态"""
    return _environment_variable_processor_injection.get_status()


def get_reference_processor_status() -> dict:
    """获取引用处理器注入状态"""
    return _reference_processor_injection.get_status()


def get_adapter_factory_status() -> dict:
    """获取适配器工厂注入状态"""
    return _adapter_factory_injection.get_status()


# 导出的公共接口
__all__ = [
    "get_config_manager",
    "get_config_manager_factory",
    "get_config_validator",
    "get_config_processor_chain",
    "get_inheritance_processor",
    "get_environment_variable_processor",
    "get_reference_processor",
    "get_adapter_factory",
    "set_config_manager_instance",
    "set_config_manager_factory_instance",
    "set_config_validator_instance",
    "set_config_processor_chain_instance",
    "set_inheritance_processor_instance",
    "set_environment_variable_processor_instance",
    "set_reference_processor_instance",
    "set_adapter_factory_instance",
    "clear_config_manager_instance",
    "clear_config_manager_factory_instance",
    "clear_config_validator_instance",
    "clear_config_processor_chain_instance",
    "clear_inheritance_processor_instance",
    "clear_environment_variable_processor_instance",
    "clear_reference_processor_instance",
    "clear_adapter_factory_instance",
    "get_config_manager_status",
    "get_config_manager_factory_status",
    "get_config_validator_status",
    "get_config_processor_chain_status",
    "get_inheritance_processor_status",
    "get_environment_variable_processor_status",
    "get_reference_processor_status",
    "get_adapter_factory_status",
]