"""线程服务依赖注入绑定配置"""

import logging
from typing import Dict, Any, List, Union

from src.adapters.storage.backends import SQLiteThreadBackend, FileThreadBackend
from src.services.threads.repository import ThreadRepository
from src.services.threads.basic_service import BasicThreadService
from src.services.threads.workflow_service import WorkflowThreadService
from src.services.threads.collaboration_service import ThreadCollaborationService
from src.services.threads.branch_service import ThreadBranchService
from src.services.threads.snapshot_service import ThreadSnapshotService
from src.services.threads.state_service import ThreadStateService
from src.services.threads.history_service import ThreadHistoryService
from src.services.threads.service import ThreadService

from src.interfaces.threads import IThreadRepository
from src.interfaces.threads.service import IThreadService
from src.interfaces.sessions.service import ISessionService
from src.core.threads.interfaces import IThreadCore
from src.interfaces.history import IHistoryManager
from src.interfaces.threads.checkpoint import IThreadCheckpointManager
from src.interfaces.common_infra import ILogger

# 导入日志绑定
from .logger_bindings import register_logger_services

logger = logging.getLogger(__name__)


def register_thread_backends(container: Any, config: Dict[str, Any]) -> None:
    """注册线程存储后端
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 主后端配置
    primary_backend_type = config.get("thread", {}).get("primary_backend", "sqlite")
    
    if primary_backend_type == "sqlite":
        sqlite_config = config.get("thread", {}).get("sqlite", {})
        db_path = sqlite_config.get("db_path", "./data/threads.db")
        primary_backend = SQLiteThreadBackend(db_path=db_path)
    else:
        raise ValueError(f"Unsupported primary backend type: {primary_backend_type}")
    
    # 辅助后端配置
    secondary_backends = []
    secondary_types = config.get("thread", {}).get("secondary_backends", [])
    
    for backend_type in secondary_types:
        if backend_type == "file":
            file_config = config.get("thread", {}).get("file", {})
            base_path = file_config.get("base_path", "./threads_backup")
            backend: Union[SQLiteThreadBackend, FileThreadBackend] = FileThreadBackend(base_path=base_path)
            secondary_backends.append(backend)
        elif backend_type == "sqlite":
            sqlite_config = config.get("thread", {}).get("sqlite_secondary", {})
            db_path = sqlite_config.get("db_path", "./data/threads_backup.db")
            backend = SQLiteThreadBackend(db_path=db_path)
            secondary_backends.append(backend)
        else:
            logger.warning(f"Unknown secondary backend type: {backend_type}")
    
    # 注册主后端为单例
    container.register_singleton("thread_primary_backend", primary_backend)
    
    # 注册辅助后端列表
    if secondary_backends:
        container.register_singleton("thread_secondary_backends", secondary_backends)
    
    logger.info(f"Thread backends registered: primary={primary_backend_type}, secondary={secondary_types}")


def register_thread_repository(container: Any, config: Dict[str, Any]) -> None:
    """注册线程仓储
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保后端已注册
    register_thread_backends(container, config)
    
    # 创建仓储工厂函数
    def thread_repository_factory() -> ThreadRepository:
        primary_backend = container.get("thread_primary_backend")
        secondary_backends = container.get("thread_secondary_backends", default=[])
        return ThreadRepository(primary_backend, secondary_backends)
    
    # 注册仓储为单例
    container.register_singleton("thread_repository", thread_repository_factory)
    
    # 注册接口
    container.register_singleton(
        IThreadRepository,
        lambda: container.get("thread_repository")
    )
    
    logger.info("Thread repository registered")


