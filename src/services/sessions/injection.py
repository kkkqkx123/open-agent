"""Session服务依赖注入便利层

使用通用依赖注入框架提供简洁的Session服务获取方式。
"""

from typing import Optional
from unittest.mock import Mock

from src.interfaces.sessions import ISessionRepository
from src.interfaces.sessions.service import ISessionService
from src.interfaces.sessions.association import (
    ISessionThreadAssociationRepository,
    ISessionThreadSynchronizer,
    ISessionThreadTransaction
)
from src.services.sessions.repository import SessionRepository
from src.services.sessions.service import SessionService
from src.services.sessions.coordinator import SessionThreadCoordinator
from src.services.sessions.synchronizer import SessionThreadSynchronizer
from src.services.sessions.transaction import SessionThreadTransaction
from src.services.container.injection.injection_base import get_global_injection_registry
from src.services.container.injection.injection_decorators import injectable


def _create_fallback_session_repository() -> ISessionRepository:
    """创建fallback Session仓储"""
    return Mock(spec=ISessionRepository)


def _create_fallback_session_service() -> ISessionService:
    """创建fallback Session服务"""
    return Mock(spec=ISessionService)


def _create_fallback_session_thread_association_repository() -> ISessionThreadAssociationRepository:
    """创建fallback Session-Thread关联仓储"""
    return Mock(spec=ISessionThreadAssociationRepository)


def _create_fallback_session_thread_synchronizer() -> ISessionThreadSynchronizer:
    """创建fallback Session-Thread同步器"""
    return Mock(spec=ISessionThreadSynchronizer)


def _create_fallback_session_thread_transaction() -> ISessionThreadTransaction:
    """创建fallback Session-Thread事务管理器"""
    return Mock(spec=ISessionThreadTransaction)


def _create_fallback_session_thread_coordinator() -> SessionThreadCoordinator:
    """创建fallback Session-Thread协调器"""
    return Mock(spec=SessionThreadCoordinator)


# 注册Session服务注入
_session_repository_injection = get_global_injection_registry().register(
    ISessionRepository, _create_fallback_session_repository
)

_session_service_injection = get_global_injection_registry().register(
    ISessionService, _create_fallback_session_service
)

_session_thread_association_repository_injection = get_global_injection_registry().register(
    ISessionThreadAssociationRepository, _create_fallback_session_thread_association_repository
)

_session_thread_synchronizer_injection = get_global_injection_registry().register(
    ISessionThreadSynchronizer, _create_fallback_session_thread_synchronizer
)

_session_thread_transaction_injection = get_global_injection_registry().register(
    ISessionThreadTransaction, _create_fallback_session_thread_transaction
)

_session_thread_coordinator_injection = get_global_injection_registry().register(
    SessionThreadCoordinator, _create_fallback_session_thread_coordinator
)


@injectable(ISessionRepository, _create_fallback_session_repository)
def get_session_repository() -> ISessionRepository:
    """获取Session仓储实例
    
    Returns:
        ISessionRepository: Session仓储实例
    """
    return _session_repository_injection.get_instance()


@injectable(ISessionService, _create_fallback_session_service)
def get_session_service() -> ISessionService:
    """获取Session服务实例
    
    Returns:
        ISessionService: Session服务实例
    """
    return _session_service_injection.get_instance()


@injectable(ISessionThreadAssociationRepository, _create_fallback_session_thread_association_repository)
def get_session_thread_association_repository() -> ISessionThreadAssociationRepository:
    """获取Session-Thread关联仓储实例
    
    Returns:
        ISessionThreadAssociationRepository: Session-Thread关联仓储实例
    """
    return _session_thread_association_repository_injection.get_instance()


@injectable(ISessionThreadSynchronizer, _create_fallback_session_thread_synchronizer)
def get_session_thread_synchronizer() -> ISessionThreadSynchronizer:
    """获取Session-Thread同步器实例
    
    Returns:
        ISessionThreadSynchronizer: Session-Thread同步器实例
    """
    return _session_thread_synchronizer_injection.get_instance()


@injectable(ISessionThreadTransaction, _create_fallback_session_thread_transaction)
def get_session_thread_transaction() -> ISessionThreadTransaction:
    """获取Session-Thread事务管理器实例
    
    Returns:
        ISessionThreadTransaction: Session-Thread事务管理器实例
    """
    return _session_thread_transaction_injection.get_instance()


