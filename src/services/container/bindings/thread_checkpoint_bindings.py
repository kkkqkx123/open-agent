"""Thread检查点依赖注入绑定配置

配置Thread检查点相关服务的依赖注入。
使用基础设施层组件，通过继承BaseServiceBindings简化代码。
重构后使用接口依赖，避免循环依赖。
"""

import sys
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    # 仅在类型检查时导入，避免运行时循环依赖
    from src.core.threads.checkpoints.storage import (
        ThreadCheckpointDomainService,
        CheckpointManager,
        ThreadCheckpointRepository,
        IThreadCheckpointRepository
    )
    from src.core.threads.checkpoints.manager import ThreadCheckpointManager
    from src.services.storage import (
        StorageOrchestrator,
        ThreadStorageService
    )
    from src.core.storage import StorageConfigManager
    from src.adapters.threads.checkpoints import (
        LangGraphCheckpointAdapter,
        MemoryLangGraphCheckpointAdapter
    )

# 接口导入 - 集中化的接口定义
from src.interfaces.container import IDependencyContainer
from src.interfaces.threads.checkpoint import IThreadCheckpointManager
from src.interfaces.container.core import ServiceLifetime
from src.interfaces.logger import ILogger
from src.services.container.core.base_service_bindings import BaseServiceBindings


