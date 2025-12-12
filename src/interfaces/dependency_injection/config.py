"""Config依赖注入空实现

提供Config服务的空实现，避免循环依赖。
"""

from typing import Any, Optional
from pathlib import Path

from src.interfaces.config import IConfigManager, IConfigValidator, ConfigError, ConfigurationValidationError as ConfigValidationError
from src.infrastructure.config.impl.base_impl import ConfigProcessorChain
from src.infrastructure.config.processor import (
    InheritanceProcessor,
    EnvironmentProcessor,
    ReferenceProcessor,
)
from src.core.config.adapter_factory import AdapterFactory
from src.infrastructure.validation.result import ValidationResult
from src.infrastructure.config.loader import ConfigLoader


class _StubConfigManager(IConfigManager):
    """临时 ConfigManager 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def load_config(self, config_path: str, module_type: Optional[str] = None) -> dict:
        """加载配置文件"""
        return {}
    
    def load_config_with_module(self, config_path: str, module_type: str) -> dict:
        """加载模块特定配置"""
        return {}
    
    def save_config(self, config: dict, config_path: str) -> None:
        """保存配置文件"""
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return default
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值"""
        pass
    
    def validate_config(self, config: dict) -> ValidationResult:
        """验证配置"""
        return ValidationResult(is_valid=True, errors=[], warnings=[])
    
    def register_module_validator(self, module_type: str, validator: IConfigValidator) -> None:
        """注册模块特定验证器"""
        pass
    
    def get_module_config(self, module_type: str) -> dict:
        """获取模块配置"""
        return {}
    
    def reload_module_configs(self, module_type: str) -> None:
        """重新加载模块配置"""
        pass
    
    def reload_config(self, config_path: str) -> dict:
        """重新加载配置"""
        return {}
    
    def invalidate_cache(self, config_path: Optional[str] = None) -> None:
        """清除缓存"""
        pass
    
    def list_config_files(self, config_directory: str) -> list:
        """列出配置文件"""
        return []


class _StubConfigLoader(ConfigLoader):
    """临时 ConfigLoader 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    @property
    def base_path(self) -> Path:
        """获取配置基础路径"""
        return Path("configs")
    
    def load_config(self, config_path: str, config_type: Optional[str] = None) -> dict:
        """加载配置文件"""
        return {}
    
    def load(self, config_path: str) -> dict:
        """加载配置文件（简化接口）"""
        return {}
    
    def reload(self) -> None:
        """重新加载所有配置"""
        pass
    
    def watch_for_changes(self, callback: Any) -> None:
        """监听配置变化"""
        pass
    
    def stop_watching(self) -> None:
        """停止监听配置变化"""
        pass
    
    def resolve_env_vars(self, config: dict) -> dict:
        """解析环境变量"""
        return config
    
    def get_config(self, config_path: str) -> Optional[dict]:
        """获取缓存中的配置"""
        return None
    
    def save_config(self, config: dict, config_path: str, config_type: Optional[str] = None) -> None:
        """保存配置"""
        pass
    
    def list_configs(self, config_type: Optional[str] = None) -> list:
        """列出配置文件"""
        return []
    
    def validate_config_path(self, config_path: str) -> bool:
        """验证配置路径"""
        return True


class _StubConfigValidator(IConfigValidator):
    """临时 ConfigValidator 实现（用于极端情况）"""
    
    def validate(self, config: dict[str, Any]) -> ValidationResult:
        """验证配置"""
        return ValidationResult(is_valid=True, errors=[], warnings=[])
    
    def supports_module_type(self, module_type: str) -> bool:
        """检查是否支持指定模块类型"""
        return True


class _StubConfigProcessorChain(ConfigProcessorChain):
    """临时 ConfigProcessorChain 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def process(self, config: dict, config_path: str = "") -> dict:
        """处理配置"""
        return config


class _StubInheritanceProcessor(InheritanceProcessor):
    """临时 InheritanceProcessor 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def process(self, config: dict, config_path: str = "") -> dict:
        """处理继承"""
        return config


class _StubEnvironmentVariableProcessor(EnvironmentProcessor):
    """临时 EnvironmentVariableProcessor 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def process(self, config: dict, config_path: str = "") -> dict:
        """处理环境变量"""
        return config


