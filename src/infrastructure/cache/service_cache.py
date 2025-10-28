"""服务缓存实现"""

import threading
import time
import weakref
from typing import Type, Any, Optional, Dict
from dataclasses import dataclass

from ..container_interfaces import IServiceCache
from ..types import T


@dataclass
class ServiceCacheEntry:
    """服务缓存条目"""
    instance: Any
    created_at: float
    access_count: int = 0
    last_accessed: float = 0.0
    size_bytes: int = 0
    
    def update_access(self) -> None:
        """更新访问信息"""
        self.last_accessed = time.time()
        self.access_count += 1


class LRUServiceCache(IServiceCache):
    """LRU服务缓存实现"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """初始化LRU服务缓存
        
        Args:
            max_size: 最大缓存大小
            ttl_seconds: 缓存过期时间（秒）
        """
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._cache: Dict[Type, ServiceCacheEntry] = {}
        self._lock = threading.RLock()
    
    def get(self, service_type: Type) -> Optional[Any]:
        """从缓存获取服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            缓存的服务实例，如果不存在则返回None
        """
        with self._lock:
            if service_type in self._cache:
                entry = self._cache[service_type]
                
                # 检查是否过期
                if time.time() - entry.created_at > self._ttl_seconds:
                    del self._cache[service_type]
                    return None
                
                # 更新访问信息
                entry.update_access()
                return entry.instance
            
            return None
    
    def put(self, service_type: Type, instance: Any) -> None:
        """将服务实例放入缓存
        
        Args:
            service_type: 服务类型
            instance: 服务实例
        """
        with self._lock:
            # 检查缓存大小
            if len(self._cache) >= self._max_size:
                self._evict_lru_service()
            
            # 估算实例大小
            size_bytes = self._estimate_instance_size(instance)
            
            # 创建缓存条目
            entry = ServiceCacheEntry(
                instance=instance,
                created_at=time.time(),
                access_count=1,
                last_accessed=time.time(),
                size_bytes=size_bytes
            )
            
            self._cache[service_type] = entry
    
    def remove(self, service_type: Type) -> None:
        """从缓存移除服务实例
        
        Args:
            service_type: 服务类型
        """
        with self._lock:
            if service_type in self._cache:
                del self._cache[service_type]
    
    def clear(self) -> None:
        """清除所有缓存"""
        with self._lock:
            self._cache.clear()
    
    def get_size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存中的服务数量
        """
        with self._lock:
            return len(self._cache)
    
    def get_memory_usage(self) -> int:
        """获取内存使用量
        
        Returns:
            缓存占用的内存大小（字节）
        """
        with self._lock:
            return sum(entry.size_bytes for entry in self._cache.values())
    
    def optimize(self) -> Dict[str, Any]:
        """优化缓存
        
        Returns:
            优化结果
        """
        with self._lock:
            # 移除过期的缓存条目
            expired_keys = []
            current_time = time.time()
            
            for service_type, entry in self._cache.items():
                if current_time - entry.created_at > self._ttl_seconds:
                    expired_keys.append(service_type)
            
            for key in expired_keys:
                del self._cache[key]
            
            # 如果缓存仍然过大，移除最少使用的条目
            remove_count = 0
            if len(self._cache) > self._max_size:
                # 按访问次数排序
                sorted_items = sorted(
                    self._cache.items(),
                    key=lambda x: x[1].access_count
                )
                
                remove_count = len(self._cache) - self._max_size
                for i in range(remove_count):
                    service_type = sorted_items[i][0]
                    del self._cache[service_type]
            
            return {
                "expired_removed": len(expired_keys),
                "lru_removed": remove_count,
                "final_cache_size": len(self._cache)
            }
    
    def _evict_lru_service(self) -> None:
        """淘汰最少使用的服务"""
        if not self._cache:
            return
        
        # 找到最少使用的服务
        lru_service_type = min(
            self._cache.items(),
            key=lambda x: x[1].access_count
        )[0]
        
        del self._cache[lru_service_type]
    
    def _estimate_instance_size(self, instance: Any) -> int:
        """估算实例大小
        
        Args:
            instance: 实例对象
            
        Returns:
            估算的大小（字节）
        """
        try:
            import pickle
            serialized = pickle.dumps(instance)
            return len(serialized)
        except Exception:
            # 如果序列化失败，使用默认估算
            return 1024