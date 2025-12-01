"""LLM缓存接口定义

提供LLM专用缓存的抽象接口，支持客户端和服务器端缓存策略。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict


class ICacheProvider(ABC):
    """缓存提供者接口
    
    定义LLM缓存提供者的基本契约，支持同步和异步操作。
    """
    
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

    @abstractmethod
    async def get_async(self, key: str) -> Optional[Any]:
        """
        异步获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        异步设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认TTL
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            包含缓存统计信息的字典
        """
        pass


class ICacheKeyGenerator(ABC):
    """缓存键生成器接口
    
    定义LLM缓存键生成的契约，支持多种键生成策略。
    """
    
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