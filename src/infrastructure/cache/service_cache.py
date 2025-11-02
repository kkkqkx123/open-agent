"""服务缓存实现"""

import threading
import time
import sys
import weakref
from collections import OrderedDict
from typing import Type, Any, Optional, Dict, Callable, Union, Set
from dataclasses import dataclass
from contextlib import contextmanager

from ..container_interfaces import IServiceCache
from ..types import T


class ServiceCacheEntry:
    """服务缓存条目 - 优化版本"""
    __slots__ = ['instance', 'created_at', 'last_accessed', 'size_bytes', 'access_count']
    
    def __init__(self, instance: Any, created_at: float, last_accessed: float, size_bytes: int, access_count: int = 0):
        self.instance = instance
        self.created_at = created_at
        self.last_accessed = last_accessed
        self.size_bytes = size_bytes
        self.access_count = access_count
    
    def update_access(self) -> None:
        """更新访问信息"""
        self.last_accessed = time.time()
        self.access_count += 1
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at > ttl_seconds


class OptimizedServiceCache(IServiceCache):
    """优化的服务缓存实现"""
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
        cleanup_interval: Union[int, float] = 60,
        cleanup_batch_size: int = 100,
        enable_memory_tracking: bool = False,
        memory_estimator: Optional[Callable[[Any], int]] = None,
        enable_stats: bool = True,
        use_weak_references: bool = False
    ):
        """初始化优化的服务缓存
        
        Args:
            max_size: 最大缓存大小
            ttl_seconds: 缓存过期时间（秒）
            cleanup_interval: 清理间隔（秒），0表示禁用后台清理
            cleanup_batch_size: 每次清理的最大条目数
            enable_memory_tracking: 是否启用内存跟踪
            memory_estimator: 自定义内存估算函数
            enable_stats: 是否启用统计信息
            use_weak_references: 是否使用弱引用存储实例（避免内存泄漏）
        """
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._cleanup_interval = max(0, cleanup_interval)
        self._cleanup_batch_size = max(1, cleanup_batch_size)
        self._enable_memory_tracking = enable_memory_tracking
        self._memory_estimator = memory_estimator or self._default_memory_estimator
        self._enable_stats = enable_stats
        self._use_weak_references = use_weak_references
        
        # 使用 OrderedDict 实现 LRU
        self._cache: OrderedDict[Type, ServiceCacheEntry] = OrderedDict()
        
        # 使用单一 RLock 简化线程安全
        self._lock = threading.RLock()
        
        # 后台清理线程
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        
        # 统计信息（使用原子操作）
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'total_accesses': 0
        }
        self._stats_lock = threading.Lock()
        
        # 启动后台清理线程
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self) -> None:
        """启动后台清理线程"""
        if self._cleanup_interval > 0:
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_worker,
                daemon=True
            )
            self._stop_cleanup.clear()
            self._cleanup_thread.start()
    
    def _cleanup_worker(self) -> None:
        """后台清理工作线程"""
        while not self._stop_cleanup.wait(self._cleanup_interval):
            try:
                self._cleanup_expired_entries()
            except Exception as e:
                # 静默处理清理错误，避免影响主线程
                pass
    
    def _cleanup_expired_entries(self) -> int:
        """清理过期条目"""
        with self._lock:
            expired_keys = []
            current_time = time.time()
            
            # 只检查部分条目，避免长时间持有锁
            items_to_check = min(len(self._cache), self._cleanup_batch_size)
            for i, (service_type, entry) in enumerate(list(self._cache.items())):
                if i >= items_to_check:
                    break
                if entry.is_expired(self._ttl_seconds):
                    expired_keys.append(service_type)
            
            for key in expired_keys:
                del self._cache[key]
            
            if self._enable_stats:
                with self._stats_lock:
                    self._stats['expirations'] += len(expired_keys)
            
            return len(expired_keys)
    
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
                if entry.is_expired(self._ttl_seconds):
                    del self._cache[service_type]
                    if self._enable_stats:
                        with self._stats_lock:
                            self._stats['expirations'] += 1
                            self._stats['misses'] += 1
                            self._stats['total_accesses'] += 1
                    return None
                
                # 检查弱引用是否仍然有效
                if self._use_weak_references and not isinstance(entry.instance, weakref.ref):
                    # 如果使用弱引用但存储的不是弱引用对象，可能是配置变更
                    del self._cache[service_type]
                    return None
                elif self._use_weak_references:
                    # 获取弱引用的实际对象
                    actual_instance = entry.instance()
                    if actual_instance is None:
                        # 弱引用已失效，移除条目
                        del self._cache[service_type]
                        if self._enable_stats:
                            with self._stats_lock:
                                self._stats['expirations'] += 1
                                self._stats['misses'] += 1
                                self._stats['total_accesses'] += 1
                        return None
                    # 更新条目为实际对象
                    entry.instance = actual_instance
                
                # 更新访问信息和 LRU 顺序
                entry.update_access()
                # 移动到末尾表示最近使用
                self._cache.move_to_end(service_type)
                
                if self._enable_stats:
                    with self._stats_lock:
                        self._stats['hits'] += 1
                        self._stats['total_accesses'] += 1
                return entry.instance
            
            if self._enable_stats:
                with self._stats_lock:
                    self._stats['misses'] += 1
                    self._stats['total_accesses'] += 1
            return None
    
    def put(self, service_type: Type, instance: Any) -> None:
        """将服务实例放入缓存
        
        Args:
            service_type: 服务类型
            instance: 服务实例
        """
        with self._lock:
            # 检查缓存大小，如果超过限制则淘汰最旧的条目
            if len(self._cache) >= self._max_size:
                self._evict_lru_service()
            
            # 估算实例大小（如果启用）
            size_bytes = 0
            if self._enable_memory_tracking:
                size_bytes = self._memory_estimator(instance)
            
            # 如果使用弱引用，存储弱引用而不是直接引用
            if self._use_weak_references:
                # 使用弱引用包装实例
                instance = weakref.ref(instance)
            
            # 创建缓存条目
            entry = ServiceCacheEntry(
                instance=instance,
                created_at=time.time(),
                last_accessed=time.time(),
                size_bytes=size_bytes,
                access_count=1
            )
            # 在__post_init__中处理默认值
            
            # 放入缓存并移动到末尾
            self._cache[service_type] = entry
            self._cache.move_to_end(service_type)
    
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
            if self._enable_stats:
                with self._stats_lock:
                    # 重置统计信息
                    self._stats = {
                        'hits': 0,
                        'misses': 0,
                        'evictions': 0,
                        'expirations': 0,
                        'total_accesses': 0
                    }
    
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
            # 清理过期条目
            expired_count = self._cleanup_expired_entries()
            
            # 如果缓存仍然过大，淘汰最旧的条目
            eviction_count = 0
            if len(self._cache) > self._max_size:
                eviction_count = len(self._cache) - self._max_size
                for _ in range(eviction_count):
                    self._evict_lru_service()
            
            return {
                "expired_removed": expired_count,
                "lru_removed": eviction_count,
                "final_cache_size": len(self._cache),
                "hit_rate": self.get_hit_rate()
            }
    
    def _evict_lru_service(self) -> None:
        """淘汰最少使用的服务（LRU）"""
        if not self._cache:
            return
        
        # OrderedDict 的第一个元素是最久未使用的
        service_type, _ = self._cache.popitem(last=False)
        if self._enable_stats:
            with self._stats_lock:
                self._stats['evictions'] += 1
    
    def _default_memory_estimator(self, instance: Any) -> int:
        """默认的内存估算方法"""
        try:
            # 添加递归深度限制，避免栈溢出
            return self._deep_getsizeof(instance, set(), max_depth=100)
        except Exception:
            # 如果估算失败，使用默认值
            return 1024
    
    def _deep_getsizeof(self, obj: Any, seen: Set[int], max_depth: int = 100) -> int:
        """递归计算对象的内存大小，添加深度限制"""
        # 检查递归深度
        if len(seen) > max_depth:
            return 0
            
        size = sys.getsizeof(obj)
        obj_id = id(obj)
        if obj_id in seen:
            return 0
        seen.add(obj_id)
        
        if isinstance(obj, dict):
            size += sum(
                self._deep_getsizeof(k, seen, max_depth) + self._deep_getsizeof(v, seen, max_depth)
                for k, v in obj.items()
            )
        elif hasattr(obj, '__dict__'):
            size += self._deep_getsizeof(obj.__dict__, seen, max_depth)
        elif hasattr(obj, '__slots__'):
            size += sum(
                self._deep_getsizeof(getattr(obj, s), seen, max_depth)
                for s in obj.__slots__
                if hasattr(obj, s)
            )
        elif isinstance(obj, (list, tuple, set, frozenset)):
            size += sum(self._deep_getsizeof(i, seen, max_depth) for i in obj)
        
        return size
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        if not self._enable_stats:
            return {"enabled": False}
        
        with self._lock:
            with self._stats_lock:
                hit_rate = self._stats['hits'] / max(1, self._stats['total_accesses'])
                return {
                    "enabled": True,
                    "hits": self._stats['hits'],
                    "misses": self._stats['misses'],
                    "evictions": self._stats['evictions'],
                    "expirations": self._stats['expirations'],
                    "total_accesses": self._stats['total_accesses'],
                    "hit_rate": hit_rate,
                    "cache_size": len(self._cache),
                    "max_size": self._max_size,
                    "memory_usage": sum(entry.size_bytes for entry in self._cache.values())
                }
    
    def get_hit_rate(self) -> float:
        """获取缓存命中率
        
        Returns:
            命中率（0-1之间）
        """
        if not self._enable_stats:
            return 0.0
        
        with self._lock:
            with self._stats_lock:
                return self._stats['hits'] / max(1, self._stats['total_accesses'])
    
    def resize(self, new_max_size: int) -> None:
        """调整缓存大小
        
        Args:
            new_max_size: 新的最大缓存大小
        """
        with self._lock:
            old_max_size = self._max_size
            self._max_size = new_max_size
            
            # 如果新大小小于当前大小，需要淘汰条目
            if new_max_size < old_max_size:
                eviction_count = len(self._cache) - new_max_size
                for _ in range(eviction_count):
                    self._evict_lru_service()
    
    def set_ttl(self, new_ttl_seconds: int) -> None:
        """设置新的 TTL
        
        Args:
            new_ttl_seconds: 新的 TTL（秒）
        """
        with self._lock:
            self._ttl_seconds = new_ttl_seconds
    
    def stop_cleanup_thread(self) -> None:
        """停止后台清理线程"""
        self._stop_cleanup.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=1.0)
    
    def close(self) -> None:
        """关闭缓存，释放资源"""
        self.stop_cleanup_thread()
        # 清理缓存
        with self._lock:
            self._cache.clear()
    
    def __enter__(self):
        """支持上下文管理"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时关闭缓存"""
        self.close()