def register_basic_thread_service(container: Any, config: Dict[str, Any]) -> None:
    """注册基础线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保依赖已注册
    register_thread_repository(container, config)
    
    # 创建服务工厂函数
    def basic_thread_service_factory() -> BasicThreadService:
        thread_core = container.get(IThreadCore)
        thread_repository = container.get(IThreadRepository)
        checkpoint_domain_service = container.get("ThreadCheckpointDomainService", default=None)
        
        return BasicThreadService(
            thread_core=thread_core,
            thread_repository=thread_repository,
            checkpoint_domain_service=checkpoint_domain_service
        )
    
    # 注册服务为单例
    container.register_singleton("basic_thread_service", basic_thread_service_factory)
    
    logger.info("Basic thread service registered")


def register_workflow_thread_service(container: Any, config: Dict[str, Any]) -> None:
    """注册工作流线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保依赖已注册
    register_thread_repository(container, config)
    
    # 创建服务工厂函数
    def workflow_thread_service_factory() -> WorkflowThreadService:
        thread_repository = container.get(IThreadRepository)
        
        return WorkflowThreadService(
            thread_repository=thread_repository
        )
    
    # 注册服务为单例
    container.register_singleton("workflow_thread_service", workflow_thread_service_factory)
    
    logger.info("Workflow thread service registered")


def register_collaboration_thread_service(container: Any, config: Dict[str, Any]) -> None:
    """注册协作线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保依赖已注册
    register_thread_repository(container, config)
    
    # 创建服务工厂函数
    def collaboration_thread_service_factory() -> ThreadCollaborationService:
        thread_repository = container.get(IThreadRepository)
        checkpoint_manager = container.get(IThreadCheckpointManager, default=None)
        
        return ThreadCollaborationService(
            thread_repository=thread_repository,
            checkpoint_manager=checkpoint_manager
        )
    
    # 注册服务为单例
    container.register_singleton("collaboration_thread_service", collaboration_thread_service_factory)
    
    logger.info("Collaboration thread service registered")


def register_branch_thread_service(container: Any, config: Dict[str, Any]) -> None:
    """注册分支线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保依赖已注册
    register_thread_repository(container, config)
    
    # 创建服务工厂函数
    def branch_thread_service_factory() -> ThreadBranchService:
        thread_core = container.get(IThreadCore)
        thread_repository = container.get(IThreadRepository)
        
        # 需要IThreadBranchCore和IThreadBranchRepository
        # 这里简化处理，假设它们已经注册
        thread_branch_core = container.get("IThreadBranchCore", default=None)
        thread_branch_repository = container.get("IThreadBranchRepository", default=None)
        checkpoint_domain_service = container.get("ThreadCheckpointDomainService", default=None)
        
        if not thread_branch_core or not thread_branch_repository:
            logger.error("ThreadBranchCore or ThreadBranchRepository not available")
            raise ValueError("Required dependencies for ThreadBranchService are not available")
        
        return ThreadBranchService(
            thread_core=thread_core,
            thread_branch_core=thread_branch_core,
            thread_repository=thread_repository,
            thread_branch_repository=thread_branch_repository,
            checkpoint_domain_service=checkpoint_domain_service
        )
    
    # 注册服务为单例
    container.register_singleton("branch_thread_service", branch_thread_service_factory)
    
    logger.info("Branch thread service registered")


def register_snapshot_thread_service(container: Any, config: Dict[str, Any]) -> None:
    """注册快照线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保依赖已注册
    register_thread_repository(container, config)
    
    # 创建服务工厂函数
    def snapshot_thread_service_factory() -> ThreadSnapshotService:
        thread_core = container.get(IThreadCore)
        thread_repository = container.get(IThreadRepository)
        
        # 需要IThreadSnapshotCore和IThreadSnapshotRepository
        # 这里简化处理，假设它们已经注册
        thread_snapshot_core = container.get("IThreadSnapshotCore", default=None)
        thread_snapshot_repository = container.get("IThreadSnapshotRepository", default=None)
        
        if not thread_snapshot_core or not thread_snapshot_repository:
            logger.error("ThreadSnapshotCore or ThreadSnapshotRepository not available")
            raise ValueError("Required dependencies for ThreadSnapshotService are not available")
        
        return ThreadSnapshotService(
            thread_core=thread_core,
            thread_snapshot_core=thread_snapshot_core,
            thread_repository=thread_repository,
            thread_snapshot_repository=thread_snapshot_repository
        )
    
    # 注册服务为单例
    container.register_singleton("snapshot_thread_service", snapshot_thread_service_factory)
    
    logger.info("Snapshot thread service registered")




def register_state_thread_service(container: Any, config: Dict[str, Any]) -> None:
    """注册状态线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保依赖已注册
    register_thread_repository(container, config)
    
    # 创建服务工厂函数
    def state_thread_service_factory() -> ThreadStateService:
        thread_repository = container.get(IThreadRepository)
        
        return ThreadStateService(
            thread_repository=thread_repository
        )
    
    # 注册服务为单例
    container.register_singleton("state_thread_service", state_thread_service_factory)
    
    logger.info("State thread service registered")


