"""内存缓存实现"""
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import asyncio


class MemoryCache:
    """内存缓存实现"""
    
    def __init__(self, default_ttl: int = 300):  # 默认5分钟
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            if key in self._cache:
                item = self._cache[key]
                if item['expires_at'] > datetime.now():
                    return item['value']
                else:
                    # 过期，删除
                    del self._cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        async with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at
            }
    
    async def delete(self, key: str) -> None:
        """删除缓存"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def clear(self) -> None:
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
    
    async def cleanup_expired(self) -> None:
        """清理过期缓存"""
        now = datetime.now()
        async with self._lock:
            expired_keys = [
                key for key, item in self._cache.items()
                if item['expires_at'] <= now
            ]
            for key in expired_keys:
                del self._cache[key]
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        async with self._lock:
            total_items = len(self._cache)
            expired_items = sum(
                1 for item in self._cache.values()
                if item['expires_at'] <= datetime.now()
            )
            
            return {
                "total_items": total_items,
                "expired_items": expired_items,
                "active_items": total_items - expired_items
            }
    
    async def get_all_keys(self) -> List[str]:
        """获取所有缓存键"""
        async with self._lock:
            return list(self._cache.keys())