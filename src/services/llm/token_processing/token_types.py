"""Token相关的数据类型定义

统一的Token数据结构，避免重复定义。
"""

from dataclasses import dataclass
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
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            source=self.source,  # 保持原有的source
            timestamp=self.timestamp,  # 保持原有的timestamp
            additional_info=self.additional_info.copy() if self.additional_info else {}
        )

    def copy(self) -> 'TokenUsage':
        """创建TokenUsage的副本"""
        return TokenUsage(
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            total_tokens=self.total_tokens,
            source=self.source,
            timestamp=self.timestamp,
            additional_info=self.additional_info.copy() if self.additional_info else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "additional_info": self.additional_info
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
            additional_info=data.get("additional_info")
        )