def register_history_thread_service(container: Any, config: Dict[str, Any]) -> None:
    """注册历史线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保依赖已注册
    register_thread_repository(container, config)
    
    # 创建服务工厂函数
    def history_thread_service_factory() -> ThreadHistoryService:
        thread_repository = container.get(IThreadRepository)
        history_manager = container.get(IHistoryManager, default=None)
        
        return ThreadHistoryService(
            thread_repository=thread_repository,
            history_manager=history_manager
        )
    
    # 注册服务为单例
    container.register_singleton("history_thread_service", history_thread_service_factory)
    
    logger.info("History thread service registered")


def register_thread_service(container: Any, config: Dict[str, Any]) -> None:
    """注册主线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保所有子服务已注册
    register_basic_thread_service(container, config)
    register_workflow_thread_service(container, config)
    register_collaboration_thread_service(container, config)
    register_branch_thread_service(container, config)
    register_snapshot_thread_service(container, config)
    register_state_thread_service(container, config)
    register_history_thread_service(container, config)
    
    # 创建主服务工厂函数
    def thread_service_factory() -> ThreadService:
        thread_core = container.get(IThreadCore)
        thread_repository = container.get(IThreadRepository)
        basic_service = container.get("basic_thread_service")
        workflow_service = container.get("workflow_thread_service")
        collaboration_service = container.get("collaboration_thread_service")
        branch_service = container.get("branch_thread_service")
        snapshot_service = container.get("snapshot_thread_service")
        state_service = container.get("state_thread_service")
        history_service = container.get("history_thread_service")
        session_service = container.get(ISessionService, default=None)
        history_manager = container.get(IHistoryManager, default=None)
        logger = container.get(ILogger, default=None)
        
        return ThreadService(
            thread_core=thread_core,
            thread_repository=thread_repository,
            basic_service=basic_service,
            workflow_service=workflow_service,
            collaboration_service=collaboration_service,
            branch_service=branch_service,
            snapshot_service=snapshot_service,
            state_service=state_service,
            history_service=history_service,
            session_service=session_service,
            history_manager=history_manager,
            logger=logger
        )
    
    # 注册主服务为单例
    container.register_singleton("thread_service", thread_service_factory)
    
    # 注册接口
    container.register_singleton(
        IThreadService,
        lambda: container.get("thread_service")
    )
    
    logger.info("Main thread service registered")

def register_all_thread_services(container: Any, config: Dict[str, Any]) -> None:
    """注册所有线程相关服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 首先注册日志服务
    register_logger_services(container, config)
    
    register_thread_backends(container, config)
    register_thread_repository(container, config)
    register_thread_service(container, config)
    logger.info("All thread services registered")


# === 模拟服务类 ===

class MockThreadBranchService:
    """模拟分支服务"""
    
    async def create_branch_from_checkpoint(self, source_thread_id: str, checkpoint_id: str, branch_name: str, metadata: Dict[str, Any] | None = None) -> str:
        import uuid
        return str(uuid.uuid4())
    
    async def list_active_branches(self, thread_id: str) -> List[Dict[str, Any]]:
        return []
    
    async def merge_branch_to_main(self, thread_id: str, branch_id: str, merge_strategy: str = "overwrite") -> bool:
        return True


class MockThreadSnapshotService:
    """模拟快照服务"""
    
    async def create_snapshot_from_thread(self, thread_id: str, snapshot_name: str, description: str | None = None) -> str:
        import uuid
        return str(uuid.uuid4())
    
    async def restore_thread_from_snapshot(self, thread_id: str, snapshot_id: str) -> bool:
        return True