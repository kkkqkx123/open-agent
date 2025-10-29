"""增强的缓存配置，支持Gemini服务器端缓存"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from .cache_config import CacheConfig


@dataclass
class EnhancedCacheConfig(CacheConfig):
    """增强的缓存配置，支持Gemini服务器端缓存"""
    
    # 服务器端缓存配置
    server_cache_enabled: bool = False
    auto_server_cache: bool = False  # 自动创建服务器端缓存
    server_cache_ttl: str = "3600s"  # 服务器端缓存TTL
    server_cache_display_name: Optional[str] = None  # 服务器端缓存显示名称
    large_content_threshold: int = 1048576  # 大内容阈值（1MB）
    
    # 缓存策略配置
    cache_strategy: str = "client_first"  # 缓存策略：client_first, server_first, hybrid
    server_cache_for_large_content: bool = True  # 对大内容使用服务器端缓存
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        super().__post_init__()
        
        # 验证缓存策略
        valid_strategies = ["client_first", "server_first", "hybrid"]
        if self.cache_strategy not in valid_strategies:
            raise ValueError(f"无效的缓存策略: {self.cache_strategy}，必须是: {valid_strategies}")
        
        # 验证TTL格式
        if not self._is_valid_ttl_format(self.server_cache_ttl):
            raise ValueError(f"无效的服务器端缓存TTL格式: {self.server_cache_ttl}")
    
    def _is_valid_ttl_format(self, ttl: str) -> bool:
        """验证TTL格式是否有效"""
        import re
        # 支持的格式：300s, 1h, 1d, 1w
        pattern = r'^\d+[smhdw]$'
        return bool(re.match(pattern, ttl))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        
        # 添加服务器端缓存配置
        result.update({
            "server_cache_enabled": self.server_cache_enabled,
            "auto_server_cache": self.auto_server_cache,
            "server_cache_ttl": self.server_cache_ttl,
            "server_cache_display_name": self.server_cache_display_name,
            "large_content_threshold": self.large_content_threshold,
            "cache_strategy": self.cache_strategy,
            "server_cache_for_large_content": self.server_cache_for_large_content
        })
        
        return result
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "EnhancedCacheConfig":
        """从字典创建配置"""
        # 提取基础配置
        base_config = {
            "enabled": config_dict.get("enabled", True),
            "max_size": config_dict.get("max_size", 1000),
            "ttl": config_dict.get("ttl", 3600),
            "provider": config_dict.get("provider", "memory"),
            "content_cache_enabled": config_dict.get("content_cache_enabled", False),
            "content_cache_ttl": config_dict.get("content_cache_ttl", "3600s"),
            "content_cache_display_name": config_dict.get("content_cache_display_name"),
        }
        
        # 提取增强配置
        enhanced_config = {
            "server_cache_enabled": config_dict.get("server_cache_enabled", False),
            "auto_server_cache": config_dict.get("auto_server_cache", False),
            "server_cache_ttl": config_dict.get("server_cache_ttl", "3600s"),
            "server_cache_display_name": config_dict.get("server_cache_display_name"),
            "large_content_threshold": config_dict.get("large_content_threshold", 1048576),
            "cache_strategy": config_dict.get("cache_strategy", "client_first"),
            "server_cache_for_large_content": config_dict.get("server_cache_for_large_content", True),
        }
        
        # 合并配置
        all_config = {**base_config, **enhanced_config}
        
        return cls(**all_config)
    
    def should_use_server_cache(self, content_size: int) -> bool:
        """
        判断是否应该使用服务器端缓存
        
        Args:
            content_size: 内容大小（字节）
            
        Returns:
            是否应该使用服务器端缓存
        """
        if not self.server_cache_enabled:
            return False
        
        if self.server_cache_for_large_content:
            return content_size >= self.large_content_threshold
        
        return self.auto_server_cache
    
    def get_cache_priority(self) -> str:
        """
        获取缓存优先级
        
        Returns:
            缓存优先级：client, server, hybrid
        """
        if self.cache_strategy == "client_first":
            return "client"
        elif self.cache_strategy == "server_first":
            return "server"
        else:  # hybrid
            return "hybrid"
    
    def merge_with(self, other: "EnhancedCacheConfig") -> "EnhancedCacheConfig":
        """
        与另一个配置合并
        
        Args:
            other: 另一个配置
            
        Returns:
            合并后的配置
        """
        return EnhancedCacheConfig(
            # 基础配置
            enabled=other.enabled if other.enabled != self.enabled else self.enabled,
            max_size=other.max_size if other.max_size != self.max_size else self.max_size,
            ttl=other.ttl if other.ttl != self.ttl else self.ttl,
            provider=other.provider if other.provider != self.provider else self.provider,
            content_cache_enabled=other.content_cache_enabled if other.content_cache_enabled != self.content_cache_enabled else self.content_cache_enabled,
            content_cache_ttl=other.content_cache_ttl if other.content_cache_ttl != self.content_cache_ttl else self.content_cache_ttl,
            content_cache_display_name=other.content_cache_display_name or self.content_cache_display_name,
            
            # 服务器端缓存配置
            server_cache_enabled=other.server_cache_enabled if other.server_cache_enabled != self.server_cache_enabled else self.server_cache_enabled,
            auto_server_cache=other.auto_server_cache if other.auto_server_cache != self.auto_server_cache else self.auto_server_cache,
            server_cache_ttl=other.server_cache_ttl if other.server_cache_ttl != self.server_cache_ttl else self.server_cache_ttl,
            server_cache_display_name=other.server_cache_display_name or self.server_cache_display_name,
            large_content_threshold=other.large_content_threshold if other.large_content_threshold != self.large_content_threshold else self.large_content_threshold,
            cache_strategy=other.cache_strategy if other.cache_strategy != self.cache_strategy else self.cache_strategy,
            server_cache_for_large_content=other.server_cache_for_large_content if other.server_cache_for_large_content != self.server_cache_for_large_content else self.server_cache_for_large_content,
        )


@dataclass
class GeminiCacheConfig(EnhancedCacheConfig):
    """Gemini专用缓存配置"""
    
    # Gemini特定配置
    model_name: str = "gemini-2.0-flash-001"
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        super().__post_init__()
        
        # Gemini特定的默认值调整
        if self.large_content_threshold == 1048576:  # 默认值
            # Gemini对大文件处理更优化，可以降低阈值
            self.large_content_threshold = 512 * 1024  # 512KB
        
        # 默认启用服务器端缓存（如果支持）
        if not self.server_cache_enabled and self.auto_server_cache:
            self.server_cache_enabled = True
    
    @classmethod
    def create_default(cls) -> "GeminiCacheConfig":
        """创建默认的Gemini缓存配置"""
        return cls(
            enabled=True,
            max_size=1000,
            ttl=3600,
            provider="memory",
            server_cache_enabled=True,
            auto_server_cache=True,
            server_cache_ttl="3600s",
            large_content_threshold=512 * 1024,  # 512KB
            cache_strategy="hybrid",
            server_cache_for_large_content=True,
            model_name="gemini-2.0-flash-001"
        )
    
    @classmethod
    def create_client_only(cls) -> "GeminiCacheConfig":
        """创建仅客户端缓存的配置"""
        return cls(
            enabled=True,
            max_size=1000,
            ttl=3600,
            provider="memory",
            server_cache_enabled=False,
            auto_server_cache=False,
            cache_strategy="client_first",
            server_cache_for_large_content=False,
            model_name="gemini-2.0-flash-001"
        )
    
    @classmethod
    def create_server_focused(cls) -> "GeminiCacheConfig":
        """创建以服务器端缓存为主的配置"""
        return cls(
            enabled=True,
            max_size=100,  # 减少客户端缓存大小
            ttl=1800,  # 减少客户端缓存TTL
            provider="memory",
            server_cache_enabled=True,
            auto_server_cache=True,
            server_cache_ttl="7200s",  # 增加服务器端缓存TTL
            large_content_threshold=256 * 1024,  # 降低阈值到256KB
            cache_strategy="server_first",
            server_cache_for_large_content=True,
            model_name="gemini-2.0-flash-001"
        )