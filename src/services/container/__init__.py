"""服务容器模块

提供依赖注入容器和生命周期管理功能。
"""

from .lifecycle_manager import LifecycleManager, get_global_lifecycle_manager
from .container import DependencyContainer, get_global_container
from .storage_bindings import (
    register_all_storage_services,
    register_session_storage_only,
    register_thread_storage_only,
)
from .session_bindings import register_all_session_services
from .thread_bindings import register_all_thread_services

__all__ = [
    "LifecycleManager",
    "get_global_lifecycle_manager",
    "DependencyContainer",
    "get_global_container",
    "register_all_storage_services",
    "register_session_storage_only",
    "register_thread_storage_only",
    "register_all_session_services",
    "register_all_thread_services",
]