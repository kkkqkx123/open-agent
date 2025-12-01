"""存储相关服务依赖注入绑定配置

统一注册 Session 和 Thread 的存储服务。
"""

from src.services.logger import get_logger
from typing import Dict, Any

from .session_bindings import (
    register_session_backends,
    register_session_repository,
    register_session_service,
)
from .thread_bindings import (
    register_thread_backends,
    register_thread_repository,
    register_thread_service,
)
from .logger_bindings import register_logger_services

logger = get_logger(__name__)


def register_all_storage_services(container, config: Dict[str, Any]) -> None:
    """注册所有存储相关服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典，应包含 session 和 thread 配置节
    
    示例配置:
    ```yaml
    session:
      primary_backend: sqlite
      secondary_backends:
        - file
      sqlite:
        db_path: ./data/sessions.db
      file:
        base_path: ./sessions_backup
    
    thread:
      primary_backend: sqlite
      secondary_backends:
        - file
      sqlite:
        db_path: ./data/threads.db
      file:
        base_path: ./threads_backup
    ```
    """
    logger.info("Starting to register all storage services...")
    
    try:
        # 首先注册日志服务
        logger.info("Registering Logger services...")
        register_logger_services(container, config)
        logger.info("Logger services registered successfully")
        
        # 注册 Session 服务
        logger.info("Registering Session services...")
        register_session_backends(container, config)
        register_session_repository(container, config)
        register_session_service(container, config)
        logger.info("Session services registered successfully")
        
        # 注册 Thread 服务
        logger.info("Registering Thread services...")
        register_thread_backends(container, config)
        register_thread_repository(container, config)
        register_thread_service(container, config)
        logger.info("Thread services registered successfully")
        
        logger.info("All storage services registered successfully")
        
    except Exception as e:
        logger.error(f"Failed to register storage services: {e}")
        raise


def register_session_storage_only(container, config: Dict[str, Any]) -> None:
    """仅注册 Session 存储服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    logger.info("Registering Session storage services only...")
    register_session_backends(container, config)
    register_session_repository(container, config)
    register_session_service(container, config)
    logger.info("Session storage services registered")


def register_thread_storage_only(container, config: Dict[str, Any]) -> None:
    """仅注册 Thread 存储服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    logger.info("Registering Thread storage services only...")
    register_thread_backends(container, config)
    register_thread_repository(container, config)
    register_thread_service(container, config)
    logger.info("Thread storage services registered")
