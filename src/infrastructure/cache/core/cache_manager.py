"""统一缓存管理器

提供通用的缓存管理功能。LLM专用的缓存管理器已移动到 llm 模块中。
"""

import time
import threading
from typing import Any, Optional, List, Dict, Sequence
from src.interfaces.messages import IBaseMessage

from ..config.cache_config import BaseCacheConfig
from src.interfaces.llm import ICacheProvider, ICacheKeyGenerator
from src.interfaces.cache import ICacheAdapter
from .key_generator import DefaultCacheKeyGenerator
from ..providers.memory.memory_provider import MemoryCacheProvider


class CacheManager(ICacheAdapter):
    """统一缓存管理器，支持通用缓存功能"""
    
    def __init__(self,
                 config: BaseCacheConfig,
                 client_provider: Optional[ICacheProvider] = None,
                 server_provider: Optional[Any] = None,
                 key_generator: Optional[ICacheKeyGenerator] = None):
        """
        初始化统一缓存管理器
        
        Args:
            config: 缓存配置
            client_provider: 客户端缓存提供者（可选，默认使用内存提供者）
            server_provider: 服务器端缓存提供者（可选，保留兼容性）
            key_generator: 键生成器（可选）
        """
        self.config = config
        
        # 初始化客户端缓存提供者
        if client_provider is None:
            self._client_provider = MemoryCacheProvider(
                max_size=config.get_max_size(),
                default_ttl=config.get_ttl_seconds()
            )
        else:
            self._client_provider = client_provider
            
        self._server_provider = server_provider  # 保留兼容性，但不再使用
        self._key_generator = key_generator or DefaultCacheKeyGenerator()
        self._lock = threading.RLock()
        
        # 基础统计信息
        self._stats: Dict[str, Any] = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "cleanups": 0,
        }
        
        # 启动清理线程
        self._cleanup_thread = None
        if config.is_enabled():
            self._start_cleanup_thread()
    
    def _start_cleanup_thread(self) -> None:
        """启动清理线程"""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_worker,
                daemon=True,
                name="CacheCleanupWorker"
            )
            self._cleanup_thread.start()
    
    def _cleanup_worker(self) -> None:
        """清理工作线程"""
        while self.config.is_enabled():
            try:
                time.sleep(300)  # 5分钟清理一次
                if self._client_provider:
                    cleaned = self._client_provider.cleanup_expired()
                    if cleaned > 0:
                        with self._lock:
                            self._stats["cleanups"] += 1
            except Exception:
                # 清理错误不应该影响主流程
                pass
    
    def is_enabled(self) -> bool:
        """检查缓存是否启用"""
        return self.config.is_enabled()
    
    def exists(self, key: str) -> bool:
        """检查缓存键是否存在"""
        if not self.is_enabled() or not self._client_provider:
            return False
        
        try:
            return self._client_provider.exists(key)
        except Exception:
            return False
    
    def get_size(self) -> int:
        """获取缓存大小"""
        if not self.is_enabled() or not self._client_provider:
            return 0
        
        try:
            return self._client_provider.get_size()
        except Exception:
            return 0
    
    def cleanup_expired(self) -> int:
        """清理过期的缓存项"""
        if not self.is_enabled() or not self._client_provider:
            return 0
        
        try:
            cleaned = self._client_provider.cleanup_expired()
            if cleaned > 0:
                with self._lock:
                    self._stats["cleanups"] += 1
            return cleaned
        except Exception:
            return 0
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        with self._lock:
            self._stats = {
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "deletes": 0,
                "cleanups": 0,
            }
    
    def close(self) -> None:
        """关闭缓存管理器"""
        # 停止清理线程
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            # 线程是守护线程，会自动退出
            pass
        
        # 清理资源
        if self._client_provider:
            self.clear()
            self._client_provider = None
    
    async def get_async(self, key: str) -> Optional[Any]:
        """异步获取缓存值"""
        if not self.is_enabled() or not self._client_provider:
            with self._lock:
                self._stats["misses"] += 1
            return None

        try:
            value = await self._client_provider.get_async(key)
            if value is not None:
                with self._lock:
                    self._stats["hits"] += 1
            else:
                with self._lock:
                    self._stats["misses"] += 1
            return value
        except Exception:
            with self._lock:
                self._stats["misses"] += 1
            return None

    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """异步设置缓存值"""
        if not self.is_enabled() or not self._client_provider:
            return

        try:
            await self._client_provider.set_async(key, value, ttl)
            with self._lock:
                self._stats["sets"] += 1
        except Exception:
            pass
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.is_enabled() or not self._client_provider:
            with self._lock:
                self._stats["misses"] += 1
            return None
        
        try:
            value = self._client_provider.get(key)
            if value is not None:
                with self._lock:
                    self._stats["hits"] += 1
            else:
                with self._lock:
                    self._stats["misses"] += 1
            return value
        except Exception:
            with self._lock:
                self._stats["misses"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        if not self.is_enabled() or not self._client_provider:
            return
        
        try:
            self._client_provider.set(key, value, ttl)
            with self._lock:
                self._stats["sets"] += 1
        except Exception:
            pass
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        if not self.is_enabled() or not self._client_provider:
            return False
        
        try:
            result = self._client_provider.delete(key)
            if result:
                with self._lock:
                    self._stats["deletes"] += 1
            return result
        except Exception:
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        if not self.is_enabled() or not self._client_provider:
            return
        
        try:
            self._client_provider.clear()
        except Exception:
            pass  # 忽略清理错误
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            stats = self._stats.copy()
        
        # 计算命中率
        total_requests = stats["hits"] + stats["misses"]
        hit_rate = stats["hits"] / total_requests if total_requests > 0 else 0.0
        stats["hit_rate"] = hit_rate
        
        # 添加提供者统计信息
        if self._client_provider and hasattr(self._client_provider, "get_stats"):
            try:
                client_stats = self._client_provider.get_stats()
                stats["client_provider"] = client_stats
            except Exception:
                pass
        
        return stats
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置信息"""
        config_info = {
            "enabled": self.config.enabled,
            "cache_type": self.config.cache_type,
            "ttl_seconds": self.config.get_ttl_seconds(),
            "max_size": self.config.get_max_size()
        }
        
        return config_info
    
    def get_all_keys(self) -> List[str]:
        """获取所有缓存键"""
        if not self.is_enabled() or not self._client_provider:
            return []
        
        try:
            # 如果提供者支持获取所有键
            if hasattr(self._client_provider, "get_all_keys"):
                return self._client_provider.get_all_keys()
            # 否则返回空列表
            return []
        except Exception:
            return []