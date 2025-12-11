"""
增强的缓存系统 - 基于cachetools库并整合基础设施层高级功能

使用time.time()作为时间戳基础以保证轻量级、高效和与interfaces接口兼容
"""

import time
import threading
import asyncio
from typing import Any, Optional, Dict, Union, List, TYPE_CHECKING, Callable, Awaitable
from collections import OrderedDict
from dataclasses import dataclass

from cachetools import TTLCache, LRUCache, cached
from src.interfaces.logger import ILogger

if TYPE_CHECKING:
    from .serialization import Serializer

# 延迟获取logger实例，避免循环依赖
def _get_logger() -> ILogger:
    from src.interfaces.dependency_injection import get_logger
    return get_logger(__name__)


logger = _get_logger()

@dataclass
class CacheEntry:
    """缓存条目
    
    使用float时间戳（秒级）存储时间，与IPromptCache接口兼容
    """
    key: str
    value: Any
    created_at: float  # time.time()返回的时间戳
    expires_at: Optional[float] = None  # TTL过期时间戳
    access_count: int = 0
    last_accessed: Optional[float] = None
    
    def __post_init__(self) -> None:
        if self.last_accessed is None:
            self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def access(self) -> Any:
        """访问缓存项"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value
    
    def extend_ttl(self, seconds: int) -> None:
        """延长TTL（秒）"""
        if self.expires_at:
            self.expires_at = max(self.expires_at, time.time() + seconds)
        else:
            self.expires_at = time.time() + seconds


@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    
    @property
    def hit_rate(self) -> float:
        """命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    def record_hit(self) -> None:
        """记录命中"""
        self.hits += 1
        self.total_requests += 1
    
    def record_miss(self) -> None:
        """记录未命中"""
        self.misses += 1
        self.total_requests += 1
    
    def record_eviction(self) -> None:
        """记录淘汰"""
        self.evictions += 1


