"""存储缓存接口定义

定义存储缓存的接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class IStorageCache(ABC):
    """存储缓存接口
    
    定义了存储缓存的接口。
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """清空缓存"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        pass