"""统一缓存管理器

提供统一的缓存接口，整合序列化、缓存条目管理和统计功能
"""

import threading
import asyncio
from typing import Any, Optional, Dict, List, Union
from collections import OrderedDict
from datetime import datetime, timedelta
import logging

from .cache_entry import CacheEntry, CacheStats
from ..serialization.serializer import Serializer

logger = logging.getLogger(__name__)


class CacheManager:
    """统一缓存管理器
    
    提供统一的缓存接口，支持：
    - 内存缓存存储
    - TTL过期机制
    - LRU淘汰策略
    - 统计信息收集
    - 序列化支持
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,
        enable_serialization: bool = True,
        serialization_format: str = "json"
    ):
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
        
        # 缓存存储 - 使用OrderedDict支持LRU
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # 统计信息
        self._stats = CacheStats()
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 序列化器
        self._serializer = Serializer() if enable_serialization else None
        
        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 300  # 5分钟清理一次
        self._stop_cleanup = False
        
        logger.info(f"统一缓存管理器初始化完成 (max_size={max_size}, ttl={default_ttl})")
    
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
            
            value = entry.access()
            
            # 反序列化值
            return self._deserialize_value(value)
    
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
        expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
        
        # 序列化值
        serialized_value = self._serialize_value(value)
        
        with self._lock:
            # 检查是否需要淘汰
            if key not in self._cache and len(self._cache) >= self.max_size:
                # LRU淘汰 - 删除最久未使用的项
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats.record_eviction()
                logger.debug(f"LRU淘汰缓存项: {oldest_key}")
            
            # 创建缓存条目
            entry = CacheEntry(
                key=key,
                value=serialized_value,
                created_at=datetime.now(),
                expires_at=expires_at
            )
            
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            logger.debug(f"缓存项设置成功: key={key}, ttl={ttl}")
    
    async def delete(self, key: str) -> bool:
        """删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"缓存项删除成功: {key}")
                return True
            return False
    
    async def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            logger.info("缓存已清空")
    
    async def exists(self, key: str) -> bool:
        """检查缓存项是否存在且未过期
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            
            if entry.is_expired():
                del self._cache[key]
                return False
            
            return True
    
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
                "cache_size": len(self._cache),
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
            expired_keys = []
            current_time = datetime.now()
            
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            cleanup_count = len(expired_keys)
            if cleanup_count > 0:
                logger.debug(f"清理过期缓存项: {cleanup_count}个")
            
            return cleanup_count
    
    async def get_all_keys(self) -> List[str]:
        """获取所有缓存键（不包含过期项）
        
        Returns:
            缓存键列表
        """
        with self._lock:
            # 先清理过期项
            await self.cleanup_expired()
            return list(self._cache.keys())
    
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
    
    def start_cleanup_task(self) -> None:
        """启动后台清理任务"""
        if self._cleanup_task is None:
            self._stop_cleanup = False
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("后台清理任务已启动")
    
    def stop_cleanup_task(self) -> None:
        """停止后台清理任务"""
        if self._cleanup_task:
            self._stop_cleanup = True
            self._cleanup_task.cancel()
            self._cleanup_task = None
            logger.info("后台清理任务已停止")
    
    async def _cleanup_loop(self) -> None:
        """后台清理循环"""
        try:
            while not self._stop_cleanup:
                await asyncio.sleep(self._cleanup_interval)
                cleanup_count = await self.cleanup_expired()
                if cleanup_count > 0:
                    logger.debug(f"后台清理完成: {cleanup_count}个过期项")
        except asyncio.CancelledError:
            logger.debug("后台清理任务被取消")
        except Exception as e:
            logger.error(f"后台清理任务异常: {e}")
    
    def __del__(self) -> None:
        """析构函数"""
        if self._cleanup_task:
            self.stop_cleanup_task()


# 同步包装器，用于兼容同步代码
class SyncCacheManager:
    """同步缓存管理器包装器"""
    
    def __init__(self, cache_manager: CacheManager):
        """初始化同步包装器
        
        Args:
            cache_manager: 异步缓存管理器实例
        """
        self._cache_manager = cache_manager
        self._loop = None
    
    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """获取事件循环"""
        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                # 如果没有事件循环，创建新的
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop
    
    def get(self, key: str) -> Optional[Any]:
        """同步获取缓存值"""
        return self._get_loop().run_until_complete(self._cache_manager.get(key))
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """同步设置缓存值"""
        self._get_loop().run_until_complete(self._cache_manager.set(key, value, ttl))
    
    def delete(self, key: str) -> bool:
        """同步删除缓存项"""
        return self._get_loop().run_until_complete(self._cache_manager.delete(key))
    
    def clear(self) -> None:
        """同步清空缓存"""
        self._get_loop().run_until_complete(self._cache_manager.clear())
    
    def exists(self, key: str) -> bool:
        """同步检查缓存项是否存在"""
        return self._get_loop().run_until_complete(self._cache_manager.exists(key))
    
    def get_stats(self) -> Dict[str, Any]:
        """同步获取缓存统计信息"""
        return self._get_loop().run_until_complete(self._cache_manager.get_stats())