"""状态管理工具模块

提供状态管理相关的工具类和适配器。
"""

# 缓存适配器
from .state_cache_adapter import StateCacheAdapter

__all__ = [
    "StateCacheAdapter"
]