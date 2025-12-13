"""
LLM服务绑定
"""

from typing import Dict, Any
from src.interfaces.llm.manager import ILLMManager
from src.interfaces.container.core import IDependencyContainer, ServiceLifetime

class LLMServiceBindings:
    """LLM服务绑定"""
    
    def register_services(self, container: IDependencyContainer, config: Dict[str, Any]):
        """注册LLM服务
        
        Args:
            container: 依赖注入容器
            config: 配置信息
        """
        # 注册LLM工厂
        def llm_factory_factory():
            from src.core.llm.factory import LLMFactory
            return LLMFactory()
        
        from src.core.llm.factory import LLMFactory
        container.register_factory(
            LLMFactory,
            llm_factory_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册配置工厂
        def config_factory_factory():
            from src.infrastructure.config.factory import ConfigFactory
            return ConfigFactory()
        
        from src.infrastructure.config.factory import ConfigFactory
        container.register_factory(
            ConfigFactory,
            config_factory_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册配置门面
        def config_facade_factory():
            from src.core.config.config_facade import ConfigFacade
            from src.infrastructure.config.factory import ConfigFactory
            
            config_factory = container.get(ConfigFactory)
            return ConfigFacade(config_factory)
        
        from src.core.config.config_facade import ConfigFacade
        container.register_factory(
            ConfigFacade,
            config_facade_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册元数据服务
        def metadata_service_factory():
            from src.services.llm.utils.metadata_service import ClientMetadataService
            return ClientMetadataService()
        
        from src.services.llm.utils.metadata_service import ClientMetadataService
        container.register_factory(
            ClientMetadataService,
            metadata_service_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册降级管理器
        def fallback_manager_factory():
            from src.services.llm.fallback_system.fallback_manager import FallbackManager
            return FallbackManager()
        
        from src.services.llm.fallback_system.fallback_manager import FallbackManager
        container.register_factory(
            FallbackManager,
            fallback_manager_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册任务组管理器
        def task_group_manager_factory():
            from src.services.llm.scheduling.task_group_manager import TaskGroupManager
            from src.core.config.config_facade import ConfigFacade
            
            config_facade = container.get(ConfigFacade)
            return TaskGroupManager(config_facade)
        
        from src.services.llm.scheduling.task_group_manager import TaskGroupManager
        container.register_factory(
            TaskGroupManager,
            task_group_manager_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册LLM管理器
        def llm_manager_factory():
            from src.services.llm.manager import LLMManager
            from src.core.llm.factory import LLMFactory
            from src.services.llm.fallback_system.fallback_manager import FallbackManager
            from src.services.llm.scheduling.task_group_manager import TaskGroupManager
            from src.services.llm.utils.metadata_service import ClientMetadataService
            
            factory = container.get(LLMFactory)
            fallback_manager = container.get(FallbackManager)
            task_group_manager = container.get(TaskGroupManager)
            metadata_service = container.get(ClientMetadataService)
            
            return LLMManager(
                factory=factory,
                fallback_manager=fallback_manager,
                task_group_manager=task_group_manager,
                metadata_service=metadata_service
            )
        
        container.register_factory(
            ILLMManager,
            llm_manager_factory,
            lifetime=ServiceLifetime.SINGLETON
        )