# 为了向后兼容，保留原有的 LRUServiceCache 类
class LRUServiceCache(IServiceCache):
    """LRU服务缓存实现 - 向后兼容版本
    
    这个类保留用于向后兼容，新代码应该使用 OptimizedServiceCache
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """初始化LRU服务缓存
        
        Args:
            max_size: 最大缓存大小
            ttl_seconds: 缓存过期时间（秒）
        """
        # 使用优化版本作为实现，但禁用后台清理和内存跟踪以保持原有行为
        self._optimized_cache = OptimizedServiceCache(
            max_size=max_size,
            ttl_seconds=ttl_seconds,
            cleanup_interval=0,  # 禁用后台清理
            enable_memory_tracking=False,  # 禁用内存跟踪
            enable_stats=False,  # 禁用统计信息
            use_weak_references=False  # 不使用弱引用
        )
    
    def get(self, service_type: Type) -> Optional[Any]:
        """从缓存获取服务实例"""
        return self._optimized_cache.get(service_type)
    
    def put(self, service_type: Type, instance: Any) -> None:
        """将服务实例放入缓存"""
        self._optimized_cache.put(service_type, instance)
    
    def remove(self, service_type: Type) -> None:
        """从缓存移除服务实例"""
        self._optimized_cache.remove(service_type)
    
    def clear(self) -> None:
        """清除所有缓存"""
        self._optimized_cache.clear()
    
    def get_size(self) -> int:
        """获取缓存大小"""
        return self._optimized_cache.get_size()
    
    def get_memory_usage(self) -> int:
        """获取内存使用量"""
        return self._optimized_cache.get_memory_usage()
    
    def optimize(self) -> Dict[str, Any]:
        """优化缓存"""
        return self._optimized_cache.optimize()