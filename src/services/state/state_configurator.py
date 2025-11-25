"""状态管理模块配置器实现"""

import logging
from typing import Dict, Any, List, Type

from src.interfaces.configuration import IModuleConfigurator, ValidationResult
from src.interfaces.container import IDependencyContainer
from src.services.configuration.base_configurator import BaseModuleConfigurator
from src.services.configuration.validation_rules import (
    CommonValidationRules,
    EnumRule,
    NestedRule,
    ListRule
)
from src.core.common.types import ServiceLifetime

logger = logging.getLogger(__name__)


class StateConfigurator(BaseModuleConfigurator):
    """状态管理模块配置器"""
    
    def __init__(self):
        super().__init__("state")
        self.set_priority(10)  # 设置优先级
        
        # 添加依赖
        self.add_dependency("storage")
        
        # 设置验证规则
        self._setup_validation_rules()
    
    def _setup_validation_rules(self) -> None:
        """设置验证规则"""
        # 这里可以添加模块特定的验证规则
        pass
    
    def _configure_services(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置状态管理服务"""
        logger.info("开始配置状态管理服务")
        
        # 配置序列化器
        self._configure_serializer(container, config.get("serialization", {}))
        
        # 配置Repository实现
        self._configure_repositories(container, config.get("storage", {}))
        
        # 配置历史管理服务（使用Repository）
        self._configure_history_service_with_repository(container, config.get("history", {}))
        
        # 配置快照管理服务（使用Repository）
        self._configure_snapshot_service_with_repository(container, config.get("snapshots", {}))
        
        # 配置增强状态管理器
        self._configure_enhanced_state_manager(container, config)
        
        # 配置持久化服务（使用Repository）
        self._configure_persistence_service_with_repository(container, config.get("performance", {}))
        
        # 配置备份服务
        self._configure_backup_service(container)
        
        # 配置工作流状态管理器
        self._configure_workflow_state_manager(container, config)
        
        logger.info("状态管理服务配置完成")
    
    def _configure_serializer(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置序列化器"""
        from src.interfaces.state.serializer import IStateSerializer
        from src.core.state.core.base import BaseStateSerializer
        
        format_type = config.get("format", "json")
        compression = config.get("compression", True)
        
        def serializer_factory() -> IStateSerializer:
            return BaseStateSerializer(format=format_type, compression=compression)
        
        container.register_factory(
            IStateSerializer,
            serializer_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug(f"配置序列化器: format={format_type}, compression={compression}")
    
    def _configure_repositories(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置Repository实现"""
        from src.interfaces.repository import IHistoryRepository, ISnapshotRepository
        
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
        
        logger.debug(f"配置Repository: default_storage={default_storage}")
    
    def _configure_history_service_with_repository(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置历史管理服务（使用Repository）"""
        from src.interfaces.state.history import IStateHistoryManager
        from src.services.state import StateHistoryService
        
        max_entries = config.get("max_entries", 1000)
        enable_compression = config.get("enable_compression", True)
        
        def history_service_factory() -> IStateHistoryManager:
            # 从容器获取依赖
            from src.interfaces.repository import IHistoryRepository
            history_repository = container.get(IHistoryRepository)
            
            return StateHistoryService(
                repository=history_repository,
                max_entries=max_entries,
                enable_compression=enable_compression
            )
        
        container.register_factory(
            IStateHistoryManager,
            history_service_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug(f"配置历史管理服务: max_entries={max_entries}, compression={enable_compression}")
    
    def _configure_snapshot_service_with_repository(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置快照管理服务（使用Repository）"""
        from src.interfaces.state.snapshot import IStateSnapshotManager
        from src.services.state import StateSnapshotService
        
        max_per_agent = config.get("max_per_agent", 50)
        enable_compression = config.get("enable_compression", True)
        
        def snapshot_service_factory() -> IStateSnapshotManager:
            # 从容器获取依赖
            from src.interfaces.repository import ISnapshotRepository
            snapshot_repository = container.get(ISnapshotRepository)
            
            return StateSnapshotService(
                repository=snapshot_repository,
                max_per_agent=max_per_agent,
                enable_compression=enable_compression
            )
        
        container.register_factory(
            IStateSnapshotManager,
            snapshot_service_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug(f"配置快照管理服务: max_per_agent={max_per_agent}, compression={enable_compression}")
    
    def _configure_enhanced_state_manager(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置增强状态管理器"""
        from src.services.state import EnhancedStateManager
        
        def state_manager_factory() -> EnhancedStateManager:
            # 从容器获取依赖
            from src.interfaces.state.history import IStateHistoryManager
            from src.interfaces.state.snapshot import IStateSnapshotManager
            from src.interfaces.state.serializer import IStateSerializer
            
            history_manager = container.get(IStateHistoryManager)
            snapshot_manager = container.get(IStateSnapshotManager)
            serializer = container.get(IStateSerializer)
            
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
        
        logger.debug("配置增强状态管理器")
    
    def _configure_persistence_service_with_repository(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置持久化服务（使用Repository）"""
        from src.services.state import StatePersistenceService
        
        enable_transactions = config.get("enable_transactions", True)
        
        def persistence_service_factory() -> StatePersistenceService:
            # 从容器获取依赖
            from src.interfaces.repository import IHistoryRepository, ISnapshotRepository
            
            history_repository = container.get(IHistoryRepository)
            snapshot_repository = container.get(ISnapshotRepository)
            
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
        
        logger.debug(f"配置持久化服务: transactions={enable_transactions}")
    
    def _configure_backup_service(self, container: IDependencyContainer) -> None:
        """配置备份服务"""
        from src.services.state import StateBackupService
        
        def backup_service_factory() -> StateBackupService:
            # 从容器获取依赖
            persistence_service = container.get(StatePersistenceService)
            return StateBackupService(persistence_service)
        
        container.register_factory(
            StateBackupService,
            backup_service_factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("配置备份服务")
    
    def _configure_workflow_state_manager(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置工作流状态管理器"""
        from src.services.state import WorkflowStateManager
        
        def workflow_state_manager_factory() -> WorkflowStateManager:
            # 从容器获取依赖
            from src.interfaces.state.history import IStateHistoryManager
            from src.interfaces.state.snapshot import IStateSnapshotManager
            from src.interfaces.state.serializer import IStateSerializer
            
            history_manager = container.get(IStateHistoryManager)
            snapshot_manager = container.get(IStateSnapshotManager)
            serializer = container.get(IStateSerializer)
            
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
        
        logger.debug("配置工作流状态管理器")
    
    def _create_default_config(self) -> Dict[str, Any]:
        """创建默认配置"""
        return {
            "enabled": True,
            "version": "1.0.0",
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
    
    def get_required_fields(self) -> List[str]:
        """获取必需字段列表"""
        return ["enabled"]
    
    def get_field_types(self) -> Dict[str, Type]:
        """获取字段类型映射"""
        return {
            "enabled": bool,
            "version": str,
            "default_storage": str,
            "serialization": dict,
            "history": dict,
            "snapshots": dict,
            "storage": dict,
            "performance": dict
        }
    
    def _validate_custom(self, config: Dict[str, Any]) -> ValidationResult:
        """自定义验证逻辑"""
        errors = []
        warnings = []
        
        # 验证存储类型
        default_storage = config.get("default_storage")
        if default_storage and default_storage not in ["memory", "sqlite", "file"]:
            errors.append(f"不支持的存储类型: {default_storage}")
        
        # 验证序列化配置
        serialization = config.get("serialization", {})
        if serialization:
            format_type = serialization.get("format")
            if format_type and format_type not in ["json", "pickle"]:
                errors.append(f"不支持的序列化格式: {format_type}")
        
        # 验证历史配置
        history = config.get("history", {})
        if history:
            max_entries = history.get("max_entries")
            if max_entries is not None and (not isinstance(max_entries, int) or max_entries <= 0):
                errors.append("history.max_entries必须是正整数")
        
        # 验证快照配置
        snapshots = config.get("snapshots", {})
        if snapshots:
            max_snapshots = snapshots.get("max_per_agent")
            if max_snapshots is not None and (not isinstance(max_snapshots, int) or max_snapshots <= 0):
                errors.append("snapshots.max_per_agent必须是正整数")
        
        # 性能警告
        performance = config.get("performance", {})
        if performance and not performance.get("enable_transactions", True):
            warnings.append("禁用事务可能影响数据一致性")
        
        return ValidationResult(len(errors) == 0, errors, warnings)


# 创建配置器实例的工厂函数
def create_state_configurator() -> StateConfigurator:
    """创建状态管理配置器实例"""
    return StateConfigurator()


# 便捷函数
def configure_state_services(container: IDependencyContainer, config: Optional[Dict[str, Any]] = None) -> None:
    """便捷的状态管理服务配置函数
    
    Args:
        container: 依赖注入容器
        config: 配置字典，如果为None则使用默认配置
    """
    configurator = create_state_configurator()
    if config is None:
        config = configurator.get_default_config()
    configurator.configure(container, config)


def get_state_default_config() -> Dict[str, Any]:
    """获取状态管理默认配置"""
    configurator = create_state_configurator()
    return configurator.get_default_config()


def validate_state_config(config: Dict[str, Any]) -> ValidationResult:
    """验证状态管理配置"""
    configurator = create_state_configurator()
    return configurator.validate_config(config)