"""状态管理依赖注入配置

配置状态管理相关服务的依赖注入。
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, TYPE_CHECKING

from src.infrastructure.infrastructure_types import ServiceLifetime

if TYPE_CHECKING:
    from src.interfaces.container import IDependencyContainer as ServiceContainer
else:
    ServiceContainer = Any  # type: ignore
from src.interfaces.state.serializer import IStateSerializer
from src.interfaces.state.history import IStateHistoryManager
from src.interfaces.state.snapshot import IStateSnapshotManager
from src.core.state.core.base import BaseStateSerializer
from src.services.state import (
    EnhancedStateManager,
    StateHistoryService,
    StateSnapshotService,
    StatePersistenceService,
    StateBackupService,
    WorkflowStateManager
)
from src.interfaces.repository import IHistoryRepository, ISnapshotRepository


logger = logging.getLogger(__name__)


def configure_state_services(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置状态管理服务
    
    Args:
        container: 服务容器
        config: 配置字典
    """
    try:
        # 配置序列化器
        _configure_serializer(container, config.get("serialization", {}))
        
        # 配置Repository实现
        _configure_repositories(container, config.get("storage", {}))
        
        # 配置历史管理服务（使用Repository）
        _configure_history_service_with_repository(container, config.get("history", {}))
        
        # 配置快照管理服务（使用Repository）
        _configure_snapshot_service_with_repository(container, config.get("snapshots", {}))
        
        # 配置增强状态管理器
        _configure_enhanced_state_manager(container, config)
        
        # 配置持久化服务（使用Repository）
        _configure_persistence_service_with_repository(container, config.get("performance", {}))
        
        # 配置备份服务
        _configure_backup_service(container)
        
        # 配置工作流状态管理器
        _configure_workflow_state_manager(container, config)
        
        logger.info("状态管理服务依赖注入配置完成")
        
    except Exception as e:
        logger.error(f"配置状态管理服务失败: {e}")
        raise


