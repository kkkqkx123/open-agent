"""LLM缓存配置

提供LLM专用的缓存配置类。
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class LLMCacheConfig:
    """LLM缓存配置"""
    # 基础配置
    enabled: bool = True
    ttl_seconds: int = 3600
    max_size: int = 1000
    cache_type: str = "memory"
    provider_config: Dict[str, Any] = field(default_factory=dict)
    
    # 缓存策略
    strategy: str = "client"  # "client", "server", "hybrid"
    auto_server_cache: bool = False
    large_content_threshold: int = 1048576  # 1MB
    
    # 服务器端缓存
    server_cache_enabled: bool = False
    server_cache_ttl: str = "3600s"
    server_cache_display_name: Optional[str] = None
    server_cache_for_large_content: bool = True
    
    def is_enabled(self) -> bool:
        return self.enabled
    
    def get_ttl_seconds(self) -> int:
        return self.ttl_seconds
    
    def get_max_size(self) -> int:
        return self.max_size
    
    def get_provider_config(self) -> Dict[str, Any]:
        return self.provider_config.copy()
    
    def __post_init__(self) -> None:
        """验证配置"""
        valid_strategies = ["client", "server", "hybrid"]
        if self.strategy not in valid_strategies:
            raise ValueError(f"无效的缓存策略: {self.strategy}")
        
        if not self._is_valid_ttl_format(self.server_cache_ttl):
            raise ValueError(f"无效的TTL格式: {self.server_cache_ttl}")
    
    def _is_valid_ttl_format(self, ttl: str) -> bool:
        """验证TTL格式"""
        import re
        pattern = r'^\d+[smhdw]$'
        return bool(re.match(pattern, ttl))
    
    def should_use_server_cache(self, content_size: int) -> bool:
        """判断是否应该使用服务器端缓存"""
        if not self.server_cache_enabled:
            return False
        
        if self.server_cache_for_large_content:
            return content_size >= self.large_content_threshold
        
        return self.auto_server_cache


@dataclass
class GeminiCacheConfig(LLMCacheConfig):
    """Gemini缓存配置"""
    model_name: str = "gemini-2.0-flash-001"
    large_content_threshold: int = 512 * 1024  # 512KB
    
    @classmethod
    def create_default(cls) -> "GeminiCacheConfig":
        """创建默认配置"""
        return cls(
            enabled=True,
            strategy="hybrid",
            server_cache_enabled=True,
            auto_server_cache=True,
            server_cache_ttl="3600s"
        )


@dataclass
class AnthropicCacheConfig(LLMCacheConfig):
    """Anthropic缓存配置"""
    cache_control_type: Optional[str] = None  # ephemeral, persistent
    max_tokens: Optional[int] = None
    
    @classmethod
    def create_default(cls) -> "AnthropicCacheConfig":
        """创建默认配置"""
        return cls(
            enabled=True,
            strategy="client",
            cache_control_type="ephemeral"
        )