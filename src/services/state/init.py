"""状态管理服务初始化模块

提供状态管理服务的初始化和配置功能。
"""

import logging
from typing import Dict, Any, Optional

from src.services.container import ServiceContainer, register_service, get_service
from src.services.state.di_config import (
    configure_state_services,
    register_legacy_adapters,
    configure_state_migration,
    validate_state_configuration,
    get_state_service_config
)
from src.core.config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


def initialize_state_services(container: Optional[ServiceContainer] = None,
                            config: Optional[Dict[str, Any]] = None) -> bool:
    """初始化状态管理服务
    
    Args:
        container: 服务容器，如果为None则使用全局容器
        config: 配置字典，如果为None则使用默认配置
        
    Returns:
        是否初始化成功
    """
    try:
        # 使用全局容器（如果未提供）
        if container is None:
            from src.services.container import container as global_container
            container = global_container
        
        # 获取配置
        if config is None:
            config_manager = get_service(ConfigManager) if is_service_registered(ConfigManager) else None
            if config_manager:
                config = config_manager.get_config("state", {})
            else:
                config = get_state_service_config()
        
        # 验证配置
        validation_errors = validate_state_configuration(config)
        if validation_errors:
            logger.error(f"状态管理配置验证失败: {validation_errors}")
            return False
        
        # 配置状态管理服务
        configure_state_services(container, config)
        
        # 注册旧架构适配器（向后兼容）
        register_legacy_adapters(container)
        
        # 配置迁移服务（如果需要）
        if config.get("migration", {}).get("auto_migrate", False):
            configure_state_migration(container, config)
        
        logger.info("状态管理服务初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"初始化状态管理服务失败: {e}")
        return False


def is_service_registered(service_type: type) -> bool:
    """检查服务是否已注册
    
    Args:
        service_type: 服务类型
        
    Returns:
        是否已注册
    """
    try:
        from src.services.container import is_service_registered as check_registered
        return check_registered(service_type)
    except Exception:
        return False


def get_state_manager() -> Optional['EnhancedStateManager']:
    """获取状态管理器实例
    
    Returns:
        状态管理器实例，如果未初始化则返回None
    """
    try:
        from src.services.state import EnhancedStateManager
        return get_service(EnhancedStateManager)
    except Exception as e:
        logger.error(f"获取状态管理器失败: {e}")
        return None


def get_history_service() -> Optional['StateHistoryService']:
    """获取历史管理服务实例
    
    Returns:
        历史管理服务实例，如果未初始化则返回None
    """
    try:
        from src.services.state import StateHistoryService
        return get_service(StateHistoryService)
    except Exception as e:
        logger.error(f"获取历史管理服务失败: {e}")
        return None


def get_snapshot_service() -> Optional['StateSnapshotService']:
    """获取快照管理服务实例
    
    Returns:
        快照管理服务实例，如果未初始化则返回None
    """
    try:
        from src.services.state import StateSnapshotService
        return get_service(StateSnapshotService)
    except Exception as e:
        logger.error(f"获取快照管理服务失败: {e}")
        return None


def get_persistence_service() -> Optional['StatePersistenceService']:
    """获取持久化服务实例
    
    Returns:
        持久化服务实例，如果未初始化则返回None
    """
    try:
        from src.services.state import StatePersistenceService
        return get_service(StatePersistenceService)
    except Exception as e:
        logger.error(f"获取持久化服务失败: {e}")
        return None


def get_backup_service() -> Optional['StateBackupService']:
    """获取备份服务实例
    
    Returns:
        备份服务实例，如果未初始化则返回None
    """
    try:
        from src.services.state import StateBackupService
        return get_service(StateBackupService)
    except Exception as e:
        logger.error(f"获取备份服务失败: {e}")
        return None


def get_legacy_adapters() -> Optional[Dict[str, Any]]:
    """获取旧架构适配器
    
    Returns:
        适配器字典，如果未初始化则返回None
    """
    try:
        from src.domain.state.interfaces import IStateCrudManager
        from src.infrastructure.state.interfaces import IStateSnapshotStore, IStateHistoryManager as OldIStateHistoryManager
        
        return {
            "state_manager": get_service(IStateCrudManager),
            "history_manager": get_service(OldIStateHistoryManager),
            "snapshot_store": get_service(IStateSnapshotStore)
        }
    except Exception as e:
        logger.error(f"获取旧架构适配器失败: {e}")
        return None


def perform_migration_if_needed(config: Optional[Dict[str, Any]] = None) -> bool:
    """执行迁移（如果需要）
    
    Args:
        config: 配置字典
        
    Returns:
        是否迁移成功
    """
    try:
        if config is None:
            config_manager = get_service(ConfigManager) if is_service_registered(ConfigManager) else None
            if config_manager:
                config = config_manager.get_config("state", {})
            else:
                config = get_state_service_config()
        
        migration_config = config.get("migration", {})
        if not migration_config.get("auto_migrate", False):
            logger.debug("自动迁移未启用")
            return True
        
        from src.adapters.state import migrate_to_new_architecture
        
        # 这里需要获取旧组件，简化处理
        old_components = {}  # 实际应用中需要从旧系统获取
        
        # 执行迁移
        new_components = migrate_to_new_architecture(old_components)
        
        # 验证迁移结果
        validation_results = new_components.get("migration_validation", {})
        if all(validation_results.values()):
            logger.info("自动迁移完成并验证成功")
            return True
        else:
            logger.error(f"自动迁移验证失败: {validation_results}")
            return False
            
    except Exception as e:
        logger.error(f"执行自动迁移失败: {e}")
        return False


def shutdown_state_services() -> None:
    """关闭状态管理服务"""
    try:
        # 关闭存储适配器
        from src.adapters.storage import get_storage_manager
        storage_manager = get_storage_manager()
        if storage_manager:
            storage_manager.close_all()
        
        logger.info("状态管理服务已关闭")
        
    except Exception as e:
        logger.error(f"关闭状态管理服务失败: {e}")


def get_service_status() -> Dict[str, Any]:
    """获取服务状态
    
    Returns:
        服务状态字典
    """
    status = {
        "initialized": False,
        "services": {},
        "storage": {},
        "errors": []
    }
    
    try:
        # 检查核心服务
        from src.services.state import EnhancedStateManager, StateHistoryService, StateSnapshotService
        
        services_to_check = [
            ("state_manager", EnhancedStateManager),
            ("history_service", StateHistoryService),
            ("snapshot_service", StateSnapshotService)
        ]
        
        for service_name, service_type in services_to_check:
            try:
                service = get_service(service_type)
                status["services"][service_name] = service is not None
            except Exception as e:
                status["services"][service_name] = False
                status["errors"].append(f"{service_name}: {e}")
        
        # 检查存储状态
        from src.adapters.storage import get_storage_manager
        storage_manager = get_storage_manager()
        if storage_manager:
            status["storage"] = storage_manager.get_statistics()
            status["storage"]["health"] = storage_manager.health_check_all()
        
        # 检查是否所有核心服务都已初始化
        status["initialized"] = all(status["services"].values())
        
    except Exception as e:
        status["errors"].append(f"获取服务状态失败: {e}")
    
    return status


# 便捷函数
def ensure_state_services_initialized() -> bool:
    """确保状态管理服务已初始化
    
    Returns:
        是否初始化成功
    """
    if not is_service_registered(type(get_state_manager() or object())):
        return initialize_state_services()
    return True


# 导出接口
__all__ = [
    "initialize_state_services",
    "get_state_manager",
    "get_history_service", 
    "get_snapshot_service",
    "get_persistence_service",
    "get_backup_service",
    "get_legacy_adapters",
    "perform_migration_if_needed",
    "shutdown_state_services",
    "get_service_status",
    "ensure_state_services_initialized"
]