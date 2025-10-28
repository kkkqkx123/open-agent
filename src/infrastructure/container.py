"""依赖注入容器模块

提供依赖注入容器的接口和工厂函数。
"""

from typing import Optional

# 为了向后兼容，重新导出一些类型和类
from .container import (
    IDependencyContainer,
    IServiceTracker,
    ILifecycleAware,
    ServiceStatus,
    EnhancedDependencyContainer,
    DependencyContainer,  # 从子模块导入别名
    get_global_container
)
from .types import ServiceRegistration, ServiceLifetime, T
from .exceptions import (
    ServiceNotRegisteredError,
    ServiceCreationError,
    CircularDependencyError,
)

__all__ = [
    "IDependencyContainer",
    "ServiceRegistration", 
    "ServiceLifetime",
    "ServiceStatus",
    "ServiceNotRegisteredError",
    "ServiceCreationError", 
    "CircularDependencyError",
    "ILifecycleAware",
    "IServiceTracker",
    "DependencyContainer",
    "get_global_container"
]


# 全局依赖注入容器实例（为了向后兼容）
_global_container: Optional[EnhancedDependencyContainer] = None


def get_container(
    enable_service_cache: bool = True,
    enable_path_cache: bool = True,
    max_cache_size: int = 1000,
    cache_ttl_seconds: int = 3600,
    enable_tracking: bool = False
) -> EnhancedDependencyContainer:
    """获取全局依赖注入容器（为了向后兼容）

    Returns:
        EnhancedDependencyContainer: 全局依赖注入容器
    """
    global _global_container
    if _global_container is None:
        from .container.enhanced_container import EnhancedDependencyContainer
        _global_container = EnhancedDependencyContainer(
            enable_service_cache=enable_service_cache,
            enable_path_cache=enable_path_cache,
            max_cache_size=max_cache_size,
            cache_ttl_seconds=cache_ttl_seconds,
            enable_tracking=enable_tracking
        )
    return _global_container