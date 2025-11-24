"""状态管理配置模块

提供状态管理的配置加载和管理功能。
"""

from .settings import (
    StateManagementConfig,
    get_global_config,
    set_global_config
)

__all__ = [
    "StateManagementConfig",
    "get_global_config",
    "set_global_config"
]