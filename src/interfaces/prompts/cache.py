"""
提示词缓存接口定义

提供提示词缓存的抽象接口
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, Sequence
from datetime import timedelta


class IPromptCache(ABC):
    """提示词缓存接口"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[timedelta] = None
    ) -> None:
        """设置缓存值"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """清空所有缓存"""
        pass
    
    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[timedelta]:
        """获取键的剩余生存时间"""
        pass
    
    @abstractmethod
    async def set_ttl(self, key: str, ttl: timedelta) -> bool:
        """设置键的生存时间"""
        pass
    
    @abstractmethod
    async def get_keys(self, pattern: str = "*") -> List[str]:
        """获取匹配模式的所有键"""
        pass
    
    @abstractmethod
    async def get_size(self) -> int:
        """获取缓存大小"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        pass


class ICacheEntry(ABC):
    """缓存条目接口"""
    
    @property
    @abstractmethod
    def key(self) -> str:
        """缓存键"""
        pass
    
    @property
    @abstractmethod
    def value(self) -> Any:
        """缓存值"""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> float:
        """创建时间戳"""
        pass
    
    @property
    @abstractmethod
    def expires_at(self) -> Optional[float]:
        """过期时间戳"""
        pass
    
    @property
    @abstractmethod
    def access_count(self) -> int:
        """访问次数"""
        pass
    
    @property
    @abstractmethod
    def last_accessed(self) -> float:
        """最后访问时间"""
        pass
    
    @abstractmethod
    def is_expired(self) -> bool:
        """检查是否已过期"""
        pass
    
    @abstractmethod
    def touch(self) -> None:
        """更新访问时间和次数"""
        pass


class ICacheEvictionPolicy(ABC):
    """缓存淘汰策略接口"""
    
    @abstractmethod
    def should_evict(self, entry: ICacheEntry) -> bool:
        """判断是否应该淘汰该条目"""
        pass
    
    @abstractmethod
    def select_victim(self, entries: Sequence[ICacheEntry]) -> Optional[ICacheEntry]:
        """选择要淘汰的条目"""
        pass


class ICacheSerializer(ABC):
    """缓存序列化器接口"""
    
    @abstractmethod
    def serialize(self, value: Any) -> bytes:
        """序列化值"""
        pass
    
    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """反序列化值"""
        pass