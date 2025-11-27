"""
增强的缓存系统 - 基于cachetools库并整合基础设施层高级功能

使用time.time()作为时间戳基础以保证轻量级、高效和与interfaces接口兼容
"""

import time
import threading
from typing import Any, Optional, Dict, Union, List
from collections import OrderedDict
from dataclasses import dataclass

from cachetools import TTLCache, LRUCache, cached

@dataclass
class CacheEntry:
    """缓存条目
    
    使用float时间戳（秒级）存储时间，与IPromptCache接口兼容
    """
    key: str
    value: Any
    created_at: float  # time.time()返回的时间戳
    expires_at: Optional[float] = None  # TTL过期时间戳
    access_count: int = 0
    last_accessed: Optional[float] = None
    
    def __post_init__(self) -> None:
        if self.last_accessed is None:
            self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def access(self) -> Any:
        """访问缓存项"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value
    
    def extend_ttl(self, seconds: int) -> None:
        """延长TTL（秒）"""
        if self.expires_at:
            self.expires_at = max(self.expires_at, time.time() + seconds)
        else:
            self.expires_at = time.time() + seconds


@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    
    @property
    def hit_rate(self) -> float:
        """命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    def record_hit(self) -> None:
        """记录命中"""
        self.hits += 1
        self.total_requests += 1
    
    def record_miss(self) -> None:
        """记录未命中"""
        self.misses += 1
        self.total_requests += 1
    
    def record_eviction(self) -> None:
        """记录淘汰"""
        self.evictions += 1


