"""缓存模块初始化文件"""

from .cache_manager import CacheManager
from .cache_config import CacheConfig
from .enhanced_cache_config import EnhancedCacheConfig, GeminiCacheConfig
from .interfaces import ICacheProvider, ICacheKeyGenerator
from .memory_provider import MemoryCacheProvider
from .key_generator import LLMCacheKeyGenerator
from .gemini_cache_manager import GeminiCacheManager
from .gemini_server_cache_manager import GeminiServerCacheManager
from .enhanced_gemini_cache_manager import EnhancedGeminiCacheManager

# 工厂函数
def create_cache_manager(model_type: str, config: CacheConfig, gemini_client=None) -> CacheManager:
    """
    创建缓存管理器
    
    Args:
        model_type: 模型类型
        config: 缓存配置
        gemini_client: Gemini客户端实例（用于Gemini服务器端缓存）
        
    Returns:
        缓存管理器实例
    """
    if model_type == "gemini" and isinstance(config, EnhancedCacheConfig):
        # 为Gemini创建增强缓存管理器
        return EnhancedGeminiCacheManager(config, gemini_client)
    elif model_type == "gemini":
        # 为Gemini创建专用缓存管理器
        return GeminiCacheManager(config)
    else:
        # 创建通用缓存管理器
        return CacheManager(config)

def create_gemini_cache_manager(config: CacheConfig, gemini_client=None) -> EnhancedGeminiCacheManager:
    """
    创建Gemini缓存管理器
    
    Args:
        config: 缓存配置
        gemini_client: Gemini客户端实例
        
    Returns:
        Gemini缓存管理器实例
    """
    if not isinstance(config, EnhancedCacheConfig):
        # 转换为增强配置
        config = GeminiCacheConfig.from_dict(config.to_dict())
    
    # 确保配置中有模型名称
    if not hasattr(config, 'model_name') or not config.model_name:
        raise ValueError("Gemini缓存配置必须包含model_name")
    
    return EnhancedGeminiCacheManager(config, gemini_client)

__all__ = [
    "CacheManager",
    "CacheConfig", 
    "EnhancedCacheConfig",
    "GeminiCacheConfig",
    "ICacheProvider",
    "ICacheKeyGenerator",
    "MemoryCacheProvider",
    "LLMCacheKeyGenerator",
    "GeminiCacheManager",
    "GeminiServerCacheManager", 
    "EnhancedGeminiCacheManager",
    "create_cache_manager",
    "create_gemini_cache_manager"
]