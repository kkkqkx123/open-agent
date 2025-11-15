"""缓存条目定义"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def access(self) -> Any:
        """访问缓存项"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.value
    
    def extend_ttl(self, seconds: int) -> None:
        """延长TTL"""
        if self.expires_at:
            self.expires_at = max(self.expires_at, datetime.now() + timedelta(seconds=seconds))
        else:
            self.expires_at = datetime.now() + timedelta(seconds=seconds)


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