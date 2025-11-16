"""同步缓存适配器 - 解决异步缓存同步调用问题"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional, Dict
import logging
import weakref

logger = logging.getLogger(__name__)


class SyncCacheAdapter:
    """同步缓存适配器，包装异步缓存管理器以提供同步接口"""
    
    # 类级别的线程池缓存，避免重复创建
    _executor_cache = weakref.WeakValueDictionary()
    _executor_lock = threading.Lock()
    
    def __init__(self, async_cache_manager, max_workers: int = 4, timeout: int = 5):
        """初始化同步缓存适配器
        
        Args:
            async_cache_manager: 异步缓存管理器实例
            max_workers: 线程池最大工作线程数（默认增加到4）
            timeout: 异步操作超时时间（秒）
        """
        self.async_cache = async_cache_manager
        self.timeout = timeout
        
        # 获取或创建共享的线程池
        cache_key = f"sync_cache_{max_workers}"
        with self._executor_lock:
            if cache_key not in self._executor_cache:
                self._executor_cache[cache_key] = ThreadPoolExecutor(
                    max_workers=max_workers,
                    thread_name_prefix="SyncCacheAdapter"
                )
            self._executor = self._executor_cache[cache_key]
        
        # 优化的事件循环处理
        self._loop = None
        self._loop_lock = threading.Lock()
        
    def _get_event_loop(self):
        """获取或创建事件循环"""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            # 当前线程没有事件循环，创建新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
    
    def _run_async(self, coro):
        """优化地运行异步函数 - 使用更高效的线程池机制
        
        Args:
            coro: 异步协程
            
        Returns:
            异步函数返回值
        """
        try:
            # 检查当前是否有运行的事件循环
            loop = asyncio.get_running_loop()
            # 有运行中的事件循环，使用线程池执行协程
            future = self._executor.submit(self._run_in_thread, coro)
            return future.result(timeout=self.timeout)
        except RuntimeError:
            # 没有运行中的事件循环，直接使用 asyncio.run
            return asyncio.run(coro)
    
    def _run_in_thread(self, coro):
        """在线程中运行协程 - 优化线程复用"""
        # 使用新的事件循环避免冲突
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    def get(self, key: str, default=None) -> Any:
        """同步获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存值，如果不存在或出错则返回默认值
        """
        try:
            return self._run_async(self.async_cache.get(key))
        except Exception as e:
            logger.warning(f"缓存获取失败 (key={key}): {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """同步设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒）
            
        Returns:
            是否成功设置
        """
        try:
            self._run_async(self.async_cache.set(key, value, ttl))
            return True
        except Exception as e:
            logger.warning(f"缓存设置失败 (key={key}): {e}")
            return False
    
    def remove(self, key: str) -> bool:
        """同步移除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功移除
        """
        try:
            result = self._run_async(self.async_cache.remove(key))
            return result
        except Exception as e:
            logger.warning(f"缓存移除失败 (key={key}): {e}")
            return False
    
    def remove_by_pattern(self, pattern: str) -> int:
        """根据模式同步移除缓存项
        
        Args:
            pattern: 正则表达式模式
            
        Returns:
            移除的缓存项数量
        """
        try:
            result = self._run_async(self.async_cache.remove_by_pattern(pattern))
            return result
        except Exception as e:
            logger.warning(f"缓存模式移除失败 (pattern={pattern}): {e}")
            return 0
    
    def clear(self) -> bool:
        """同步清空所有缓存
        
        Returns:
            是否成功清空
        """
        try:
            self._run_async(self.async_cache.clear())
            return True
        except Exception as e:
            logger.warning(f"缓存清空失败: {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """同步清理过期缓存项
        
        Returns:
            清理的缓存项数量
        """
        try:
            result = self._run_async(self.async_cache.cleanup_expired())
            return result
        except Exception as e:
            logger.warning(f"缓存清理失败: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息 - 包含适配器自身的性能统计
        
        Returns:
            缓存统计信息
        """
        try:
            base_stats = {}
            # 统计信息通常是同步的，直接调用
            if hasattr(self.async_cache, 'get_stats'):
                base_stats = self.async_cache.get_stats()
            
            # 添加适配器自身的统计信息
            adapter_stats = {
                "adapter_type": "SyncCacheAdapter",
                "thread_pool_size": getattr(self._executor, '_max_workers', 0),
                "thread_pool_active": len(getattr(self._executor, '_threads', set())),
                "timeout_config": self.timeout,
                "cache_type": type(self.async_cache).__name__
            }
            
            return {**base_stats, **adapter_stats}
        except Exception as e:
            logger.warning(f"获取缓存统计信息失败: {e}")
            return {"error": str(e)}
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取详细缓存信息 - 包含线程池状态
        
        Returns:
            详细缓存信息
        """
        try:
            base_info = {}
            # 详细缓存信息通常是同步的，直接调用
            if hasattr(self.async_cache, 'get_cache_info'):
                base_info = self.async_cache.get_cache_info()
            
            # 添加适配器信息
            adapter_info = {
                "adapter_type": "SyncCacheAdapter",
                "thread_pool_config": {
                    "max_workers": getattr(self._executor, '_max_workers', 0),
                    "active_threads": len(getattr(self._executor, '_threads', set())),
                    "queue_size": getattr(self._executor, '_work_queue', None).qsize() if hasattr(self._executor, '_work_queue') else 0
                },
                "timeout": self.timeout,
                "underlying_cache": type(self.async_cache).__name__
            }
            
            return {**base_info, **adapter_info}
        except Exception as e:
            logger.warning(f"获取详细缓存信息失败: {e}")
            return {"error": str(e)}
    
    def get_or_set(self, key: str, factory_func, ttl: Optional[int] = None) -> Any:
        """获取缓存值，如果不存在则通过工厂函数创建 - 原子操作优化
        
        Args:
            key: 缓存键
            factory_func: 工厂函数（同步函数）
            ttl: TTL（秒）
            
        Returns:
            缓存值
        """
        # 先尝试获取
        value = self.get(key)
        if value is not None:
            return value
        
        # 不存在，创建新值（带异常处理）
        try:
            value = factory_func()
            if value is not None:  # 确保工厂函数返回有效值
                self.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"工厂函数执行失败 (key={key}): {e}")
            return None
    
    def close(self):
        """关闭适配器，清理资源"""
        try:
            # 注意：不关闭共享的线程池，让系统自动管理
            logger.info("SyncCacheAdapter 关闭完成")
        except Exception as e:
            logger.error(f"关闭 SyncCacheAdapter 失败: {e}")
    
    def __del__(self):
        """析构函数，确保资源清理"""
        try:
            self.close()
        except Exception:
            pass  # 忽略析构时的错误
            logger.warning(f"工厂函数执行失败 (key={key}): {e}")
            return None
    
    def close(self):
        """关闭适配器，清理资源"""
        try:
            self._executor.shutdown(wait=True)
        except Exception as e:
            logger.warning(f"关闭同步缓存适配器失败: {e}")
    
    def __enter__(self):
        """上下文管理器支持"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器清理"""
        self.close()