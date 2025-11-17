"""LLM模块依赖注入配置"""

import logging
from typing import Dict, Any

from src.core.llm.interfaces import (
    ITaskGroupManager, 
    IPollingPoolManager, 
    IClientFactory, 
    IFallbackManager,
    ILLMManager
)
from .task_group_manager import TaskGroupManager
from .polling_pool import PollingPoolManager
from .client_factory import ClientFactory
from .fallback_manager import FallbackManager
from .manager import LLMManager
from .configuration_service import LLMClientConfigurationService
from .client_manager import LLMClientManager
from .request_executor import LLMRequestExecutor
from .config_validator import LLMConfigValidator
from .metadata_service import ClientMetadataService
from .state_machine import StateMachine
from src.core.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


def register_llm_services(container) -> None:
    """
    注册LLM相关服务到依赖注入容器
    
    Args:
        container: 依赖注入容器
    """
    try:
        # 注册配置加载器
        from infrastructure.config.loader.file_config_loader import FileConfigLoader
        container.register_singleton(FileConfigLoader)
        
        # 注册任务组管理器
        container.register_singleton(ITaskGroupManager, TaskGroupManager)
        
        # 注册轮询池管理器
        container.register_singleton(IPollingPoolManager, PollingPoolManager)
        
        # 注册LLM工厂
        container.register_singleton(LLMFactory)
        
        # 注册客户端工厂
        container.register_singleton(IClientFactory, ClientFactory)
        
        # 注册降级管理器
        container.register_singleton(IFallbackManager, FallbackManager)
        
        # 注册配置验证器
        container.register_singleton(LLMConfigValidator)
        
        # 注册元数据服务
        container.register_singleton(ClientMetadataService)
        
        # 注册状态机
        container.register_singleton(StateMachine)
        
        # 注册配置服务
        container.register_singleton(LLMClientConfigurationService)
        
        # 注册客户端管理器
        container.register_singleton(LLMClientManager)
        
        # 注册请求执行器
        container.register_singleton(LLMRequestExecutor)
        
        # 注册LLM管理器
        container.register_singleton(ILLMManager, LLMManager)
        
        logger.info("LLM模块服务注册完成")
        
    except Exception as e:
        logger.error(f"注册LLM模块服务失败: {e}")
        raise


def create_llm_wrapper_factory(container) -> Any:
    """
    创建LLM包装器工厂
    
    Args:
        container: 依赖注入容器
        
    Returns:
        LLM包装器工厂实例
    """
    try:
        from src.core.llm.wrappers.wrapper_factory import LLMWrapperFactory
        
        # 获取依赖
        task_group_manager = container.get(ITaskGroupManager)
        polling_pool_manager = container.get(IPollingPoolManager)
        fallback_manager = container.get(IFallbackManager)
        
        # 创建工厂
        factory = LLMWrapperFactory(
            task_group_manager=task_group_manager,
            polling_pool_manager=polling_pool_manager,
            fallback_manager=fallback_manager
        )
        
        logger.info("LLM包装器工厂创建完成")
        return factory
        
    except Exception as e:
        logger.error(f"创建LLM包装器工厂失败: {e}")
        raise


def configure_llm_module(container, config: Dict[str, Any]) -> None:
    """
    配置LLM模块
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    try:
        # 注册所有LLM服务
        register_llm_services(container)
        
        # 创建并注册包装器工厂
        wrapper_factory = create_llm_wrapper_factory(container)
        container.register_instance(wrapper_factory)
        
        # 如果需要，可以在这里添加额外的配置
        llm_config = config.get("llm", {})
        if llm_config:
            logger.info(f"应用LLM配置: {llm_config}")
        
        logger.info("LLM模块配置完成")
        
    except Exception as e:
        logger.error(f"配置LLM模块失败: {e}")
        raise


def create_llm_manager_with_config(container, config: Dict[str, Any]) -> LLMManager:
    """
    创建带配置的LLM管理器实例
    
    Args:
        container: 依赖注入容器
        config: LLM配置字典
        
    Returns:
        LLMManager: LLM管理器实例
    """
    try:
        # 获取依赖
        factory = container.get(LLMFactory)
        fallback_manager = container.get(IFallbackManager)
        task_group_manager = container.get(ITaskGroupManager)
        config_validator = container.get(LLMConfigValidator)
        metadata_service = container.get(ClientMetadataService)
        
        # 创建LLM管理器
        llm_manager = LLMManager(
            factory=factory,
            fallback_manager=fallback_manager,
            task_group_manager=task_group_manager,
            config_validator=config_validator,
            metadata_service=metadata_service,
            config=config
        )
        
        logger.info("带配置的LLM管理器创建完成")
        return llm_manager
        
    except Exception as e:
        logger.error(f"创建带配置的LLM管理器失败: {e}")
        raise