"""缓存配置模块

包含各种缓存配置类。LLM专用的配置已移动到 llm 模块中。
"""

from .cache_config import (
    BaseCacheConfig,
    CacheEntry
)

__all__ = [
    "BaseCacheConfig",
    "CacheEntry",
]
