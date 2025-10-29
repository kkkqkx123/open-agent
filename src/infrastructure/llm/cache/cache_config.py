"""缓存配置"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class CacheConfig:
    """缓存配置"""
    
    # 基础配置
    enabled: bool = True
    ttl_seconds: int = 3600  # 默认1小时
    max_size: int = 1000  # 最大缓存项数
    
    # 缓存类型配置
    cache_type: str = "memory"  # memory, redis, etc.
    
    # Anthropic特定缓存配置
    cache_control_type: Optional[str] = None  # ephemeral, persistent
    max_tokens: Optional[int] = None  # 缓存的最大token数
    
    # Gemini特定缓存配置
    content_cache_enabled: bool = False
    content_cache_ttl: str = "3600s"  # Gemini使用字符串格式
    content_cache_display_name: Optional[str] = None
    
    # 通用缓存参数
    provider_config: Dict[str, Any] = field(default_factory=dict)
    
    def is_enabled(self) -> bool:
        """检查缓存是否启用"""
        return self.enabled
    
    def get_ttl_seconds(self) -> int:
        """获取TTL（秒）"""
        return self.ttl_seconds
    
    def get_max_size(self) -> int:
        """获取最大缓存大小"""
        return self.max_size
    
    def get_provider_config(self) -> Dict[str, Any]:
        """获取提供者特定配置"""
        return self.provider_config.copy()
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "CacheConfig":
        """从字典创建配置"""
        return cls(
            enabled=config_dict.get("enabled", True),
            ttl_seconds=config_dict.get("ttl_seconds", 3600),
            max_size=config_dict.get("max_size", 1000),
            cache_type=config_dict.get("cache_type", "memory"),
            cache_control_type=config_dict.get("cache_control_type"),
            max_tokens=config_dict.get("max_tokens"),
            content_cache_enabled=config_dict.get("content_cache_enabled", False),
            content_cache_ttl=config_dict.get("content_cache_ttl", "3600s"),
            content_cache_display_name=config_dict.get("content_cache_display_name"),
            provider_config=config_dict.get("provider_config", {}),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "ttl_seconds": self.ttl_seconds,
            "max_size": self.max_size,
            "cache_type": self.cache_type,
            "cache_control_type": self.cache_control_type,
            "max_tokens": self.max_tokens,
            "content_cache_enabled": self.content_cache_enabled,
            "content_cache_ttl": self.content_cache_ttl,
            "content_cache_display_name": self.content_cache_display_name,
            "provider_config": self.provider_config,
        }


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