"""统一的缓存配置体系
提供通用的缓存配置。
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class BaseCacheConfig:
    """基础缓存配置"""
    enabled: bool = True
    ttl_seconds: int = 3600
    max_size: int = 1000
    cache_type: str = "memory"
    provider_config: Dict[str, Any] = field(default_factory=dict)
    
    def is_enabled(self) -> bool:
        return self.enabled
    
    def get_ttl_seconds(self) -> int:
        return self.ttl_seconds
    
    def get_max_size(self) -> int:
        return self.max_size
    
    def get_provider_config(self) -> Dict[str, Any]:
        return self.provider_config.copy()


@dataclass
class CacheEntry:
    """缓存项"""
    
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    last_accessed: Optional[float] = None
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        import time
        return time.time() > self.expires_at
    
    def access(self) -> Any:
        """访问缓存项"""
        import time
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value
    
    def get_age_seconds(self) -> float:
        """获取缓存项年龄（秒）"""
        import time
        return time.time() - self.created_at
    
    def get_idle_seconds(self) -> Optional[float]:
        """获取空闲时间（秒）"""
        if self.last_accessed is None:
            return self.get_age_seconds()
        import time
        return time.time() - self.last_accessed
