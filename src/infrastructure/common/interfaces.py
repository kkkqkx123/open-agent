"""公用组件基础接口定义"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from datetime import datetime


class ISerializable(ABC):
    """可序列化接口"""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ISerializable':
        """从字典创建实例"""
        pass


class ICacheable(ABC):
    """可缓存接口"""
    
    @abstractmethod
    def get_cache_key(self) -> str:
        """获取缓存键"""
        pass
    
    @abstractmethod
    def get_cache_ttl(self) -> int:
        """获取缓存TTL"""
        pass


class ITimestamped(ABC):
    """时间戳接口"""
    
    @abstractmethod
    def get_created_at(self) -> datetime:
        """获取创建时间"""
        pass
    
    @abstractmethod
    def get_updated_at(self) -> datetime:
        """获取更新时间"""
        pass


class IStorage(ABC):
    """统一存储接口"""
    
    @abstractmethod
    async def save(self, data: Dict[str, Any]) -> bool:
        """保存数据"""
        pass
    
    @abstractmethod
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        pass
    
    @abstractmethod
    async def list(self, filters: Dict[str, Any]) -> list[Dict[str, Any]]:
        """列出数据"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除数据"""
        pass