class _StubReferenceProcessor(ReferenceProcessor):
    """临时 ReferenceProcessor 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def process(self, config: dict, config_path: str = "") -> dict:
        """处理引用"""
        return config


class _StubAdapterFactory(AdapterFactory):
    """临时 AdapterFactory 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def create_adapter(self, module_type: str) -> Any:
        """创建适配器"""
        # 返回一个虚拟的适配器对象
        from src.core.config.adapters import BaseConfigAdapter
        
        class _StubAdapter(BaseConfigAdapter):
            def __init__(self, base_manager: Optional[Any] = None) -> None:
                self.base_manager = base_manager
            
            def load_config(self, config_path: str, **kwargs: Any) -> dict:
                """加载配置"""
                return {}
            
            def validate_config(self, config: dict) -> bool:
                """验证配置"""
                return True
        
        return _StubAdapter(None)


# 全局实例
_global_config_loader: Optional[ConfigLoader] = None
_global_config_manager: Optional[IConfigManager] = None
_global_config_validator: Optional[IConfigValidator] = None
_global_config_processor_chain: Optional[ConfigProcessorChain] = None
_global_inheritance_processor: Optional[InheritanceProcessor] = None
_global_environment_variable_processor: Optional[EnvironmentProcessor] = None
_global_reference_processor: Optional[ReferenceProcessor] = None
_global_adapter_factory: Optional[AdapterFactory] = None


def get_config_loader() -> ConfigLoader:
    """获取配置加载器实例"""
    global _global_config_loader
    if _global_config_loader is not None:
        return _global_config_loader
    return _StubConfigLoader()


def get_config_manager() -> IConfigManager:
    """获取配置管理器实例"""
    global _global_config_manager
    if _global_config_manager is not None:
        return _global_config_manager
    return _StubConfigManager()


def get_config_validator() -> IConfigValidator:
    """获取配置验证器实例"""
    global _global_config_validator
    if _global_config_validator is not None:
        return _global_config_validator
    return _StubConfigValidator()


def get_config_processor_chain() -> ConfigProcessorChain:
    """获取配置处理器链实例"""
    global _global_config_processor_chain
    if _global_config_processor_chain is not None:
        return _global_config_processor_chain
    return _StubConfigProcessorChain()


def get_inheritance_processor() -> InheritanceProcessor:
    """获取继承处理器实例"""
    global _global_inheritance_processor
    if _global_inheritance_processor is not None:
        return _global_inheritance_processor
    return _StubInheritanceProcessor()


def get_environment_variable_processor() -> EnvironmentProcessor:
    """获取环境变量处理器实例"""
    global _global_environment_variable_processor
    if _global_environment_variable_processor is not None:
        return _global_environment_variable_processor
    return _StubEnvironmentVariableProcessor()


def get_reference_processor() -> ReferenceProcessor:
    """获取引用处理器实例"""
    global _global_reference_processor
    if _global_reference_processor is not None:
        return _global_reference_processor
    return _StubReferenceProcessor()


def get_adapter_factory() -> AdapterFactory:
    """获取适配器工厂实例"""
    global _global_adapter_factory
    if _global_adapter_factory is not None:
        return _global_adapter_factory
    return _StubAdapterFactory()


def set_config_loader_instance(config_loader: ConfigLoader) -> None:
    """设置全局配置加载器实例"""
    global _global_config_loader
    _global_config_loader = config_loader


def set_config_manager_instance(config_manager: IConfigManager) -> None:
    """设置全局配置管理器实例"""
    global _global_config_manager
    _global_config_manager = config_manager


def set_config_validator_instance(config_validator: IConfigValidator) -> None:
    """设置全局配置验证器实例"""
    global _global_config_validator
    _global_config_validator = config_validator


def set_config_processor_chain_instance(config_processor_chain: ConfigProcessorChain) -> None:
    """设置全局配置处理器链实例"""
    global _global_config_processor_chain
    _global_config_processor_chain = config_processor_chain


def set_inheritance_processor_instance(inheritance_processor: InheritanceProcessor) -> None:
    """设置全局继承处理器实例"""
    global _global_inheritance_processor
    _global_inheritance_processor = inheritance_processor


def set_environment_variable_processor_instance(environment_variable_processor: EnvironmentProcessor) -> None:
    """设置全局环境变量处理器实例"""
    global _global_environment_variable_processor
    _global_environment_variable_processor = environment_variable_processor


def set_reference_processor_instance(reference_processor: ReferenceProcessor) -> None:
    """设置全局引用处理器实例"""
    global _global_reference_processor
    _global_reference_processor = reference_processor


