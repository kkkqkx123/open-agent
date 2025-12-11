"""事件循环管理器

提供统一的事件循环管理，避免频繁创建和销毁事件循环。
"""

import asyncio
import threading
from typing import Optional, Any, Coroutine
from functools import wraps
from src.interfaces.dependency_injection import get_logger
import concurrent.futures

logger = get_logger(__name__)


class AsyncUtils:
    """事件循环管理器
    
    用于在同步代码中调用异步函数，避免频繁创建新事件循环的开销。
    
    重要提示：
    - 仅在同步代码中调用异步代码时使用
    - 不要在异步函数中使用（用 await 代替）
    - 与 asyncio.run() 的区别：本模块重用后台循环，避免频繁创建循环
    - 应用退出前必须调用 shutdown()
    
    使用场景：
    ✅ 在同步函数中需要运行异步代码
    ✅ 无法使用 asyncio.run()（已经有运行的循环）
    ✅ 频繁执行异步操作（性能要求高）
    
    不适用场景：
    ❌ 在异步函数中（用 await 代替）
    ❌ 可以使用 asyncio.run() 的地方
    ❌ 单次执行异步代码（asyncio.run() 足够）
    
    示例：
        # ✅ 正确用法
        async def fetch_data(url):
            return await http_client.get(url)
        
        def sync_function():
            result = event_loop_manager.run_async(fetch_data("https://example.com"))
            return result
    
    警告：
        - 不要与 asyncio.run() 混用
        - 应用退出时需要调用 shutdown() 清理
    """
    
    _instance: Optional['AsyncUtils'] = None
    _lock = threading.Lock()
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._initialized = True
        
        logger.info("EventLoopManager initialized")
    
    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        """确保事件循环存在"""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            # 启动事件循环线程
            if self._thread is None or not self._thread.is_alive():
                self._shutdown_event.clear()
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()
                
        return self._loop
    
    def _run_loop(self) -> None:
        """在单独线程中运行事件循环"""
        try:
            if self._loop is not None:
                self._loop.run_forever()
        except Exception as e:
            logger.error(f"Event loop error: {e}")
        finally:
            if self._loop is not None:
                self._loop.close()
    
    def run_async(self, coro: Coroutine[Any, Any, Any]) -> Any:
        """在后台事件循环中运行协程
        
        使用后台线程中的事件循环运行协程，避免创建新的事件循环。
        
        Args:
            coro: 要运行的协程
            
        Returns:
            协程的执行结果
            
        Raises:
            Exception: 如果协程执行失败
            
        警告：
            - 不要在异步函数中使用（用 await 代替）
            - 应用退出前必须调用 shutdown()
            - 对于单次执行，考虑使用 asyncio.run() 替代
        """
        loop = self._ensure_loop()
        
        # 使用线程安全的方式运行协程
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    
    def create_task(self, coro: Coroutine[Any, Any, Any]) -> concurrent.futures.Future[Any]:
        """创建异步任务
        
        Args:
            coro: 要运行的协程
            
        Returns:
            异步任务对象
        """
        loop = self._ensure_loop()
        return asyncio.run_coroutine_threadsafe(coro, loop)
    
    def shutdown(self) -> None:
        """关闭事件循环管理器
        
        应该在应用退出前调用，清理后台事件循环线程。
        """
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        if self._thread and self._thread.is_alive():
            self._shutdown_event.wait(timeout=5.0)
            
        logger.info("事件循环管理器已关闭")


# 全局事件循环管理器实例
event_loop_manager = AsyncUtils()


def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """便捷函数：运行协程
    
    Args:
        coro: 要运行的协程
        
    Returns:
        协程的执行结果
    """
    return event_loop_manager.run_async(coro)




class AsyncContextManager:
    """异步上下文管理器基类
    
    提供统一的异步资源管理。
    """
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    async def cleanup(self):
        """清理资源"""
        pass


class AsyncLock:
    """异步锁包装器
    
    提供线程安全的异步锁。
    """
    
    def __init__(self):
        self._lock = asyncio.Lock()
        self._thread_lock = threading.Lock()
    
    async def acquire(self):
        """获取锁"""
        return await self._lock.acquire()
    
    async def release(self):
        """释放锁"""
        self._lock.release()
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()