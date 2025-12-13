"""
线程服务绑定
"""

from typing import Dict, Any
from src.interfaces.threads import IThreadService
from src.interfaces.container.core import IDependencyContainer, ServiceLifetime

class ThreadServiceBindings:
    """线程服务绑定"""
    
    def register_services(self, container: IDependencyContainer, config: Dict[str, Any]):
        """注册线程服务
        
        Args:
            container: 依赖注入容器
            config: 配置信息
        """
        # 注册线程服务
        def thread_service_factory():
            from src.services.threads.service import ThreadService
            from src.core.threads.factories import ThreadFactory, ThreadBranchFactory, ThreadSnapshotFactory
            from src.services.threads.basic_service import BasicThreadService
            from src.services.threads.workflow_service import WorkflowThreadService
            from src.services.threads.collaboration_service import ThreadCollaborationService
            from src.services.threads.branch_service import ThreadBranchService
            from src.services.threads.snapshot_service import ThreadSnapshotService
            from src.services.threads.state_service import ThreadStateService
            from src.services.threads.history_service import ThreadHistoryService
            
            # 获取日志实例
            try:
                from src.interfaces.logger import ILogger
                logger = container.get(ILogger)
            except:
                logger = None
            
            # 获取线程存储库实例
            try:
                from src.interfaces.threads.storage import IThreadRepository
                thread_repository = container.get(IThreadRepository)
            except:
                thread_repository = None
            
            # 获取分支和快照存储库实例
            try:
                from src.interfaces.threads import IThreadBranchRepository
                thread_branch_repository = container.get(IThreadBranchRepository)
            except:
                thread_branch_repository = None  # type: ignore[assignment]
            
            try:
                from src.interfaces.threads import IThreadSnapshotRepository
                thread_snapshot_repository = container.get(IThreadSnapshotRepository)
            except:
                thread_snapshot_repository = None  # type: ignore[assignment]
            
            # 创建线程核心工厂
            thread_core = ThreadFactory()
            thread_branch_core = ThreadBranchFactory()
            thread_snapshot_core = ThreadSnapshotFactory()
            
            # 创建各种线程服务
            # 注意：这里thread_repository可能为None，但框架支持此情况
            basic_service = BasicThreadService(thread_core, thread_repository)  # type: ignore[arg-type]
            workflow_service = WorkflowThreadService(thread_repository)  # type: ignore[arg-type]
            collaboration_service = ThreadCollaborationService(thread_repository)  # type: ignore[arg-type]
            branch_service = ThreadBranchService(
                thread_core,
                thread_branch_core,
                thread_repository,  # type: ignore[arg-type]
                thread_branch_repository  # type: ignore[arg-type]
            )
            snapshot_service = ThreadSnapshotService(
                thread_core,
                thread_snapshot_core,
                thread_repository,  # type: ignore[arg-type]
                thread_snapshot_repository  # type: ignore[arg-type]
            )
            state_service = ThreadStateService(thread_repository)  # type: ignore[arg-type]
            history_service = ThreadHistoryService(thread_repository, None)  # type: ignore[arg-type]
            
            return ThreadService(
                thread_core=thread_core,
                thread_repository=thread_repository,  # type: ignore[arg-type]
                basic_service=basic_service,
                workflow_service=workflow_service,
                collaboration_service=collaboration_service,
                branch_service=branch_service,
                snapshot_service=snapshot_service,
                state_service=state_service,
                history_service=history_service,
                session_service=None,
                history_manager=None,
                logger=logger
            )
        
        container.register_factory(
            IThreadService,
            thread_service_factory,
            lifetime=ServiceLifetime.SINGLETON
        )