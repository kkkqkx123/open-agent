"""依赖注入配置更新 - 支持新的业务服务架构"""

from typing import Dict, Any

from src.services.container.container import DependencyContainer
from src.services.container.registry import ServiceRegistry
from src.services.container.lifecycle import ServiceLifetime

# 核心接口导入
from src.core.sessions.interfaces import ISessionCore
from src.core.threads.interfaces import IThreadCore, IThreadBranchCore, IThreadSnapshotCore, IThreadCoordinatorCore

# 业务服务接口导入
from src.interfaces.sessions import ISessionService, ISessionStore
from src.interfaces.threads import (
    IThreadService, IThreadStore,
    IThreadBranchService, IThreadBranchStore,
    IThreadSnapshotService, IThreadSnapshotStore,
    IThreadCoordinatorService
)

# 存储适配器导入
from src.adapters.storage import SQLiteSessionStore, SQLiteThreadStore

# 业务服务实现导入
from src.services.sessions import SessionService
from src.services.threads import (
    ThreadService, ThreadBranchService, 
    ThreadSnapshotService, ThreadCoordinatorService
)

# 核心实现导入
from src.core.sessions import SessionCore
from src.core.threads import ThreadCore, ThreadBranchCore, ThreadSnapshotCore, ThreadCoordinatorCore


def configure_new_services(container: DependencyContainer) -> None:
    """配置新的业务服务和存储适配器"""
    
    # 存储适配器注册
    container.register_singleton(
        ISessionStore,
        lambda: SQLiteSessionStore("data/sessions.db")
    )
    
    container.register_singleton(
        IThreadStore,
        lambda: SQLiteThreadStore("data/threads.db")
    )
    
    # 核心层注册
    container.register_singleton(
        ISessionCore,
        lambda c: SessionCore()
    )
    
    container.register_singleton(
        IThreadCore,
        lambda c: ThreadCore()
    )
    
    container.register_singleton(
        IThreadBranchCore,
        lambda c: ThreadBranchCore()
    )
    
    container.register_singleton(
        IThreadSnapshotCore,
        lambda c: ThreadSnapshotCore()
    )
    
    container.register_singleton(
        IThreadCoordinatorCore,
        lambda c: ThreadCoordinatorCore()
    )
    
    # 业务服务层注册
    container.register_singleton(
        ISessionService,
        lambda c: SessionService(
            session_core=c.resolve(ISessionCore),
            session_store=c.resolve(ISessionStore)
        )
    )
    
    container.register_singleton(
        IThreadService,
        lambda c: ThreadService(
            thread_core=c.resolve(IThreadCore),
            thread_store=c.resolve(IThreadStore),
            session_store=c.resolve(ISessionStore)
        )
    )
    
    container.register_singleton(
        IThreadBranchService,
        lambda c: ThreadBranchService(
            branch_core=c.resolve(IThreadBranchCore),
            branch_store=c.resolve(IThreadBranchStore),
            thread_store=c.resolve(IThreadStore)
        )
    )
    
    container.register_singleton(
        IThreadSnapshotService,
        lambda c: ThreadSnapshotService(
            snapshot_core=c.resolve(IThreadSnapshotCore),
            snapshot_store=c.resolve(IThreadSnapshotStore),
            thread_store=c.resolve(IThreadStore)
        )
    )
    
    container.register_singleton(
        IThreadCoordinatorService,
        lambda c: ThreadCoordinatorService(
            coordinator_core=c.resolve(IThreadCoordinatorCore),
            thread_store=c.resolve(IThreadStore),
            session_store=c.resolve(ISessionStore)
        )
    )


def create_service_registry() -> ServiceRegistry:
    """创建服务注册表"""
    registry = ServiceRegistry()
    
    # 注册服务映射
    registry.register("session_service", ISessionService)
    registry.register("thread_service", IThreadService)
    registry.register("thread_branch_service", IThreadBranchService)
    registry.register("thread_snapshot_service", IThreadSnapshotService)
    registry.register("thread_coordinator_service", IThreadCoordinatorService)
    
    registry.register("session_store", ISessionStore)
    registry.register("thread_store", IThreadStore)
    registry.register("thread_branch_store", IThreadBranchStore)
    registry.register("thread_snapshot_store", IThreadSnapshotStore)
    
    return registry


def get_service_configuration() -> Dict[str, Any]:
    """获取服务配置"""
    return {
        "services": {
            "session_service": {
                "implementation": "SessionService",
                "dependencies": ["ISessionCore", "ISessionStore"],
                "lifetime": "singleton"
            },
            "thread_service": {
                "implementation": "ThreadService", 
                "dependencies": ["IThreadCore", "IThreadStore", "ISessionStore"],
                "lifetime": "singleton"
            },
            "thread_branch_service": {
                "implementation": "ThreadBranchService",
                "dependencies": ["IThreadBranchCore", "IThreadBranchStore", "IThreadStore"],
                "lifetime": "singleton"
            },
            "thread_snapshot_service": {
                "implementation": "ThreadSnapshotService",
                "dependencies": ["IThreadSnapshotCore", "IThreadSnapshotStore", "IThreadStore"],
                "lifetime": "singleton"
            },
            "thread_coordinator_service": {
                "implementation": "ThreadCoordinatorService",
                "dependencies": ["IThreadCoordinatorCore", "IThreadStore", "ISessionStore"],
                "lifetime": "singleton"
            }
        },
        "stores": {
            "session_store": {
                "implementation": "SQLiteSessionStore",
                "config": {"db_path": "data/sessions.db"}
            },
            "thread_store": {
                "implementation": "SQLiteThreadStore",
                "config": {"db_path": "data/threads.db"}
            }
        }
    }