def set_adapter_factory_instance(adapter_factory: AdapterFactory) -> None:
    """设置全局适配器工厂实例"""
    global _global_adapter_factory
    _global_adapter_factory = adapter_factory


def clear_config_loader_instance() -> None:
    """清除全局配置加载器实例"""
    global _global_config_loader
    _global_config_loader = None


def clear_config_manager_instance() -> None:
    """清除全局配置管理器实例"""
    global _global_config_manager
    _global_config_manager = None


def clear_config_validator_instance() -> None:
    """清除全局配置验证器实例"""
    global _global_config_validator
    _global_config_validator = None


def clear_config_processor_chain_instance() -> None:
    """清除全局配置处理器链实例"""
    global _global_config_processor_chain
    _global_config_processor_chain = None


def clear_inheritance_processor_instance() -> None:
    """清除全局继承处理器实例"""
    global _global_inheritance_processor
    _global_inheritance_processor = None


def clear_environment_variable_processor_instance() -> None:
    """清除全局环境变量处理器实例"""
    global _global_environment_variable_processor
    _global_environment_variable_processor = None


def clear_reference_processor_instance() -> None:
    """清除全局引用处理器实例"""
    global _global_reference_processor
    _global_reference_processor = None


def clear_adapter_factory_instance() -> None:
    """清除全局适配器工厂实例"""
    global _global_adapter_factory
    _global_adapter_factory = None


def get_config_loader_status() -> dict:
    """获取配置加载器状态"""
    return {
        "has_instance": _global_config_loader is not None,
        "type": type(_global_config_loader).__name__ if _global_config_loader else None
    }


def get_config_manager_status() -> dict:
    """获取配置管理器状态"""
    return {
        "has_instance": _global_config_manager is not None,
        "type": type(_global_config_manager).__name__ if _global_config_manager else None
    }


def get_config_validator_status() -> dict:
    """获取配置验证器状态"""
    return {
        "has_instance": _global_config_validator is not None,
        "type": type(_global_config_validator).__name__ if _global_config_validator else None
    }


def get_config_processor_chain_status() -> dict:
    """获取配置处理器链状态"""
    return {
        "has_instance": _global_config_processor_chain is not None,
        "type": type(_global_config_processor_chain).__name__ if _global_config_processor_chain else None
    }


def get_inheritance_processor_status() -> dict:
    """获取继承处理器状态"""
    return {
        "has_instance": _global_inheritance_processor is not None,
        "type": type(_global_inheritance_processor).__name__ if _global_inheritance_processor else None
    }


def get_environment_variable_processor_status() -> dict:
    """获取环境变量处理器状态"""
    return {
        "has_instance": _global_environment_variable_processor is not None,
        "type": type(_global_environment_variable_processor).__name__ if _global_environment_variable_processor else None
    }


def get_reference_processor_status() -> dict:
    """获取引用处理器状态"""
    return {
        "has_instance": _global_reference_processor is not None,
        "type": type(_global_reference_processor).__name__ if _global_reference_processor else None
    }


def get_adapter_factory_status() -> dict:
    """获取适配器工厂状态"""
    return {
        "has_instance": _global_adapter_factory is not None,
        "type": type(_global_adapter_factory).__name__ if _global_adapter_factory else None
    }


__all__ = [
    "get_config_loader",
    "get_config_manager",
    "get_config_validator",
    "get_config_processor_chain",
    "get_inheritance_processor",
    "get_environment_variable_processor",
    "get_reference_processor",
    "get_adapter_factory",
    "set_config_loader_instance",
    "set_config_manager_instance",
    "set_config_validator_instance",
    "set_config_processor_chain_instance",
    "set_inheritance_processor_instance",
    "set_environment_variable_processor_instance",
    "set_reference_processor_instance",
    "set_adapter_factory_instance",
    "clear_config_loader_instance",
    "clear_config_manager_instance",
    "clear_config_validator_instance",
    "clear_config_processor_chain_instance",
    "clear_inheritance_processor_instance",
    "clear_environment_variable_processor_instance",
    "clear_reference_processor_instance",
    "clear_adapter_factory_instance",
    "get_config_loader_status",
    "get_config_manager_status",
    "get_config_validator_status",
    "get_config_processor_chain_status",
    "get_inheritance_processor_status",
    "get_environment_variable_processor_status",
    "get_reference_processor_status",
    "get_adapter_factory_status",
]