class CacheManager:
    """增强的缓存管理器，整合了基础设施层的高级功能
    
    修复了双重缓存存储问题，现在使用统一的缓存存储机制
    """
    
    def __init__(self,
                 max_size: int = 1000,
                 default_ttl: int = 3600,
                 enable_serialization: bool = False,
                 serialization_format: str = "json"):
        """初始化缓存管理器
        Args:
            max_size: 最大缓存项数
            default_ttl: 默认TTL（秒）
            enable_serialization: 是否启用序列化
            serialization_format: 序列化格式
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enable_serialization = enable_serialization
        self.serialization_format = serialization_format
        
        # 统一缓存存储：只使用OrderedDict存储CacheEntry，移除双重存储
        self._cache_entries: Dict[str, OrderedDict[str, CacheEntry]] = {}
        
        # 统计信息
        self._stats = CacheStats()
        
        # 细粒度锁：为不同操作使用不同的锁
        self._cache_lock = threading.RLock()  # 缓存操作锁
        self._stats_lock = threading.Lock()   # 统计信息锁
        
        # 预加载序列化器（如果需要）
        self._serializer: Optional['Serializer'] = None
        if enable_serialization:
            try:
                from .serialization import Serializer
                self._serializer = Serializer()
            except ImportError as e:
                logger.warning(f"无法加载序列化器，将禁用序列化功能: {e}")
                self.enable_serialization = False
        
        # 后台清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 300  # 5分钟清理一次
        self._stop_cleanup = threading.Event()
        self._cleanup_loop = None

    def _deserialize_value(self, value: Any) -> Any:
        """反序列化值（如果配置了序列化器）"""
        if self.enable_serialization and self._serializer is not None:
            return self._serializer.deserialize(value, self.serialization_format)
        return value

    def _serialize_value(self, value: Any) -> Any:
        """序列化值（如果配置了序列化器）"""
        if self.enable_serialization and self._serializer is not None:
            return self._serializer.serialize(value, self.serialization_format)
        return value

    def _ensure_cache_dict(self, name: str = 'default') -> OrderedDict[str, CacheEntry]:
        """确保缓存字典存在"""
        with self._cache_lock:
            if name not in self._cache_entries:
                self._cache_entries[name] = OrderedDict()
            return self._cache_entries[name]

    async def get(self, key: str, cache_name: str = 'default') -> Optional[Any]:
        """获取缓存值
        Args:
            key: 缓存键
            cache_name: 缓存名称，默认为'default'
        Returns:
            缓存值，如果不存在或过期则返回None
        """
        with self._cache_lock:
            cache_dict = self._ensure_cache_dict(cache_name)
            
            if key in cache_dict:
                entry = cache_dict[key]
                
                # 检查是否过期
                if entry.is_expired():
                    del cache_dict[key]
                    self._record_miss()
                    return None
                
                # 移动到末尾（LRU）
                cache_dict.move_to_end(key)
                self._record_hit()
                
                # 访问缓存项并返回值
                value = entry.access()
                return self._deserialize_value(value)
            else:
                self._record_miss()
                return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        cache_name: str = 'default',
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """设置缓存值
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），如果为None则使用默认值
            cache_name: 缓存名称，默认为'default'
            metadata: 元数据（暂未使用，为未来扩展保留）
        """
        if not key:
            raise ValueError("缓存键不能为空")
            
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None
        
        # 序列化值
        serialized_value = self._serialize_value(value)
        
        with self._cache_lock:
            cache_dict = self._ensure_cache_dict(cache_name)
            
            # 检查是否需要淘汰
            if key not in cache_dict and len(cache_dict) >= self.max_size:
                # LRU淘汰 - 删除最久未使用的项
                oldest_key = next(iter(cache_dict))
                del cache_dict[oldest_key]
                self._record_eviction()
            
            # 创建缓存条目
            entry = CacheEntry(
                key=key,
                value=serialized_value,
                created_at=time.time(),
                expires_at=expires_at
            )
            
            cache_dict[key] = entry
            cache_dict.move_to_end(key)

    async def delete(self, key: str, cache_name: str = 'default') -> bool:
        """删除缓存项
        Args:
            key: 缓存键
            cache_name: 缓存名称，默认为'default'
        Returns:
            是否删除成功
        """
        with self._cache_lock:
            cache_dict = self._ensure_cache_dict(cache_name)
            if key in cache_dict:
                del cache_dict[key]
                return True
            return False

    async def clear(self, cache_name: Optional[str] = None) -> None:
        """清空缓存
        Args:
            cache_name: 缓存名称，如果为None则清空所有缓存
        """
        with self._cache_lock:
            if cache_name:
                if cache_name in self._cache_entries:
                    self._cache_entries[cache_name].clear()
            else:
                for cache_dict in self._cache_entries.values():
                    cache_dict.clear()

    async def exists(self, key: str, cache_name: str = 'default') -> bool:
        """检查缓存项是否存在且未过期
        Args:
            key: 缓存键
            cache_name: 缓存名称，默认为'default'
        Returns:
            是否存在
        """
        with self._cache_lock:
            cache_dict = self._ensure_cache_dict(cache_name)
            if key in cache_dict:
                entry = cache_dict[key]
                if entry.is_expired():
                    del cache_dict[key]
                    return False
                return True
            return False

    def _record_hit(self) -> None:
        """记录缓存命中（线程安全）"""
        with self._stats_lock:
            self._stats.record_hit()

    def _record_miss(self) -> None:
        """记录缓存未命中（线程安全）"""
        with self._stats_lock:
            self._stats.record_miss()

    def _record_eviction(self) -> None:
        """记录缓存淘汰（线程安全）"""
        with self._stats_lock:
            self._stats.record_eviction()

    async def get_stats(self, cache_name: str = 'default') -> Dict[str, Any]:
        """获取缓存统计信息
        Args:
            cache_name: 缓存名称，默认为'default'
        Returns:
            统计信息字典
        """
        with self._cache_lock:
            cache_size = len(self._cache_entries.get(cache_name, {}))
        
        with self._stats_lock:
            return {
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "evictions": self._stats.evictions,
                "total_requests": self._stats.total_requests,
                "hit_rate": self._stats.hit_rate,
                "cache_size": cache_size,
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
                "enable_serialization": self.enable_serialization,
                "serialization_format": self.serialization_format,
                "cache_name": cache_name
            }

    async def cleanup_expired(self, cache_name: str = 'default') -> int:
        """清理过期缓存项
        Args:
            cache_name: 缓存名称，默认为'default'
        Returns:
            清理的项数
        """
        with self._cache_lock:
            if cache_name not in self._cache_entries:
                return 0
                
            expired_keys = []
            current_time = time.time()
            cache_dict = self._cache_entries[cache_name]
            
            for key, entry in cache_dict.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del cache_dict[key]
            
            return len(expired_keys)

    async def get_all_keys(self, cache_name: str = 'default') -> List[str]:
        """获取所有缓存键（不包含过期项）
        Args:
            cache_name: 缓存名称，默认为'default'
        Returns:
            缓存键列表
        """
        # 先清理过期项
        await self.cleanup_expired(cache_name)
        
        with self._cache_lock:
            return list(self._cache_entries.get(cache_name, {}).keys())

    async def get_many(self, keys: List[str], cache_name: str = 'default') -> Dict[str, Any]:
        """批量获取缓存值
        Args:
            keys: 缓存键列表
            cache_name: 缓存名称，默认为'default'
        Returns:
            键值对字典
        """
        result = {}
        for key in keys:
            value = await self.get(key, cache_name)
            if value is not None:
                result[key] = value
        return result

    async def set_many(self, items: Dict[str, Any], ttl: Optional[int] = None, cache_name: str = 'default') -> None:
        """批量设置缓存值
        Args:
            items: 键值对字典
            ttl: TTL（秒）
            cache_name: 缓存名称，默认为'default'
        """
        for key, value in items.items():
            await self.set(key, value, ttl, cache_name)

    def clear_cache(self, name: Optional[str] = None) -> None:
        """清除缓存（兼容原有接口）"""
        import asyncio
        if name:
            asyncio.create_task(self.clear(name))
        else:
            asyncio.create_task(self.clear())

    def get_cache_info(self, name: str) -> Dict[str, Any]:
        """获取缓存信息（兼容原有接口）"""
        with self._cache_lock:
            if name not in self._cache_entries:
                return {"error": f"Cache '{name}' not found"}
            
            cache_dict = self._cache_entries[name]
            return {
                "name": name,
                "size": len(cache_dict),
                "maxsize": self.max_size,
                "type": "OrderedDict[CacheEntry]"
            }

    def get_all_cache_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存信息（兼容原有接口）"""
        with self._cache_lock:
            return {name: self.get_cache_info(name) for name in self._cache_entries.keys()}

    async def start_cleanup_task(self) -> None:
        """启动后台清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            try:
                self._cleanup_loop = asyncio.get_event_loop()
            except RuntimeError:
                # 如果没有事件循环，创建一个新的
                self._cleanup_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._cleanup_loop)
            
            self._cleanup_task = self._cleanup_loop.create_task(self._cleanup_worker())
            logger.info("后台清理任务已启动")

    async def stop_cleanup_task(self) -> None:
        """停止后台清理任务"""
        self._stop_cleanup.set()
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("后台清理任务已停止")

    async def _cleanup_worker(self) -> None:
        """后台清理工作线程"""
        while not self._stop_cleanup.is_set():
            try:
                # 清理所有缓存的过期项
                for cache_name in list(self._cache_entries.keys()):
                    cleaned_count = await self.cleanup_expired(cache_name)
                    if cleaned_count > 0:
                        logger.debug(f"缓存 '{cache_name}' 清理了 {cleaned_count} 个过期项")
                
                # 等待下次清理
                await asyncio.sleep(self._cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"后台清理任务出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再重试


# 全局缓存管理器
_global_manager: Optional[CacheManager] = None
_manager_lock = threading.Lock()


def get_global_cache_manager() -> CacheManager:
    """获取全局缓存管理器"""
    global _global_manager
    if _global_manager is None:
        with _manager_lock:
            if _global_manager is None:
                _global_manager = CacheManager()
                # 启动后台清理任务
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(_global_manager.start_cleanup_task())
                except RuntimeError:
                    # 如果没有运行的事件循环，跳过后台任务启动
                    pass
    return _global_manager


def clear_cache(name: Optional[str] = None) -> None:
    """便捷函数：清除缓存"""
    get_global_cache_manager().clear_cache(name)


# 专用缓存类 - 适配新的统一缓存机制
class BaseCache:
    """基础缓存类
    
    提供同步接口，内部基于CacheManager的同步操作。
    所有缓存操作都是同步的，因为缓存存储是内存操作，不涉及I/O阻塞。
    """
    
    def __init__(self, cache_name: str, default_ttl: int) -> None:
        """初始化基础缓存类
        
        Args:
            cache_name: 缓存名称
            default_ttl: 默认TTL（秒）
        """
        self._manager = get_global_cache_manager()
        self._cache_name = cache_name
        self._default_ttl = default_ttl
    
    def _run_async(self, coro: Any) -> Any:
        """同步运行异步协程的通用方法
        
        Args:
            coro: 要运行的异步协程
            
        Returns:
            协程的返回值
        """
        try:
            return asyncio.run(coro)
        except RuntimeError:
            # 如果当前已有事件循环，则创建新线程来运行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                return executor.submit(asyncio.run, coro).result()
    
    def get(self, key: str) -> Optional[Any]:
        """同步获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或过期则返回None
        """
        return self._run_async(self._manager.get(key, self._cache_name))
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """同步设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），如果为None则使用默认值
        """
        self._run_async(self._manager.set(key, value, ttl or self._default_ttl, self._cache_name))
    
    def remove(self, key: str) -> bool:
        """同步删除指定的缓存键
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        result = self._run_async(self._manager.delete(key, self._cache_name))
        return bool(result)
    
    def clear(self) -> None:
        """同步清空缓存"""
        self._run_async(self._manager.clear(self._cache_name))


