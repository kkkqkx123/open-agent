"""容器模块"""

from .base_container import BaseDependencyContainer
from .enhanced_container import EnhancedDependencyContainer, create_optimized_container, get_global_container
from .dependency_analyzer import DependencyAnalyzer
from .performance_monitor_adapter import ContainerPerformanceMonitor
from .scope_manager import ScopeManager

# 重新导出一些常用的类型和接口
from ..container_interfaces import (
    IDependencyContainer,
    IServiceTracker,
    ILifecycleAware,
    ServiceStatus
)
from ..types import ServiceLifetime

# 为了向后兼容，创建一个别名
DependencyContainer = EnhancedDependencyContainer

__all__ = [
    "BaseDependencyContainer",
    "EnhancedDependencyContainer",
    "DependencyContainer",
    "create_optimized_container",
    "get_global_container",
    "DependencyAnalyzer",
    "ContainerPerformanceMonitor",
    "ScopeManager",
    "IDependencyContainer",
    "IServiceTracker",
    "ILifecycleAware",
    "ServiceStatus",
    "ServiceLifetime"
]