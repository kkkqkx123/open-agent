"""服务缓存适配器 - 将统一缓存管理器适配为IServiceCache接口"""

import asyncio
import threading
from typing import Type, Any, Optional, Dict
from ..container_interfaces import IServiceCache
from .cache_manager_protocol import CacheManagerProtocol


class ServiceCacheAdapter(IServiceCache):
    """服务缓存适配器 - 将CacheManager适配为IServiceCache接口
    
    该适配器将类型转换为字符串键，并提供同步接口包装异步调用。
    通过依赖注入的方式获取缓存管理器，避免基础设施层直接依赖展示层。
    """
    
    def __init__(self, cache_manager: Optional[CacheManagerProtocol] = None):
        """初始化服务缓存适配器
        
        Args:
            cache_manager: 统一缓存管理器实例，如果为None则创建默认实例
        """
        # 使用依赖注入，避免直接导入展示层的CacheManager
        self._cache_manager = cache_manager
        self._loop = None
        self._lock = threading.Lock()
        
        # 如果没有提供缓存管理器，创建默认实例
        if self._cache_manager is None:
            from .memory_cache_manager import MemoryCacheManager
            self._cache_manager = MemoryCacheManager()
    
    def _get_event_loop(self):
        """获取事件循环"""
        with self._lock:
            if self._loop is None:
                try:
                    self._loop = asyncio.get_event_loop()
                except RuntimeError:
                    # 如果没有事件循环，创建新的
                    self._loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self._loop)
            return self._loop
    
    def _run_async(self, coro):
        """运行异步协程"""
        loop = self._get_event_loop()
        if loop.is_running():
            # 如果事件循环已经在运行，使用run_coroutine_threadsafe
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result()
        else:
            # 否则直接运行
            return loop.run_until_complete(coro)
    
    def _get_cache_key(self, service_type: Type) -> str:
        """将服务类型转换为缓存键"""
        return f"service:{service_type.__module__}.{service_type.__name__}"
    
    def get(self, service_type: Type) -> Optional[Any]:
        """从缓存获取服务实例"""
        key = self._get_cache_key(service_type)
        return self._run_async(self._cache_manager.get(key))
    
    def put(self, service_type: Type, instance: Any) -> None:
        """将服务实例放入缓存"""
        key = self._get_cache_key(service_type)
        # 使用默认TTL，可以后续扩展为可配置
        self._run_async(self._cache_manager.set(key, instance))
    
    def remove(self, service_type: Type) -> None:
        """从缓存移除服务实例"""
        key = self._get_cache_key(service_type)
        self._run_async(self._cache_manager.delete(key))
    
    def clear(self) -> None:
        """清除所有缓存"""
        self._run_async(self._cache_manager.clear())
    
    def optimize(self) -> Dict[str, Any]:
        """优化缓存
        
        由于CacheManager没有optimize方法，
        这里返回模拟的优化结果。
        """
        stats = self.get_stats()
        return {
            "expired_removed": 0,
            "lru_removed": 0,
            "final_cache_size": stats.get("cache_size", 0),
            "hit_rate": stats.get("hit_rate", 0.0)
        }
    
    def get_size(self) -> int:
        """获取缓存大小"""
        stats = self.get_stats()
        return stats.get("cache_size", 0)
    
    def get_memory_usage(self) -> int:
        """获取内存使用量
        
        由于CacheManager没有直接的内存使用统计，
        这里返回估算值。
        """
        stats = self.get_stats()
        cache_size = stats.get("cache_size", 0)
        # 粗略估算：每个缓存项约1KB
        return cache_size * 1024
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            return self._run_async(self._cache_manager.get_stats())
        except Exception as e:
            return {
                "error": str(e),
                "cache_size": 0,
                "hit_rate": 0.0
            }
    
    def close(self) -> None:
        """关闭适配器"""
        # 不需要特别清理，CacheManager会自动处理