"""通用缓存模块

提供统一的缓存接口，支持序列化、TTL过期、LRU淘汰等功能
"""

from .cache_entry import CacheEntry, CacheStats
from .cache_manager import CacheManager

__all__ = [
    "CacheEntry",
    "CacheStats", 
    "CacheManager"
]