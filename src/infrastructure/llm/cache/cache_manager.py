"""缓存管理器"""

import time
import threading
from typing import Any, Optional, Dict, Sequence
from langchain_core.messages import BaseMessage

from .interfaces import ICacheProvider
from .cache_config import CacheConfig
from .memory_provider import MemoryCacheProvider
from .key_generator import LLMCacheKeyGenerator, AnthropicCacheKeyGenerator


class CacheManager:
    """统一的缓存管理器"""
    
    def __init__(self, config: CacheConfig):
        """
        初始化缓存管理器
        
        Args:
            config: 缓存配置
        """
        self.config = config
        self._provider: Optional[ICacheProvider] = None
        self._key_generator = LLMCacheKeyGenerator()
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "cleanups": 0,
        }
        
        # 初始化缓存提供者
        self._initialize_provider()
        
        # 启动清理线程
        self._cleanup_thread = None
        if config.is_enabled():
            self._start_cleanup_thread()
    
    def _initialize_provider(self) -> None:
        """初始化缓存提供者"""
        if not self.config.is_enabled():
            return
        
        cache_type = self.config.cache_type.lower()
        
        if cache_type == "memory":
            self._provider = MemoryCacheProvider(
                max_size=self.config.get_max_size(),
                default_ttl=self.config.get_ttl_seconds()
            )
        else:
            # 可以在这里添加其他缓存提供者（如Redis）
            raise ValueError(f"不支持的缓存类型: {cache_type}")
    
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
                if self._provider:
                    cleaned = self._provider.cleanup_expired()
                    if cleaned > 0:
                        with self._lock:
                            self._stats["cleanups"] += 1
            except Exception:
                # 清理错误不应该影响主流程
                pass
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在则返回None
        """
        if not self.is_enabled() or not self._provider:
            with self._lock:
                self._stats["misses"] += 1
            return None
        
        try:
            value = self._provider.get(key)
            if value is not None:
                with self._lock:
                    self._stats["hits"] += 1
            else:
                with self._lock:
                    self._stats["misses"] += 1
            return value
        except Exception:
            # 缓存错误不应该影响主流程
            with self._lock:
                self._stats["misses"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认TTL
        """
        if not self.is_enabled() or not self._provider:
            return
        
        try:
            self._provider.set(key, value, ttl)
            with self._lock:
                self._stats["sets"] += 1
        except Exception:
            # 缓存错误不应该影响主流程
            pass
    
    def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        if not self.is_enabled() or not self._provider:
            return False
        
        try:
            result = self._provider.delete(key)
            if result:
                with self._lock:
                    self._stats["deletes"] += 1
            return result
        except Exception:
            # 缓存错误不应该影响主流程
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        if not self.is_enabled() or not self._provider:
            return
        
        try:
            self._provider.clear()
        except Exception:
            # 缓存错误不应该影响主流程
            pass
    
    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        if not self.is_enabled() or not self._provider:
            return False
        
        try:
            return self._provider.exists(key)
        except Exception:
            # 缓存错误不应该影响主流程
            return False
    
    def get_size(self) -> int:
        """
        获取缓存大小
        
        Returns:
            缓存项数量
        """
        if not self.is_enabled() or not self._provider:
            return 0
        
        try:
            return self._provider.get_size()
        except Exception:
            # 缓存错误不应该影响主流程
            return 0
    
    def is_enabled(self) -> bool:
        """检查缓存是否启用"""
        return self.config.is_enabled()
    
    def generate_llm_key(self, messages: Sequence[BaseMessage], model: str = "",
                        parameters: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """
        生成LLM缓存键
        
        Args:
            messages: 消息列表
            model: 模型名称
            parameters: 生成参数
            **kwargs: 其他参数
            
        Returns:
            缓存键
        """
        return self._key_generator.generate_key(messages, model, parameters, **kwargs)
    
    def get_llm_response(self, messages: Sequence[BaseMessage], model: str = "",
                        parameters: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Any]:
        """
        获取LLM响应缓存
        
        Args:
            messages: 消息列表
            model: 模型名称
            parameters: 生成参数
            **kwargs: 其他参数
            
        Returns:
            缓存的响应，如果不存在则返回None
        """
        key = self.generate_llm_key(messages, model, parameters, **kwargs)
        return self.get(key)
    
    def set_llm_response(self, messages: Sequence[BaseMessage], response: Any,
                        model: str = "", parameters: Optional[Dict[str, Any]] = None, ttl: Optional[int] = None,
                        **kwargs) -> None:
        """
        设置LLM响应缓存
        
        Args:
            messages: 消息列表
            response: 响应内容
            model: 模型名称
            parameters: 生成参数
            ttl: 生存时间（秒）
            **kwargs: 其他参数
        """
        key = self.generate_llm_key(messages, model, parameters, **kwargs)
        self.set(key, response, ttl)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            stats: Dict[str, Any] = self._stats.copy()

        # 计算命中率
        total_requests = stats["hits"] + stats["misses"]
        hit_rate = stats["hits"] / total_requests if total_requests > 0 else 0.0
        stats["hit_rate"] = hit_rate
        
        # 添加提供者统计信息
        if self._provider and hasattr(self._provider, "get_stats"):
            stats["provider"] = getattr(self._provider, "get_stats")()
        
        return stats
    
    def cleanup_expired(self) -> int:
        """
        清理过期的缓存项
        
        Returns:
            清理的项数量
        """
        if not self.is_enabled() or not self._provider:
            return 0
        
        try:
            cleaned = self._provider.cleanup_expired()
            if cleaned > 0:
                with self._lock:
                    self._stats["cleanups"] += 1
            return cleaned
        except Exception:
            # 缓存错误不应该影响主流程
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

    async def get_async(self, key: str) -> Optional[Any]:
        """
        异步获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在则返回None
        """
        if not self.is_enabled() or not self._provider:
            with self._lock:
                self._stats["misses"] += 1
            return None

        try:
            value = await self._provider.get_async(key)
            if value is not None:
                with self._lock:
                    self._stats["hits"] += 1
            else:
                with self._lock:
                    self._stats["misses"] += 1
            return value
        except Exception:
            # 缓存错误不应该影响主流程
            with self._lock:
                self._stats["misses"] += 1
            return None

    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        异步设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认TTL
        """
        if not self.is_enabled() or not self._provider:
            return

        try:
            await self._provider.set_async(key, value, ttl)
            with self._lock:
                self._stats["sets"] += 1
        except Exception:
            # 缓存错误不应该影响主流程
            pass
    
    def close(self) -> None:
        """关闭缓存管理器"""
        # 停止清理线程
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            # 线程是守护线程，会自动退出
            pass
        
        # 清理资源
        if self._provider:
            self.clear()
            self._provider = None


class AnthropicCacheManager(CacheManager):
    """Anthropic专用缓存管理器"""
    
    def __init__(self, config: CacheConfig):
        """
        初始化Anthropic缓存管理器
        
        Args:
            config: 缓存配置
        """
        super().__init__(config)
        # 使用Anthropic专用的键生成器
        self._key_generator = AnthropicCacheKeyGenerator()
    
    def get_anthropic_cache_params(self) -> Dict[str, Any]:
        """
        获取Anthropic缓存参数
        
        Returns:
            Anthropic缓存参数字典
        """
        if not self.config.cache_control_type:
            return {}
        
        cache_params: Dict[str, Any] = {
            "type": self.config.cache_control_type
        }
        
        # 如果配置了max_tokens，则包含它
        # 这对于persistent和ephemeral类型都是有意义的
        if self.config.max_tokens:
            cache_params["max_tokens"] = self.config.max_tokens
        
        return {"cache_control": cache_params}