class ThreadCheckpointServiceBindings(BaseServiceBindings):
    """ThreadCheckpoint服务绑定类
    
    负责注册所有Thread检查点相关服务，包括：
    - 检查点存储后端
    - 检查点领域服务
    - 检查点管理器
    - 存储编排器
    - Thread存储服务
    """
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证ThreadCheckpoint配置"""
        # ThreadCheckpoint服务通常不需要特殊验证
        pass
    
    def _do_register_services(
        self,
        container: IDependencyContainer,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """执行ThreadCheckpoint服务注册"""
        _register_thread_checkpoint_services(container, config, environment)
    
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
                from src.core.threads.checkpoints.storage import (
                    ThreadCheckpointDomainService,
                    CheckpointManager,
                    ThreadCheckpointRepository,
                    IThreadCheckpointRepository
                )
                from src.core.threads.checkpoints.manager import ThreadCheckpointManager
                from src.services.storage import (
                    StorageOrchestrator,
                    ThreadStorageService
                )
                from src.core.storage import StorageConfigManager

                return [
                    IThreadCheckpointRepository,
                    ThreadCheckpointDomainService,
                    CheckpointManager,
                    ThreadCheckpointManager,
                    StorageOrchestrator,
                    ThreadStorageService,
                    StorageConfigManager
                ]
            
            service_types = get_service_types()
            self.setup_injection_layer(container, service_types)
            
            # 设置全局实例（向后兼容）
            from src.services.thread_checkpoint.injection import (
                set_checkpoint_repository_instance,
                set_checkpoint_domain_service_instance,
                set_checkpoint_manager_instance,
                set_thread_checkpoint_manager_instance,
                set_storage_orchestrator_instance,
                set_thread_storage_service_instance,
                set_storage_config_manager_instance
            )
            
            # 延迟导入具体实现类进行类型检查
            def get_concrete_types() -> tuple:
                from src.core.threads.checkpoints.storage import (
                    ThreadCheckpointDomainService,
                    CheckpointManager,
                    ThreadCheckpointRepository,
                    IThreadCheckpointRepository
                )
                from src.core.threads.checkpoints.manager import ThreadCheckpointManager
                from src.services.storage import (
                    StorageOrchestrator,
                    ThreadStorageService
                )
                from src.core.storage import StorageConfigManager
                return (
                    IThreadCheckpointRepository,
                    ThreadCheckpointDomainService,
                    CheckpointManager,
                    ThreadCheckpointManager,
                    StorageOrchestrator,
                    ThreadStorageService,
                    StorageConfigManager
                )
            
            IThreadCheckpointRepository, ThreadCheckpointDomainService, CheckpointManager, ThreadCheckpointManager, StorageOrchestrator, ThreadStorageService, StorageConfigManager = get_concrete_types()
            
            if container.has_service(IThreadCheckpointRepository):
                set_checkpoint_repository_instance(container.get(IThreadCheckpointRepository))
            
            if container.has_service(ThreadCheckpointDomainService):
                set_checkpoint_domain_service_instance(container.get(ThreadCheckpointDomainService))
            
            if container.has_service(CheckpointManager):
                set_checkpoint_manager_instance(container.get(CheckpointManager))
            
            if container.has_service(ThreadCheckpointManager):
                set_thread_checkpoint_manager_instance(container.get(ThreadCheckpointManager))
            
            if container.has_service(StorageOrchestrator):
                set_storage_orchestrator_instance(container.get(StorageOrchestrator))
            
            if container.has_service(ThreadStorageService):
                set_thread_storage_service_instance(container.get(ThreadStorageService))
            
            if container.has_service(StorageConfigManager):
                set_storage_config_manager_instance(container.get(StorageConfigManager))
            
            logger = self.safe_get_service(container, ILogger)
            if logger:
                logger.debug(f"已设置ThreadCheckpoint服务注入层 (environment: {environment})")
        except Exception as e:
            print(f"[WARNING] 设置ThreadCheckpoint注入层失败: {e}", file=sys.stderr)


def _register_thread_checkpoint_services(container: IDependencyContainer, config: Dict[str, Any], environment: str = "default") -> None:
    """注册Thread检查点相关服务
    
    Args:
        container: 依赖注入容器
        config: 配置参数
        environment: 环境名称
    """
    try:
        # 1. 注册存储后端（根据配置选择）
        storage_backend_type = config.get("storage_backend", "memory")
        
        # 延迟导入具体实现，避免循环依赖
        def create_memory_repository() -> 'IThreadCheckpointRepository':
            from src.core.threads.checkpoints.storage import ThreadCheckpointRepository, IThreadCheckpointRepository
            from src.adapters.threads.checkpoints import MemoryLangGraphCheckpointAdapter

            # Create a concrete implementation if ThreadCheckpointRepository is abstract
            class ConcreteThreadCheckpointRepository(ThreadCheckpointRepository):
                pass  # If ThreadCheckpointRepository is already concrete, this will work

            return ConcreteThreadCheckpointRepository(
                MemoryLangGraphCheckpointAdapter()._checkpointer
            )
        
        def create_langgraph_repository() -> 'IThreadCheckpointRepository':
            from src.core.threads.checkpoints.storage import ThreadCheckpointRepository, IThreadCheckpointRepository
            from src.adapters.threads.checkpoints import LangGraphCheckpointAdapter, MemoryLangGraphCheckpointAdapter

            # Create a concrete implementation if ThreadCheckpointRepository is abstract
            class ConcreteThreadCheckpointRepository(ThreadCheckpointRepository):
                pass  # If ThreadCheckpointRepository is already concrete, this will work

            langgraph_checkpointer = config.get("langgraph_checkpointer")
            if langgraph_checkpointer:
                return ConcreteThreadCheckpointRepository(
                    LangGraphCheckpointAdapter(langgraph_checkpointer)
                )
            else:
                print(f"[WARNING] LangGraph checkpointer not provided, using memory adapter", file=sys.stderr)
                return ConcreteThreadCheckpointRepository(
                    MemoryLangGraphCheckpointAdapter()._checkpointer
                )
        
        if storage_backend_type == "memory":
            container.register_factory(
                IThreadCheckpointRepository,
                create_memory_repository,
                environment=environment,
                lifetime=ServiceLifetime.SINGLETON
            )
        elif storage_backend_type == "langgraph":
            container.register_factory(
                IThreadCheckpointRepository,
                create_langgraph_repository,
                environment=environment,
                lifetime=ServiceLifetime.SINGLETON
            )
        else:
            raise ValueError(f"Unsupported storage backend type: {storage_backend_type}")
        
        # 2. 注册核心领域服务
        def create_domain_service() -> 'ThreadCheckpointDomainService':
            from src.core.threads.checkpoints.storage import ThreadCheckpointDomainService, IThreadCheckpointRepository
            return ThreadCheckpointDomainService(
                container.get(IThreadCheckpointRepository)
            )
        
        container.register_factory(
            ThreadCheckpointDomainService,
            create_domain_service,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 3. 注册检查点管理器
        def create_checkpoint_manager() -> 'CheckpointManager':
            from src.core.threads.checkpoints.storage import CheckpointManager, ThreadCheckpointDomainService
            return CheckpointManager(
                container.get(ThreadCheckpointDomainService)
            )
        
        container.register_factory(
            CheckpointManager,
            create_checkpoint_manager,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 4. 注册Thread检查点管理器
        def create_thread_checkpoint_manager() -> 'ThreadCheckpointManager':
            from src.core.threads.checkpoints.manager import ThreadCheckpointManager
            from src.core.threads.checkpoints.storage import ThreadCheckpointDomainService, CheckpointManager
            return ThreadCheckpointManager(
                container.get(ThreadCheckpointDomainService),
                container.get(CheckpointManager)
            )
        
        container.register_factory(
            ThreadCheckpointManager,
            create_thread_checkpoint_manager,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 5. 注册存储编排器
        def create_storage_orchestrator() -> 'StorageOrchestrator':
            from src.services.storage import StorageOrchestrator
            from src.core.threads.checkpoints.storage import ThreadCheckpointDomainService
            from src.core.threads.checkpoints.manager import ThreadCheckpointManager
            from src.core.threads.checkpoints.storage import CheckpointManager
            return StorageOrchestrator(
                container.get(ThreadCheckpointDomainService),
                container.get(ThreadCheckpointManager),
                container.get(CheckpointManager)
            )
        
        container.register_factory(
            StorageOrchestrator,
            create_storage_orchestrator,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 6. 注册Thread存储服务
        def create_thread_storage_service() -> 'ThreadStorageService':
            from src.services.storage import ThreadStorageService
            from src.core.threads.checkpoints.storage import ThreadCheckpointDomainService
            return ThreadStorageService(
                container.get(StorageOrchestrator),
                container.get(ThreadCheckpointDomainService)
            )
        
        container.register_factory(
            ThreadStorageService,
            create_thread_storage_service,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 7. 注册存储配置管理器
        def create_storage_config_manager() -> 'StorageConfigManager':
            from src.core.storage import StorageConfigManager
            return StorageConfigManager()
        
        container.register_factory(
            StorageConfigManager,
            create_storage_config_manager,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        print(f"[INFO] Thread checkpoint services registered successfully", file=sys.stdout)
        
    except Exception as e:
        print(f"[ERROR] Failed to register thread checkpoint services: {e}", file=sys.stderr)
        raise


