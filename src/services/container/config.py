"""配置系统依赖注入配置

注册配置相关的服务到依赖注入容器。
使用基础设施层组件，通过继承BaseServiceBindings简化代码。
"""

import sys
from typing import Dict, Any

from src.interfaces.container import IDependencyContainer
from src.interfaces.common_infra import ServiceLifetime
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
from src.services.container.core.base_service_bindings import BaseServiceBindings


class ConfigServiceBindings(BaseServiceBindings):
    """配置服务绑定类
    
    负责注册所有配置相关服务，包括：
    - 配置管理器和工厂
    - 配置验证器
    - 配置处理器链
    - 适配器工厂
    """
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证配置配置"""
        # 配置服务通常不需要特殊验证
        pass
    
    def _do_register_services(
        self,
        container: IDependencyContainer,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """执行配置服务注册"""
        _register_config_manager(container, config, environment)
        _register_config_manager_factory(container, config, environment)
        _register_config_validator(container, config, environment)
        _register_config_processor_chain(container, config, environment)
        _register_inheritance_processor(container, config, environment)
        _register_environment_variable_processor(container, config, environment)
        _register_reference_processor(container, config, environment)
        _register_adapter_factory(container, config, environment)
    
    def _post_register(
        self,
        container: IDependencyContainer,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """注册后处理"""
        # 设置注入层
        try:
            # 为配置服务设置注入层
            service_types = [
                ConfigManager,
                ConfigManagerFactory,
                IConfigValidator,
                ConfigProcessorChain,
                InheritanceProcessor,
                EnvironmentVariableProcessor,
                ReferenceProcessor,
                AdapterFactory
            ]
            
            self.setup_injection_layer(container, service_types)
            
            # 设置全局实例（向后兼容）
            from src.services.config.injection import (
                set_config_manager_instance,
                set_config_manager_factory_instance,
                set_config_validator_instance,
                set_config_processor_chain_instance,
                set_inheritance_processor_instance,
                set_environment_variable_processor_instance,
                set_reference_processor_instance,
                set_adapter_factory_instance
            )
            
            if container.has_service(ConfigManager):
                set_config_manager_instance(container.get(ConfigManager))
            
            if container.has_service(ConfigManagerFactory):
                set_config_manager_factory_instance(container.get(ConfigManagerFactory))
            
            if container.has_service(IConfigValidator):
                set_config_validator_instance(container.get(IConfigValidator))
            
            if container.has_service(ConfigProcessorChain):
                set_config_processor_chain_instance(container.get(ConfigProcessorChain))
            
            if container.has_service(InheritanceProcessor):
                set_inheritance_processor_instance(container.get(InheritanceProcessor))
            
            if container.has_service(EnvironmentVariableProcessor):
                set_environment_variable_processor_instance(container.get(EnvironmentVariableProcessor))
            
            if container.has_service(ReferenceProcessor):
                set_reference_processor_instance(container.get(ReferenceProcessor))
            
            if container.has_service(AdapterFactory):
                set_adapter_factory_instance(container.get(AdapterFactory))
            
            print(f"[INFO] 已设置配置服务注入层 (environment: {environment})", file=sys.stdout)
        except Exception as e:
            print(f"[WARNING] 设置配置注入层失败: {e}", file=sys.stderr)


def register_config_services(container: IDependencyContainer, config: Dict[str, Any] = None, environment: str = "default") -> None:
    """注册配置相关服务的便捷函数
    
    Args:
        container: 依赖注入容器
        config: 配置字典（可选）
        environment: 环境名称
    """
    if config is None:
        config = {}
    
    bindings = ConfigServiceBindings()
    bindings.register_services(container, config, environment)


def _register_config_manager(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册核心配置管理器"""
    container.register(
        ConfigManager,
        ConfigManager,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    print(f"[DEBUG] 已注册 ConfigManager", file=sys.stdout)


def _register_config_manager_factory(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册配置管理器工厂"""
    container.register(
        ConfigManagerFactory,
        ConfigManagerFactory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    print(f"[DEBUG] 已注册 ConfigManagerFactory", file=sys.stdout)


def _register_config_validator(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册默认配置验证器"""
    container.register(
        IConfigValidator,
        DefaultConfigValidator,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    print(f"[DEBUG] 已注册 DefaultConfigValidator", file=sys.stdout)


def _register_config_processor_chain(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册配置处理器链"""
    container.register_factory(
        ConfigProcessorChain,
        _create_processor_chain,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    print(f"[DEBUG] 已注册 ConfigProcessorChain", file=sys.stdout)


def _register_inheritance_processor(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册继承处理器"""
    container.register(
        InheritanceProcessor,
        InheritanceProcessor,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    print(f"[DEBUG] 已注册 InheritanceProcessor", file=sys.stdout)


def _register_environment_variable_processor(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册环境变量处理器"""
    container.register(
        EnvironmentVariableProcessor,
        EnvironmentVariableProcessor,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    print(f"[DEBUG] 已注册 EnvironmentVariableProcessor", file=sys.stdout)


def _register_reference_processor(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册引用处理器"""
    container.register(
        ReferenceProcessor,
        ReferenceProcessor,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    print(f"[DEBUG] 已注册 ReferenceProcessor", file=sys.stdout)


def _register_adapter_factory(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册适配器工厂"""
    container.register_factory(
        AdapterFactory,
        _create_adapter_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    print(f"[DEBUG] 已注册 AdapterFactory", file=sys.stdout)


def _create_processor_chain() -> ConfigProcessorChain:
    """创建配置处理器链
    
    Returns:
        配置置处理器链实例
    """
    try:
        processor_chain = ConfigProcessorChain()
        
        # 按顺序添加处理器
        processor_chain.add_processor(InheritanceProcessor())
        processor_chain.add_processor(EnvironmentVariableProcessor())
        processor_chain.add_processor(ReferenceProcessor())
        
        print(f"[DEBUG] 配置处理器链创建完成，包含 3 个处理器", file=sys.stdout)
        return processor_chain
        
    except Exception as e:
        print(f"[ERROR] 创建配置处理器链失败: {e}", file=sys.stderr)
        raise


def _create_adapter_factory() -> AdapterFactory:
    """创建适配器工厂
    Returns:
        适配器工厂实例
    """
    try:
        from ...core.config.config_manager import get_default_manager
        config_manager = get_default_manager()
        adapter_factory = AdapterFactory(config_manager)
        print(f"[DEBUG] 适配器工厂创建完成", file=sys.stdout)
        return adapter_factory
    except Exception as e:
        print(f"[ERROR] 创建适配器工厂失败: {e}", file=sys.stderr)
        raise


def register_module_validators(container: IDependencyContainer) -> None:
    """注册模块特定验证器
    
    Args:
        container: 依赖注入容器
    """
    try:
        # 这里可以注册模块特定的验证器
        # 例如：
        # container.register(
        #     IConfigValidator,
        #     LLMConfigValidator,
        #     lifetime=ServiceLifetime.SINGLETON,
        #     name="llm"
        # )
        
        print(f"[INFO] 模块特定验证器注册完成", file=sys.stdout)
        
    except Exception as e:
        print(f"[ERROR] 注册模块特定验证器失败: {e}", file=sys.stderr)
        raise


def configure_config_manager_factory(container: IDependencyContainer) -> None:
    """配置配置管理器工厂
    
    Args:
        container: 依赖注入容器
    """
    try:
        # 获取配置管理器工厂
        factory = container.get(ConfigManagerFactory)
        
        # 这里可以注册模块特定的装饰器
        # 例如：
        # from .decorators.llm_config_manager_decorator import LLMConfigManagerDecorator
        # factory.register_manager_decorator("llm", LLMConfigManagerDecorator)
        
        print(f"[INFO] 配置管理器工厂配置完成", file=sys.stdout)
        
    except Exception as e:
        print(f"[ERROR] 配置配置管理器工厂失败: {e}", file=sys.stderr)
        raise


def get_config_service_status(container: IDependencyContainer) -> Dict[str, Any]:
    """获取配置服务状态
    
    Args:
        container: 依赖注入容器
        
    Returns:
        服务状态信息
    """
    status = {
        "registered_services": [],
        "processor_chain_status": {},
        "factory_status": {}
    }
    
    try:
        # 检查已注册的服务
        service_types = [
            ConfigManager,
            ConfigManagerFactory,
            IConfigValidator,
            ConfigProcessorChain,
            InheritanceProcessor,
            EnvironmentVariableProcessor,
            ReferenceProcessor,
            AdapterFactory
        ]
        
        for service_type in service_types:
            if container.has_service(service_type):
                status["registered_services"].append(service_type.__name__)
        
        # 获取处理器链状态
        if container.has_service(ConfigProcessorChain):
            processor_chain = container.get(ConfigProcessorChain)
            status["processor_chain_status"] = {
                "processor_count": processor_chain.get_processor_count(),
                "processor_names": processor_chain.get_processor_names()
            }
        
        # 获取工厂状态
        if container.has_service(ConfigManagerFactory):
            factory = container.get(ConfigManagerFactory)
            status["factory_status"] = factory.get_factory_status()
        
    except Exception as e:
        print(f"[ERROR] 获取配置服务状态失败: {e}", file=sys.stderr)
        status["error"] = str(e)
    
    return status


def validate_config_services(container: IDependencyContainer) -> bool:
    """验证配置服务是否正确注册
    
    Args:
        container: 依赖注入容器
        
    Returns:
        是否验证通过
    """
    try:
        # 检查核心服务
        required_services = [
            ConfigManager,
            ConfigManagerFactory,
            IConfigValidator,
            ConfigProcessorChain
        ]
        
        for service_type in required_services:
            if not container.has_service(service_type):
                print(f"[ERROR] 缺少必需的服务: {service_type.__name__}", file=sys.stderr)
                return False
        
        # 尝试获取服务实例
        container.get(ConfigManager)
        container.get(ConfigManagerFactory)
        container.get(IConfigValidator)
        container.get(ConfigProcessorChain)
        
        print(f"[INFO] 配置服务验证通过", file=sys.stdout)
        return True
        
    except Exception as e:
        print(f"[ERROR] 配置服务验证失败: {e}", file=sys.stderr)
        return False