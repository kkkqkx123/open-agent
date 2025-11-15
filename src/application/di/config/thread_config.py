"""线程服务DI配置

负责注册线程服务相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.application.threads.interfaces import IThreadService
from src.application.threads.thread_service import ThreadService

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
        container.register_factory(
            IThreadService,
            lambda: ThreadService(
                thread_repository=container.get(
                    "src.domain.threads.repository.IThreadRepository"
                ) if container.has_service(
                    "src.domain.threads.repository.IThreadRepository"
                ) else None,
                thread_domain_service=container.get(
                    "src.domain.threads.domain_service.ThreadDomainService"
                ) if container.has_service(
                    "src.domain.threads.domain_service.ThreadDomainService"
                ) else None,
                branch_repository=container.get(
                    "src.domain.threads.repository.IThreadBranchRepository"
                ) if container.has_service(
                    "src.domain.threads.repository.IThreadBranchRepository"
                ) else None,
                snapshot_repository=container.get(
                    "src.domain.threads.repository.IThreadSnapshotRepository"
                ) if container.has_service(
                    "src.domain.threads.repository.IThreadSnapshotRepository"
                ) else None,
                checkpoint_manager=container.get(
                    "src.application.checkpoint.manager.ICheckpointManager"
                ) if container.has_service(
                    "src.application.checkpoint.manager.ICheckpointManager"
                ) else None,
                metadata_store=container.get(
                    "src.infrastructure.threads.metadata_store.IThreadMetadataStore"
                ) if container.has_service(
                    "src.infrastructure.threads.metadata_store.IThreadMetadataStore"
                ) else None,
                branch_store=container.get(
                    "src.infrastructure.threads.branch_store.IThreadBranchStore"
                ) if container.has_service(
                    "src.infrastructure.threads.branch_store.IThreadBranchStore"
                ) else None,
                snapshot_store=container.get(
                    "src.infrastructure.threads.snapshot_store.IThreadSnapshotStore"
                ) if container.has_service(
                    "src.infrastructure.threads.snapshot_store.IThreadSnapshotStore"
                ) else None,
                langgraph_adapter=container.get(
                    "src.infrastructure.langgraph.adapter.LangGraphAdapter"
                ) if container.has_service(
                    "src.infrastructure.langgraph.adapter.LangGraphAdapter"
                ) else None
            ),
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