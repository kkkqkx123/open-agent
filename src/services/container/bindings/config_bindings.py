"""配置系统依赖注入配置

注册配置相关的服务到依赖注入容器。
使用基础设施层组件，通过继承BaseServiceBindings简化代码。
重构后使用接口依赖，避免循环依赖。
"""

import sys
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    # 仅在类型检查时导入，避免运行时循环依赖
    from src.core.config.config_manager import ConfigManager
    from src.infrastructure.config.validation import BaseConfigValidator
    from src.core.config.config_manager_factory import CoreConfigManagerFactory
    from src.infrastructure.config.impl.base_impl import ConfigProcessorChain
    from src.infrastructure.config.processor import (
        InheritanceProcessor,
        ReferenceProcessor
    )
    from src.core.config.adapter_factory import AdapterFactory

# 接口导入 - 集中化的接口定义
from src.interfaces.container import IDependencyContainer
from src.interfaces.container.core import ServiceLifetime
from src.interfaces.config import IConfigValidator, IConfigLoader
from src.infrastructure.config.validation import BaseConfigValidator
from src.services.container.core.base_service_bindings import BaseServiceBindings


class ConfigServiceBindings(BaseServiceBindings):
    """配置服务绑定类
    
    负责注册所有配置相关服务，包括：
    - 配置管理器和工厂
    - 配置验证器
    - 配置处理器链
    - 适配器工厂
    - 配置加载器接口
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
        # _register_environment_variable_processor 已弃用，因为InheritanceProcessor已包含环境变量处理功能
        _register_reference_processor(container, config, environment)
        _register_adapter_factory(container, config, environment)
        _register_config_loader(container, config, environment)
    
    def _post_register(
        self,
        container: IDependencyContainer,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """注册后处理"""
        # 设置注入层
        try:
            # 延迟导入具体实现类，避免循环依赖
            def get_service_types() -> list:
                from src.core.config.config_manager import ConfigManager
                from src.core.config.config_manager_factory import CoreConfigManagerFactory
                from src.infrastructure.config.impl.base_impl import ConfigProcessorChain
                from src.infrastructure.config.processor import (
                    InheritanceProcessor,
                    ReferenceProcessor
                )
                from src.core.config.adapter_factory import AdapterFactory
                
                return [
                    ConfigManager,
                    CoreConfigManagerFactory,
                    BaseConfigValidator,
                    ConfigProcessorChain,
                    InheritanceProcessor,
                    ReferenceProcessor,
                    AdapterFactory
                ]
            
            service_types = get_service_types()
            self.setup_injection_layer(container, service_types)
            
            print(f"[INFO] 已设置配置服务注入层 (environment: {environment})", file=sys.stdout)
        except Exception as e:
            print(f"[WARNING] 设置配置注入层失败: {e}", file=sys.stderr)


def _register_config_manager(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册核心配置管理器"""
    # 延迟导入具体实现
    def create_config_manager() -> 'ConfigManager':
        from src.core.config.config_manager import ConfigManager
        from src.infrastructure.config import ConfigLoader
        from src.infrastructure.config.processor import (
            InheritanceProcessor,
            ReferenceProcessor
        )
        from src.infrastructure.config.impl.base_impl import ConfigProcessorChain
        
        # 创建基础设施层组件
        config_loader = ConfigLoader()
        processor_chain = ConfigProcessorChain()
        inheritance_processor = InheritanceProcessor(config_loader)
        
        # 添加处理器：InheritanceProcessor已包含环境变量处理功能
        processor_chain.add_processor(inheritance_processor)
        processor_chain.add_processor(ReferenceProcessor())
        
        # 通过依赖注入创建配置管理器
        return ConfigManager(config_loader, processor_chain, inheritance_handler=inheritance_processor)

    container.register_factory(
        ConfigManager,
        create_config_manager,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    print(f"[DEBUG] 已注册 ConfigManager", file=sys.stdout)


def _register_config_manager_factory(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册配置管理器工厂"""
    # 延迟导入具体实现
    def create_config_manager_factory() -> CoreConfigManagerFactory:
        from src.core.config.config_manager_factory import CoreConfigManagerFactory
        from src.infrastructure.config import ConfigLoader
        from src.infrastructure.config.processor import InheritanceProcessor
        
        config_loader = ConfigLoader()
        inheritance_handler = InheritanceProcessor(config_loader)
        return CoreConfigManagerFactory(config_loader, inheritance_handler)

    container.register_factory(
        CoreConfigManagerFactory,
        create_config_manager_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    print(f"[DEBUG] 已注册 ConfigManagerFactory", file=sys.stdout)


def _register_config_validator(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册默认配置验证器"""
    # 延迟导入具体实现
    def create_config_validator() -> BaseConfigValidator:
        from src.infrastructure.config.validation import BaseConfigValidator
        return BaseConfigValidator("DefaultValidator")

    from src.infrastructure.config.validation import BaseConfigValidator
    
    # 注册具体类型和接口
    container.register_factory(
        BaseConfigValidator,
        create_config_validator,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    container.register_factory(
        IConfigValidator,
        create_config_validator,
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
    # 延迟导入具体实现
    def create_inheritance_processor() -> 'InheritanceProcessor':
        from src.infrastructure.config.processor import InheritanceProcessor
        from src.infrastructure.config import ConfigLoader
        return InheritanceProcessor(ConfigLoader())

    container.register_factory(
        InheritanceProcessor,
        create_inheritance_processor,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    print(f"[DEBUG] 已注册 InheritanceProcessor", file=sys.stdout)


def _register_environment_variable_processor(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册环境变量处理器（已弃用，因为InheritanceProcessor已包含此功能）"""
    # 注意：此处理器已不再需要，因为InheritanceProcessor已包含环境变量处理功能
    # 保留此函数仅用于向后兼容，但不注册服务
    print(f"[DEBUG] EnvironmentProcessor 已弃用，使用 InheritanceProcessor 的环境变量处理功能", file=sys.stdout)


def _register_reference_processor(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册引用处理器"""
    # 延迟导入具体实现
    def create_reference_processor() -> 'ReferenceProcessor':
        from src.infrastructure.config.processor import ReferenceProcessor
        return ReferenceProcessor()

    container.register_factory(
        ReferenceProcessor,
        create_reference_processor,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    print(f"[DEBUG] 已注册 ReferenceProcessor", file=sys.stdout)


def _register_adapter_factory(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册适配器工厂"""
    container.register_factory(
        AdapterFactory,
        lambda: _create_adapter_factory(),
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
        from src.infrastructure.config import ConfigLoader
        
        processor_chain = ConfigProcessorChain()
        config_loader = ConfigLoader()
        
        # 按顺序添加处理器：InheritanceProcessor已包含环境变量处理功能
        processor_chain.add_processor(InheritanceProcessor(config_loader))
        processor_chain.add_processor(ReferenceProcessor())
        
        print(f"[DEBUG] 配置处理器链创建完成，包含 2 个处理器", file=sys.stdout)
        return processor_chain
        
    except Exception as e:
        print(f"[ERROR] 创建配置处理器链失败: {e}", file=sys.stderr)
        raise


def _create_adapter_factory() -> 'AdapterFactory':
    """创建适配器工厂
    Returns:
        适配器工厂实例
    """
    try:
        from src.core.config.config_manager import ConfigManager
        from src.infrastructure.config import ConfigLoader
        from src.infrastructure.config.processor import InheritanceProcessor, ReferenceProcessor
        from src.infrastructure.config.impl.base_impl import ConfigProcessorChain
        
        # 创建配置管理器
        config_loader = ConfigLoader()
        processor_chain = ConfigProcessorChain()
        inheritance_processor = InheritanceProcessor(config_loader)
        processor_chain.add_processor(inheritance_processor)
        processor_chain.add_processor(ReferenceProcessor())
        
        config_manager = ConfigManager(config_loader, processor_chain, inheritance_handler=inheritance_processor)
        adapter_factory = AdapterFactory(config_manager)
        print(f"[DEBUG] 适配器工厂创建完成", file=sys.stdout)
        return adapter_factory
    except Exception as e:
        print(f"[ERROR] 创建适配器工厂失败: {e}", file=sys.stderr)
        raise


def _register_config_loader(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册配置加载器接口"""
    # 延迟导入具体实现
    def create_config_loader() -> IConfigLoader:
        from src.infrastructure.config import ConfigLoader
        return ConfigLoader()

    container.register_factory(
        IConfigLoader,
        create_config_loader,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    print(f"[DEBUG] 已注册 IConfigLoader", file=sys.stdout)

