"""统一缓存管理器 - 整合API层和业务层的缓存策略"""

from typing import Any, Optional, Dict, Union
import logging
from pathlib import Path

from ....infrastructure.common.cache.enhanced_cache_manager import EnhancedCacheManager
from ....infrastructure.common.cache.sync_cache_adapter import SyncCacheAdapter
from .memory_cache import MemoryCache

logger = logging.getLogger(__name__)


class CacheManager:
    """统一缓存管理器 - 提供API层和业务层的统一缓存接口
    
    该类整合了MemoryCache和EnhancedCacheManager的功能，
    允许API层受益于业务层的高级缓存特性，同时保持向后兼容性。
    """
    
    def __init__(
        self,
        cache_type: str = "unified",  # "memory", "enhanced", "unified"
        default_ttl: int = 300,  # 默认5分钟
        max_size: int = 1000,
        enable_stats: bool = True,
        use_sync_adapter: bool = False,
        sync_max_workers: int = 4,
        unified_enabled: bool = True,
        fallback_enabled: bool = True,
        invalidation_enabled: bool = True
    ):
        """初始化统一缓存管理器
        
        Args:
            cache_type: 缓存类型 ("memory", "enhanced", "unified")
            default_ttl: 默认TTL（秒）
            max_size: 最大缓存项数
            enable_stats: 是否启用统计
            use_sync_adapter: 是否使用同步适配器
            sync_max_workers: 同步适配器最大工作线程数
            unified_enabled: 是否启用统一缓存管理
            fallback_enabled: 是否启用缓存降级机制
            invalidation_enabled: 是否启用缓存失效机制
        """
        self.cache_type = cache_type
        self.default_ttl = default_ttl
        self.enable_stats = enable_stats
        self.unified_enabled = unified_enabled
        self.fallback_enabled = fallback_enabled
        self.invalidation_enabled = invalidation_enabled
        
        # 根据类型创建底层缓存
        if cache_type == "memory":
            self._cache = MemoryCache(default_ttl=default_ttl)
            self._enhanced_cache = None
        elif cache_type == "enhanced":
            self._cache = None
            self._enhanced_cache = EnhancedCacheManager(
                max_size=max_size,
                default_ttl=default_ttl
            )
        else:  # unified
            self._cache = MemoryCache(default_ttl=default_ttl)
            self._enhanced_cache = EnhancedCacheManager(
                max_size=max_size,
                default_ttl=default_ttl
            )
        
        # 配置同步适配器
        self._sync_adapter = None
        if use_sync_adapter and self._enhanced_cache:
            self._sync_adapter = SyncCacheAdapter(
                self._enhanced_cache,
                max_workers=sync_max_workers
            )
        
        logger.info(f"统一缓存管理器初始化完成 (类型: {cache_type}, 统一模式: {unified_enabled}, 降级: {fallback_enabled}, 失效: {invalidation_enabled})")
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值 - 统一接口"""
        if not self.unified_enabled:
            logger.debug(f"统一缓存管理已禁用，跳过获取 (key={key})")
            return None
            
        try:
            if self.cache_type == "memory":
                return await self._cache.get(key)
            elif self.cache_type == "enhanced":
                return await self._enhanced_cache.get(key)
            else:  # unified
                # 先检查内存缓存，再检查增强缓存
                memory_result = await self._cache.get(key)
                if memory_result is not None:
                    return memory_result
                return await self._enhanced_cache.get(key)
        except Exception as e:
            logger.warning(f"缓存获取失败 (key={key}): {e}")
            if self.fallback_enabled:
                logger.info(f"启用降级机制，返回None (key={key})")
                return None
            else:
                raise
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值 - 统一接口"""
        if not self.unified_enabled:
            logger.debug(f"统一缓存管理已禁用，跳过设置 (key={key})")
            return True
            
        try:
            ttl = ttl or self.default_ttl
            
            if self.cache_type == "memory":
                await self._cache.set(key, value, ttl)
                return True
            elif self.cache_type == "enhanced":
                await self._enhanced_cache.set(key, value, ttl)
                return True
            else:  # unified
                # 同时设置到两层缓存
                await self._cache.set(key, value, ttl)
                await self._enhanced_cache.set(key, value, ttl)
                return True
        except Exception as e:
            logger.warning(f"缓存设置失败 (key={key}): {e}")
            if self.fallback_enabled:
                logger.info(f"启用降级机制，返回True (key={key})")
                return True
            else:
                return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存 - 统一接口"""
        if not self.unified_enabled:
            logger.debug(f"统一缓存管理已禁用，跳过删除 (key={key})")
            return True
            
        try:
            if self.cache_type == "memory":
                await self._cache.delete(key)
                return True
            elif self.cache_type == "enhanced":
                result = await self._enhanced_cache.remove(key)
                return result
            else:  # unified
                await self._cache.delete(key)
                result = await self._enhanced_cache.remove(key)
                return result
        except Exception as e:
            logger.warning(f"缓存删除失败 (key={key}): {e}")
            if self.fallback_enabled:
                logger.info(f"启用降级机制，返回True (key={key})")
                return True
            else:
                return False
    
    async def clear(self) -> bool:
        """清空缓存 - 统一接口"""
        if not self.unified_enabled:
            logger.debug("统一缓存管理已禁用，跳过清空")
            return True
            
        try:
            if self.cache_type == "memory":
                await self._cache.clear()
                return True
            elif self.cache_type == "enhanced":
                await self._enhanced_cache.clear()
                return True
            else:  # unified
                await self._cache.clear()
                await self._enhanced_cache.clear()
                return True
        except Exception as e:
            logger.warning(f"缓存清空失败: {e}")
            if self.fallback_enabled:
                logger.info("启用降级机制，返回True")
                return True
            else:
                return False
    
    def get_sync_adapter(self) -> Optional[SyncCacheAdapter]:
        """获取同步适配器（如果可用）"""
        return self._sync_adapter
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "cache_type": self.cache_type,
            "default_ttl": self.default_ttl,
            "enable_stats": self.enable_stats,
            "unified_enabled": self.unified_enabled,
            "fallback_enabled": self.fallback_enabled,
            "invalidation_enabled": self.invalidation_enabled
        }
        
        try:
            if self._enhanced_cache and hasattr(self._enhanced_cache, 'get_stats'):
                enhanced_stats = self._enhanced_cache.get_stats()
                stats["enhanced_cache"] = enhanced_stats
            
            if self._sync_adapter:
                adapter_stats = self._sync_adapter.get_stats()
                stats["sync_adapter"] = adapter_stats
            
        except Exception as e:
            stats["error"] = str(e)
        
        return stats
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取详细缓存信息"""
        info = {
            "cache_type": self.cache_type,
            "default_ttl": self.default_ttl,
            "enable_stats": self.enable_stats,
            "unified_enabled": self.unified_enabled,
            "fallback_enabled": self.fallback_enabled,
            "invalidation_enabled": self.invalidation_enabled
        }
        
        try:
            if self._enhanced_cache and hasattr(self._enhanced_cache, 'get_cache_info'):
                enhanced_info = self._enhanced_cache.get_cache_info()
                info["enhanced_cache"] = enhanced_info
            
            if self._sync_adapter:
                adapter_info = self._sync_adapter.get_cache_info()
                info["sync_adapter"] = adapter_info
            
        except Exception as e:
            info["error"] = str(e)
        
        return info
    
    def switch_cache_type(self, new_type: str) -> bool:
        """动态切换缓存类型
        
        Args:
            new_type: 新的缓存类型
            
        Returns:
            是否成功切换
        """
        if new_type not in ["memory", "enhanced", "unified"]:
            logger.error(f"不支持的缓存类型: {new_type}")
            return False
        
        try:
            old_type = self.cache_type
            self.cache_type = new_type
            logger.info(f"缓存类型已切换: {old_type} -> {new_type}")
            return True
        except Exception as e:
            logger.error(f"切换缓存类型失败: {e}")
            return False