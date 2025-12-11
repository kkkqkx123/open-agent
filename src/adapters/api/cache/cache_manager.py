"""内存缓存管理器 - 提供轻量级缓存服务"""

from typing import Any, Optional, Dict, Union, List
from src.interfaces.dependency_injection import get_logger
from pathlib import Path

from .memory_cache import MemoryCache

logger = get_logger(__name__)


class CacheManager:
    """内存缓存管理器 - 提供轻量级缓存服务
    
    该类提供基于内存的缓存服务，支持TTL过期机制，
    专注于性能和内存效率。
    """
    
    def __init__(
        self,
        default_ttl: int = 300,  # 默认5分钟
        enable_stats: bool = True,
        fallback_enabled: bool = True,
        invalidation_enabled: bool = True
    ):
        """初始化内存缓存管理器
        
        Args:
            default_ttl: 默认TTL（秒）
            enable_stats: 是否启用统计
            fallback_enabled: 是否启用缓存降级机制
            invalidation_enabled: 是否启用缓存失效机制
        """
        self.default_ttl = default_ttl
        self.enable_stats = enable_stats
        self.fallback_enabled = fallback_enabled
        self.invalidation_enabled = invalidation_enabled
        
        # 创建内存缓存实例
        self._cache = MemoryCache(default_ttl=default_ttl)
        
        logger.info(f"内存缓存管理器初始化完成 (降级: {fallback_enabled}, 失效: {invalidation_enabled})")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            return await self._cache.get(key)
        except Exception as e:
            logger.warning(f"缓存获取失败 (key={key}): {e}")
            if self.fallback_enabled:
                logger.info(f"启用降级机制，返回None (key={key})")
                return None
            else:
                raise
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            ttl = ttl or self.default_ttl
            await self._cache.set(key, value, ttl)
            return True
        except Exception as e:
            logger.warning(f"缓存设置失败 (key={key}): {e}")
            if self.fallback_enabled:
                logger.info(f"启用降级机制，返回True (key={key})")
                return True
            else:
                return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            await self._cache.delete(key)
            return True
        except Exception as e:
            logger.warning(f"缓存删除失败 (key={key}): {e}")
            if self.fallback_enabled:
                logger.info(f"启用降级机制，返回True (key={key})")
                return True
            else:
                return False
    
    async def clear(self) -> bool:
        """清空缓存"""
        try:
            await self._cache.clear()
            return True
        except Exception as e:
            logger.warning(f"缓存清空失败: {e}")
            if self.fallback_enabled:
                logger.info("启用降级机制，返回True")
                return True
            else:
                return False
    

    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "default_ttl": self.default_ttl,
            "enable_stats": self.enable_stats,
            "fallback_enabled": self.fallback_enabled,
            "invalidation_enabled": self.invalidation_enabled
        }
        
        return stats
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取详细缓存信息"""
        info = {
            "cache_type": "memory",
            "default_ttl": self.default_ttl,
            "enable_stats": self.enable_stats,
            "fallback_enabled": self.fallback_enabled,
            "invalidation_enabled": self.invalidation_enabled
        }
        
        try:
            # 从内存缓存中获取缓存统计信息
            if hasattr(self._cache, '_cache'):
                info["cache_entries"] = len(self._cache._cache)
            
        except Exception as e:
            info["error"] = str(e)
        
        return info
    
    def switch_cache_type(self, new_type: str) -> bool:
        """动态切换缓存类型
        
        Args:
            new_type: 新的缓存类型
            
        Returns:
            是否成功切换
        """
        if new_type != "memory":
            logger.error(f"不支持的缓存类型: {new_type}")
            return False
        
        logger.info("当前仅支持内存缓存类型，无需切换")
        return True
    
    async def get_all_keys(self) -> List[str]:
        """获取所有缓存键"""
        try:
            return await self._cache.get_all_keys()
        except Exception as e:
            logger.warning(f"获取缓存键失败: {e}")
            if self.fallback_enabled:
                logger.info("启用降级机制，返回空列表")
                return []
            else:
                raise