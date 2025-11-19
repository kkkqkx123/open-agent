"""
简化的缓存系统 - 基于cachetools库
"""

import time
import threading
from typing import Any, Optional, Dict, Union

from cachetools import TTLCache, LRUCache, cached


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self._caches: Dict[str, Union[TTLCache, LRUCache]] = {}
        self._lock = threading.RLock()
    
    def get_cache(self, name: str, maxsize: int = 1000, ttl: Optional[int] = None) -> Union[TTLCache, LRUCache]:
        """获取缓存实例"""
        with self._lock:
            if name not in self._caches:
                if ttl and ttl > 0:
                    self._caches[name] = TTLCache(maxsize=maxsize, ttl=ttl)
                else:
                    self._caches[name] = LRUCache(maxsize=maxsize)
            return self._caches[name]
    
    def clear_cache(self, name: Optional[str] = None):
        """清除缓存"""
        with self._lock:
            if name:
                if name in self._caches:
                    self._caches[name].clear()
            else:
                for cache in self._caches.values():
                    cache.clear()
    
    def get_cache_info(self, name: str) -> Dict[str, Any]:
        """获取缓存信息"""
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
        """获取所有缓存信息"""
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


def clear_cache(name: Optional[str] = None):
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