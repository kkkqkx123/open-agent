"""基础设施缓存模块

这个模块提供了统一的缓存系统，支持多种提供者实现。
LLM 专用缓存功能在 .llm 子模块中，通过以下方式导入：
  from src.infrastructure.cache.llm import LLMCacheManager, GeminiCacheConfig
"""

from typing import Any, Optional

# Core 模块导入
from .core.cache_manager import CacheManager
from .core.key_generator import (
    DefaultCacheKeyGenerator,
    ICacheKeyGenerator
)

# 配置导入
from .config.cache_config import (
    BaseCacheConfig,
    CacheEntry
)

# 接口导入
from src.interfaces.llm import ICacheProvider, ICacheKeyGenerator as IICacheKeyGenerator

# 提供者导入
from .providers.memory.memory_provider import MemoryCacheProvider
from src.infrastructure.cache.interfaces.server_cache_provider import IServerCacheProvider


# 工厂函数
def create_cache_manager(config: BaseCacheConfig,
                        client_provider: Optional[ICacheProvider] = None,
                        server_provider: Optional[Any] = None,
                        key_generator: Optional[IICacheKeyGenerator] = None) -> CacheManager:
    """
    创建缓存管理器
    
    Args:
        config: 缓存配置
        client_provider: 客户端缓存提供者（可选）
        server_provider: 服务器端缓存提供者（可选，保留兼容性）
        key_generator: 键生成器（可选）
        
    Returns:
        缓存管理器实例
    """
    return CacheManager(
        config=config,
        client_provider=client_provider,
        server_provider=server_provider,
        key_generator=key_generator
    )

__all__ = [
    # 核心类
    "CacheManager",
    
    # 配置类
    "BaseCacheConfig",
    "CacheEntry",
    
    # 接口
    "ICacheProvider",
    "ICacheKeyGenerator",
    "IServerCacheProvider",
    
    # 提供者
    "MemoryCacheProvider",
    
    # 键生成器
    "DefaultCacheKeyGenerator",
    
    # 工厂函数
    "create_cache_manager",
]