@injectable(SessionThreadCoordinator, _create_fallback_session_thread_coordinator)
def get_session_thread_coordinator() -> SessionThreadCoordinator:
    """获取Session-Thread协调器实例
    
    Returns:
        SessionThreadCoordinator: Session-Thread协调器实例
    """
    return _session_thread_coordinator_injection.get_instance()


# 设置实例的便捷函数
def set_session_repository_instance(repository: ISessionRepository) -> None:
    """设置Session仓储实例"""
    _session_repository_injection.set_instance(repository)


def set_session_service_instance(service: ISessionService) -> None:
    """设置Session服务实例"""
    _session_service_injection.set_instance(service)


def set_session_thread_association_repository_instance(repository: ISessionThreadAssociationRepository) -> None:
    """设置Session-Thread关联仓储实例"""
    _session_thread_association_repository_injection.set_instance(repository)


def set_session_thread_synchronizer_instance(synchronizer: ISessionThreadSynchronizer) -> None:
    """设置Session-Thread同步器实例"""
    _session_thread_synchronizer_injection.set_instance(synchronizer)


def set_session_thread_transaction_instance(transaction: ISessionThreadTransaction) -> None:
    """设置Session-Thread事务管理器实例"""
    _session_thread_transaction_injection.set_instance(transaction)


def set_session_thread_coordinator_instance(coordinator: SessionThreadCoordinator) -> None:
    """设置Session-Thread协调器实例"""
    _session_thread_coordinator_injection.set_instance(coordinator)


# 清除实例的便捷函数（主要用于测试）
def clear_session_repository_instance() -> None:
    """清除Session仓储实例"""
    _session_repository_injection.clear_instance()


def clear_session_service_instance() -> None:
    """清除Session服务实例"""
    _session_service_injection.clear_instance()


def clear_session_thread_association_repository_instance() -> None:
    """清除Session-Thread关联仓储实例"""
    _session_thread_association_repository_injection.clear_instance()


def clear_session_thread_synchronizer_instance() -> None:
    """清除Session-Thread同步器实例"""
    _session_thread_synchronizer_injection.clear_instance()


def clear_session_thread_transaction_instance() -> None:
    """清除Session-Thread事务管理器实例"""
    _session_thread_transaction_injection.clear_instance()


def clear_session_thread_coordinator_instance() -> None:
    """清除Session-Thread协调器实例"""
    _session_thread_coordinator_injection.clear_instance()


# 获取状态的便捷函数
def get_session_repository_status() -> dict:
    """获取Session仓储状态"""
    return _session_repository_injection.get_status()


def get_session_service_status() -> dict:
    """获取Session服务状态"""
    return _session_service_injection.get_status()


def get_session_thread_association_repository_status() -> dict:
    """获取Session-Thread关联仓储状态"""
    return _session_thread_association_repository_injection.get_status()


def get_session_thread_synchronizer_status() -> dict:
    """获取Session-Thread同步器状态"""
    return _session_thread_synchronizer_injection.get_status()


def get_session_thread_transaction_status() -> dict:
    """获取Session-Thread事务管理器状态"""
    return _session_thread_transaction_injection.get_status()


def get_session_thread_coordinator_status() -> dict:
    """获取Session-Thread协调器状态"""
    return _session_thread_coordinator_injection.get_status()


# 导出的公共接口
__all__ = [
    # 获取函数
    "get_session_repository",
    "get_session_service",
    "get_session_thread_association_repository",
    "get_session_thread_synchronizer",
    "get_session_thread_transaction",
    "get_session_thread_coordinator",
    
    # 设置函数
    "set_session_repository_instance",
    "set_session_service_instance",
    "set_session_thread_association_repository_instance",
    "set_session_thread_synchronizer_instance",
    "set_session_thread_transaction_instance",
    "set_session_thread_coordinator_instance",
    
    # 清除函数
    "clear_session_repository_instance",
    "clear_session_service_instance",
    "clear_session_thread_association_repository_instance",
    "clear_session_thread_synchronizer_instance",
    "clear_session_thread_transaction_instance",
    "clear_session_thread_coordinator_instance",
    
    # 状态函数
    "get_session_repository_status",
    "get_session_service_status",
    "get_session_thread_association_repository_status",
    "get_session_thread_synchronizer_status",
    "get_session_thread_transaction_status",
    "get_session_thread_coordinator_status",
]