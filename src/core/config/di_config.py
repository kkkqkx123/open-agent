"""配置系统依赖注入配置

注册配置相关的服务到依赖注入容器。
为了避免架构层次问题，不集中到service层的container目录中。
"""

import logging
from typing import Dict, Any

from src.interfaces.container import IDependencyContainer
from src.interfaces.common_infra import ServiceLifetime
from src.interfaces.config.interfaces import IConfigValidator
from .config_manager import ConfigManager, DefaultConfigValidator
from .config_manager_factory import ConfigManagerFactory
from .processor.config_processor_chain import (
    ConfigProcessorChain,
    InheritanceProcessor,
    EnvironmentVariableProcessor,
    ReferenceProcessor
)
from .adapter_factory import AdapterFactory

logger = logging.getLogger(__name__)


def register_config_services(container: IDependencyContainer) -> None:
    """注册配置相关服务
    
    Args:
        container: 依赖注入容器
    """
    try:
        # 注册核心配置管理器
        container.register(
            ConfigManager,
            ConfigManager,
            lifetime=ServiceLifetime.SINGLETON
        )
        logger.debug("已注册 ConfigManager")
        
        # 注册配置管理器工厂
        container.register(
            ConfigManagerFactory,
            ConfigManagerFactory,
            lifetime=ServiceLifetime.SINGLETON
        )
        logger.debug("已注册 ConfigManagerFactory")
        
        # 注册默认配置验证器
        container.register(
            IConfigValidator,
            DefaultConfigValidator,
            lifetime=ServiceLifetime.SINGLETON
        )
        logger.debug("已注册 DefaultConfigValidator")
        
        # 注册配置处理器链
        container.register_factory(
            ConfigProcessorChain,
            _create_processor_chain,
            lifetime=ServiceLifetime.SINGLETON
        )
        logger.debug("已注册 ConfigProcessorChain")
        
        # 注册具体处理器
        container.register(
            InheritanceProcessor,
            InheritanceProcessor,
            lifetime=ServiceLifetime.SINGLETON
        )
        logger.debug("已注册 InheritanceProcessor")
        
        container.register(
            EnvironmentVariableProcessor,
            EnvironmentVariableProcessor,
            lifetime=ServiceLifetime.SINGLETON
        )
        logger.debug("已注册 EnvironmentVariableProcessor")
        
        container.register(
            ReferenceProcessor,
            ReferenceProcessor,
            lifetime=ServiceLifetime.SINGLETON
        )
        # 注册适配器工厂
        container.register_factory(
            AdapterFactory,
            _create_adapter_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        logger.debug("已注册 AdapterFactory")
        logger.debug("已注册 ReferenceProcessor")
        
        logger.info("配置系统服务注册完成")
        
    except Exception as e:
        logger.error(f"注册配置系统服务失败: {e}")
        raise


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
        
        logger.debug("配置处理器链创建完成，包含 3 个处理器")
        return processor_chain
        
    except Exception as e:
        logger.error(f"创建配置处理器链失败: {e}")
        raise


def _create_adapter_factory() -> AdapterFactory:
    """创建适配器工厂
    Returns:
        适配器工厂实例
    """
    try:
        from .config_manager import get_default_manager
        config_manager = get_default_manager()
        adapter_factory = AdapterFactory(config_manager)
        logger.debug("适配器工厂创建完成")
        return adapter_factory
    except Exception as e:
        logger.error(f"创建适配器工厂失败: {e}")
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
        
        logger.info("模块特定验证器注册完成")
        
    except Exception as e:
        logger.error(f"注册模块特定验证器失败: {e}")
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
        
        logger.info("配置管理器工厂配置完成")
        
    except Exception as e:
        logger.error(f"配置配置管理器工厂失败: {e}")
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
        logger.error(f"获取配置服务状态失败: {e}")
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
                logger.error(f"缺少必需的服务: {service_type.__name__}")
                return False
        
        # 尝试获取服务实例
        container.get(ConfigManager)
        container.get(ConfigManagerFactory)
        container.get(IConfigValidator)
        container.get(ConfigProcessorChain)
        
        logger.info("配置服务验证通过")
        return True
        
    except Exception as e:
        logger.error(f"配置服务验证失败: {e}")
        return False