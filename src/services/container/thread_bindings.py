"""线程服务依赖注入绑定配置"""

import logging
from typing import Dict, Any

from src.adapters.storage.backends import SQLiteThreadBackend, FileThreadBackend
from src.services.threads.repository import ThreadRepository
from src.services.threads.service import ThreadService
from src.interfaces.threads import IThreadRepository, IThreadStorageBackend
from src.interfaces.threads.service import IThreadService
from src.interfaces.sessions.service import ISessionService
from src.core.threads.interfaces import IThreadCore

logger = logging.getLogger(__name__)


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


def register_thread_service(container, config: Dict[str, Any]) -> None:
    """注册线程服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 确保仓储已注册
    register_thread_repository(container, config)
    
    # 创建服务工厂函数
    def thread_service_factory():
        thread_core = container.get(IThreadCore)
        thread_repository = container.get(IThreadRepository)
        session_service = container.get(ISessionService, default=None)
        
        return ThreadService(
            thread_core=thread_core,
            thread_repository=thread_repository,
            session_service=session_service
        )
    
    # 注册服务为单例
    container.register_singleton("thread_service", thread_service_factory)
    
    # 注册接口
    container.register_singleton(
        IThreadService,
        lambda: container.get("thread_service")
    )
    
    logger.info("Thread service registered")


def register_all_thread_services(container, config: Dict[str, Any]) -> None:
    """注册所有线程相关服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    register_thread_backends(container, config)
    register_thread_repository(container, config)
    register_thread_service(container, config)
    logger.info("All thread services registered")
