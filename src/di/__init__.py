"""统一依赖注入模块

提供分层架构的依赖注入容器管理。
"""

from .unified_container import UnifiedContainerManager, get_unified_container, reset_unified_container
from .interfaces import IServiceModule
from .environment_config import EnvironmentConfigManager

__all__ = [
    "UnifiedContainerManager",
    "get_unified_container", 
    "reset_unified_container",
    "IServiceModule",
    "EnvironmentConfigManager"
]