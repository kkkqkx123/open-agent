"""状态管理服务初始化模块

提供状态管理服务的初始化和配置功能，使用简化的架构。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, TYPE_CHECKING

from src.core.config.config_facade import ConfigFacade
from .config import (
    get_state_service_config,
    validate_state_configuration,
    configure_state_services
)

if TYPE_CHECKING:
    from src.interfaces.container import IDependencyContainer as ServiceContainer
    from src.interfaces.state.manager import IStateManager
    from src.interfaces.state.session import ISessionStateManager

from .manager import StateManager
from .session_manager import SessionStateManager


logger = get_logger(__name__)


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
            from src.services.container import get_global_container
            actual_container = get_global_container()
        
        # 获取配置
        actual_config = config
        if actual_config is None:
            try:
                config_facade = actual_container.get(ConfigFacade)
                actual_config = config_facade.get_config("state", "state_management")
            except Exception:
                actual_config = get_state_service_config()
        
        # 验证配置
        validation_errors = validate_state_configuration(actual_config)
        if validation_errors:
            logger.error(f"状态管理配置验证失败: {validation_errors}")
            return False
        
        # 获取Repository实例
        history_repository = _get_repository(actual_container, "history")
        snapshot_repository = _get_repository(actual_container, "snapshot")
        
        if not history_repository or not snapshot_repository:
            logger.error("无法获取必要的Repository实例")
            return False
        
        # 创建核心服务
        state_manager = StateManager(
            history_repository=history_repository,
            snapshot_repository=snapshot_repository,
            serializer=_get_serializer(actual_container),
            cache_size=actual_config.get("cache", {}).get("max_size", 1000),
            cache_ttl=actual_config.get("cache", {}).get("ttl", 300)
        )
        actual_container.register_instance(StateManager, state_manager)
        
        # 创建会话管理器
        session_config = actual_config.get("sessions", {})
        session_manager = SessionStateManager(
            serializer=_get_serializer(actual_container),
            session_timeout_minutes=session_config.get("max_inactive_duration", 3600) // 60,
            cleanup_interval_minutes=session_config.get("cleanup_interval", 600) // 60,
            cache_size=actual_config.get("cache", {}).get("max_size", 1000)
        )
        actual_container.register_instance(SessionStateManager, session_manager)
        
        # 配置状态管理服务
        configure_state_services(actual_container, actual_config)
        
        logger.info("状态管理服务初始化成功（简化版本）")
        return True
        
    except Exception as e:
        logger.error(f"初始化状态管理服务失败: {e}")
        return False


def get_state_manager() -> Optional["IStateManager"]:
    """获取状态管理器实例
    
    Returns:
        状态管理器实例，如果未初始化则返回None
    """
    try:
        from src.services.container.core import container
        return container.get(StateManager)  # type: ignore
    except Exception as e:
        logger.error(f"获取状态管理器失败: {e}")
        return None


def get_session_manager() -> Optional["ISessionStateManager"]:
    """获取会话管理器实例
    
    Returns:
        会话管理器实例，如果未初始化则返回None
    """
    try:
        from src.services.container.core import container
        return container.get(SessionStateManager)  # type: ignore
    except Exception as e:
        logger.error(f"获取会话管理器失败: {e}")
        return None


def shutdown_state_services() -> None:
    """关闭状态管理服务"""
    try:
        # 清理缓存
        state_manager = get_state_manager()
        if state_manager:
            state_manager.cleanup_cache()
        
        # 清理会话缓存
        session_manager = get_session_manager()
        if session_manager:
            session_manager.clear_cache()
        
        logger.info("状态管理服务已关闭")
    except Exception as e:
        logger.error(f"关闭状态管理服务失败: {e}")


def get_service_status() -> Dict[str, Any]:
    """获取服务状态
    
    Returns:
        服务状态字典
    """
    status: Dict[str, Any] = {
        "initialized": False,
        "services": {},
        "errors": []
    }
    
    try:
        from src.services.container import get_global_container
        container = get_global_container()
        
        services_to_check = [
            ("state_manager", StateManager),
            ("session_manager", SessionStateManager)
        ]
        
        for service_name, service_type in services_to_check:
            try:
                service = container.get(service_type)
                status["services"][service_name] = service is not None
            except Exception as e:
                status["services"][service_name] = False
                status["errors"].append(f"{service_name}: {e}")
        
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


def _get_repository(container: Any, repository_type: str) -> Optional[Any]:
    """获取Repository实例
    
    Args:
        container: 服务容器
        repository_type: Repository类型
        
    Returns:
        Repository实例，如果获取失败则返回None
    """
    try:
        if repository_type == "history":
            from src.interfaces.repository import IHistoryRepository
            return container.get(IHistoryRepository)
        elif repository_type == "snapshot":
            from src.interfaces.repository import ISnapshotRepository
            return container.get(ISnapshotRepository)
    except Exception as e:
        logger.warning(f"获取{repository_type} Repository失败: {e}")
    
    return None


def _get_serializer(container: Any) -> Optional[Any]:
    """获取序列化器实例
    
    Args:
        container: 服务容器
        
    Returns:
        序列化器实例，如果获取失败则返回None
    """
    try:
        from src.infrastructure.common.serialization import Serializer
        return container.get(Serializer)
    except Exception as e:
        logger.warning(f"获取序列化器失败: {e}")
    
    return None


# 导出接口
__all__ = [
    "initialize_state_services",
    "get_state_manager",
    "get_session_manager",
    "shutdown_state_services",
    "get_service_status",
    "ensure_state_services_initialized"
]