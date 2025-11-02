"""图缓存管理器

提供高效的图实例缓存和管理功能。
"""

import time
import threading
import hashlib
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from collections import OrderedDict
from enum import Enum

from langgraph.graph import StateGraph


class CacheEvictionPolicy(Enum):
    """缓存淘汰策略"""
    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最少使用频率
    TTL = "ttl"  # 时间过期


@dataclass
class CacheEntry:
    """缓存条目"""
    graph: Any
    config_hash: str
    created_at: float
    last_accessed: float
    access_count: int = 0
    size_bytes: int = 0
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at > ttl_seconds
    
    def update_access(self) -> None:
        """更新访问信息"""
        self.last_accessed = time.time()
        self.access_count += 1


class GraphCache:
    """图缓存管理器
    
    提供以下功能：
    1. 图实例缓存
    2. 多种淘汰策略
    3. 缓存统计
    4. 并发安全
    """
    
    def __init__(
        self,
        max_size: int = 100,
        ttl_seconds: int = 3600,
        eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LRU,
        enable_compression: bool = True
    ):
        """初始化图缓存管理器
        
        Args:
            max_size: 最大缓存大小
            ttl_seconds: 缓存过期时间（秒）
            eviction_policy: 淘汰策略
            enable_compression: 是否启用压缩
        """
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._eviction_policy = eviction_policy
        self._enable_compression = enable_compression
        
        # 缓存存储
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # 访问频率统计（用于LFU策略）
        self._access_frequency: Dict[str, int] = {}
        
        # 性能统计
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0,
            "memory_saved": 0
        }
    
    def get_graph(self, config_hash: str) -> Optional[Any]:
        """获取缓存的图
        
        Args:
            config_hash: 配置哈希
            
        Returns:
            缓存的图实例，如果不存在则返回None
        """
        with self._lock:
            self._stats["total_requests"] += 1
            
            if config_hash not in self._cache:
                self._stats["misses"] += 1
                return None
            
            entry = self._cache[config_hash]
            
            # 检查是否过期
            if entry.is_expired(self._ttl_seconds):
                del self._cache[config_hash]
                self._access_frequency.pop(config_hash, None)
                self._stats["misses"] += 1
                return None
            
            # 更新访问信息
            entry.update_access()
            self._access_frequency[config_hash] = entry.access_count
            
            # LRU策略：移动到末尾
            if self._eviction_policy == CacheEvictionPolicy.LRU:
                self._cache.move_to_end(config_hash)
            
            self._stats["hits"] += 1
            return entry.graph
    
    def cache_graph(self, config_hash: str, graph: Any) -> None:
        """缓存图实例
        
        Args:
            config_hash: 配置哈希
            graph: 图实例
        """
        with self._lock:
            # 检查是否需要淘汰
            if len(self._cache) >= self._max_size:
                self._evict_entries()
            
            # 估算图大小
            size_bytes = self._estimate_graph_size(graph)
            
            # 创建缓存条目
            entry = CacheEntry(
                graph=graph,
                config_hash=config_hash,
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=1,
                size_bytes=size_bytes
            )
            
            self._cache[config_hash] = entry
            self._access_frequency[config_hash] = 1
            
            # LRU策略：新条目添加到末尾
            if self._eviction_policy == CacheEvictionPolicy.LRU:
                self._cache.move_to_end(config_hash)
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """按模式失效缓存
        
        Args:
            pattern: 匹配模式（支持通配符）
            
        Returns:
            失效的条目数量
        """
        with self._lock:
            keys_to_remove = []
            
            for key in self._cache.keys():
                if self._match_pattern(key, pattern):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._cache[key]
                self._access_frequency.pop(key, None)
            
            return len(keys_to_remove)
    
    def invalidate_by_hash(self, config_hash: str) -> bool:
        """按哈希失效缓存
        
        Args:
            config_hash: 配置哈希
            
        Returns:
            是否成功失效
        """
        with self._lock:
            if config_hash in self._cache:
                del self._cache[config_hash]
                self._access_frequency.pop(config_hash, None)
                return True
            return False
    
    def clear(self) -> None:
        """清除所有缓存"""
        with self._lock:
            self._cache.clear()
            self._access_frequency.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        with self._lock:
            total_requests = self._stats["total_requests"]
            hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            total_memory = sum(entry.size_bytes for entry in self._cache.values())
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hit_rate": f"{hit_rate:.2f}%",
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "total_requests": total_requests,
                "memory_usage_bytes": total_memory,
                "memory_saved_bytes": self._stats["memory_saved"],
                "eviction_policy": self._eviction_policy.value,
                "ttl_seconds": self._ttl_seconds
            }
    
    def get_cache_entries(self) -> List[Dict[str, Any]]:
        """获取缓存条目信息
        
        Returns:
            缓存条目信息列表
        """
        with self._lock:
            entries = []
            for config_hash, entry in self._cache.items():
                entries.append({
                    "config_hash": config_hash,
                    "created_at": entry.created_at,
                    "last_accessed": entry.last_accessed,
                    "access_count": entry.access_count,
                    "size_bytes": entry.size_bytes,
                    "is_expired": entry.is_expired(self._ttl_seconds)
                })
            return entries
    
    def optimize_cache(self) -> Dict[str, Any]:
        """优化缓存
        
        Returns:
            优化结果统计
        """
        with self._lock:
            # 移除过期条目
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired(self._ttl_seconds):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self._access_frequency.pop(key, None)
            
            # 如果仍然超过大小限制，继续淘汰
            if len(self._cache) > self._max_size:
                self._evict_entries()
            
            return {
                "expired_removed": len(expired_keys),
                "final_size": len(self._cache),
                "memory_freed": sum(
                    entry.size_bytes for key, entry in self._cache.items()
                    if key in expired_keys
                )
            }
    
    def _evict_entries(self) -> None:
        """淘汰缓存条目"""
        if not self._cache:
            return
        
        # 计算需要淘汰的数量
        evict_count = len(self._cache) - self._max_size + 1
        if evict_count <= 0:
            return
        
        if self._eviction_policy == CacheEvictionPolicy.LRU:
            self._evict_lru(evict_count)
        elif self._eviction_policy == CacheEvictionPolicy.LFU:
            self._evict_lfu(evict_count)
        elif self._eviction_policy == CacheEvictionPolicy.TTL:
            self._evict_ttl(evict_count)
        
        self._stats["evictions"] += evict_count
    
    def _evict_lru(self, count: int) -> None:
        """LRU淘汰策略"""
        for _ in range(count):
            if self._cache:
                key, _ = self._cache.popitem(last=False)  # 移除最久未使用的
                self._access_frequency.pop(key, None)
    
    def _evict_lfu(self, count: int) -> None:
        """LFU淘汰策略"""
        # 按访问频率排序
        sorted_items = sorted(
            self._access_frequency.items(),
            key=lambda x: x[1]
        )
        
        for i in range(min(count, len(sorted_items))):
            key = sorted_items[i][0]
            if key in self._cache:
                del self._cache[key]
            self._access_frequency.pop(key, None)
    
    def _evict_ttl(self, count: int) -> None:
        """TTL淘汰策略"""
        # 按创建时间排序，淘汰最旧的
        sorted_items = sorted(
            self._cache.items(),
            key=lambda x: x[1].created_at
        )
        
        for i in range(min(count, len(sorted_items))):
            key = sorted_items[i][0]
            del self._cache[key]
            self._access_frequency.pop(key, None)
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """匹配模式
        
        Args:
            key: 缓存键
            pattern: 模式（支持*通配符）
            
        Returns:
            是否匹配
        """
        if "*" in pattern:
            # 简单的通配符匹配
            import fnmatch
            return fnmatch.fnmatch(key, pattern)
        else:
            return pattern in key
    
    def _estimate_graph_size(self, graph: Any) -> int:
        """估算图大小
        
        Args:
            graph: 图实例
            
        Returns:
            估算的大小（字节）
        """
        try:
            # 尝试序列化图来估算大小
            import pickle
            serialized = pickle.dumps(graph)
            return len(serialized)
        except Exception:
            # 如果序列化失败，使用默认估算
            return 2048


def create_graph_cache(
    max_size: int = 100,
    ttl_seconds: int = 3600,
    eviction_policy: str = "lru",
    enable_compression: bool = True
) -> GraphCache:
    """创建图缓存实例
    
    Args:
        max_size: 最大缓存大小
        ttl_seconds: 缓存过期时间
        eviction_policy: 淘汰策略
        enable_compression: 是否启用压缩
        
    Returns:
        图缓存实例
    """
    policy = CacheEvictionPolicy(eviction_policy)
    return GraphCache(
        max_size=max_size,
        ttl_seconds=ttl_seconds,
        eviction_policy=policy,
        enable_compression=enable_compression
    )


def calculate_config_hash(config: Dict[str, Any]) -> str:
    """计算配置哈希
    
    Args:
        config: 配置字典
        
    Returns:
        配置哈希
    """
    import json
    
    # 使用稳定的序列化格式计算哈希
    serialized = json.dumps(config, sort_keys=True, separators=(',', ':'))
    return hashlib.md5(serialized.encode()).hexdigest()