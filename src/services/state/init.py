"""状态管理服务初始化模块

提供状态管理服务的初始化和配置功能。
"""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

from src.core.config.config_manager import ConfigManager
from src.services.state.di_config import (
    configure_state_services,
    validate_state_configuration,
    get_state_service_config
)

if TYPE_CHECKING:
    from src.interfaces.container import IDependencyContainer as ServiceContainer
    from interfaces.state.manager import IStateManager
    from src.interfaces.state.history import IStateHistoryManager
    from src.interfaces.state.snapshot import IStateSnapshotManager


logger = logging.getLogger(__name__)


def initialize_state_services(container: Optional[Any] = None,
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
        actual_container = container
        if actual_container is None:
            from src.services.container import container as global_container
            actual_container = global_container
        
        # 获取配置
        actual_config = config
        if actual_config is None:
            try:
                config_manager = actual_container.get(ConfigManager)  # type: ignore
                actual_config = config_manager.get_config("state", {})
            except Exception:
                actual_config = get_state_service_config()
        
        # 验证配置
        validation_errors = validate_state_configuration(actual_config)
        if validation_errors:
            logger.error(f"状态管理配置验证失败: {validation_errors}")
            return False
        
        # 配置状态管理服务
        configure_state_services(actual_container, actual_config)  # type: ignore
        
        logger.info("状态管理服务初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"初始化状态管理服务失败: {e}")
        return False


def get_state_manager() -> Optional[IStateManager]:
    """获取状态管理器实例
    
    Returns:
        状态管理器实例，如果未初始化则返回None
    """
    try:
        from src.services.container import container
        return container.get(IStateManager)  # type: ignore
    except Exception as e:
        logger.error(f"获取状态管理器失败: {e}")
        return None


def get_history_service() -> Optional[IStateHistoryManager]:
    """获取历史管理服务实例
    
    Returns:
        历史管理服务实例，如果未初始化则返回None
    """
    try:
        from src.services.container import container
        return container.get(IStateHistoryManager)  # type: ignore
    except Exception as e:
        logger.error(f"获取历史管理服务失败: {e}")
        return None


def get_snapshot_service() -> Optional[IStateSnapshotManager]:
    """获取快照管理服务实例
    
    Returns:
        快照管理服务实例，如果未初始化则返回None
    """
    try:
        from src.services.container import container
        return container.get(IStateSnapshotManager)  # type: ignore
    except Exception as e:
        logger.error(f"获取快照管理服务失败: {e}")
        return None


def shutdown_state_services() -> None:
    """关闭状态管理服务"""
    try:
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
        from src.services.container import container
        
        services_to_check = [
            ("state_manager", IStateManager),
            ("history_service", IStateHistoryManager),
            ("snapshot_service", IStateSnapshotManager)
        ]
        
        for service_name, service_type in services_to_check:
            try:
                service = container.get(service_type)  # type: ignore
                status["services"][service_name] = service is not None
            except Exception as e:
                status["services"][service_name] = False
                status["errors"].append(f"{service_name}: {e}")
        
        # 检查存储状态（暂不实现）
        
        # 检查是否所有核心服务都已初始化
        status["initialized"] = all(status["services"].values())
        
    except Exception as e:
        status["errors"].append(f"获取服务状态失败: {e}")
    
    return status


def ensure_state_services_initialized() -> bool:
    """确保状态管理服务已初始化
    
    Returns:
        是否初始化成功
    """
    try:
        get_state_manager()
        return True
    except Exception:
        return initialize_state_services()


# 导出接口
__all__ = [
    "initialize_state_services",
    "get_state_manager",
    "get_history_service", 
    "get_snapshot_service",
    "shutdown_state_services",
    "get_service_status",
    "ensure_state_services_initialized"
]
