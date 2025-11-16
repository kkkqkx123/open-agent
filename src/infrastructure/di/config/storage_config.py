"""存储服务DI配置

负责注册存储系统相关服务。
"""

import logging
from typing import Dict, Type
from pathlib import Path

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.domain.checkpoint.interfaces import ICheckpointStore
from src.infrastructure.checkpoint.sqlite_store import SQLiteCheckpointStore
from src.domain.sessions.store import ISessionStore, FileSessionStore
from src.infrastructure.threads.metadata_store import IThreadMetadataStore, FileThreadMetadataStore
from src.infrastructure.state.interfaces import IStateSnapshotStore, IStateHistoryManager
from src.infrastructure.state.sqlite_snapshot_store import SQLiteSnapshotStore
from src.infrastructure.state.sqlite_history_manager import SQLiteHistoryManager

logger = logging.getLogger(__name__)


class StorageConfigRegistration:
    """存储服务注册类
    
    负责注册存储系统相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册存储服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册存储系统服务")
        
        # 注册检查点存储
        container.register_factory(
            ICheckpointStore,
            lambda: SQLiteCheckpointStore(),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册会话存储
        container.register_factory(
            ISessionStore,
            lambda: FileSessionStore(Path("./history")),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册线程元数据存储
        container.register_factory(
            IThreadMetadataStore,
            lambda: FileThreadMetadataStore(Path("./storage/threads")),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册状态快照存储
        container.register_factory(
            IStateSnapshotStore,
            lambda: SQLiteSnapshotStore(Path("./storage/state_snapshots")),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册状态历史管理器
        container.register_factory(
            IStateHistoryManager,
            lambda: SQLiteHistoryManager(Path("./storage/state_history")),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("存储系统服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "checkpoint_store": ICheckpointStore,
            "session_store": ISessionStore,
            "thread_metadata_store": IThreadMetadataStore,
            "state_snapshot_store": IStateSnapshotStore,
            "state_history_manager": IStateHistoryManager,
        }