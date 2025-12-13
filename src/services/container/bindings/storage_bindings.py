"""
存储服务绑定
"""

from typing import Dict, Any
from src.interfaces.storage import IStorageService
from src.interfaces.container.core import IDependencyContainer, ServiceLifetime

class StorageServiceBindings:
    """存储服务绑定"""
    
    def register_services(self, container: IDependencyContainer, config: Dict[str, Any]):
        """注册存储服务
        
        Args:
            container: 依赖注入容器
            config: 配置信息
        """
        # 注册存储后端
        def storage_backend_factory():
            from src.adapters.storage.factory.storage_factory import create_storage
            return create_storage("memory", config.get("storage", {}).get("backends", {}).get("memory", {}))
        
        from src.interfaces.storage.backend import IStorageBackend
        container.register_factory(
            IStorageBackend,
            storage_backend_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册检查点仓储
        def checkpoint_repository_factory():
            from src.core.threads.checkpoints.storage.repository import ThreadCheckpointRepository
            from src.interfaces.storage.backend import IStorageBackend
            
            storage_backend = container.get(IStorageBackend)
            return ThreadCheckpointRepository(storage_backend)
        
        from src.core.threads.checkpoints.storage.repository import IThreadCheckpointRepository
        container.register_factory(
            IThreadCheckpointRepository,
            checkpoint_repository_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册检查点领域服务
        def checkpoint_domain_service_factory():
            from src.core.threads.checkpoints.storage import ThreadCheckpointDomainService
            from src.core.threads.checkpoints.storage.repository import IThreadCheckpointRepository
            
            repository = container.get(IThreadCheckpointRepository)
            return ThreadCheckpointDomainService(repository)
        
        from src.core.threads.checkpoints.storage import ThreadCheckpointDomainService
        container.register_factory(
            ThreadCheckpointDomainService,
            checkpoint_domain_service_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册检查点管理器
        def checkpoint_manager_factory():
            from src.core.threads.checkpoints.storage import CheckpointManager
            from src.core.threads.checkpoints.storage import ThreadCheckpointDomainService
            
            domain_service = container.get(ThreadCheckpointDomainService)
            return CheckpointManager(domain_service)
        
        from src.core.threads.checkpoints.storage import CheckpointManager
        container.register_factory(
            CheckpointManager,
            checkpoint_manager_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册线程检查点管理器
        def thread_checkpoint_manager_factory():
            from src.core.threads.checkpoints.manager import ThreadCheckpointManager
            from src.core.threads.checkpoints.storage import ThreadCheckpointDomainService
            from src.core.threads.checkpoints.storage import CheckpointManager
            
            domain_service = container.get(ThreadCheckpointDomainService)
            checkpoint_manager = container.get(CheckpointManager)
            return ThreadCheckpointManager(
                domain_service=domain_service,
                checkpoint_manager=checkpoint_manager
            )
        
        from src.core.threads.checkpoints.manager import ThreadCheckpointManager
        container.register_factory(
            ThreadCheckpointManager,
            thread_checkpoint_manager_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册存储编排器
        def storage_orchestrator_factory():
            from src.services.storage.orchestrator import StorageOrchestrator
            from src.core.threads.checkpoints.storage import ThreadCheckpointDomainService
            from src.core.threads.checkpoints.manager import ThreadCheckpointManager
            from src.core.threads.checkpoints.storage import CheckpointManager
            
            checkpoint_domain_service = container.get(ThreadCheckpointDomainService)
            checkpoint_manager = container.get(ThreadCheckpointManager)
            checkpoint_storage_manager = container.get(CheckpointManager)
            
            return StorageOrchestrator(
                checkpoint_domain_service=checkpoint_domain_service,
                checkpoint_manager=checkpoint_manager,
                checkpoint_storage_manager=checkpoint_storage_manager
            )
        
        container.register_factory(
            IStorageService,
            storage_orchestrator_factory,
            lifetime=ServiceLifetime.SINGLETON
        )