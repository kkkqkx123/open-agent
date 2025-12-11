"""配置缓存管理器实现

提供配置系统的缓存管理功能，基于现有的缓存基础设施。
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from src.infrastructure.cache.core.cache_manager import CacheManager as BaseCacheManager
    from src.infrastructure.cache.config.cache_config import BaseCacheConfig

logger = logging.getLogger(__name__)


class CacheManager:
    """配置缓存管理器
    
    提供配置系统的缓存管理功能，封装现有的缓存基础设施。
    """
    
    def __init__(self, config: Optional['BaseCacheConfig'] = None):
        """初始化缓存管理器
        
        Args:
            config: 缓存配置，如果为None则使用默认配置
        """
        # 延迟导入避免循环依赖
        from src.infrastructure.cache.core.cache_manager import CacheManager as BaseCacheManager
        from src.infrastructure.cache.config.cache_config import BaseCacheConfig
        
        if config is None:
            # 创建默认配置
            config = BaseCacheConfig(
                enabled=True,
                cache_type="memory",
                ttl_seconds=300,
                max_size=1000
            )
        
        self._cache_manager = BaseCacheManager(config)
        logger.debug(f"初始化配置缓存管理器，类型: {config.cache_type}")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或过期则返回None
        """
        try:
            value = self._cache_manager.get(key)
            if value is not None:
                logger.debug(f"缓存命中: {key}")
            else:
                logger.debug(f"缓存未命中: {key}")
            return value
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），如果为None则使用默认TTL
        """
        try:
            self._cache_manager.set(key, value, ttl)
            logger.debug(f"设置缓存: {key}, TTL: {ttl}秒")
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
    
    def delete(self, key: str) -> bool:
        """删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        try:
            result = self._cache_manager.delete(key)
            if result:
                logger.debug(f"删除缓存: {key}")
            return result
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False
    
    def clear(self) -> None:
        """清除所有缓存"""
        try:
            self._cache_manager.clear()
            logger.debug("清除所有缓存")
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        try:
            return self._cache_manager.exists(key)
        except Exception as e:
            logger.error(f"检查缓存存在性失败 {key}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        try:
            stats = self._cache_manager.get_stats()
            stats.update({
                "config_type": "config_cache"
            })
            return stats
        except Exception as e:
            logger.error(f"获取缓存统计信息失败: {e}")
            return {
                "error": str(e),
                "config_type": "config_cache"
            }
    
    def get_all_keys(self) -> list:
        """获取所有缓存键"""
        try:
            return self._cache_manager.get_all_keys()
        except Exception as e:
            logger.error(f"获取所有缓存键失败: {e}")
            return []
    
    def cleanup_expired(self) -> int:
        """清理过期的缓存项"""
        try:
            return self._cache_manager.cleanup_expired()
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return 0
    
    def is_enabled(self) -> bool:
        """检查缓存是否启用"""
        return self._cache_manager.is_enabled()
    
    def enable_cache(self, enabled: bool) -> None:
        """启用或禁用缓存
        
        Args:
            enabled: 是否启用缓存
        """
        # 注意：现有的CacheManager不支持动态启用/禁用
        # 这里只是记录日志，实际功能需要在配置层面控制
        logger.debug(f"缓存{'启用' if enabled else '禁用'}（需要重启生效）")
    
    def set_default_ttl(self, ttl: int) -> None:
        """设置默认TTL
        
        Args:
            ttl: 默认生存时间（秒）
        """
        # 注意：现有的CacheManager不支持动态设置TTL
        # 这里只是记录日志，实际功能需要在配置层面控制
        logger.debug(f"设置默认TTL: {ttl}秒（需要重启生效）")