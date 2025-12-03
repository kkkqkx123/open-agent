"""缓存模块初始化文件（向后兼容层）

本模块已迁移到 src/infrastructure/cache/，此文件仅为向后兼容性保留。
新代码应该直接从 src/infrastructure/cache/ 导入。
"""

from typing import Optional
# 从新位置导入，提供向后兼容性
from src.infrastructure.cache.core.cache_manager import CacheManager
from src.infrastructure.cache.config.cache_config import (
    BaseCacheConfig, LLMCacheConfig, GeminiCacheConfig, AnthropicCacheConfig
)
from src.interfaces.llm import ICacheProvider, ICacheKeyGenerator
from .server_interfaces import IServerCacheProvider
from src.infrastructure.cache.providers.memory.memory_provider import MemoryCacheProvider
from src.infrastructure.cache.core.key_generator import (
    LLMCacheKeyGenerator,
    GeminiCacheKeyGenerator,
    AnthropicCacheKeyGenerator,
    DefaultCacheKeyGenerator
)
from src.infrastructure.cache.providers.gemini.gemini_cache_manager import GeminiCacheManager
from .providers.gemini_server_provider import GeminiServerCacheProvider

# 工厂函数
def create_cache_manager(config: BaseCacheConfig,
                        client_provider: Optional[ICacheProvider] = None,
                        server_provider: Optional[IServerCacheProvider] = None,
                        key_generator: Optional[ICacheKeyGenerator] = None) -> CacheManager:
    """
    创建缓存管理器
    
    Args:
        config: 缓存配置
        client_provider: 客户端缓存提供者（可选）
        server_provider: 服务器端缓存提供者（可选）
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

def create_gemini_cache_manager(config: Optional[GeminiCacheConfig] = None,
                               gemini_client=None) -> CacheManager:
    """
    创建Gemini缓存管理器
    
    Args:
        config: Gemini缓存配置（可选，使用默认配置）
        gemini_client: Gemini客户端实例（用于服务器端缓存）
        
    Returns:
        Gemini缓存管理器实例
    """
    if config is None:
        config = GeminiCacheConfig.create_default()
    
    # 创建服务器端缓存提供者
    server_provider = None
    if gemini_client and config.server_cache_enabled:
        server_provider = GeminiServerCacheProvider(
            gemini_client=gemini_client,
            model_name=config.model_name
        )
    
    # 创建Gemini专用键生成器
    key_generator = GeminiCacheKeyGenerator()
    
    return CacheManager(
        config=config,
        server_provider=server_provider,
        key_generator=key_generator
    )

def create_anthropic_cache_manager(config: Optional[AnthropicCacheConfig] = None) -> CacheManager:
    """
    创建Anthropic缓存管理器
    
    Args:
        config: Anthropic缓存配置（可选，使用默认配置）
        
    Returns:
        Anthropic缓存管理器实例
    """
    if config is None:
        config = AnthropicCacheConfig.create_default()
    
    return CacheManager(config=config)

# 向后兼容的工厂函数
def create_legacy_cache_manager(model_type: str, config: BaseCacheConfig, gemini_client=None) -> CacheManager:
    """
    创建缓存管理器（向后兼容）
    
    Args:
        model_type: 模型类型 ("gemini", "anthropic", "general")
        config: 缓存配置
        gemini_client: Gemini客户端实例
        
    Returns:
        缓存管理器实例
    """
    if model_type == "gemini":
        if isinstance(config, GeminiCacheConfig):
            return create_gemini_cache_manager(config, gemini_client)
        else:
            # 转换为Gemini配置
            gemini_config = GeminiCacheConfig.create_default()
            gemini_config.enabled = config.enabled
            gemini_config.ttl_seconds = config.ttl_seconds
            gemini_config.max_size = config.max_size
            gemini_config.cache_type = config.cache_type
            return create_gemini_cache_manager(gemini_config, gemini_client)
    elif model_type == "anthropic":
        if isinstance(config, AnthropicCacheConfig):
            return create_anthropic_cache_manager(config)
        else:
            # 转换为Anthropic配置
            anthropic_config = AnthropicCacheConfig.create_default()
            anthropic_config.enabled = config.enabled
            anthropic_config.ttl_seconds = config.ttl_seconds
            anthropic_config.max_size = config.max_size
            anthropic_config.cache_type = config.cache_type
            return create_anthropic_cache_manager(anthropic_config)
    else:
        # 通用缓存管理器
        return create_cache_manager(config)

__all__ = [
    # 核心类
    "CacheManager",
    
    # 配置类
    "BaseCacheConfig",
    "LLMCacheConfig",
    "GeminiCacheConfig",
    "AnthropicCacheConfig",
    
    # 接口
    "ICacheProvider",
    "ICacheKeyGenerator",
    "IServerCacheProvider",
    
    # 提供者
    "MemoryCacheProvider",
    "GeminiServerCacheProvider",
    
    # 键生成器
    "LLMCacheKeyGenerator",
    "GeminiCacheKeyGenerator",
    "AnthropicCacheKeyGenerator",
    "DefaultCacheKeyGenerator",
    
    # 专用管理器
    "GeminiCacheManager",
    
    # 工厂函数
    "create_cache_manager",
    "create_gemini_cache_manager",
    "create_anthropic_cache_manager",
    "create_legacy_cache_manager"
]