"""统一缓存管理器"""

import time
import threading
from typing import Any, Optional, List, Dict, Sequence
from langchain_core.messages import BaseMessage

from .cache_config import BaseCacheConfig, LLMCacheConfig
from .interfaces import ICacheProvider
from .server_interfaces import IServerCacheProvider
from .key_generator import ICacheKeyGenerator, LLMCacheKeyGenerator
from .memory_provider import MemoryCacheProvider


class CacheManager:
    """统一缓存管理器，支持客户端和服务器端缓存"""
    
    def __init__(self,
                 config: BaseCacheConfig,
                 client_provider: Optional[ICacheProvider] = None,
                 server_provider: Optional[IServerCacheProvider] = None,
                 key_generator: Optional[ICacheKeyGenerator] = None):
        """
        初始化统一缓存管理器
        
        Args:
            config: 缓存配置
            client_provider: 客户端缓存提供者（可选，默认使用内存提供者）
            server_provider: 服务器端缓存提供者（可选）
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
            
        self._server_provider = server_provider
        self._key_generator = key_generator or self._create_default_key_generator()
        self._lock = threading.RLock()
        
        # 基础统计信息
        self._stats: Dict[str, Any] = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "cleanups": 0,
        }
        
        # LLM缓存统计信息
        self._llm_stats = {
            "client_hits": 0,
            "server_hits": 0,
            "client_sets": 0,
            "server_sets": 0
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
            self._llm_stats = {
                "client_hits": 0,
                "server_hits": 0,
                "client_sets": 0,
                "server_sets": 0
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
        
        # 如果是基础配置，直接使用客户端缓存
        if not isinstance(self.config, LLMCacheConfig):
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
        
        # LLM缓存策略处理
        if self.config.strategy == "client":
            # 客户端优先策略
            result = self._client_provider.get(key)
            if result is not None:
                with self._lock:
                    self._stats["hits"] += 1
                    self._llm_stats["client_hits"] += 1
                return result
            
            # 客户端未命中，尝试服务器端缓存
            if self._server_provider and self._should_try_server_cache():
                result = self._server_provider.get_cache(key)
                if result is not None:
                    with self._lock:
                        self._stats["hits"] += 1
                        self._llm_stats["server_hits"] += 1
                    return result
                    
        elif self.config.strategy == "server":
            # 服务器端优先策略
            if self._server_provider:
                result = self._server_provider.get_cache(key)
                if result is not None:
                    with self._lock:
                        self._stats["hits"] += 1
                        self._llm_stats["server_hits"] += 1
                    return result
            
            # 服务器端未命中，尝试客户端缓存
            result = self._client_provider.get(key)
            if result is not None:
                with self._lock:
                    self._stats["hits"] += 1
                    self._llm_stats["client_hits"] += 1
                return result
                
        else:  # hybrid
            # 混合策略：根据内容大小决定优先级
            if self._should_prefer_server_cache():
                if self._server_provider:
                    result = self._server_provider.get_cache(key)
                    if result is not None:
                        with self._lock:
                            self._stats["hits"] += 1
                            self._llm_stats["server_hits"] += 1
                        return result
                
                result = self._client_provider.get(key)
                if result is not None:
                    with self._lock:
                        self._stats["hits"] += 1
                        self._llm_stats["client_hits"] += 1
                    return result
            else:
                result = self._client_provider.get(key)
                if result is not None:
                    with self._lock:
                        self._stats["hits"] += 1
                        self._llm_stats["client_hits"] += 1
                    return result
                
                if self._server_provider:
                    result = self._server_provider.get_cache(key)
                    if result is not None:
                        with self._lock:
                            self._stats["hits"] += 1
                            self._llm_stats["server_hits"] += 1
                        return result
        
        with self._lock:
            self._stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        if not self.is_enabled() or not self._client_provider:
            return
        
        # 如果是基础配置，直接使用客户端缓存
        if not isinstance(self.config, LLMCacheConfig):
            try:
                self._client_provider.set(key, value, ttl)
                with self._lock:
                    self._stats["sets"] += 1
            except Exception:
                pass
            return
        
        # LLM缓存策略处理
        if self.config.strategy == "client":
            # 客户端优先策略：主要存储到客户端
            self._client_provider.set(key, value, ttl)
            with self._lock:
                self._stats["sets"] += 1
                self._llm_stats["client_sets"] += 1
            
            # 仅在满足条件时也存储到服务器端
            if self._server_provider and self._should_use_server_cache_for_content():
                with self._lock:
                    self._llm_stats["server_sets"] += 1
                
        elif self.config.strategy == "server":
            # 服务器端优先策略：主要存储到服务器端
            if self._server_provider:
                with self._lock:
                    self._llm_stats["server_sets"] += 1
            # 也存储到客户端作为备份
            self._client_provider.set(key, value, ttl)
            with self._lock:
                self._stats["sets"] += 1
                self._llm_stats["client_sets"] += 1
            
        else:  # hybrid
            # 混合策略：根据内容大小决定存储位置
            if self._should_prefer_server_cache():
                if self._server_provider:
                    with self._lock:
                        self._llm_stats["server_sets"] += 1
                self._client_provider.set(key, value, ttl)
                with self._lock:
                    self._stats["sets"] += 1
                    self._llm_stats["client_sets"] += 1
            else:
                self._client_provider.set(key, value, ttl)
                with self._lock:
                    self._stats["sets"] += 1
                    self._llm_stats["client_sets"] += 1
                if self._server_provider and self._should_use_server_cache_for_content():
                    with self._lock:
                        self._llm_stats["server_sets"] += 1
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        if not self.is_enabled() or not self._client_provider:
            return False
        
        client_result = self._client_provider.delete(key)
        server_result = False
        
        if self._server_provider:
            # 尝试从服务器端缓存删除
            try:
                # 这里需要根据实际的键映射逻辑来实现
                server_result = True  # 简化处理
            except Exception:
                server_result = False
        
        if client_result or server_result:
            with self._lock:
                self._stats["deletes"] += 1
            return True
        
        return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        if not self.is_enabled() or not self._client_provider:
            return
        
        try:
            self._client_provider.clear()
            if self._server_provider:
                try:
                    # 清理服务器端缓存
                    caches = self._server_provider.list_caches()
                    for cache in caches:
                        self._server_provider.delete_cache(cache.name)
                except Exception:
                    pass  # 忽略清理错误
        except Exception:
            pass  # 忽略清理错误
    
    def generate_llm_key(self, messages: Sequence[BaseMessage], model: str = "",
                        parameters: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """生成LLM缓存键"""
        if isinstance(self._key_generator, LLMCacheKeyGenerator):
            return self._key_generator.generate_key(messages, model, parameters, **kwargs)
        else:
            # 使用默认键生成器
            return self._key_generator.generate_key(messages, model, parameters)
    
    def get_llm_response(self, messages: Sequence[BaseMessage], model: str = "",
                        parameters: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """获取LLM响应缓存"""
        key = self.generate_llm_key(messages, model, parameters)
        return self.get(key)
    
    def set_llm_response(self, messages: Sequence[BaseMessage], response: Any,
                        model: str = "", parameters: Optional[Dict[str, Any]] = None,
                        ttl: Optional[int] = None) -> None:
        """设置LLM响应缓存"""
        key = self.generate_llm_key(messages, model, parameters)
        self.set(key, response, ttl)
    
    def create_server_cache(self, contents: List[Any], **kwargs) -> Optional[Any]:
        """创建服务器端缓存"""
        if not self._server_provider:
            return None
        
        try:
            return self._server_provider.create_cache(contents, **kwargs)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"创建服务器端缓存失败: {e}")
            return None
    
    def use_server_cache(self, cache_name: str, contents: Any) -> Optional[Any]:
        """使用服务器端缓存"""
        if not self._server_provider:
            return None
        
        try:
            return self._server_provider.use_cache(cache_name, contents)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"使用服务器端缓存失败: {e}")
            return None
    
    def get_or_create_server_cache(self, contents: List[Any], **kwargs) -> Optional[Any]:
        """获取或创建服务器端缓存"""
        if not self._server_provider:
            return None
        
        try:
            return self._server_provider.get_or_create_cache(contents, **kwargs)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"获取或创建服务器端缓存失败: {e}")
            return None
    
    def delete_server_cache(self, cache_name: str) -> bool:
        """删除服务器端缓存"""
        if not self._server_provider:
            return False
        
        return self._server_provider.delete_cache(cache_name)
    
    def list_server_caches(self) -> List[Any]:
        """列出所有服务器端缓存"""
        if not self._server_provider:
            return []
        
        return self._server_provider.list_caches()
    
    def cleanup_expired_server_caches(self) -> int:
        """清理过期的服务器端缓存"""
        if not self._server_provider:
            return 0
        
        return self._server_provider.cleanup_expired_caches()
    
    def should_use_server_cache(self, contents: List[Any]) -> bool:
        """判断是否应该使用服务器端缓存"""
        if not self._server_provider or not isinstance(self.config, LLMCacheConfig):
            return False
        
        return self._server_provider.should_use_server_cache(
            contents, self.config.large_content_threshold
        )
    
    def smart_cache_decision(
        self, 
        messages: Sequence[BaseMessage], 
        contents: Optional[List[Any]] = None,
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """智能缓存决策"""
        decision = {
            "use_client_cache": True,
            "use_server_cache": False,
            "server_cache_name": None,
            "reason": "default"
        }
        
        # 只有LLM配置才支持服务器端缓存
        if not isinstance(self.config, LLMCacheConfig):
            return decision
        
        # 检查是否应该使用服务器端缓存
        if self.config.auto_server_cache and contents and self.should_use_server_cache(contents):
            decision["use_server_cache"] = True
            decision["reason"] = "large_content_detected"
            
            # 尝试获取或创建服务器端缓存
            cache = self.get_or_create_server_cache(
                contents,
                system_instruction=system_instruction,
                ttl=self.config.server_cache_ttl,
                display_name=self.config.server_cache_display_name
            )
            
            if cache:
                decision["server_cache_name"] = cache.name
            else:
                decision["use_server_cache"] = False
                decision["reason"] = "server_cache_creation_failed"
        
        return decision
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            stats = self._stats.copy()
            llm_stats = self._llm_stats.copy()
        
        # 计算命中率
        total_requests = stats["hits"] + stats["misses"]
        hit_rate = stats["hits"] / total_requests if total_requests > 0 else 0.0
        stats["hit_rate"] = hit_rate
        
        # 添加LLM缓存统计
        if isinstance(self.config, LLMCacheConfig):
            llm_total_requests = llm_stats["client_hits"] + llm_stats["server_hits"] + stats["misses"]
            llm_hit_rate = (llm_stats["client_hits"] + llm_stats["server_hits"]) / llm_total_requests if llm_total_requests > 0 else 0.0
            stats.update(llm_stats)
            stats["llm_hit_rate"] = llm_hit_rate
            stats["strategy"] = self.config.strategy
        
        # 添加提供者统计信息
        if self._client_provider and hasattr(self._client_provider, "get_stats"):
            try:
                client_stats = self._client_provider.get_stats()
                stats["client_provider"] = client_stats
            except Exception:
                pass
        
        if self._server_provider and hasattr(self._server_provider, "get_cache_stats"):
            try:
                server_stats = self._server_provider.get_cache_stats()
                stats["server_provider"] = server_stats
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
        
        if isinstance(self.config, LLMCacheConfig):
            config_info.update({
                "server_cache_enabled": self.config.server_cache_enabled,
                "auto_server_cache": self.config.auto_server_cache,
                "large_content_threshold": self.config.large_content_threshold,
                "server_cache_ttl": self.config.server_cache_ttl,
                "server_cache_display_name": self.config.server_cache_display_name,
                "strategy": self.config.strategy
            })
        
        return config_info
    
    def _create_default_key_generator(self) -> ICacheKeyGenerator:
        """创建默认键生成器"""
        from .key_generator import DefaultCacheKeyGenerator, LLMCacheKeyGenerator
        
        # 如果是LLM配置，使用LLM键生成器
        if isinstance(self.config, LLMCacheConfig):
            return LLMCacheKeyGenerator()
        else:
            return DefaultCacheKeyGenerator()
    
    def _should_try_server_cache(self) -> bool:
        """判断是否应该尝试服务器端缓存"""
        if not isinstance(self.config, LLMCacheConfig):
            return False
        return (self.config.server_cache_enabled and
                self.config.auto_server_cache)
    
    def _should_use_server_cache_for_content(self) -> bool:
        """判断是否应该对内容使用服务器端缓存"""
        if not isinstance(self.config, LLMCacheConfig):
            return False
        return (self.config.server_cache_enabled and
                self.config.server_cache_for_large_content and
                self.config.auto_server_cache)
    
    def _should_prefer_server_cache(self) -> bool:
        """判断是否应该优先使用服务器端缓存"""
        if not isinstance(self.config, LLMCacheConfig):
            return False
        # 在混合策略中，根据配置的阈值决定
        return self.config.server_cache_enabled