"""Thread检查点依赖注入绑定

配置Thread检查点相关服务的依赖注入。
"""

from src.services.logger import get_logger
from typing import Dict, Any

from src.services.container import DependencyContainer
from src.core.threads.checkpoints.storage import (
    ThreadCheckpointDomainService,
    CheckpointManager,
    ThreadCheckpointRepository,
    IThreadCheckpointRepository
)
from src.core.threads.checkpoints.manager import ThreadCheckpointManager
from src.core.common.types import ServiceLifetime
from src.services.storage import (
    StorageOrchestrator,
    ThreadStorageService,
    StorageConfigManager
)
from src.adapters.threads.checkpoints import (
    LangGraphCheckpointAdapter,
    MemoryLangGraphCheckpointAdapter
)


logger = get_logger(__name__)


def register_thread_checkpoint_services(container: DependencyContainer, config: Dict[str, Any]) -> None:
    """注册Thread检查点相关服务
    
    Args:
        container: 依赖注入容器
        config: 配置参数
    """
    try:
        # 1. 注册存储后端（根据配置选择）
        storage_backend_type = config.get("storage_backend", "memory")
        
        if storage_backend_type == "memory":
            container.register_factory(
                IThreadCheckpointRepository,
                lambda: ThreadCheckpointRepository(
                    MemoryLangGraphCheckpointAdapter()._checkpointer
                ),
                lifetime=ServiceLifetime.SINGLETON
            )
        elif storage_backend_type == "langgraph":
            # 如果有自定义的LangGraph检查点保存器
            langgraph_checkpointer = config.get("langgraph_checkpointer")
            if langgraph_checkpointer:
                container.register_factory(
                    IThreadCheckpointRepository,
                    lambda: ThreadCheckpointRepository(
                        LangGraphCheckpointAdapter(langgraph_checkpointer)
                    ),
                    lifetime=ServiceLifetime.SINGLETON
                )
            else:
                logger.warning("LangGraph checkpointer not provided, using memory adapter")
                container.register_factory(
                    IThreadCheckpointRepository,
                    lambda: ThreadCheckpointRepository(
                        MemoryLangGraphCheckpointAdapter()._checkpointer
                    ),
                    lifetime=ServiceLifetime.SINGLETON
                )
        else:
            raise ValueError(f"Unsupported storage backend type: {storage_backend_type}")
        
        # 2. 注册核心领域服务
        container.register_factory(
            ThreadCheckpointDomainService,
            lambda: ThreadCheckpointDomainService(
                container.get(IThreadCheckpointRepository)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 3. 注册检查点管理器
        container.register_factory(
            CheckpointManager,
            lambda: CheckpointManager(
                container.get(ThreadCheckpointDomainService)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 4. 注册Thread检查点管理器
        container.register_factory(
            ThreadCheckpointManager,
            lambda: ThreadCheckpointManager(
                container.get(ThreadCheckpointDomainService),
                container.get(CheckpointManager)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 5. 注册存储编排器
        container.register_factory(
            StorageOrchestrator,
            lambda: StorageOrchestrator(
                container.get(ThreadCheckpointDomainService),
                container.get(ThreadCheckpointManager),
                container.get(CheckpointManager)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 6. 注册Thread存储服务
        container.register_factory(
            ThreadStorageService,
            lambda: ThreadStorageService(
                container.get(StorageOrchestrator),
                container.get(ThreadCheckpointDomainService)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 7. 注册存储配置管理器
        container.register_factory(
            StorageConfigManager,
            lambda: StorageConfigManager(),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.info("Thread checkpoint services registered successfully")
        
    except Exception as e:
        logger.error(f"Failed to register thread checkpoint services: {e}")
        raise


def register_thread_checkpoint_services_with_custom_backend(
    container: DependencyContainer, 
    custom_backend: Any
) -> None:
    """注册Thread检查点服务，使用自定义后端
    
    Args:
        container: 依赖注入容器
        custom_backend: 自定义存储后端
    """
    try:
        # 注册自定义存储后端
        container.register_factory(
            IThreadCheckpointRepository,
            lambda: ThreadCheckpointRepository(custom_backend),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册其他服务
        container.register_factory(
            ThreadCheckpointDomainService,
            lambda: ThreadCheckpointDomainService(
                container.get(IThreadCheckpointRepository)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        container.register_factory(
            CheckpointManager,
            lambda: CheckpointManager(
                container.get(ThreadCheckpointDomainService)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        container.register_factory(
            ThreadCheckpointManager,
            lambda: ThreadCheckpointManager(
                container.get(ThreadCheckpointDomainService),
                container.get(CheckpointManager)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        container.register_factory(
            StorageOrchestrator,
            lambda: StorageOrchestrator(
                container.get(ThreadCheckpointDomainService),
                container.get(ThreadCheckpointManager),
                container.get(CheckpointManager)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        container.register_factory(
            ThreadStorageService,
            lambda: ThreadStorageService(
                container.get(StorageOrchestrator),
                container.get(ThreadCheckpointDomainService)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.info("Thread checkpoint services registered with custom backend")
        
    except Exception as e:
        logger.error(f"Failed to register thread checkpoint services with custom backend: {e}")
        raise


def register_thread_checkpoint_test_services(container: DependencyContainer) -> None:
    """注册Thread检查点测试服务
    
    Args:
        container: 依赖注入容器
    """
    try:
        # 注册内存存储后端用于测试
        container.register_factory(
            IThreadCheckpointRepository,
            lambda: ThreadCheckpointRepository(
                MemoryLangGraphCheckpointAdapter()._checkpointer
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册其他服务
        container.register_factory(
            ThreadCheckpointDomainService,
            lambda: ThreadCheckpointDomainService(
                container.get(IThreadCheckpointRepository)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        container.register_factory(
            CheckpointManager,
            lambda: CheckpointManager(
                container.get(ThreadCheckpointDomainService)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        container.register_factory(
            ThreadCheckpointManager,
            lambda: ThreadCheckpointManager(
                container.get(ThreadCheckpointDomainService),
                container.get(CheckpointManager)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        container.register_factory(
            StorageOrchestrator,
            lambda: StorageOrchestrator(
                container.get(ThreadCheckpointDomainService),
                container.get(ThreadCheckpointManager),
                container.get(CheckpointManager)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        container.register_factory(
            ThreadStorageService,
            lambda: ThreadStorageService(
                container.get(StorageOrchestrator),
                container.get(ThreadCheckpointDomainService)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.info("Thread checkpoint test services registered successfully")
        
    except Exception as e:
        logger.error(f"Failed to register thread checkpoint test services: {e}")
        raise


def get_thread_checkpoint_service_config() -> Dict[str, Any]:
    """获取Thread检查点服务配置
    
    Returns:
        默认配置字典
    """
    return {
        "storage_backend": "memory",  # memory, langgraph
        "langgraph_checkpointer": None,  # 可选的自定义LangGraph检查点保存器
        "checkpoint_limits": {
            "max_checkpoints_per_thread": 100,
            "default_expiration_hours": 24,
            "max_checkpoint_size_mb": 100
        },
        "cleanup_settings": {
            "cleanup_interval_hours": 1,
            "archive_days": 30,
            "min_checkpoint_age_hours_for_cleanup": 1
        },
        "backup_settings": {
            "auto_backup_important_checkpoints": True,
            "max_backups_per_checkpoint": 5
        }
    }
