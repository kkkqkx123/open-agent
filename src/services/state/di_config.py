"""状态管理依赖注入配置

配置状态管理相关服务的依赖注入。
"""

import logging
from typing import Dict, Any, Optional

from src.services.container import ServiceContainer, ServiceLifetime
from src.interfaces.state_core import IStateSerializer, IStateHistoryManager, IStateSnapshotManager
from src.core.state.base import BaseStateSerializer
from src.services.state import (
    EnhancedStateManager,
    StateHistoryService,
    StateSnapshotService,
    StatePersistenceService,
    StateBackupService,
    WorkflowStateManager
)
from src.adapters.storage import (
    IStateStorageAdapter,
    StorageAdapterFactory,
    StorageAdapterManager,
    create_storage_adapter
)


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
        
        # 配置存储适配器
        _configure_storage_adapter(container, config.get("storage", {}))
        
        # 配置历史管理服务
        _configure_history_service(container, config.get("history", {}))
        
        # 配置快照管理服务
        _configure_snapshot_service(container, config.get("snapshots", {}))
        
        # 配置增强状态管理器
        _configure_enhanced_state_manager(container, config)
        
        # 配置持久化服务
        _configure_persistence_service(container, config.get("performance", {}))
        
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
    
    container.register(
        IStateSerializer,
        factory=serializer_factory,
        lifetime=ServiceLifetime.SINGLETON
    )


def _configure_storage_adapter(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置存储适配器"""
    default_storage = config.get("default", "sqlite")
    storage_configs = config.get("sqlite", {})
    
    def storage_adapter_factory() -> IStateStorageAdapter:
        return create_storage_adapter(default_storage, storage_configs)
    
    container.register(
        IStateStorageAdapter,
        factory=storage_adapter_factory,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册存储适配器管理器
    def storage_manager_factory() -> StorageAdapterManager:
        manager = StorageAdapterManager()
        manager.create_adapter("default", default_storage, storage_configs)
        return manager
    
    container.register(
        StorageAdapterManager,
        factory=storage_manager_factory,
        lifetime=ServiceLifetime.SINGLETON
    )


def _configure_history_service(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置历史管理服务"""
    max_entries = config.get("max_entries", 1000)
    
    def history_service_factory(storage_adapter: IStateStorageAdapter, 
                               serializer: IStateSerializer) -> IStateHistoryManager:
        return StateHistoryService(
            storage_adapter=storage_adapter,
            serializer=serializer,
            max_history_size=max_entries
        )
    
    container.register(
        IStateHistoryManager,
        factory=history_service_factory,
        lifetime=ServiceLifetime.SINGLETON
    )


def _configure_snapshot_service(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置快照管理服务"""
    max_snapshots = config.get("max_per_agent", 50)
    
    def snapshot_service_factory(storage_adapter: IStateStorageAdapter,
                                serializer: IStateSerializer) -> IStateSnapshotManager:
        return StateSnapshotService(
            storage_adapter=storage_adapter,
            serializer=serializer,
            max_snapshots_per_agent=max_snapshots
        )
    
    container.register(
        IStateSnapshotManager,
        factory=snapshot_service_factory,
        lifetime=ServiceLifetime.SINGLETON
    )


def _configure_enhanced_state_manager(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置增强状态管理器"""
    def state_manager_factory(history_manager: IStateHistoryManager,
                             snapshot_manager: IStateSnapshotManager,
                             serializer: IStateSerializer) -> EnhancedStateManager:
        return EnhancedStateManager(
            history_manager=history_manager,
            snapshot_manager=snapshot_manager,
            serializer=serializer
        )
    
    container.register(
        EnhancedStateManager,
        factory=state_manager_factory,
        lifetime=ServiceLifetime.SINGLETON
    )


def _configure_persistence_service(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置持久化服务"""
    enable_transactions = config.get("enable_transactions", True)
    
    def persistence_service_factory(storage_adapter: IStateStorageAdapter) -> StatePersistenceService:
        return StatePersistenceService(
            storage_adapter=storage_adapter,
            enable_transactions=enable_transactions
        )
    
    container.register(
        StatePersistenceService,
        factory=persistence_service_factory,
        lifetime=ServiceLifetime.SINGLETON
    )


def _configure_backup_service(container: ServiceContainer) -> None:
    """配置备份服务"""
    def backup_service_factory(persistence_service: StatePersistenceService) -> StateBackupService:
        return StateBackupService(persistence_service)
    
    container.register(
        StateBackupService,
        factory=backup_service_factory,
        lifetime=ServiceLifetime.SINGLETON
    )


def _configure_workflow_state_manager(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置工作流状态管理器"""
    def workflow_state_manager_factory(history_manager: IStateHistoryManager,
                                     snapshot_manager: IStateSnapshotManager,
                                     serializer: IStateSerializer) -> WorkflowStateManager:
        return WorkflowStateManager(
            history_manager=history_manager,
            snapshot_manager=snapshot_manager,
            serializer=serializer
        )
    
    container.register(
        WorkflowStateManager,
        factory=workflow_state_manager_factory,
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


def register_legacy_adapters(container: ServiceContainer) -> None:
    """注册旧架构适配器
    
    Args:
        container: 服务容器
    """
    try:
        from src.adapters.state import (
            LegacyStateManagerAdapter,
            LegacyHistoryManagerAdapter,
            LegacySnapshotStoreAdapter
        )
        from src.domain.state.interfaces import IStateCrudManager
        from src.infrastructure.state.interfaces import IStateSnapshotStore, IStateHistoryManager as OldIStateHistoryManager
        
        # 注册旧状态管理器适配器
        def legacy_state_manager_factory(enhanced_manager: EnhancedStateManager) -> IStateCrudManager:
            return LegacyStateManagerAdapter(enhanced_manager)
        
        container.register(
            IStateCrudManager,
            factory=legacy_state_manager_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册旧历史管理器适配器
        def legacy_history_manager_factory(history_service: StateHistoryService) -> OldIStateHistoryManager:
            return LegacyHistoryManagerAdapter(history_service)
        
        container.register(
            OldIStateHistoryManager,
            factory=legacy_history_manager_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册旧快照存储适配器
        def legacy_snapshot_store_factory(snapshot_service: StateSnapshotService) -> IStateSnapshotStore:
            return LegacySnapshotStoreAdapter(snapshot_service)
        
        container.register(
            IStateSnapshotStore,
            factory=legacy_snapshot_store_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.info("旧架构适配器注册完成")
        
    except Exception as e:
        logger.error(f"注册旧架构适配器失败: {e}")
        raise


def configure_state_migration(container: ServiceContainer, config: Dict[str, Any]) -> None:
    """配置状态迁移服务
    
    Args:
        container: 服务容器
        config: 迁移配置
    """
    try:
        from src.adapters.state import StateMigrationService
        
        migration_config = config.get("migration", {})
        
        def migration_service_factory() -> StateMigrationService:
            return StateMigrationService()
        
        container.register(
            StateMigrationService,
            factory=migration_service_factory,
            lifetime=ServiceLifetime.TRANSIENT
        )
        
        logger.info("状态迁移服务配置完成")
        
    except Exception as e:
        logger.error(f"配置状态迁移服务失败: {e}")
        raise


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