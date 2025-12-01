"""会话服务依赖注入绑定配置 - 更新版本"""

import logging
from typing import Dict, Any

from adapters.storage.backends.file_thread_backend import FileThreadBackend
from adapters.storage.backends.sqlite_thread_backend import SQLiteThreadBackend
from src.adapters.storage.association_repository import SessionThreadAssociationRepository
from src.adapters.storage.backends import SQLiteSessionBackend, FileSessionBackend

from src.services.threads.repository import ThreadRepository
from src.services.sessions.repository import SessionRepository
from src.services.sessions.service import SessionService
from src.services.sessions.coordinator import SessionThreadCoordinator
from src.services.sessions.synchronizer import SessionThreadSynchronizer
from src.services.sessions.transaction import SessionThreadTransaction
from src.interfaces.sessions import ISessionRepository
from src.adapters.storage.backends.base import ISessionStorageBackend
from src.interfaces.sessions.service import ISessionService
from src.interfaces.sessions.association import (
    ISessionThreadAssociationRepository,
    ISessionThreadSynchronizer,
    ISessionThreadTransaction
)
from src.interfaces.threads import IThreadRepository
from src.adapters.storage.backends.thread_base import IThreadStorageBackend
from src.interfaces.threads.service import IThreadService
from src.core.sessions.interfaces import ISessionCore, ISessionStateTransition, ISessionValidator
from src.interfaces.common_infra import ILogger

# 导入日志绑定
from .logger_bindings import register_logger_services

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
        logger = container.get(ILogger, default=None)
        return SessionRepository(primary_backend, secondary_backends, logger)
    
    # 注册仓储为单例
    container.register_singleton("session_repository", session_repository_factory)
    
    # 注册接口
    container.register_singleton(
        ISessionRepository,
        lambda: container.get("session_repository")
    )
    
    logger.info("Session repository registered")


def register_thread_backends(container, config: Dict[str, Any]) -> None:
    """注册线程存储后端
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 主后端配置
    primary_backend_type = config.get("thread", {}).get("primary_backend", "sqlite")
    
    if primary_backend_type == "sqlite":
        sqlite_config = config.get("thread", {}).get("sqlite", {})
        db_path = sqlite_config.get("db_path", "./data/threads.db")
        primary_backend = SQLiteThreadBackend(db_path=db_path)
    else:
        raise ValueError(f"Unsupported primary backend type: {primary_backend_type}")
    
    # 辅助后端配置
    secondary_backends = []
    secondary_types = config.get("thread", {}).get("secondary_backends", [])
    
    for backend_type in secondary_types:
        if backend_type == "file":
            file_config = config.get("thread", {}).get("file", {})
            base_path = file_config.get("base_path", "./threads_backup")
            backend = FileThreadBackend(base_path=base_path)
            secondary_backends.append(backend)
        elif backend_type == "sqlite":
            sqlite_config = config.get("thread", {}).get("sqlite_secondary", {})
            db_path = sqlite_config.get("db_path", "./data/threads_backup.db")
            backend = SQLiteThreadBackend(db_path=db_path)
            secondary_backends.append(backend)
        else:
            logger.warning(f"Unknown secondary backend type: {backend_type}")
    
    # 注册主后端为单例
    container.register_singleton("thread_primary_backend", primary_backend)
    
    # 注册辅助后端列表
    if secondary_backends:
        container.register_singleton("thread_secondary_backends", secondary_backends)
    
    logger.info(f"Thread backends registered: primary={primary_backend_type}, secondary={secondary_types}")


def register_thread_repository(container, config: Dict[str, Any]) -> None:
    """注册线程仓储
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保后端已注册
    register_thread_backends(container, config)
    
    # 创建仓储工厂函数
    def thread_repository_factory():
        primary_backend = container.get("thread_primary_backend")
        secondary_backends = container.get("thread_secondary_backends", default=[])
        return ThreadRepository(primary_backend, secondary_backends)
    
    # 注册仓储为单例
    container.register_singleton("thread_repository", thread_repository_factory)
    
    # 注册接口
    container.register_singleton(
        IThreadRepository,
        lambda: container.get("thread_repository")
    )
    
    logger.info("Thread repository registered")


