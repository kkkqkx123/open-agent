"""内存缓存提供者"""

import time
import threading
import asyncio
from typing import Any, Optional, Dict
from collections import OrderedDict

from src.interfaces.llm import ICacheProvider
from ...config.cache_config import CacheEntry


class MemoryCacheProvider(ICacheProvider):
    """内存缓存提供者"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        初始化内存缓存提供者
        
        Args:
            max_size: 最大缓存项数
            default_ttl: 默认TTL（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            # 检查是否过期
            if entry.is_expired():
                del self._cache[key]
                return None
            
            # 移动到末尾（LRU）
            self._cache.move_to_end(key)
            return entry.access()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认TTL
        """
        with self._lock:
            current_time = time.time()
            
            # 计算过期时间
            if ttl is None:
                ttl = self.default_ttl
            
            # 如果TTL为负数，表示不过期（ttl=None），使用默认值
            if ttl < 0:
                ttl = self.default_ttl
            # 如果TTL为0，表示立即过期，不存储
            elif ttl == 0:
                return
            
            expires_at = current_time + ttl
            
            # 如果max_size为0，则不存储任何项
            if self.max_size == 0:
                return
            
            # 创建缓存项
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=current_time,
                expires_at=expires_at
            )
            
            # 如果键已存在，更新值
            if key in self._cache:
                self._cache[key] = entry
                self._cache.move_to_end(key)
                return
            
            # 检查容量限制
            while len(self._cache) >= self.max_size and self.max_size > 0:
                # 移除最旧的项（LRU）
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            
            # 添加新项
            self._cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
    
    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            
            # 检查是否过期
            if entry.is_expired():
                del self._cache[key]
                return False
            
            return True
    
    def get_size(self) -> int:
        """
        获取缓存大小
        
        Returns:
            缓存项数量
        """
        with self._lock:
            # 获取大小时清理过期项以保持一致性
            self._cleanup_expired_entries()
            return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """
        清理过期的缓存项
        
        Returns:
            清理的项数量
        """
        with self._lock:
            return self._cleanup_expired_entries()
    
    def _cleanup_expired_entries(self) -> int:
        """内部方法：清理过期项"""
        expired_keys = []
        current_time = time.time()
        
        for key, entry in list(self._cache.items()):  # 使用list()避免迭代时修改字典
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            if key in self._cache:  # 确保键仍然存在
                del self._cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            # 先清理过期项
            self._cleanup_expired_entries()
            
            total_entries = len(self._cache)
            total_access_count = 0
            oldest_age = 0
            newest_age = 0
            
            current_time = time.time()
            ages = []
            
            for entry in self._cache.values():
                total_access_count += entry.access_count
                age = entry.get_age_seconds()
                ages.append(age)
            
            if ages:
                oldest_age = max(ages) if ages else 0
                newest_age = min(ages) if ages else 0
            
            return {
                "total_entries": total_entries,
                "expired_entries": 0,  # 过期项已经被清理
                "valid_entries": total_entries,
                "max_size": self.max_size,
                "utilization": total_entries / self.max_size if self.max_size > 0 else 0,
                "total_access_count": total_access_count,
                "oldest_entry_age_seconds": oldest_age,
                "newest_entry_age_seconds": newest_age,
            }

    async def get_async(self, key: str) -> Optional[Any]:
        """
        异步获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在则返回None
        """
        return await asyncio.to_thread(self.get, key)

    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        异步设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认TTL
        """
        await asyncio.to_thread(self.set, key, value, ttl)