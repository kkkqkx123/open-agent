"""缓存接口定义"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from datetime import datetime, timedelta


class ICacheProvider(ABC):
    """缓存提供者接口"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认TTL
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空所有缓存"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    def get_size(self) -> int:
        """
        获取缓存大小
        
        Returns:
            缓存项数量
        """
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """
        清理过期的缓存项
        
        Returns:
            清理的项数量
        """
        pass


class ICacheKeyGenerator(ABC):
    """缓存键生成器接口"""
    
    @abstractmethod
    def generate_key(self, *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键
        """
        pass