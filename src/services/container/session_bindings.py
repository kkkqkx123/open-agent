"""会话服务依赖注入绑定配置"""

import logging
from typing import Dict, Any

from src.adapters.storage.backends import SQLiteSessionBackend, FileSessionBackend
from src.services.session.repository import SessionRepository
from src.services.session.service import SessionService
from src.interfaces.sessions import ISessionRepository, ISessionStorageBackend
from src.interfaces.sessions.service import ISessionService
from src.core.sessions.interfaces import ISessionCore

logger = logging.getLogger(__name__)


def register_session_backends(container, config: Dict[str, Any]) -> None:
    """注册会话存储后端
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 主后端配置
    primary_backend_type = config.get("session", {}).get("primary_backend", "sqlite")
    
    if primary_backend_type == "sqlite":
        sqlite_config = config.get("session", {}).get("sqlite", {})
        db_path = sqlite_config.get("db_path", "./data/sessions.db")
        primary_backend = SQLiteSessionBackend(db_path=db_path)
    else:
        raise ValueError(f"Unsupported primary backend type: {primary_backend_type}")
    
    # 辅助后端配置
    secondary_backends = []
    secondary_types = config.get("session", {}).get("secondary_backends", [])
    
    for backend_type in secondary_types:
        if backend_type == "file":
            file_config = config.get("session", {}).get("file", {})
            base_path = file_config.get("base_path", "./sessions_backup")
            backend = FileSessionBackend(base_path=base_path)
            secondary_backends.append(backend)
        elif backend_type == "sqlite":
            sqlite_config = config.get("session", {}).get("sqlite_secondary", {})
            db_path = sqlite_config.get("db_path", "./data/sessions_backup.db")
            backend = SQLiteSessionBackend(db_path=db_path)
            secondary_backends.append(backend)
        else:
            logger.warning(f"Unknown secondary backend type: {backend_type}")
    
    # 注册主后端为单例
    container.register_singleton("session_primary_backend", primary_backend)
    
    # 注册辅助后端列表
    if secondary_backends:
        container.register_singleton("session_secondary_backends", secondary_backends)
    
    logger.info(f"Session backends registered: primary={primary_backend_type}, secondary={secondary_types}")


def register_session_repository(container, config: Dict[str, Any]) -> None:
    """注册会话仓储
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保后端已注册
    register_session_backends(container, config)
    
    # 创建仓储工厂函数
    def session_repository_factory():
        primary_backend = container.get("session_primary_backend")
        secondary_backends = container.get("session_secondary_backends", default=[])
        return SessionRepository(primary_backend, secondary_backends)
    
    # 注册仓储为单例
    container.register_singleton("session_repository", session_repository_factory)
    
    # 注册接口
    container.register_singleton(
        ISessionRepository,
        lambda: container.get("session_repository")
    )
    
    logger.info("Session repository registered")


def register_session_service(container, config: Dict[str, Any]) -> None:
    """注册会话服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保仓储已注册
    register_session_repository(container, config)
    
    # 创建服务工厂函数
    def session_service_factory():
        session_core = container.get(ISessionCore)
        session_repository = container.get(ISessionRepository)
        thread_service = container.get("thread_service", default=None)
        
        return SessionService(
            session_core=session_core,
            session_repository=session_repository,
            thread_service=thread_service,
            storage_path=config.get("session", {}).get("storage_path", "./sessions")
        )
    
    # 注册服务为单例
    container.register_singleton("session_service", session_service_factory)
    
    # 注册接口
    container.register_singleton(
        ISessionService,
        lambda: container.get("session_service")
    )
    
    logger.info("Session service registered")


def register_all_session_services(container, config: Dict[str, Any]) -> None:
    """注册所有会话相关服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    register_session_backends(container, config)
    register_session_repository(container, config)
    register_session_service(container, config)
    logger.info("All session services registered")
