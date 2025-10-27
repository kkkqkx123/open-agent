"""Thread缓存管理器实现"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CacheEntryType(Enum):
    """缓存条目类型"""
    THREAD_STATE = "thread_state"
    THREAD_METADATA = "thread_metadata"
    THREAD_HISTORY = "thread_history"
    THREAD_LIST = "thread_list"
    CHECKPOINT = "checkpoint"


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    entry_type: CacheEntryType
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = None


class CacheMetrics:
    """缓存性能指标"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_requests = 0
        self.start_time = datetime.now()
    
    def hit_rate(self) -> float:
        """命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    def miss_rate(self) -> float:
        """未命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.misses / self.total_requests
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = datetime.now() - self.start_time
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total_requests": self.total_requests,
            "hit_rate": self.hit_rate(),
            "miss_rate": self.miss_rate(),
            "uptime_seconds": uptime.total_seconds()
        }


class ThreadCacheManager:
    """Thread缓存管理器，提供缓存和性能监控功能"""
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 300,  # 5分钟
        cleanup_interval: int = 60  # 1分钟清理一次
    ):
        """初始化缓存管理器
        
        Args:
            max_size: 最大缓存大小
            default_ttl: 默认TTL（秒）
            cleanup_interval: 清理间隔（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        # 缓存存储
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # 用于LRU淘汰
        
        # 指标统计
        self._metrics = CacheMetrics()
        
        # 锁
        self._lock = asyncio.Lock()
        
        # 启动清理任务
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """启动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_entries()
                await self._enforce_max_size()
            except asyncio.CancelledError:
                logger.info("缓存清理任务被取消")
                break
            except Exception as e:
                logger.error(f"缓存清理任务出错: {e}")
    
    async def _cleanup_expired_entries(self):
        """清理过期条目"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if entry.expires_at <= current_time:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            self._metrics.evictions += 1
        
        if expired_keys:
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存条目")
    
    async def _enforce_max_size(self):
        """强制执行最大大小限制（LRU）"""
        while len(self._cache) > self.max_size:
            if not self._access_order:
                break
            
            # 移除最少访问的条目
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                self._metrics.evictions += 1
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或过期则返回None
        """
        async with self._lock:
            self._metrics.total_requests += 1
            
            if key not in self._cache:
                self._metrics.misses += 1
                return None
            
            entry = self._cache[key]
            
            # 检查是否过期
            if entry.expires_at <= datetime.now():
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._metrics.misses += 1
                self._metrics.evictions += 1
                return None
            
            # 更新访问信息
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            
            # 更新LRU顺序
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            self._metrics.hits += 1
            return entry.value
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        entry_type: CacheEntryType,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            entry_type: 条目类型
            ttl: TTL（秒），如果为None则使用默认值
            
        Returns:
            是否设置成功
        """
        async with self._lock:
            ttl = ttl or self.default_ttl
            expires_at = datetime.now() + timedelta(seconds=ttl)
            
            entry = CacheEntry(
                key=key,
                value=value,
                entry_type=entry_type,
                created_at=datetime.now(),
                expires_at=expires_at,
                access_count=0,
                last_accessed=datetime.now()
            )
            
            # 如果键已存在，更新LRU顺序
            if key in self._cache:
                if key in self._access_order:
                    self._access_order.remove(key)
            else:
                # 检查是否需要淘汰
                while len(self._cache) >= self.max_size:
                    if not self._access_order:
                        break
                    oldest_key = self._access_order.pop(0)
                    if oldest_key in self._cache:
                        del self._cache[oldest_key]
                        self._metrics.evictions += 1
            
            self._cache[key] = entry
            self._access_order.append(key)
            
            return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                return True
            return False
    
    async def clear(self) -> None:
        """清空所有缓存"""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """获取缓存指标
        
        Returns:
            缓存指标字典
        """
        async with self._lock:
            stats = self._metrics.get_stats()
            stats.update({
                "current_size": len(self._cache),
                "max_size": self.max_size,
                "cache_keys": list(self._cache.keys())
            })
            return stats
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """获取详细缓存信息
        
        Returns:
            详细缓存信息
        """
        async with self._lock:
            cache_info = {}
            for key, entry in self._cache.items():
                cache_info[key] = {
                    "type": entry.entry_type.value,
                    "size_estimate": len(str(entry.value)) if entry.value else 0,
                    "created_at": entry.created_at.isoformat(),
                    "expires_at": entry.expires_at.isoformat(),
                    "access_count": entry.access_count,
                    "last_accessed": entry.last_accessed.isoformat() if entry.last_accessed else None,
                    "ttl_remaining": (entry.expires_at - datetime.now()).total_seconds()
                }
            return cache_info
    
    async def invalidate_by_type(self, entry_type: CacheEntryType) -> int:
        """按类型清除缓存
        
        Args:
            entry_type: 条目类型
            
        Returns:
            清除的条目数量
        """
        async with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry.entry_type == entry_type
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
            
            self._metrics.evictions += len(keys_to_remove)
            return len(keys_to_remove)
    
    async def get_size_by_type(self) -> Dict[str, int]:
        """按类型统计缓存大小
        
        Returns:
            按类型统计的大小
        """
        async with self._lock:
            size_by_type = {}
            for entry in self._cache.values():
                type_name = entry.entry_type.value
                size_by_type[type_name] = size_by_type.get(type_name, 0) + 1
            return size_by_type
    
    def close(self):
        """关闭缓存管理器"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self._operations: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
    
    def record_operation(
        self, 
        operation: str, 
        duration: float, 
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录操作
        
        Args:
            operation: 操作名称
            duration: 持续时间（秒）
            success: 是否成功
            metadata: 元数据
        """
        operation_record = {
            "operation": operation,
            "duration": duration,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self._operations.append(operation_record)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计
        
        Returns:
            性能统计信息
        """
        if not self._operations:
            return {
                "total_operations": 0,
                "average_duration": 0.0,
                "success_rate": 0.0,
                "operations_by_type": {},
                "duration_percentiles": {}
            }
        
        total_ops = len(self._operations)
        successful_ops = sum(1 for op in self._operations if op["success"])
        total_duration = sum(op["duration"] for op in self._operations)
        
        # 按操作类型统计
        ops_by_type = {}
        for op in self._operations:
            op_type = op["operation"]
            if op_type not in ops_by_type:
                ops_by_type[op_type] = {
                    "count": 0,
                    "total_duration": 0.0,
                    "avg_duration": 0.0,
                    "success_count": 0
                }
            ops_by_type[op_type]["count"] += 1
            ops_by_type[op_type]["total_duration"] += op["duration"]
            if op["success"]:
                ops_by_type[op_type]["success_count"] += 1
        
        # 计算平均值
        for op_type in ops_by_type:
            ops_by_type[op_type]["avg_duration"] = (
                ops_by_type[op_type]["total_duration"] / 
                ops_by_type[op_type]["count"]
            )
            ops_by_type[op_type]["success_rate"] = (
                ops_by_type[op_type]["success_count"] / 
                ops_by_type[op_type]["count"]
            )
        
        # 计算百分位数
        durations = [op["duration"] for op in self._operations]
        durations.sort()
        
        def percentile(data, p):
            if not data:
                return 0.0
            k = (len(data) - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < len(data):
                return data[f] * (1 - c) + data[f + 1] * c
            else:
                return data[f]
        
        duration_percentiles = {
            "p50": percentile(durations, 0.5),
            "p90": percentile(durations, 0.9),
            "p95": percentile(durations, 0.95),
            "p99": percentile(durations, 0.99)
        }
        
        uptime = datetime.now() - self.start_time
        
        return {
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "failed_operations": total_ops - successful_ops,
            "average_duration": total_duration / total_ops if total_ops > 0 else 0.0,
            "success_rate": successful_ops / total_ops if total_ops > 0 else 0.0,
            "uptime_seconds": uptime.total_seconds(),
            "operations_by_type": ops_by_type,
            "duration_percentiles": duration_percentiles
        }
    
    def clear_operations(self) -> None:
        """清空操作记录"""
        self._operations.clear()
    
    def get_slow_operations(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """获取慢操作
        
        Args:
            threshold: 阈值（秒）
            
        Returns:
            慢操作列表
        """
        return [op for op in self._operations if op["duration"] > threshold]