"""线程服务依赖注入绑定配置

使用基础设施层组件，通过继承BaseServiceBindings简化代码。
重构后使用接口依赖，避免循环依赖。
"""

import sys
from typing import Dict, Any, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    # 仅在类型检查时导入，避免运行时循环依赖
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

# 接口导入 - 集中化的接口定义
from src.interfaces.threads import IThreadRepository
from src.interfaces.threads.service import IThreadService
from src.interfaces.sessions.service import ISessionService
from src.core.threads.interfaces import IThreadCore
from src.interfaces.history import IHistoryManager
from src.interfaces.threads.checkpoint import IThreadCheckpointManager
from src.interfaces.logger import ILogger
from src.interfaces.container.core import ServiceLifetime
from src.services.container.core.base_service_bindings import BaseServiceBindings


class ThreadServiceBindings(BaseServiceBindings):
    """Thread服务绑定类
    
    负责注册所有Thread相关服务，包括：
    - Thread存储后端
    - Thread仓储
    - 各种Thread服务（基础、工作流、协作、分支、快照、状态、历史）
    - 主Thread服务
    """
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证Thread配置"""
        # Thread服务通常不需要特殊验证
        pass
    
    def _do_register_services(
        self,
        container: Any,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """执行Thread服务注册"""
        _register_thread_backends(container, config, environment)
        _register_thread_repository(container, config, environment)
        _register_basic_thread_service(container, config, environment)
        _register_workflow_thread_service(container, config, environment)
        _register_collaboration_thread_service(container, config, environment)
        _register_branch_thread_service(container, config, environment)
        _register_snapshot_thread_service(container, config, environment)
        _register_state_thread_service(container, config, environment)
        _register_history_thread_service(container, config, environment)
        _register_thread_service(container, config, environment)
    
    def _post_register(
        self,
        container: Any,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """注册后处理"""
        # 设置注入层
        try:
            # 为Thread服务设置注入层
            service_types = [
                IThreadRepository,
                IThreadService,
                BasicThreadService,
                WorkflowThreadService,
                ThreadCollaborationService,
                ThreadBranchService,
                ThreadSnapshotService,
                ThreadStateService,
                ThreadHistoryService
            ]
            
            self.setup_injection_layer(container, service_types)
            
            # 设置全局实例（向后兼容）
            from src.services.threads.injection import (
                set_thread_repository_instance,
                set_thread_service_instance,
                set_basic_thread_service_instance,
                set_workflow_thread_service_instance,
                set_collaboration_thread_service_instance,
                set_branch_thread_service_instance,
                set_snapshot_thread_service_instance,
                set_state_thread_service_instance,
                set_history_thread_service_instance
            )
            
            if container.has_service(IThreadRepository):
                set_thread_repository_instance(container.get(IThreadRepository))
            
            if container.has_service(IThreadService):
                set_thread_service_instance(container.get(IThreadService))
            
            if container.has_service(BasicThreadService):
                set_basic_thread_service_instance(container.get(BasicThreadService))
            
            if container.has_service(WorkflowThreadService):
                set_workflow_thread_service_instance(container.get(WorkflowThreadService))
            
            if container.has_service(ThreadCollaborationService):
                set_collaboration_thread_service_instance(container.get(ThreadCollaborationService))
            
            if container.has_service(ThreadBranchService):
                set_branch_thread_service_instance(container.get(ThreadBranchService))
            
            if container.has_service(ThreadSnapshotService):
                set_snapshot_thread_service_instance(container.get(ThreadSnapshotService))
            
            if container.has_service(ThreadStateService):
                set_state_thread_service_instance(container.get(ThreadStateService))
            
            if container.has_service(ThreadHistoryService):
                set_history_thread_service_instance(container.get(ThreadHistoryService))
            
            logger = self.safe_get_service(container, ILogger)
            if logger:
                logger.debug(f"已设置Thread服务注入层 (environment: {environment})")
        except Exception as e:
            print(f"[WARNING] 设置Thread注入层失败: {e}", file=sys.stderr)


def _register_thread_backends(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册线程存储后端
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 主后端配置
    primary_backend_type = config.get("thread", {}).get("primary_backend", "sqlite")
    
    # 延迟导入具体实现，避免循环依赖
    def create_primary_backend() -> 'SQLiteThreadBackend':
        if primary_backend_type == "sqlite":
            from src.adapters.storage.backends import SQLiteThreadBackend
            sqlite_config = config.get("thread", {}).get("sqlite", {})
            db_path = sqlite_config.get("db_path", "./data/threads.db")
            return SQLiteThreadBackend(db_path=db_path)
        else:
            raise ValueError(f"Unsupported primary backend type: {primary_backend_type}")
    
    def create_secondary_backends() -> List[Union['SQLiteThreadBackend', 'FileThreadBackend']]:
        secondary_backends = []
        secondary_types = config.get("thread", {}).get("secondary_backends", [])
        
        for backend_type in secondary_types:
            if backend_type == "file":
                from src.adapters.storage.backends import FileThreadBackend
                file_config = config.get("thread", {}).get("file", {})
                base_path = file_config.get("base_path", "./threads_backup")
                backend: Union[SQLiteThreadBackend, FileThreadBackend] = FileThreadBackend(base_path=base_path)
                secondary_backends.append(backend)
            elif backend_type == "sqlite":
                from src.adapters.storage.backends import SQLiteThreadBackend
                sqlite_config = config.get("thread", {}).get("sqlite_secondary", {})
                db_path = sqlite_config.get("db_path", "./data/threads_backup.db")
                backend = SQLiteThreadBackend(db_path=db_path)
                secondary_backends.append(backend)
            else:
                print(f"[WARNING] Unknown secondary backend type: {backend_type}", file=sys.stderr)
        
        return secondary_backends
    
    # 注册主后端为单例
    container.register(
        "thread_primary_backend",
        create_primary_backend,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册辅助后端列表
    secondary_types = config.get("thread", {}).get("secondary_backends", [])
    if secondary_types:
        container.register(
            "thread_secondary_backends",
            create_secondary_backends,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
    
    print(f"[INFO] Thread backends registered: primary={primary_backend_type}, secondary={secondary_types}", file=sys.stdout)


def _register_thread_repository(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册线程仓储
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保后端已注册
    _register_thread_backends(container, config, environment)
    
    # 创建仓储工厂函数
    def thread_repository_factory() -> ThreadRepository:
        from src.services.threads.repository import ThreadRepository
        primary_backend = container.get("thread_primary_backend")
        secondary_backends = container.get("thread_secondary_backends", default=[])
        return ThreadRepository(primary_backend, secondary_backends)
    
    # 注册仓储为单例
    container.register(
        "thread_repository",
        thread_repository_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册接口
    container.register(
        IThreadRepository,
        lambda: container.get("thread_repository"),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Thread repository registered", file=sys.stdout)


def _register_basic_thread_service(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册基础线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保依赖已注册
    _register_thread_repository(container, config, environment)
    
    # 创建服务工厂函数
    def basic_thread_service_factory() -> BasicThreadService:
        from src.services.threads.basic_service import BasicThreadService
        thread_core = container.get(IThreadCore)
        thread_repository = container.get(IThreadRepository)
        checkpoint_domain_service = container.get("ThreadCheckpointDomainService", default=None)
        
        return BasicThreadService(
            thread_core=thread_core,
            thread_repository=thread_repository,
            checkpoint_domain_service=checkpoint_domain_service
        )
    
    # 注册服务为单例
    container.register(
        "basic_thread_service",
        basic_thread_service_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Basic thread service registered", file=sys.stdout)


def _register_workflow_thread_service(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册工作流线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保依赖已注册
    _register_thread_repository(container, config, environment)
    
    # 创建服务工厂函数
    def workflow_thread_service_factory() -> WorkflowThreadService:
        from src.services.threads.workflow_service import WorkflowThreadService
        thread_repository = container.get(IThreadRepository)
        
        return WorkflowThreadService(
            thread_repository=thread_repository
        )
    
    # 注册服务为单例
    container.register(
        "workflow_thread_service",
        workflow_thread_service_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Workflow thread service registered", file=sys.stdout)


def _register_collaboration_thread_service(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册协作线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保依赖已注册
    _register_thread_repository(container, config, environment)
    
    # 创建服务工厂函数
    def collaboration_thread_service_factory() -> ThreadCollaborationService:
        from src.services.threads.collaboration_service import ThreadCollaborationService
        thread_repository = container.get(IThreadRepository)
        checkpoint_manager = container.get(IThreadCheckpointManager, default=None)
        
        return ThreadCollaborationService(
            thread_repository=thread_repository,
            checkpoint_manager=checkpoint_manager
        )
    
    # 注册服务为单例
    container.register(
        "collaboration_thread_service",
        collaboration_thread_service_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Collaboration thread service registered", file=sys.stdout)


def _register_branch_thread_service(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册分支线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保依赖已注册
    _register_thread_repository(container, config, environment)
    
    # 创建服务工厂函数
    def branch_thread_service_factory() -> ThreadBranchService:
        from src.services.threads.branch_service import ThreadBranchService
        thread_core = container.get(IThreadCore)
        thread_repository = container.get(IThreadRepository)
        
        # 需要IThreadBranchCore和IThreadBranchRepository
        # 这里简化处理，假设它们已经注册
        thread_branch_core = container.get("IThreadBranchCore", default=None)
        thread_branch_repository = container.get("IThreadBranchRepository", default=None)
        checkpoint_domain_service = container.get("ThreadCheckpointDomainService", default=None)
        
        if not thread_branch_core or not thread_branch_repository:
            print(f"[ERROR] ThreadBranchCore or ThreadBranchRepository not available", file=sys.stderr)
            raise ValueError("Required dependencies for ThreadBranchService are not available")
        
        return ThreadBranchService(
            thread_core=thread_core,
            thread_branch_core=thread_branch_core,
            thread_repository=thread_repository,
            thread_branch_repository=thread_branch_repository,
            checkpoint_domain_service=checkpoint_domain_service
        )
    
    # 注册服务为单例
    container.register(
        "branch_thread_service",
        branch_thread_service_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Branch thread service registered", file=sys.stdout)


def _register_snapshot_thread_service(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册快照线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保依赖已注册
    _register_thread_repository(container, config, environment)
    
    # 创建服务工厂函数
    def snapshot_thread_service_factory() -> ThreadSnapshotService:
        from src.services.threads.snapshot_service import ThreadSnapshotService
        thread_core = container.get(IThreadCore)
        thread_repository = container.get(IThreadRepository)
        
        # 需要IThreadSnapshotCore和IThreadSnapshotRepository
        # 这里简化处理，假设它们已经注册
        thread_snapshot_core = container.get("IThreadSnapshotCore", default=None)
        thread_snapshot_repository = container.get("IThreadSnapshotRepository", default=None)
        
        if not thread_snapshot_core or not thread_snapshot_repository:
            print(f"[ERROR] ThreadSnapshotCore or ThreadSnapshotRepository not available", file=sys.stderr)
            raise ValueError("Required dependencies for ThreadSnapshotService are not available")
        
        return ThreadSnapshotService(
            thread_core=thread_core,
            thread_snapshot_core=thread_snapshot_core,
            thread_repository=thread_repository,
            thread_snapshot_repository=thread_snapshot_repository
        )
    
    # 注册服务为单例
    container.register(
        "snapshot_thread_service",
        snapshot_thread_service_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Snapshot thread service registered", file=sys.stdout)




def _register_state_thread_service(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册状态线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保依赖已注册
    _register_thread_repository(container, config, environment)
    
    # 创建服务工厂函数
    def state_thread_service_factory() -> ThreadStateService:
        from src.services.threads.state_service import ThreadStateService
        thread_repository = container.get(IThreadRepository)
        
        return ThreadStateService(
            thread_repository=thread_repository
        )
    
    # 注册服务为单例
    container.register(
        "state_thread_service",
        state_thread_service_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] State thread service registered", file=sys.stdout)


def _register_history_thread_service(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册历史线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保依赖已注册
    _register_thread_repository(container, config, environment)
    
    # 创建服务工厂函数
    def history_thread_service_factory() -> ThreadHistoryService:
        from src.services.threads.history_service import ThreadHistoryService
        thread_repository = container.get(IThreadRepository)
        history_manager = container.get(IHistoryManager, default=None)
        
        return ThreadHistoryService(
            thread_repository=thread_repository,
            history_manager=history_manager
        )
    
    # 注册服务为单例
    container.register(
        "history_thread_service",
        history_thread_service_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] History thread service registered", file=sys.stdout)


def _register_thread_service(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册主线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保所有子服务已注册
    _register_basic_thread_service(container, config, environment)
    _register_workflow_thread_service(container, config, environment)
    _register_collaboration_thread_service(container, config, environment)
    _register_branch_thread_service(container, config, environment)
    _register_snapshot_thread_service(container, config, environment)
    _register_state_thread_service(container, config, environment)
    _register_history_thread_service(container, config, environment)
    
    # 创建主服务工厂函数
    def thread_service_factory() -> ThreadService:
        from src.services.threads.service import ThreadService
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
    container.register(
        "thread_service",
        thread_service_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册接口
    container.register(
        IThreadService,
        lambda: container.get("thread_service"),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Main thread service registered", file=sys.stdout)

