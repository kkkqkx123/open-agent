"""服务容器模块

提供依赖注入容器和生命周期管理功能。
"""

from .lifecycle_manager import LifecycleManager, get_global_lifecycle_manager

__all__ = [
    "LifecycleManager",
    "get_global_lifecycle_manager",
]