"""默认缓存管理器 - 基础设施层内部的简单实现"""

import asyncio
import time
from typing import Any, Optional, Dict
from collections import OrderedDict
from .cache_manager_protocol import CacheManagerProtocol


class MemoryCacheManager(CacheManagerProtocol):
    """内存缓存管理器 - 简单的内存缓存实现
    
    该实现完全在基础设施层内部，不依赖其他任何层，
    用于在ServiceCacheAdapter中提供默认的缓存功能。
    """
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """初始化内存缓存管理器
        
        Args:
            default_ttl: 默认TTL（秒）
            max_size: 最大缓存项数
        """
        self._cache: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        self._access_time: Dict[str, float] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        async with self._lock:
            # 检查是否过期
            if key in self._expiry and time.time() > self._expiry[key]:
                await self.delete(key)
                return None
            
            if key in self._cache:
                self._access_time[key] = time.time()
                return self._cache[key]
            
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），如果为None则使用默认值
            
        Returns:
            是否设置成功
        """
        ttl = ttl or self.default_ttl
        expiry_time = time.time() + ttl
        
        async with self._lock:
            # LRU: 如果缓存满了，删除最久未使用的项
            if len(self._cache) >= self.max_size and key not in self._cache:
                oldest_key = min(self._access_time, key=self._access_time.get)
                await self.delete(oldest_key)
            
            self._cache[key] = value
            self._expiry[key] = expiry_time
            self._access_time[key] = time.time()
            
            return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        async with self._lock:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
            self._access_time.pop(key, None)
            return True
    
    async def clear(self) -> bool:
        """清空缓存
        
        Returns:
            是否清空成功
        """
        async with self._lock:
            self._cache.clear()
            self._expiry.clear()
            self._access_time.clear()
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "cache_size": len(self._cache),
            "hit_rate": 0.0,  # 简化实现
            "max_size": self.max_size,
            "default_ttl": self.default_ttl
        }