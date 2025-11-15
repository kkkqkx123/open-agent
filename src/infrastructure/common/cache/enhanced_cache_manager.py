"""增强缓存管理器"""

import threading
from collections import OrderedDict
from typing import Any, Dict, Optional, List, Pattern
import re
from datetime import datetime, timedelta

from .cache_entry import CacheEntry, CacheStats
from ..temporal.temporal_manager import TemporalManager


class EnhancedCacheManager:
    """增强缓存管理器"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """初始化缓存管理器
        
        Args:
            max_size: 最大缓存项数
            default_ttl: 默认TTL（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或过期则返回None
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats.record_miss()
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._stats.record_miss()
                return None
            
            # 移动到末尾（LRU）
            self._cache.move_to_end(key)
            self._stats.record_hit()
            return entry.access()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），如果为None则使用默认TTL
        """
        with self._lock:
            # 如果最大大小为0，不存储任何项
            if self.max_size == 0:
                return
            
            now = TemporalManager.now()
            expires_at = None
            if ttl is not None and ttl > 0:
                expires_at = now + timedelta(seconds=ttl)
            elif self.default_ttl > 0:
                expires_at = now + timedelta(seconds=self.default_ttl)
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=expires_at
            )
            
            # 如果键已存在，更新值
            if key in self._cache:
                self._cache[key] = entry
                self._cache.move_to_end(key)
                return
            
            # 检查容量限制
            while len(self._cache) >= self.max_size and self.max_size > 0:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats.record_eviction()
            
            # 添加新项
            self._cache[key] = entry
    
    async def remove(self, key: str) -> bool:
        """移除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功移除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def remove_by_pattern(self, pattern: str) -> int:
        """根据模式移除缓存项
        
        Args:
            pattern: 正则表达式模式
            
        Returns:
            移除的缓存项数量
        """
        with self._lock:
            regex = re.compile(pattern)
            keys_to_remove = [key for key in self._cache.keys() if regex.match(key)]
            
            for key in keys_to_remove:
                del self._cache[key]
            
            return len(keys_to_remove)
    
    async def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
    
    async def cleanup_expired(self) -> int:
        """清理过期的缓存项
        
        Returns:
            清理的缓存项数量
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "evictions": self._stats.evictions,
                "total_requests": self._stats.total_requests,
                "hit_rate": self._stats.hit_rate,
                "keys": list(self._cache.keys())
            }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取详细缓存信息
        
        Returns:
            详细缓存信息
        """
        with self._lock:
            cache_info = {}
            now = TemporalManager.now()
            
            for key, entry in self._cache.items():
                cache_info[key] = {
                    "created_at": entry.created_at.isoformat(),
                    "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
                    "access_count": entry.access_count,
                    "last_accessed": entry.last_accessed.isoformat(),
                    "is_expired": entry.is_expired(),
                    "ttl_remaining": (entry.expires_at - now).total_seconds() if entry.expires_at else None
                }
            
            return cache_info
    
    async def get_or_set(self, key: str, factory_func, ttl: Optional[int] = None) -> Any:
        """获取缓存值，如果不存在则通过工厂函数创建
        
        Args:
            key: 缓存键
            factory_func: 工厂函数
            ttl: TTL（秒）
            
        Returns:
            缓存值
        """
        value = await self.get(key)
        if value is not None:
            return value
        
        value = await factory_func()
        await self.set(key, value, ttl)
        return value