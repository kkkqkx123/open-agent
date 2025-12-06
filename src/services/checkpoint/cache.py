"""
检查点缓存服务

提供检查点的内存缓存功能，提高访问性能。
"""

from typing import Any, Dict, Optional, NamedTuple
from datetime import datetime, timedelta
import threading
from collections import OrderedDict

from src.core.checkpoint.models import Checkpoint


class CacheEntry(NamedTuple):
    """缓存条目"""
    checkpoint: Checkpoint
    created_at: datetime
    expires_at: Optional[datetime]


class CheckpointCache:
    """检查点缓存
    
    提供线程安全的LRU缓存功能，支持TTL过期策略。
    """
    
    def __init__(self, max_size: int = 100, default_ttl: Optional[int] = None):
        """初始化检查点缓存
        
        Args:
            max_size: 最大缓存大小
            default_ttl: 默认TTL（秒），None表示永不过期
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
    
    def get(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """获取检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            检查点实例，如果不存在或已过期则返回None
        """
        with self._lock:
            if checkpoint_id not in self._cache:
                return None
            
            cache_entry = self._cache[checkpoint_id]
            
            # 检查是否过期
            if self._is_expired(cache_entry):
                del self._cache[checkpoint_id]
                return None
            
            # 移动到末尾（LRU更新）
            self._cache.move_to_end(checkpoint_id)
            
            return cache_entry.checkpoint
    
    def set(
        self, 
        checkpoint_id: str, 
        checkpoint: Checkpoint, 
        ttl: Optional[int] = None
    ) -> None:
        """设置检查点缓存
        
        Args:
            checkpoint_id: 检查点ID
            checkpoint: 检查点实例
            ttl: TTL（秒），None表示使用默认TTL
        """
        with self._lock:
            # 如果已存在，先删除
            if checkpoint_id in self._cache:
                del self._cache[checkpoint_id]
            
            # 检查缓存大小限制
            while len(self._cache) >= self.max_size:
                # 移除最旧的项
                self._cache.popitem(last=False)
            
            # 计算过期时间
            ttl = ttl if ttl is not None else self.default_ttl
            expires_at = None
            if ttl is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            
            # 添加到缓存
            self._cache[checkpoint_id] = CacheEntry(
                checkpoint=checkpoint,
                created_at=datetime.now(),
                expires_at=expires_at
            )
    
    def delete(self, checkpoint_id: str) -> bool:
        """删除检查点缓存
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否删除成功
        """
        with self._lock:
            if checkpoint_id in self._cache:
                del self._cache[checkpoint_id]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存中的项目数量
        """
        with self._lock:
            return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """清理过期的缓存项
        
        Returns:
            清理的项目数量
        """
        with self._lock:
            expired_keys = []
            
            for key, cache_entry in self._cache.items():
                if self._is_expired(cache_entry):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            now = datetime.now()
            expired_count = 0
            
            for cache_entry in self._cache.values():
                if self._is_expired(cache_entry, now):
                    expired_count += 1
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "expired_count": expired_count,
                "default_ttl": self.default_ttl
            }
    
    def set_max_size(self, max_size: int) -> None:
        """设置最大缓存大小
        
        Args:
            max_size: 最大缓存大小
        """
        with self._lock:
            self.max_size = max_size
            
            # 如果当前缓存超过限制，截断
            while len(self._cache) > max_size:
                self._cache.popitem(last=False)
    
    def _is_expired(self, cache_entry: CacheEntry, now: Optional[datetime] = None) -> bool:
        """检查缓存项是否过期
        
        Args:
            cache_entry: 缓存项
            now: 当前时间，用于测试
            
        Returns:
            是否过期
        """
        if cache_entry.expires_at is None:
            return False
        
        now = now or datetime.now()
        return now >= cache_entry.expires_at
    
    def get_checkpoint_ids(self) -> list[str]:
        """获取所有缓存的检查点ID
        
        Returns:
            检查点ID列表
        """
        with self._lock:
            return list(self._cache.keys())
    
    def contains(self, checkpoint_id: str) -> bool:
        """检查是否包含指定的检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否包含
        """
        with self._lock:
            if checkpoint_id not in self._cache:
                return False
            
            # 检查是否过期
            if self._is_expired(self._cache[checkpoint_id]):
                del self._cache[checkpoint_id]
                return False
            
            return True
    
    def get_created_at(self, checkpoint_id: str) -> Optional[datetime]:
        """获取检查点的缓存创建时间
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            创建时间，如果不存在则返回None
        """
        with self._lock:
            if checkpoint_id not in self._cache:
                return None
            
            return self._cache[checkpoint_id].created_at
    
    def get_expires_at(self, checkpoint_id: str) -> Optional[datetime]:
        """获取检查点的过期时间
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            过期时间，如果不存在或永不过期则返回None
        """
        with self._lock:
            if checkpoint_id not in self._cache:
                return None
            
            return self._cache[checkpoint_id].expires_at