class CacheManager:
    """增强的缓存管理器，整合了基础设施层的高级功能"""
    
    def __init__(self, 
                 max_size: int = 1000, 
                 default_ttl: int = 3600, 
                 enable_serialization: bool = False, 
                 serialization_format: str = "json"):
        """初始化缓存管理器
        Args:
            max_size: 最大缓存项数
            default_ttl: 默认TTL（秒）
            enable_serialization: 是否启用序列化
            serialization_format: 序列化格式
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enable_serialization = enable_serialization
        self.serialization_format = serialization_format
        
        # 使用cachetools的缓存作为底层存储
        self._caches: Dict[str, Union[TTLCache, LRUCache]] = {}
        self._cache_entries: Dict[str, OrderedDict[str, CacheEntry]] = {}  # 用于高级功能
        
        # 统计信息
        self._stats = CacheStats()
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 序列化器（如果需要）
        self._serializer = None
        if enable_serialization:
            from .serialization import Serializer
            self._serializer = Serializer()
        
        # 清理任务
        self._cleanup_task = None
        self._cleanup_interval = 30  # 5分钟清理一次
        self._stop_cleanup = False

    def _deserialize_value(self, value: Any) -> Any:
        """反序列化值（如果配置了序列化器）"""
        if self.enable_serialization and self._serializer is not None:
            return self._serializer.deserialize(value, self.serialization_format)
        return value

    def _serialize_value(self, value: Any) -> Any:
        """序列化值（如果配置了序列化器）"""
        if self.enable_serialization and self._serializer is not None:
            return self._serializer.serialize(value, self.serialization_format)
        return value

    def get_cache(self, name: str, maxsize: int = 1000, ttl: Optional[int] = None) -> Union[TTLCache, LRUCache]:
        """获取缓存实例"""
        with self._lock:
            if name not in self._caches:
                if ttl and ttl > 0:
                    self._caches[name] = TTLCache(maxsize=maxsize, ttl=ttl)
                else:
                    self._caches[name] = LRUCache(maxsize=maxsize)
            return self._caches[name]

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        Args:
            key: 缓存键
        Returns:
            缓存值，如果不存在或过期则返回None
        """
        with self._lock:
            # 检查高级缓存条目（用于统计和过期检查）
            if key in self._cache_entries.get('default', {}):
                entry = self._cache_entries['default'][key]
                if entry.is_expired():
                    del self._cache_entries['default'][key]
                    self._stats.record_miss()
                    return None
                
                # 移动到末尾（LRU）
                cache_dict = self._cache_entries['default']
                cache_dict.move_to_end(key)
                self._stats.record_hit()
                
                value = entry.access()
                return self._deserialize_value(value)
            else:
                # 检查cachetools缓存
                cache = self.get_cache('default')
                value = cache.get(key)
                if value is not None:
                    self._stats.record_hit()
                    return self._deserialize_value(value)
                else:
                    self._stats.record_miss()
                    return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """设置缓存值
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），如果为None则使用默认值
            metadata: 元数据
        """
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None
        
        # 序列化值
        serialized_value = self._serialize_value(value)
        
        with self._lock:
            # 确保cache_entries字典存在
            if 'default' not in self._cache_entries:
                self._cache_entries['default'] = OrderedDict()
            
            cache_dict = self._cache_entries['default']
            
            # 检查是否需要淘汰
            if key not in cache_dict and len(cache_dict) >= self.max_size:
                # LRU淘汰 - 删除最久未使用的项
                oldest_key = next(iter(cache_dict))
                del cache_dict[oldest_key]
                self._stats.record_eviction()
            
            # 创建缓存条目
            entry = CacheEntry(
                key=key,
                value=serialized_value,
                created_at=time.time(),
                expires_at=expires_at
            )
            
            cache_dict[key] = entry
            cache_dict.move_to_end(key)
            
            # 同时设置到cachetools缓存
            cache = self.get_cache('default')
            cache[key] = serialized_value

    async def delete(self, key: str) -> bool:
        """删除缓存项
        Args:
            key: 缓存键
        Returns:
            是否删除成功
        """
        with self._lock:
            success = False
            if 'default' in self._cache_entries and key in self._cache_entries['default']:
                del self._cache_entries['default'][key]
                success = True
            # 同时从cachetools缓存删除
            cache = self.get_cache('default')
            if key in cache:
                del cache[key]
                success = True
            return success

    async def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            if 'default' in self._cache_entries:
                self._cache_entries['default'].clear()
            for cache in self._caches.values():
                cache.clear()

    async def exists(self, key: str) -> bool:
        """检查缓存项是否存在且未过期
        Args:
            key: 缓存键
        Returns:
            是否存在
        """
        with self._lock:
            if key in self._cache_entries.get('default', {}):
                entry = self._cache_entries['default'][key]
                if entry.is_expired():
                    del self._cache_entries['default'][key]
                    return False
                return True
            else:
                cache = self.get_cache('default')
                return key in cache

    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        Returns:
            统计信息字典
        """
        with self._lock:
            return {
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "evictions": self._stats.evictions,
                "total_requests": self._stats.total_requests,
                "hit_rate": self._stats.hit_rate,
                "cache_size": len(self._cache_entries.get('default', {})),
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
                "enable_serialization": self.enable_serialization,
                "serialization_format": self.serialization_format
            }

    async def cleanup_expired(self) -> int:
        """清理过期缓存项
        Returns:
            清理的项数
        """
        with self._lock:
            if 'default' not in self._cache_entries:
                return 0
                
            expired_keys = []
            current_time = time.time()
            
            for key, entry in self._cache_entries['default'].items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache_entries['default'][key]
            
            cleanup_count = len(expired_keys)
            if cleanup_count > 0:
                # 也从cachetools缓存中清理
                cache = self.get_cache('default')
                for key in expired_keys:
                    if key in cache:
                        del cache[key]
            
            return cleanup_count

    async def get_all_keys(self) -> List[str]:
        """获取所有缓存键（不包含过期项）
        Returns:
            缓存键列表
        """
        with self._lock:
            # 先清理过期项
            await self.cleanup_expired()
            return list(self._cache_entries.get('default', {}).keys())

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存值
        Args:
            keys: 缓存键列表
        Returns:
            键值对字典
        """
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(self, items: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """批量设置缓存值
        Args:
            items: 键值对字典
            ttl: TTL（秒）
        """
        for key, value in items.items():
            await self.set(key, value, ttl)

    def clear_cache(self, name: Optional[str] = None) -> None:
        """清除缓存（兼容原有接口）"""
        with self._lock:
            if name:
                if name in self._caches:
                    self._caches[name].clear()
            else:
                for cache in self._caches.values():
                    cache.clear()

    def get_cache_info(self, name: str) -> Dict[str, Any]:
        """获取缓存信息（兼容原有接口）"""
        with self._lock:
            if name not in self._caches:
                return {"error": f"Cache '{name}' not found"}
            
            cache = self._caches[name]
            return {
                "name": name,
                "size": len(cache),
                "maxsize": getattr(cache, 'maxsize', 'unknown'),
                "type": type(cache).__name__
            }

    def get_all_cache_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存信息（兼容原有接口）"""
        with self._lock:
            return {name: self.get_cache_info(name) for name in self._caches.keys()}


# 全局缓存管理器
_global_manager: Optional[CacheManager] = None
_manager_lock = threading.Lock()


def get_global_cache_manager() -> CacheManager:
    """获取全局缓存管理器"""
    global _global_manager
    if _global_manager is None:
        with _manager_lock:
            if _global_manager is None:
                _global_manager = CacheManager()
    return _global_manager


def get_cache(name: str, maxsize: int = 1000, ttl: Optional[int] = None) -> Union[TTLCache, LRUCache]:
    """便捷函数：获取缓存实例"""
    return get_global_cache_manager().get_cache(name, maxsize, ttl)


def clear_cache(name: Optional[str] = None) -> None:
    """便捷函数：清除缓存"""
    get_global_cache_manager().clear_cache(name)


# 专用缓存类
class ConfigCache:
    """配置专用缓存"""
    
    def __init__(self):
        self._cache = get_cache("config", maxsize=500, ttl=7200)  # 2小时
    
    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    def put(self, key: str, value: Any):
        self._cache[key] = value
    
    def remove(self, key: str) -> None:
        """删除指定的缓存键"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        self._cache.clear()


class LLMCache:
    """LLM专用缓存"""
    
    def __init__(self):
        self._cache = get_cache("llm", maxsize=1000, ttl=3600)  # 1小时
    
    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    def put(self, key: str, value: Any):
        self._cache[key] = value
    
    def remove(self, key: str) -> None:
        """删除指定的缓存键"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        self._cache.clear()


class GraphCache:
    """图实例专用缓存"""
    
    def __init__(self):
        self._cache = get_cache("graph", maxsize=100, ttl=1800)  # 30分钟
    
    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    def put(self, key: str, value: Any):
        self._cache[key] = value
    
    def remove(self, key: str) -> None:
        """删除指定的缓存键"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        self._cache.clear()


# 缓存装饰器 - 直接使用cachetools的cached装饰器
def config_cached(maxsize: int = 128, ttl: Optional[int] = None):
    """配置缓存装饰器"""
    cache = get_cache("config_func", maxsize, ttl or 7200)
    return cached(cache)


def llm_cached(maxsize: int = 256, ttl: Optional[int] = None):
    """LLM缓存装饰器"""
    cache = get_cache("llm_func", maxsize, ttl or 3600)
    return cached(cache)


def graph_cached(maxsize: int = 64, ttl: Optional[int] = None):
    """图缓存装饰器"""
    cache = get_cache("graph_func", maxsize, ttl or 1800)
    return cached(cache)


def simple_cached(cache_name: str, maxsize: int = 1000, ttl: Optional[int] = None):
    """简单缓存装饰器"""
    cache = get_cache(cache_name, maxsize, ttl)
    return cached(cache)