class ConfigCache(BaseCache):
    """配置专用缓存
    
    提供同步接口，内部基于CacheManager的同步操作。
    所有缓存操作都是同步的，因为缓存存储是内存操作，不涉及I/O阻塞。
    """
    
    def __init__(self) -> None:
        super().__init__(cache_name="config", default_ttl=7200)  # 2小时


class LLMCache(BaseCache):
    """LLM专用缓存
    
    提供同步接口，内部基于CacheManager的同步操作。
    """
    
    def __init__(self) -> None:
        super().__init__(cache_name="llm", default_ttl=3600)  # 1小时


class GraphCache(BaseCache):
    """图实例专用缓存
    
    提供同步接口，内部基于CacheManager的同步操作。
    """
    
    def __init__(self) -> None:
        super().__init__(cache_name="graph", default_ttl=1800)  # 30分钟


# 缓存装饰器 - 使用新的缓存机制
def _create_cached_decorator(cache_name: str, default_ttl: Optional[int] = None) -> Callable:
    """创建缓存装饰器的通用函数
    
    Args:
        cache_name: 缓存名称
        default_ttl: 默认TTL（秒）
        
    Returns:
        缓存装饰器函数
    """
    manager = get_global_cache_manager()
    
    def decorator(maxsize: int = 1000, ttl: Optional[int] = None) -> Callable:
        """缓存装饰器
        
        Args:
            maxsize: 最大缓存大小（暂未使用，为兼容性保留）
            ttl: TTL（秒），如果为None则使用默认值
            
        Returns:
            装饰后的函数
        """
        def wrapper_func(func: Callable) -> Callable:
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # 生成缓存键
                import inspect
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                from src.infrastructure.cache.core.key_generator import DefaultCacheKeyGenerator as CacheKeyGenerator
                cache_key = CacheKeyGenerator.generate_params_key(
                    {"func": func.__name__, "args": bound_args.arguments},
                    algorithm="md5"  # 装饰器使用md5以保持兼容性
                )
                
                # 尝试从缓存获取
                cached_result = await manager.get(cache_key, cache_name)
                if cached_result is not None:
                    return cached_result
                
                # 执行函数并缓存结果
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                await manager.set(cache_key, result, ttl or default_ttl, cache_name)
                return result
            
            return wrapper
        return wrapper_func
    return decorator


def config_cached(maxsize: int = 128, ttl: Optional[int] = None) -> Callable[..., Any]:
    """配置缓存装饰器"""
    return _create_cached_decorator("config_func", 7200)(maxsize, ttl)


def llm_cached(maxsize: int = 256, ttl: Optional[int] = None) -> Callable[..., Any]:
    """LLM缓存装饰器"""
    return _create_cached_decorator("llm_func", 3600)(maxsize, ttl)


def graph_cached(maxsize: int = 64, ttl: Optional[int] = None) -> Callable[..., Any]:
    """图缓存装饰器"""
    return _create_cached_decorator("graph_func", 1800)(maxsize, ttl)


def simple_cached(cache_name: str, maxsize: int = 1000, ttl: Optional[int] = None) -> Callable[..., Any]:
    """简单缓存装饰器"""
    return _create_cached_decorator(cache_name, None)(maxsize, ttl)