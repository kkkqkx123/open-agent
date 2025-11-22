"""
内存提示词缓存实现

提供基于内存的提示词缓存功能
"""

import time
import re
from typing import Any, Optional, Dict, List, Sequence
from datetime import timedelta
from collections import OrderedDict
import pickle
import threading

from ....interfaces.prompts.cache import (
    IPromptCache, 
    ICacheEntry, 
    ICacheEvictionPolicy, 
    ICacheSerializer
)
from ....core.common.exceptions import PromptCacheError


class MemoryCacheEntry(ICacheEntry):
    """内存缓存条目"""
    
    def __init__(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[timedelta] = None
    ):
        self._key = key
        self._value = value
        self._created_at = time.time()
        self._expires_at = (
            self._created_at + ttl.total_seconds() 
            if ttl else None
        )
        self._access_count = 0
        self._last_accessed = self._created_at
    
    @property
    def key(self) -> str:
        return self._key
    
    @property
    def value(self) -> Any:
        return self._value
    
    @property
    def created_at(self) -> float:
        return self._created_at
    
    @property
    def expires_at(self) -> Optional[float]:
        return self._expires_at
    
    @property
    def access_count(self) -> int:
        return self._access_count
    
    @property
    def last_accessed(self) -> float:
        return self._last_accessed
    
    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self._expires_at is None:
            return False
        return time.time() > self._expires_at
    
    def touch(self) -> None:
        """更新访问时间和次数"""
        self._access_count += 1
        self._last_accessed = time.time()


class LRUEvictionPolicy(ICacheEvictionPolicy):
    """LRU淘汰策略"""
    
    def should_evict(self, entry: ICacheEntry) -> bool:
        """LRU策略不主动淘汰，由缓存容量控制"""
        return False
    
    def select_victim(self, entries: Sequence[ICacheEntry]) -> Optional[ICacheEntry]:
        """选择最近最少使用的条目"""
        if not entries:
            return None
        
        # 按最后访问时间排序，选择最早的
        sorted_entries = sorted(
            entries, 
            key=lambda e: e.last_accessed
        )
        return sorted_entries[0]


class LFUEvictionPolicy(ICacheEvictionPolicy):
    """LFU淘汰策略"""
    
    def should_evict(self, entry: ICacheEntry) -> bool:
        """LFU策略不主动淘汰，由缓存容量控制"""
        return False
    
    def select_victim(self, entries: Sequence[ICacheEntry]) -> Optional[ICacheEntry]:
        """选择使用频率最低的条目"""
        if not entries:
            return None
        
        # 按访问次数排序，选择最少的
        sorted_entries = sorted(
            entries, 
            key=lambda e: (e.access_count, e.last_accessed)
        )
        return sorted_entries[0]


class PickleSerializer(ICacheSerializer):
    """Pickle序列化器"""
    
    def serialize(self, value: Any) -> bytes:
        """序列化值"""
        try:
            return pickle.dumps(value)
        except Exception as e:
            raise PromptCacheError(f"序列化失败: {e}")
    
    def deserialize(self, data: bytes) -> Any:
        """反序列化值"""
        try:
            return pickle.loads(data)
        except Exception as e:
            raise PromptCacheError(f"反序列化失败: {e}")


class MemoryPromptCache(IPromptCache):
    """内存提示词缓存实现"""
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[timedelta] = None,
        eviction_policy: Optional[ICacheEvictionPolicy] = None,
        serializer: Optional[ICacheSerializer] = None
    ):
        self._max_size = max_size
        self._default_ttl = default_ttl or timedelta(hours=1)
        self._eviction_policy = eviction_policy or LRUEvictionPolicy()
        self._serializer = serializer or PickleSerializer()
        
        self._cache: OrderedDict[str, MemoryCacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # 统计信息
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            
            # 更新访问信息
            entry.touch()
            # 移动到末尾（LRU）
            self._cache.move_to_end(key)
            self._hits += 1
            
            return entry.value
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[timedelta] = None
    ) -> None:
        """设置缓存值"""
        with self._lock:
            # 检查是否需要淘汰
            if key not in self._cache and len(self._cache) >= self._max_size:
                await self._evict_one()
            
            # 创建新条目
            entry = MemoryCacheEntry(
                key=key,
                value=value,
                ttl=ttl or self._default_ttl
            )
            
            self._cache[key] = entry
            self._cache.move_to_end(key)
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            
            if entry.is_expired():
                del self._cache[key]
                return False
            
            return True
    
    async def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    async def get_ttl(self, key: str) -> Optional[timedelta]:
        """获取键的剩余生存时间"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None or entry.expires_at is None:
                return None
            
            remaining = entry.expires_at - time.time()
            if remaining <= 0:
                return None
            
            return timedelta(seconds=remaining)
    
    async def set_ttl(self, key: str, ttl: timedelta) -> bool:
        """设置键的生存时间"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            
            entry._expires_at = time.time() + ttl.total_seconds()
            return True
    
    async def get_keys(self, pattern: str = "*") -> List[str]:
        """获取匹配模式的所有键"""
        with self._lock:
            # 转换glob模式到正则表达式
            regex_pattern = pattern.replace("*", ".*").replace("?", ".")
            regex_pattern = f"^{regex_pattern}$"
            
            regex = re.compile(regex_pattern)
            keys = []
            
            # 清理过期条目
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
                elif regex.match(key):
                    keys.append(key)
            
            # 删除过期条目
            for key in expired_keys:
                del self._cache[key]
            
            return keys
    
    async def get_size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            # 清理过期条目
            await self._cleanup_expired()
            return len(self._cache)
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "size": len(self._cache),
                "max_size": self._max_size
            }
    
    async def _evict_one(self) -> None:
        """淘汰一个条目"""
        if not self._cache:
            return
        
        # 清理过期条目
        await self._cleanup_expired()
        
        # 如果仍然需要淘汰，使用策略选择
        if len(self._cache) >= self._max_size:
            entries = list(self._cache.values())
            victim = self._eviction_policy.select_victim(entries)
            
            if victim:
                del self._cache[victim.key]
                self._evictions += 1
    
    async def _cleanup_expired(self) -> None:
        """清理过期条目"""
        expired_keys = []
        for key, entry in self._cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]