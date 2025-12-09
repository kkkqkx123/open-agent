"""通用缓存接口定义

提供通用的缓存抽象接口，支持同步和异步操作，适用于各种缓存场景。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List


class ICacheManager(ABC):
    """通用缓存管理器接口
    
    定义缓存管理器的基本契约，支持多种缓存操作和统计功能。
    """
    
    @abstractmethod
    async def get(self, key: str, cache_name: str = 'default') -> Optional[Any]:
        """异步获取缓存值
        
        Args:
            key: 缓存键
            cache_name: 缓存名称
            
        Returns:
            缓存值，如果不存在或过期则返回None
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                 cache_name: str = 'default', metadata: Optional[Dict[str, Any]] = None) -> None:
        """异步设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），如果为None则使用默认值
            cache_name: 缓存名称
            metadata: 元数据
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str, cache_name: str = 'default') -> bool:
        """异步删除缓存项
        
        Args:
            key: 缓存键
            cache_name: 缓存名称
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def clear(self, cache_name: Optional[str] = None) -> None:
        """异步清空缓存
        
        Args:
            cache_name: 缓存名称，如果为None则清空所有缓存
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str, cache_name: str = 'default') -> bool:
        """异步检查缓存项是否存在
        
        Args:
            key: 缓存键
            cache_name: 缓存名称
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def get_stats(self, cache_name: str = 'default') -> Dict[str, Any]:
        """异步获取缓存统计信息
        
        Args:
            cache_name: 缓存名称
            
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    async def cleanup_expired(self, cache_name: str = 'default') -> int:
        """异步清理过期缓存项
        
        Args:
            cache_name: 缓存名称
            
        Returns:
            清理的项数
        """
        pass
    
    @abstractmethod
    async def get_all_keys(self, cache_name: str = 'default') -> List[str]:
        """异步获取所有缓存键
        
        Args:
            cache_name: 缓存名称
            
        Returns:
            缓存键列表
        """
        pass
    
    @abstractmethod
    async def get_many(self, keys: List[str], cache_name: str = 'default') -> Dict[str, Any]:
        """异步批量获取缓存值
        
        Args:
            keys: 缓存键列表
            cache_name: 缓存名称
            
        Returns:
            键值对字典
        """
        pass
    
    @abstractmethod
    async def set_many(self, items: Dict[str, Any], ttl: Optional[int] = None, 
                      cache_name: str = 'default') -> None:
        """异步批量设置缓存值
        
        Args:
            items: 键值对字典
            ttl: TTL（秒）
            cache_name: 缓存名称
        """
        pass


class ICacheAdapter(ABC):
    """通用缓存适配器接口
    
    提供同步缓存操作接口，适配异步缓存管理器。
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """同步获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或过期则返回None
        """
        pass
    
    @abstractmethod
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """同步设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），如果为None则使用默认值
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """同步删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """同步清空缓存"""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """同步获取缓存大小
        
        Returns:
            缓存项数量
        """
        pass
    
    @abstractmethod
    def get_all_keys(self) -> List[str]:
        """同步获取所有缓存键
        
        Returns:
            缓存键列表
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """同步获取统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """同步清理过期缓存项
        
        Returns:
            清理的项数
        """
        pass
    
    @abstractmethod
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """同步批量获取缓存值
        
        Args:
            keys: 缓存键列表
            
        Returns:
            键值对字典
        """
        pass
    
    @abstractmethod
    def set_many(self, items: Dict[str, Any]) -> None:
        """同步批量设置缓存值
        
        Args:
            items: 键值对字典
        """
        pass


class ICacheProvider(ABC):
    """缓存提供者接口
    
    定义缓存存储提供者的基本契约，支持同步和异步操作。
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """同步获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """同步设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认TTL
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """同步删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """同步清空所有缓存"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """同步检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    def get_size(self) -> int:
        """同步获取缓存大小
        
        Returns:
            缓存项数量
        """
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """同步清理过期的缓存项
        
        Returns:
            清理的项数量
        """
        pass
    
    @abstractmethod
    async def get_async(self, key: str) -> Optional[Any]:
        """异步获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """异步设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认TTL
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """同步获取缓存统计信息
        
        Returns:
            包含缓存统计信息的字典
        """
        pass


class ICacheKeyGenerator(ABC):
    """缓存键生成器接口
    
    定义缓存键生成的契约，支持多种键生成策略。
    """
    
    @abstractmethod
    def generate_key(self, *args, **kwargs) -> str:
        """生成缓存键
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键
        """
        pass


class ICacheEntry(ABC):
    """缓存条目接口
    
    定义缓存条目的基本属性和操作。
    """
    
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


class ICacheStatistics(ABC):
    """缓存统计接口
    
    定义缓存统计信息的契约。
    """
    
    @property
    @abstractmethod
    def hits(self) -> int:
        """命中次数"""
        pass
    
    @property
    @abstractmethod
    def misses(self) -> int:
        """未命中次数"""
        pass
    
    @property
    @abstractmethod
    def evictions(self) -> int:
        """淘汰次数"""
        pass
    
    @property
    @abstractmethod
    def total_requests(self) -> int:
        """总请求次数"""
        pass
    
    @property
    @abstractmethod
    def hit_rate(self) -> float:
        """命中率"""
        pass
    
    @abstractmethod
    def record_hit(self) -> None:
        """记录命中"""
        pass
    
    @abstractmethod
    def record_miss(self) -> None:
        """记录未命中"""
        pass
    
    @abstractmethod
    def record_eviction(self) -> None:
        """记录淘汰"""
        pass


class ICacheFactory(ABC):
    """缓存工厂接口
    
    定义缓存实例创建的契约。
    """
    
    @abstractmethod
    def create_cache(self, config: Dict[str, Any]) -> ICacheAdapter:
        """创建缓存实例
        
        Args:
            config: 缓存配置
            
        Returns:
            缓存适配器实例
        """
        pass
    
    @abstractmethod
    def create_memory_cache(self, max_size: int = 1000) -> ICacheAdapter:
        """创建内存缓存
        
        Args:
            max_size: 最大大小
            
        Returns:
            内存缓存实例
        """
        pass
    
    @abstractmethod
    def create_distributed_cache(self, config: Dict[str, Any]) -> ICacheAdapter:
        """创建分布式缓存
        
        Args:
            config: 缓存配置
            
        Returns:
            分布式缓存实例
        """
        pass


__all__ = [
    "ICacheManager",
    "ICacheAdapter", 
    "ICacheProvider",
    "ICacheKeyGenerator",
    "ICacheEntry",
    "ICacheStatistics",
    "ICacheFactory"
]