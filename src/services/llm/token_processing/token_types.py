"""Token相关的数据类型定义

统一的Token数据结构，避免重复定义。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class TokenUsage:
    """Token使用数据结构"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    source: str = "local"  # "local" 或 "api"
    timestamp: Optional[datetime] = None
    additional_info: Optional[Dict[str, Any]] = None
    
    # 缓存相关token统计（从API响应中提取，用于提高计费准确性）
    cached_tokens: int = 0  # 缓存的token数量
    cached_prompt_tokens: int = 0  # 缓存的提示词token数量
    cached_completion_tokens: int = 0  # 缓存的完成token数量
    
    # 扩展token统计（从API响应中提取，用于特殊功能的精确计费）
    # 注意：这些字段主要用于音频、推理、预测等高级功能
    extended_tokens: Dict[str, int] = field(default_factory=dict)  # 扩展token统计的通用容器
    
    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.additional_info is None:
            self.additional_info = {}

    @property
    def is_from_api(self) -> bool:
        """检查token数据是否来自API"""
        return self.source == "api"

    @property
    def is_from_local(self) -> bool:
        """检查token数据是否来自本地计算"""
        return self.source == "local"

    def add(self, other: 'TokenUsage') -> 'TokenUsage':
        """添加另一个TokenUsage的数据"""
        # 合并扩展token统计
        merged_extended = self.extended_tokens.copy()
        for key, value in other.extended_tokens.items():
            merged_extended[key] = merged_extended.get(key, 0) + value
        
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            source=self.source,  # 保持原有的source
            timestamp=self.timestamp,  # 保持原有的timestamp
            additional_info=self.additional_info.copy() if self.additional_info else {},
            # 缓存token累加
            cached_tokens=self.cached_tokens + other.cached_tokens,
            cached_prompt_tokens=self.cached_prompt_tokens + other.cached_prompt_tokens,
            cached_completion_tokens=self.cached_completion_tokens + other.cached_completion_tokens,
            # 扩展token合并
            extended_tokens=merged_extended,
        )
    
    @property
    def has_cached_tokens(self) -> bool:
        """检查是否有缓存token"""
        return self.cached_tokens > 0
    
    @property
    def cache_hit_rate(self) -> float:
        """计算缓存命中率"""
        if self.prompt_tokens == 0:
            return 0.0
        return self.cached_tokens / self.prompt_tokens
    
    @property
    def effective_prompt_tokens(self) -> int:
        """有效的提示词token数量（排除缓存）"""
        return max(0, self.prompt_tokens - self.cached_tokens)
    
    def has_extended_token(self, token_type: str) -> bool:
        """检查是否有指定类型的扩展token"""
        return self.extended_tokens.get(token_type, 0) > 0
    
    def get_extended_token(self, token_type: str) -> int:
        """获取指定类型的扩展token数量"""
        return self.extended_tokens.get(token_type, 0)
    
    def set_extended_token(self, token_type: str, count: int) -> None:
        """设置指定类型的扩展token数量"""
        self.extended_tokens[token_type] = count
    
    def get_cache_summary(self) -> Dict[str, Any]:
        """获取缓存统计摘要"""
        return {
            "cached_tokens": self.cached_tokens,
            "cached_prompt_tokens": self.cached_prompt_tokens,
            "cached_completion_tokens": self.cached_completion_tokens,
            "cache_hit_rate": self.cache_hit_rate,
            "effective_prompt_tokens": self.effective_prompt_tokens,
            "has_cached_tokens": self.has_cached_tokens,
        }
    
    def get_detailed_summary(self) -> Dict[str, Any]:
        """获取详细的token统计摘要"""
        return {
            "basic": {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
            },
            "cache": self.get_cache_summary(),
            "extended": {
                "tokens": self.extended_tokens,
                "types": list(self.extended_tokens.keys()),
            },
            "metadata": {
                "source": self.source,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            }
        }

    def copy(self) -> 'TokenUsage':
        """创建TokenUsage的副本"""
        return TokenUsage(
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            total_tokens=self.total_tokens,
            source=self.source,
            timestamp=self.timestamp,
            additional_info=self.additional_info.copy() if self.additional_info else None,
            # 缓存token
            cached_tokens=self.cached_tokens,
            cached_prompt_tokens=self.cached_prompt_tokens,
            cached_completion_tokens=self.cached_completion_tokens,
            # 扩展token
            extended_tokens=self.extended_tokens.copy(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "additional_info": self.additional_info,
            # 缓存token信息
            "cached_tokens": self.cached_tokens,
            "cached_prompt_tokens": self.cached_prompt_tokens,
            "cached_completion_tokens": self.cached_completion_tokens,
            # 扩展token信息
            "extended_tokens": self.extended_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenUsage':
        """从字典创建TokenUsage"""
        timestamp = data.get("timestamp")
        if timestamp and isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            source=data.get("source", "local"),
            timestamp=timestamp,
            additional_info=data.get("additional_info"),
            # 缓存token
            cached_tokens=data.get("cached_tokens", 0),
            cached_prompt_tokens=data.get("cached_prompt_tokens", 0),
            cached_completion_tokens=data.get("cached_completion_tokens", 0),
            # 扩展token
            extended_tokens=data.get("extended_tokens", {}),
        )