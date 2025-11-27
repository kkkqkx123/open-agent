"""
服务缓存接口

定义服务实例缓存的相关接口，支持多种缓存策略和优化机制。
"""

from abc import ABC, abstractmethod
from typing import Type, Optional, Any, Dict, List, Callable
from datetime import datetime, timedelta
from enum import Enum


'''
缓存策略枚举
'''

class CacheEvictionPolicy(Enum):
    """
    缓存淘汰策略枚举
    """
    LRU = "lru"          # 最近最少使用
    LFU = "lfu"          # 最少使用频率
    FIFO = "fifo"        # 先进先出
    TTL = "ttl"          # 基于时间
    MANUAL = "manual"    # 手动淘汰


class CacheStatus(Enum):
    """
    缓存状态枚举
    """
    ACTIVE = "active"      # 活跃
    EXPIRED = "expired"    # 已过期
    EVICTED = "evicted"    # 已淘汰
    DISABLED = "disabled"  # 已禁用


'''
缓存条目接口
'''

class ICacheEntry(ABC):
    """
    缓存条目接口
    
    定义缓存中单个条目的契约，包含值、元数据和生命周期信息。
    """
    
    @property
    @abstractmethod
    def key(self) -> str:
        """
        获取缓存键
        
        Returns:
            str: 缓存键
        """
        pass
    
    @property
    @abstractmethod
    def value(self) -> Any:
        """
        获取缓存值
        
        Returns:
            Any: 缓存值
        """
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """
        获取创建时间
        
        Returns:
            datetime: 创建时间
        """
        pass
    
    @property
    @abstractmethod
    def expires_at(self) -> Optional[datetime]:
        """
        获取过期时间
        
        Returns:
            Optional[datetime]: 过期时间，如果不过期则返回None
        """
        pass
    
    @property
    @abstractmethod
    def access_count(self) -> int:
        """
        获取访问次数
        
        Returns:
            int: 访问次数
        """
        pass
    
    @property
    @abstractmethod
    def last_accessed(self) -> datetime:
        """
        获取最后访问时间
        
        Returns:
            datetime: 最后访问时间
        """
        pass
    
    @property
    @abstractmethod
    def size(self) -> int:
        """
        获取条目大小（字节）
        
        Returns:
            int: 大小
        """
        pass
    
    @abstractmethod
    def is_expired(self) -> bool:
        """
        检查是否已过期
        
        Returns:
            bool: 是否已过期
        """
        pass
    
    @abstractmethod
    def touch(self) -> None:
        """
        更新访问时间和次数
        
        在访问缓存条目时调用，用于统计和淘汰策略。
        """
        pass
    
    @abstractmethod
    def get_metadata(self, key: str) -> Optional[Any]:
        """
        获取元数据
        
        Args:
            key: 元数据键
            
        Returns:
            Optional[Any]: 元数据值
        """
        pass
    
    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> None:
        """
        设置元数据
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        pass


'''
缓存统计接口
'''

class ICacheStatistics(ABC):
    """
    缓存统计接口
    
    定义缓存统计信息的契约。
    """
    
    @property
    @abstractmethod
    def hit_count(self) -> int:
        """缓存命中次数"""
        pass
    
    @property
    @abstractmethod
    def miss_count(self) -> int:
        """缓存未命中次数"""
        pass
    
    @property
    @abstractmethod
    def eviction_count(self) -> int:
        """缓存淘汰次数"""
        pass
    
    @property
    @abstractmethod
    def total_requests(self) -> int:
        """总请求次数"""
        pass
    
    @property
    @abstractmethod
    def hit_rate(self) -> float:
        """缓存命中率"""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """重置统计信息"""
        pass


'''
服务缓存接口
'''

class IServiceCache(ABC):
    """
    服务缓存接口
    
    负责服务实例的缓存管理，支持多种缓存策略和优化机制。
    这是依赖注入容器的性能优化组件。
    
    主要功能：
    - 服务实例缓存
    - 多种淘汰策略
    - TTL支持
    - 缓存统计
    - 内存管理
    
    使用示例：
        ```python
        # 基本缓存操作
        cache.put(IUserService, user_instance)
        user_instance = cache.get(IUserService)
        
        # 带TTL的缓存
        cache.put_with_ttl(IUserService, user_instance, timedelta(hours=1))
        
        # 批量操作
        cache.put_batch({
            IUserService: user_instance,
            ILogger: logger_instance
        })
        ```
    """
    
    @abstractmethod
    def get(self, service_type: Type) -> Optional[Any]:
        """
        从缓存获取服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            Optional[Any]: 服务实例，如果不存在则返回None
            
        Examples:
            ```python
            # 基本获取
            user_service = cache.get(IUserService)
            if user_service:
                return user_service
            
            # 安全获取
            logger = cache.get(ILogger) or create_default_logger()
            ```
        """
        pass
    
    @abstractmethod
    def put(self, service_type: Type, instance: Any) -> None:
        """
        将服务实例放入缓存
        
        Args:
            service_type: 服务类型
            instance: 服务实例
            
        Examples:
            ```python
            # 缓存服务实例
            user_service = UserService()
            cache.put(IUserService, user_service)
            
            # 更新缓存
            new_user_service = UserService()
            cache.put(IUserService, new_user_service)
            ```
        """
        pass
    
    @abstractmethod
    def put_with_ttl(
        self, 
        service_type: Type, 
        instance: Any, 
        ttl: timedelta
    ) -> None:
        """
        带TTL的缓存存储
        
        Args:
            service_type: 服务类型
            instance: 服务实例
            ttl: 生存时间
            
        Examples:
            ```python
            # 缓存1小时
            cache.put_with_ttl(
                ICacheService, 
                cache_instance, 
                timedelta(hours=1)
            )
            
            # 缓存30分钟
            cache.put_with_ttl(
                ISessionService, 
                session_instance, 
                timedelta(minutes=30)
            )
            ```
        """
        pass
    
    @abstractmethod
    def remove(self, service_type: Type) -> bool:
        """
        从缓存移除服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            bool: 是否成功移除
            
        Examples:
            ```python
            # 移除特定服务
            success = cache.remove(IUserService)
            
            # 条件移除
            if cache.remove(IUserService):
                print("UserService removed from cache")
            ```
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """
        清除所有缓存
        
        Examples:
            ```python
            # 清除所有缓存
            cache.clear()
            print("All cache cleared")
            
            # 在容器重置时清除
            container.clear()
            cache.clear()
            ```
        """
        pass
    
    @abstractmethod
    def get_size(self) -> int:
        """
        获取缓存大小
        
        Returns:
            int: 缓存中的服务数量
            
        Examples:
            ```python
            size = cache.get_size()
            print(f"Cache size: {size}")
            
            # 监控缓存大小
            if size > 1000:
                logger.warning("Large cache size detected")
            ```
        """
        pass
    
    @abstractmethod
    def get_memory_usage(self) -> int:
        """
        获取内存使用量
        
        Returns:
            int: 内存使用量（字节）
            
        Examples:
            ```python
            memory_bytes = cache.get_memory_usage()
            memory_mb = memory_bytes / (1024 * 1024)
            print(f"Cache memory usage: {memory_mb:.2f} MB")
            
            # 内存监控
            if memory_mb > 100:
                logger.warning("High memory usage in cache")
            ```
        """
        pass
    
    @abstractmethod
    def contains(self, service_type: Type) -> bool:
        """
        检查服务是否在缓存中
        
        Args:
            service_type: 服务类型
            
        Returns:
            bool: 是否在缓存中
            
        Examples:
            ```python
            if cache.contains(IUserService):
                user_service = cache.get(IUserService)
            else:
                user_service = create_user_service()
                cache.put(IUserService, user_service)
            ```
        """
        pass
    
    @abstractmethod
    def get_or_create(self, service_type: Type, factory: Callable[[], Any]) -> Any:
        """
        获取或创建服务实例
        
        如果缓存中存在则返回，否则使用工厂函数创建并缓存。
        
        Args:
            service_type: 服务类型
            factory: 工厂函数
            
        Returns:
            Any: 服务实例
            
        Examples:
            ```python
            # 获取或创建
            user_service = cache.get_or_create(
                IUserService,
                lambda: UserService()
            )
            
            # 带参数的工厂
            db_service = cache.get_or_create(
                IDatabaseService,
                lambda: DatabaseService(config.connection_string)
            )
            ```
        """
        pass
    
    @abstractmethod
    def put_batch(self, services: Dict[Type, Any]) -> None:
        """
        批量缓存服务实例
        
        Args:
            services: 服务类型到实例的映射
            
        Examples:
            ```python
            # 批量缓存
            services = {
                IUserService: UserService(),
                ILogger: Logger(),
                IConfigService: ConfigService()
            }
            cache.put_batch(services)
            
            # 从注册信息批量缓存
            for registration in registrations:
                instance = create_instance(registration)
                services[registration.interface] = instance
            cache.put_batch(services)
            ```
        """
        pass
    
    @abstractmethod
    def get_batch(self, service_types: List[Type]) -> Dict[Type, Any]:
        """
        批量获取服务实例
        
        Args:
            service_types: 服务类型列表
            
        Returns:
            Dict[Type, Any]: 服务类型到实例的映射
            
        Examples:
            ```python
            # 批量获取
            services = cache.get_batch([
                IUserService, 
                ILogger, 
                IConfigService
            ])
            
            for service_type, instance in services.items():
                if instance:
                    print(f"Found cached {service_type.__name__}")
                else:
                    print(f"No cached {service_type.__name__}")
            ```
        """
        pass
    
    @abstractmethod
    def get_expired_entries(self) -> List[ICacheEntry]:
        """
        获取过期的缓存条目
        
        Returns:
            List[ICacheEntry]: 过期条目列表
            
        Examples:
            ```python
            # 清理过期条目
            expired = cache.get_expired_entries()
            for entry in expired:
                cache.remove(entry.service_type)
            
            print(f"Cleaned up {len(expired)} expired entries")
            ```
        """
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """
        清理过期条目
        
        Returns:
            int: 清理的条目数量
            
        Examples:
            ```python
            # 定期清理
            cleaned = cache.cleanup_expired()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired cache entries")
            ```
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> ICacheStatistics:
        """
        获取缓存统计信息
        
        Returns:
            ICacheStatistics: 统计信息对象
            
        Examples:
            ```python
            stats = cache.get_statistics()
            print(f"Hit rate: {stats.hit_rate:.2%}")
            print(f"Total requests: {stats.total_requests}")
            print(f"Hit count: {stats.hit_count}")
            print(f"Miss count: {stats.miss_count}")
            ```
        """
        pass
    
    @abstractmethod
    def set_eviction_policy(self, policy: CacheEvictionPolicy) -> None:
        """
        设置缓存淘汰策略
        
        Args:
            policy: 淘汰策略
            
        Examples:
            ```python
            # 设置LRU淘汰策略
            cache.set_eviction_policy(CacheEvictionPolicy.LRU)
            
            # 设置TTL淘汰策略
            cache.set_eviction_policy(CacheEvictionPolicy.TTL)
            
            # 设置手动淘汰策略
            cache.set_eviction_policy(CacheEvictionPolicy.MANUAL)
            ```
        """
        pass
    
    @abstractmethod
    def set_max_size(self, max_size: int) -> None:
        """
        设置最大缓存大小
        
        Args:
            max_size: 最大条目数
            
        Examples:
            ```python
            # 限制缓存大小
            cache.set_max_size(1000)
            
            # 动态调整
            current_size = cache.get_size()
            if current_size > 500:
                cache.set_max_size(500)
            ```
        """
        pass
    
    @abstractmethod
    def set_max_memory(self, max_memory: int) -> None:
        """
        设置最大内存使用量
        
        Args:
            max_memory: 最大内存使用量（字节）
            
        Examples:
            ```python
            # 限制内存使用（100MB）
            cache.set_max_memory(100 * 1024 * 1024)
            
            # 根据可用内存调整
            available = get_available_memory()
            cache.set_max_memory(int(available * 0.1))
            ```
        """
        pass
    
    @abstractmethod
    def optimize(self) -> Dict[str, Any]:
        """
        优化缓存
        
        执行缓存优化操作，如清理过期条目、压缩内存等。
        
        Returns:
            Dict[str, Any]: 优化结果
            
        Examples:
            ```python
            # 定期优化
            result = cache.optimize()
            print(f"Optimization result:")
            print(f"  Entries removed: {result['entries_removed']}")
            print(f"  Memory freed: {result['memory_freed']} bytes")
            print(f"  Time taken: {result['time_taken']:.3f}s")
            ```
        """
        pass


'''
缓存工厂接口
'''

class ICacheFactory(ABC):
    """
    缓存工厂接口
    
    定义缓存实例创建的契约。
    """
    
    @abstractmethod
    def create_cache(self, config: Dict[str, Any]) -> IServiceCache:
        """
        创建缓存实例
        
        Args:
            config: 缓存配置
            
        Returns:
            IServiceCache: 缓存实例
        """
        pass
    
    @abstractmethod
    def create_memory_cache(self, max_size: int = 1000) -> IServiceCache:
        """
        创建内存缓存
        
        Args:
            max_size: 最大大小
            
        Returns:
            IServiceCache: 内存缓存实例
        """
        pass
    
    @abstractmethod
    def create_distributed_cache(self, config: Dict[str, Any]) -> IServiceCache:
        """
        创建分布式缓存
        
        Args:
            config: 缓存配置
            
        Returns:
            IServiceCache: 分布式缓存实例
        """
        pass