def register_association_repository(container, config: Dict[str, Any]) -> None:
    """注册Session-Thread关联仓储
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保后端已注册
    register_session_backends(container, config)
    register_thread_backends(container, config)
    
    # 创建关联仓储工厂函数
    def association_repository_factory():
        session_backend = container.get("session_primary_backend")
        thread_backend = container.get("thread_primary_backend")
        return SessionThreadAssociationRepository(session_backend, thread_backend)
    
    # 注册关联仓储为单例
    container.register_singleton("association_repository", association_repository_factory)
    
    # 注册接口
    container.register_singleton(
        ISessionThreadAssociationRepository,
        lambda: container.get("association_repository")
    )
    
    logger.info("Session-Thread association repository registered")


def register_synchronizer(container, config: Dict[str, Any]) -> None:
    """注册数据同步器
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保依赖已注册
    register_association_repository(container, config)
    register_session_repository(container, config)
    register_thread_repository(container, config)
    
    # 创建同步器工厂函数
    def synchronizer_factory():
        association_repository = container.get(ISessionThreadAssociationRepository)
        session_repository = container.get(ISessionRepository)
        thread_repository = container.get(IThreadRepository)
        return SessionThreadSynchronizer(
            association_repository=association_repository,
            session_repository=session_repository,
            thread_repository=thread_repository
        )
    
    # 注册同步器为单例
    container.register_singleton("session_thread_synchronizer", synchronizer_factory)
    
    # 注册接口
    container.register_singleton(
        ISessionThreadSynchronizer,
        lambda: container.get("session_thread_synchronizer")
    )
    
    logger.info("Session-Thread synchronizer registered")


def register_transaction_manager(container, config: Dict[str, Any]) -> None:
    """注册事务管理器
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保依赖已注册
    register_association_repository(container, config)
    register_session_repository(container, config)
    register_thread_repository(container, config)
    
    # 创建事务管理器工厂函数
    def transaction_factory():
        association_repository = container.get(ISessionThreadAssociationRepository)
        session_repository = container.get(ISessionRepository)
        thread_repository = container.get(IThreadRepository)
        thread_service = container.get(IThreadService)
        return SessionThreadTransaction(
            association_repository=association_repository,
            session_repository=session_repository,
            thread_repository=thread_repository,
            thread_service=thread_service
        )
    
    # 注册事务管理器为单例
    container.register_singleton("session_thread_transaction", transaction_factory)
    
    # 注册接口
    container.register_singleton(
        ISessionThreadTransaction,
        lambda: container.get("session_thread_transaction")
    )
    
    logger.info("Session-Thread transaction manager registered")


def register_coordinator(container, config: Dict[str, Any]) -> None:
    """注册协调器
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保依赖已注册
    register_synchronizer(container, config)
    register_transaction_manager(container, config)
    
    # 创建协调器工厂函数
    def coordinator_factory():
        session_service = container.get(ISessionService)
        thread_service = container.get(IThreadService)
        association_repository = container.get(ISessionThreadAssociationRepository)
        synchronizer = container.get(ISessionThreadSynchronizer)
        transaction = container.get(ISessionThreadTransaction)
        logger = container.get(ILogger, default=None)
        return SessionThreadCoordinator(
            session_service=session_service,
            thread_service=thread_service,
            association_repository=association_repository,
            synchronizer=synchronizer,
            transaction=transaction,
            logger=logger
        )
    
    # 注册协调器为单例
    container.register_singleton("session_thread_coordinator", coordinator_factory)
    
    logger.info("Session-Thread coordinator registered")


def register_session_service(container, config: Dict[str, Any]) -> None:
    """注册会话服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保依赖已注册
    register_session_repository(container, config)
    register_coordinator(container, config)
    
    # 创建服务工厂函数
    def session_service_factory():
        session_core = container.get(ISessionCore)
        session_repository = container.get(ISessionRepository)
        thread_service = container.get(IThreadService)
        coordinator = container.get("session_thread_coordinator")
        session_validator = container.get(ISessionValidator, default=None)
        state_transition = container.get(ISessionStateTransition, default=None)
        git_service = container.get("IGitService", default=None)
        logger = container.get(ILogger, default=None)
        
        return SessionService(
            session_core=session_core,
            session_repository=session_repository,
            thread_service=thread_service,
            coordinator=coordinator,
            session_validator=session_validator,
            state_transition=state_transition,
            git_service=git_service,
            storage_path=config.get("session", {}).get("storage_path", "./sessions"),
            logger=logger
        )
    
    # 注册服务为单例
    container.register_singleton("session_service", session_service_factory)
    
    # 注册接口
    container.register_singleton(
        ISessionService,
        lambda: container.get("session_service")
    )
    
    logger.info("Session service registered with coordinator")


def register_all_session_services(container, config: Dict[str, Any]) -> None:
    """注册所有会话相关服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 首先注册日志服务
    register_logger_services(container, config)
    
    register_session_backends(container, config)
    register_session_repository(container, config)
    register_thread_backends(container, config)
    register_thread_repository(container, config)
    register_association_repository(container, config)
    register_synchronizer(container, config)
    register_transaction_manager(container, config)
    register_coordinator(container, config)
    register_session_service(container, config)
    logger.info("All session services registered with coordinator support")