def _configure_serializer(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置序列化器"""
    format_type = config.get("format", "json")
    compression = config.get("compression", True)
    
    def serializer_factory() -> IStateSerializer:
        return BaseStateSerializer(format=format_type, compression=compression)
    
    container.register_factory(
        IStateSerializer,
        serializer_factory,
        lifetime=ServiceLifetime.SINGLETON
    )


def _configure_repositories(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置Repository实现"""
    default_storage = config.get("default", "sqlite")
    storage_configs = config.get("sqlite", {})
    
    def history_repository_factory() -> IHistoryRepository:
        # 创建历史记录Repository
        if default_storage == "sqlite":
            from src.adapters.repository.history.sqlite_repository import SQLiteHistoryRepository
            # 确保配置中包含数据库路径
            if "db_path" not in storage_configs:
                storage_configs["db_path"] = "data/state_storage.db"
            return SQLiteHistoryRepository(**storage_configs)
        elif default_storage == "memory":
            from src.adapters.repository.history.memory_repository import MemoryHistoryRepository
            return MemoryHistoryRepository()
        else:
            from src.adapters.repository.history.sqlite_repository import SQLiteHistoryRepository
            if "db_path" not in storage_configs:
                storage_configs["db_path"] = "data/state_storage.db"
            return SQLiteHistoryRepository(**storage_configs)
    
    def snapshot_repository_factory() -> ISnapshotRepository:
        # 创建快照Repository
        if default_storage == "sqlite":
            from src.adapters.repository.snapshot.sqlite_repository import SQLiteSnapshotRepository
            # 确保配置中包含数据库路径
            if "db_path" not in storage_configs:
                storage_configs["db_path"] = "data/state_storage.db"
            return SQLiteSnapshotRepository(**storage_configs)
        elif default_storage == "memory":
            from src.adapters.repository.snapshot.memory_repository import MemorySnapshotRepository
            return MemorySnapshotRepository()
        else:
            from src.adapters.repository.snapshot.sqlite_repository import SQLiteSnapshotRepository
            if "db_path" not in storage_configs:
                storage_configs["db_path"] = "data/state_storage.db"
            return SQLiteSnapshotRepository(**storage_configs)
    
    container.register_factory(
        IHistoryRepository,
        history_repository_factory,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    container.register_factory(
        ISnapshotRepository,
        snapshot_repository_factory,
        lifetime=ServiceLifetime.SINGLETON
    )




def _configure_enhanced_state_manager(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置增强状态管理器"""
    def state_manager_factory() -> EnhancedStateManager:
        # 从容器获取依赖
        history_manager: IStateHistoryManager = container.get(IStateHistoryManager)  # type: ignore
        snapshot_manager: IStateSnapshotManager = container.get(IStateSnapshotManager)  # type: ignore
        serializer: IStateSerializer = container.get(IStateSerializer)  # type: ignore
        return EnhancedStateManager(
            history_manager=history_manager,
            snapshot_manager=snapshot_manager,
            serializer=serializer
        )
    
    container.register_factory(
        EnhancedStateManager,
        state_manager_factory,
        lifetime=ServiceLifetime.SINGLETON
    )


def _configure_persistence_service_with_repository(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置持久化服务（使用Repository）"""
    enable_transactions = config.get("enable_transactions", True)
    
    def persistence_service_factory() -> StatePersistenceService:
        # 从容器获取依赖
        history_repository: IHistoryRepository = container.get(IHistoryRepository)  # type: ignore
        snapshot_repository: ISnapshotRepository = container.get(ISnapshotRepository)  # type: ignore
        return StatePersistenceService(
            history_repository=history_repository,
            snapshot_repository=snapshot_repository,
            enable_transactions=enable_transactions
        )
    
    container.register_factory(
        StatePersistenceService,
        persistence_service_factory,
        lifetime=ServiceLifetime.SINGLETON
    )


def _configure_backup_service(container: ServiceContainer) -> None:
    """配置备份服务"""
    def backup_service_factory() -> StateBackupService:
        # 从容器获取依赖
        persistence_service: StatePersistenceService = container.get(StatePersistenceService)
        return StateBackupService(persistence_service)
    
    container.register_factory(
        StateBackupService,
        backup_service_factory,
        lifetime=ServiceLifetime.SINGLETON
    )


def _configure_workflow_state_manager(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置工作流状态管理器"""
    def workflow_state_manager_factory() -> WorkflowStateManager:
        # 从容器获取依赖
        history_manager: IStateHistoryManager = container.get(IStateHistoryManager)  # type: ignore
        snapshot_manager: IStateSnapshotManager = container.get(IStateSnapshotManager)  # type: ignore
        serializer: IStateSerializer = container.get(IStateSerializer)  # type: ignore
        return WorkflowStateManager(
            history_manager=history_manager,
            snapshot_manager=snapshot_manager,
            serializer=serializer
        )
    
    container.register_factory(
        WorkflowStateManager,
        workflow_state_manager_factory,
        lifetime=ServiceLifetime.SINGLETON
    )


def get_state_service_config() -> Dict[str, Any]:
    """获取状态管理服务配置
    
    Returns:
        默认配置字典
    """
    return {
        "default_storage": "sqlite",
        "serialization": {
            "format": "json",
            "compression": True
        },
        "history": {
            "max_entries": 1000,
            "enable_compression": True
        },
        "snapshots": {
            "max_per_agent": 50,
            "enable_compression": True
        },
        "storage": {
            "sqlite": {
                "db_path": "data/state_storage.db"
            }
        },
        "performance": {
            "enable_transactions": True
        }
    }


def configure_state_migration(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置状态迁移服务
    
    Args:
        container: 服务容器
        config: 迁移配置
    """
    # 由于迁移服务不存在，跳过配置
    logger.info("状态迁移服务配置已跳过，因为服务不存在")
    return


def validate_state_configuration(config: Dict[str, Any]) -> List[str]:
    """验证状态管理配置
    
    Args:
        config: 配置字典
        
    Returns:
        验证错误列表，空列表表示验证通过
    """
    errors = []
    
    try:
        # 验证存储类型
        default_storage = config.get("default_storage")
        if not default_storage:
            errors.append("缺少default_storage配置")
        elif default_storage not in ["memory", "sqlite", "file"]:
            errors.append(f"不支持的存储类型: {default_storage}")
        
        # 验证序列化配置
        serialization = config.get("serialization", {})
        format_type = serialization.get("format")
        if format_type and format_type not in ["json", "pickle"]:
            errors.append(f"不支持的序列化格式: {format_type}")
        
        # 验证历史配置
        history = config.get("history", {})
        max_entries = history.get("max_entries")
        if max_entries is not None and (not isinstance(max_entries, int) or max_entries <= 0):
            errors.append("history.max_entries必须是正整数")
        
        # 验证快照配置
        snapshots = config.get("snapshots", {})
        max_snapshots = snapshots.get("max_per_agent")
        if max_snapshots is not None and (not isinstance(max_snapshots, int) or max_snapshots <= 0):
            errors.append("snapshots.max_per_agent必须是正整数")
        
    except Exception as e:
        errors.append(f"配置验证异常: {e}")
    
    return errors