"""状态缓存适配器

将现有的缓存模块适配到状态管理接口。
"""

import asyncio
from src.interfaces.dependency_injection import get_logger
from typing import Any, Dict, List, Optional

from src.infrastructure.common.cache import CacheManager
from src.interfaces.state.base import IState
from src.interfaces.state.cache import IStateCache


logger = get_logger(__name__)


class StateCacheAdapter(IStateCache):
    """状态缓存适配器
    
    将现有的CacheManager适配到IStateCache接口。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化状态缓存适配器
        
        Args:
            config: 缓存配置
        """
        self.config = config
        self.max_size = config.get('max_size', 1000)
        self.default_ttl = config.get('ttl', 300)  # 5分钟
        
        # 创建缓存管理器
        self._cache_manager = CacheManager(
            max_size=self.max_size,
            default_ttl=self.default_ttl,
            enable_serialization=config.get('enable_serialization', False),
            serialization_format=config.get('serialization_format', 'json')
        )
        
        logger.debug(f"初始化状态缓存适配器，max_size={self.max_size}, ttl={self.default_ttl}")
    
    def get(self, key: str) -> Optional[IState]:
        """获取缓存状态
        
        Args:
            key: 状态ID
            
        Returns:
            状态实例，如果未找到或已过期则返回None
        """
        try:
            # 使用同步方式调用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                value = loop.run_until_complete(self._cache_manager.get(key))
                return value
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"获取缓存状态失败: {e}")
            return None
    
    def put(self, key: str, state: IState, ttl: Optional[int] = None) -> None:
        """设置缓存状态
        
        Args:
            key: 状态ID
            state: 状态实例
            ttl: TTL（秒），如果为None则使用默认值
        """
        try:
            # 使用同步方式调用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._cache_manager.set(key, state, ttl=ttl or self.default_ttl))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"设置缓存状态失败: {e}")
    
    def delete(self, key: str) -> bool:
        """删除缓存状态
        
        Args:
            key: 状态ID
            
        Returns:
            是否删除成功
        """
        try:
            # 使用同步方式调用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._cache_manager.delete(key))
                return result
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"删除缓存状态失败: {e}")
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        try:
            # 使用同步方式调用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._cache_manager.clear())
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
    
    def size(self) -> int:
        """获取缓存大小
        
        Returns:
            缓存中的状态数量
        """
        try:
            # 使用同步方式调用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                stats = loop.run_until_complete(self._cache_manager.get_stats())
                return int(stats.get('cache_size', 0))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"获取缓存大小失败: {e}")
            return 0
    
    def get_all_keys(self) -> List[str]:
        """获取所有键
        
        Returns:
            所有状态ID列表
        """
        try:
            # 使用同步方式调用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                keys = loop.run_until_complete(self._cache_manager.get_all_keys())
                return keys
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"获取所有键失败: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 使用同步方式调用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                stats = loop.run_until_complete(self._cache_manager.get_stats())
                return {
                    "hits": stats.get("hits", 0),
                    "misses": stats.get("misses", 0),
                    "evictions": stats.get("evictions", 0),
                    "size": stats.get("cache_size", 0),
                    "max_size": self.max_size,
                    "hit_rate": stats.get("hit_rate", 0.0),
                    "ttl": self.default_ttl
                }
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def cleanup_expired(self) -> int:
        """清理过期条目
        
        Returns:
            清理的条目数量
        """
        try:
            # 使用同步方式调用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                count = loop.run_until_complete(self._cache_manager.cleanup_expired())
                return count
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"清理过期条目失败: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """检查缓存项是否存在
        
        Args:
            key: 状态ID
            
        Returns:
            是否存在
        """
        try:
            # 使用同步方式调用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                exists = loop.run_until_complete(self._cache_manager.exists(key))
                return exists
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"检查缓存项是否存在失败: {e}")
            return False
    
    def get_many(self, keys: List[str]) -> Dict[str, IState]:
        """批量获取缓存状态
        
        Args:
            keys: 状态ID列表
            
        Returns:
            状态字典
        """
        try:
            # 使用同步方式调用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                states = loop.run_until_complete(self._cache_manager.get_many(keys))
                return states
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"批量获取缓存状态失败: {e}")
            return {}
    
    def set_many(self, states: Dict[str, IState], ttl: Optional[int] = None) -> None:
        """批量设置缓存状态
        
        Args:
            states: 状态字典
            ttl: TTL（秒）
        """
        try:
            # 使用同步方式调用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._cache_manager.set_many(states, ttl=ttl or self.default_ttl))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"批量设置缓存状态失败: {e}")