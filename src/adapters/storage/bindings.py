"""
存储适配器依赖注入绑定配置

负责在容器中注册存储后端工厂和关联工厂。
这个文件应该由bootstrap或其他引导代码调用，以完成依赖注入的配置。
"""

from src.services.logger.injection import get_logger
from typing import Dict, Any

from .interfaces import (
    ISessionStorageBackendFactory,
    IThreadStorageBackendFactory,
    ISessionThreadAssociationFactory,
)
from .backend_factory import SessionStorageBackendFactory, ThreadStorageBackendFactory
from .association_factory import SessionThreadAssociationFactory


logger = get_logger(__name__)


def register_storage_factories(container, config: Dict[str, Any]) -> None:
    """注册存储后端工厂
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    # 注册会话后端工厂
    session_factory = SessionStorageBackendFactory()
    container.register_singleton(ISessionStorageBackendFactory, session_factory)
    
    # 注册线程后端工厂
    thread_factory = ThreadStorageBackendFactory()
    container.register_singleton(IThreadStorageBackendFactory, thread_factory)
    
    # 注册关联仓储工厂
    association_factory = SessionThreadAssociationFactory()
    container.register_singleton(ISessionThreadAssociationFactory, association_factory)
    
    logger.info("存储工厂已注册到容器")


def register_all_storage_adapters(container, config: Dict[str, Any]) -> None:
    """注册所有存储适配器
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    register_storage_factories(container, config)
    logger.info("所有存储适配器已注册")
