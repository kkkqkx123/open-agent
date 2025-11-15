"""线程服务DI配置

负责注册线程服务相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.application.threads.interfaces import IThreadService
from src.application.threads.thread_service import ThreadService
from src.domain.threads.repository import IThreadRepository, IThreadBranchRepository, IThreadSnapshotRepository
from src.domain.threads.domain_service import ThreadDomainService
from src.application.checkpoint.manager import ICheckpointManager
from src.infrastructure.threads.metadata_store import IThreadMetadataStore
from src.infrastructure.threads.branch_store import IThreadBranchStore
from src.infrastructure.threads.snapshot_store import IThreadSnapshotStore
from src.infrastructure.langgraph.adapter import LangGraphAdapter

logger = logging.getLogger(__name__)


class ThreadConfigRegistration:
    """线程服务注册类
    
    负责注册线程服务相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册线程服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册线程服务")
        
        # 注册线程服务
        def create_thread_service() -> IThreadService:
            return ThreadService(
                thread_repository=container.get(IThreadRepository),
                thread_domain_service=container.get(ThreadDomainService),
                branch_repository=container.get(IThreadBranchRepository),
                snapshot_repository=container.get(IThreadSnapshotRepository),
                checkpoint_manager=container.get(ICheckpointManager),
                metadata_store=container.get(IThreadMetadataStore),
                branch_store=container.get(IThreadBranchStore),
                snapshot_store=container.get(IThreadSnapshotStore),
                langgraph_adapter=container.get(LangGraphAdapter),
            )
        
        container.register_factory(
            IThreadService,
            create_thread_service,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("线程服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "thread_service": IThreadService,
        }