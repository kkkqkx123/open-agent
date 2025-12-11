"""状态缓存适配器

复用现有的通用缓存系统来为状态管理提供缓存功能。
"""

from src.interfaces.dependency_injection import get_logger
import asyncio
from typing import Any, Dict, List, Optional

from src.infrastructure.common.cache import get_global_cache_manager
from src.interfaces.state.base import IState
from src.interfaces.state.cache import IStateCache

logger = get_logger(__name__)


class StateCacheAdapter(IStateCache):
    """状态缓存适配器
    
    使用现有的通用缓存管理器来实现状态缓存功能。
    提供同步接口，内部处理异步操作。
    """
    
    def __init__(self,
                 cache_name: str = "state",
                 max_size: int = 1000,
                 ttl: int = 300,
                 enable_serialization: bool = False):
        """初始化状态缓存适配器
        
        Args:
            cache_name: 缓存名称
            max_size: 最大缓存大小
            ttl: 默认TTL（秒）
            enable_serialization: 是否启用序列化
        """
        self.cache_name = cache_name
        self.max_size = max_size
        self.ttl = ttl
        self.enable_serialization = enable_serialization
        
        # 获取全局缓存管理器或创建新的
        self._cache_manager = get_global_cache_manager()
        
        # 配置缓存参数
        self._cache_config = {
            'max_size': max_size,
            'default_ttl': ttl,
            'enable_serialization': enable_serialization
        }
        
        logger.debug(f"初始化状态缓存适配器: {cache_name}, max_size={max_size}, ttl={ttl}")
    
    def _run_async(self, coro: Any) -> Any:
        """运行异步协程的辅助方法"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建新的线程来运行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
            else:
                # 如果没有事件循环，直接运行
                return asyncio.run(coro)
        except RuntimeError:
            # 如果无法获取事件循环，创建新的
            return asyncio.run(coro)
    
    def get(self, key: str) -> Optional[IState]:
        """获取缓存状态
        
        Args:
            key: 状态ID
            
        Returns:
            状态实例，如果未找到或已过期则返回None
        """
        try:
            result = self._run_async(self._cache_manager.get(key))
            return result  # type: ignore
        except Exception as e:
            logger.warning(f"获取缓存状态失败: {key}, 错误: {e}")
            return None
    
    def put(self, key: str, state: IState, ttl: Optional[int] = None) -> None:
        """设置缓存状态
        
        Args:
            key: 状态ID
            state: 状态实例
            ttl: TTL（秒），如果为None则使用默认值
        """
        try:
            self._run_async(self._cache_manager.set(key, state, ttl=ttl or self.ttl))
        except Exception as e:
            logger.warning(f"设置缓存状态失败: {key}, 错误: {e}")
    
    def delete(self, key: str) -> bool:
        """删除缓存状态
        
        Args:
            key: 状态ID
            
        Returns:
            是否删除成功
        """
        try:
            result = self._run_async(self._cache_manager.delete(key))
            return result  # type: ignore
        except Exception as e:
            logger.warning(f"删除缓存状态失败: {key}, 错误: {e}")
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        try:
            self._run_async(self._cache_manager.clear())
            logger.debug("清空状态缓存")
        except Exception as e:
            logger.warning(f"清空缓存失败: {e}")
    
    def size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存中的状态数量
        """
        try:
            # 同步获取缓存大小
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，使用同步方式
                stats = self._cache_manager._stats
                return len(self._cache_manager._cache_entries.get('default', {}))
            else:
                # 如果没有事件循环，创建新的
                return asyncio.run(self._get_size_async())
        except Exception as e:
            logger.warning(f"获取缓存大小失败: {e}")
            return 0
    
    async def _get_size_async(self) -> int:
        """异步获取缓存大小"""
        keys = await self._cache_manager.get_all_keys()
        return len(keys)
    
    async def _get_all_keys_async(self) -> List[str]:
        """异步获取所有键"""
        return await self._cache_manager.get_all_keys()
    
    def get_all_keys(self) -> List[str]:
        """获取所有键
        
        Returns:
            所有状态ID列表
        """
        try:
            result = self._run_async(self._get_all_keys_async())
            return result  # type: ignore
        except Exception as e:
            logger.warning(f"获取所有键失败: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 同步获取统计信息
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，使用同步方式
                stats = self._cache_manager._stats
                cache_size = len(self._cache_manager._cache_entries.get('default', {}))
                
                return {
                    "hits": stats.hits,
                    "misses": stats.misses,
                    "evictions": stats.evictions,
                    "total_requests": stats.total_requests,
                    "hit_rate": stats.hit_rate,
                    "size": cache_size,
                    "max_size": self.max_size,
                    "ttl": self.ttl,
                    "cache_name": self.cache_name,
                    "enable_serialization": self.enable_serialization
                }
            else:
                # 如果没有事件循环，创建新的
                return asyncio.run(self._get_statistics_async())
        except Exception as e:
            logger.warning(f"获取统计信息失败: {e}")
            return {}
    
    async def _get_statistics_async(self) -> Dict[str, Any]:
        """异步获取统计信息"""
        stats = await self._cache_manager.get_stats()
        return {
            **stats,
            "cache_name": self.cache_name,
            "enable_serialization": self.enable_serialization
        }
    
    def cleanup_expired(self) -> int:
        """清理过期缓存项
        
        Returns:
            清理的项数
        """
        try:
            result = self._run_async(self._cache_manager.cleanup_expired())
            return result  # type: ignore
        except Exception as e:
            logger.warning(f"清理过期缓存项失败: {e}")
            return 0
    
    def get_many(self, keys: List[str]) -> Dict[str, IState]:
        """批量获取缓存状态
        
        Args:
            keys: 状态ID列表
            
        Returns:
            状态字典
        """
        try:
            values = self._run_async(self._cache_manager.get_many(keys))
            return values  # type: ignore
        except Exception as e:
            logger.warning(f"批量获取缓存状态失败: {e}")
            return {}
    
    def set_many(self, states: Dict[str, IState], ttl: Optional[int] = None) -> None:
        """批量设置缓存状态
        
        Args:
            states: 状态字典
            ttl: TTL（秒）
        """
        try:
            self._run_async(self._cache_manager.set_many(states, ttl=ttl or self.ttl))
        except Exception as e:
            logger.warning(f"批量设置缓存状态失败: {e}")


class NoOpCacheAdapter(IStateCache):
    """无操作缓存适配器
    
    不执行任何缓存操作，用于禁用缓存功能。
    """
    
    def get(self, key: str) -> Optional[IState]:
        """获取缓存状态（总是返回None）"""
        return None
    
    def put(self, key: str, state: IState, ttl: Optional[int] = None) -> None:
        """设置缓存状态（无操作）"""
        pass
    
    def delete(self, key: str) -> bool:
        """删除缓存状态（总是返回False）"""
        return False
    
    def clear(self) -> None:
        """清空缓存（无操作）"""
        pass
    
    def size(self) -> int:
        """获取缓存大小（总是返回0）"""
        return 0
    
    def get_all_keys(self) -> List[str]:
        """获取所有键（总是返回空列表）"""
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息（返回空统计）"""
        return {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0,
            "hit_rate": 0.0,
            "size": 0,
            "max_size": 0,
            "ttl": 0,
            "cache_name": "noop",
            "enable_serialization": False
        }
    
    def get_many(self, keys: List[str]) -> Dict[str, IState]:
        """批量获取（总是返回空字典）"""
        return {}
    
    def set_many(self, states: Dict[str, IState], ttl: Optional[int] = None) -> None:
        """批量设置（无操作）"""
        pass
    
    def cleanup_expired(self) -> int:
        """清理过期项（总是返回0）"""
        return 0


class TieredStateCacheAdapter(IStateCache):
    """分层状态缓存适配器
    
    实现多级缓存，先检查内存缓存，再检查其他缓存层。
    """
    
    def __init__(self, primary_cache: IStateCache, secondary_cache: IStateCache):
        """初始化分层缓存适配器
        
        Args:
            primary_cache: 主缓存（通常是内存缓存）
            secondary_cache: 次级缓存
        """
        self.primary_cache = primary_cache
        self.secondary_cache = secondary_cache
    
    def get(self, key: str) -> Optional[IState]:
        """获取缓存状态"""
        # 先从主缓存获取
        state = self.primary_cache.get(key)
        if state:
            return state
        
        # 从次级缓存获取
        state = self.secondary_cache.get(key)
        if state:
            # 将状态提升到主缓存
            self.primary_cache.put(key, state)
        
        return state
    
    def put(self, key: str, state: IState, ttl: Optional[int] = None) -> None:
        """设置缓存状态"""
        # 同时写入两级缓存
        self.primary_cache.put(key, state, ttl)
        self.secondary_cache.put(key, state, ttl)
    
    def delete(self, key: str) -> bool:
        """删除缓存状态"""
        primary_deleted = self.primary_cache.delete(key)
        secondary_deleted = self.secondary_cache.delete(key)
        return primary_deleted or secondary_deleted
    
    def clear(self) -> None:
        """清空缓存"""
        self.primary_cache.clear()
        self.secondary_cache.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return self.primary_cache.size()
    
    def get_all_keys(self) -> List[str]:
        """获取所有键"""
        return self.primary_cache.get_all_keys()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "primary_cache": self.primary_cache.get_statistics() if hasattr(self.primary_cache, 'get_statistics') else {},
            "secondary_cache": self.secondary_cache.get_statistics() if hasattr(self.secondary_cache, 'get_statistics') else {}
        }
    
    def get_many(self, keys: List[str]) -> Dict[str, IState]:
        """批量获取缓存状态"""
        result: Dict[str, IState] = {}
        missing_keys = []
        
        # 从主缓存获取
        primary_result = self.primary_cache.get_many(keys)
        result.update(primary_result)
        
        # 记录缺失的键
        missing_keys = [k for k in keys if k not in primary_result]
        
        if missing_keys:
            # 从次级缓存获取缺失的
            secondary_result = self.secondary_cache.get_many(missing_keys)
            # 将次级缓存的结果提升到主缓存
            for k, v in secondary_result.items():
                self.primary_cache.put(k, v)
            result.update(secondary_result)
        
        return result
    
    def set_many(self, states: Dict[str, IState], ttl: Optional[int] = None) -> None:
        """批量设置缓存状态"""
        self.primary_cache.set_many(states, ttl)
        self.secondary_cache.set_many(states, ttl)
    
    def cleanup_expired(self) -> int:
        """清理过期缓存项"""
        primary_cleaned = self.primary_cache.cleanup_expired()
        secondary_cleaned = self.secondary_cache.cleanup_expired()
        return primary_cleaned + secondary_cleaned


# 便捷函数
def create_state_cache(cache_name: str = "state",
                      max_size: int = 1000,
                      ttl: int = 300,
                      enable_serialization: bool = False) -> StateCacheAdapter:
    """创建状态缓存适配器的便捷函数
    
    Args:
        cache_name: 缓存名称
        max_size: 最大缓存大小
        ttl: 默认TTL（秒）
        enable_serialization: 是否启用序列化
        
    Returns:
        StateCacheAdapter: 状态缓存适配器实例
    """
    return StateCacheAdapter(cache_name, max_size, ttl, enable_serialization)


def create_noop_cache() -> NoOpCacheAdapter:
    """创建无操作缓存适配器的便捷函数
    
    Returns:
        NoOpCacheAdapter: 无操作缓存适配器实例
    """
    return NoOpCacheAdapter()


def create_tiered_cache(primary_cache: IStateCache, 
                       secondary_cache: IStateCache) -> TieredStateCacheAdapter:
    """创建分层缓存适配器的便捷函数
    
    Args:
        primary_cache: 主缓存
        secondary_cache: 次级缓存
        
    Returns:
        TieredStateCacheAdapter: 分层缓存适配器实例
    """
    return TieredStateCacheAdapter(primary_cache, secondary_cache)