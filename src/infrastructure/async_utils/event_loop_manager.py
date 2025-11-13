"""事件循环管理器

提供统一的事件循环管理，避免频繁创建和销毁事件循环。
"""

import asyncio
import threading
from typing import Optional, Any, Coroutine
from functools import wraps
import logging
import concurrent.futures

logger = logging.getLogger(__name__)


class EventLoopManager:
    """事件循环管理器
    
    提供单例模式的事件循环管理，确保在同步环境中正确运行异步代码。
    """
    
    _instance: Optional['EventLoopManager'] = None
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
        """在事件循环中运行协程
        
        Args:
            coro: 要运行的协程
            
        Returns:
            协程的执行结果
        """
        loop = self._ensure_loop()
        
        # 如果在事件循环线程中，直接运行
        if threading.current_thread() == self._thread:
            # 创建任务并等待完成
            task = asyncio.run_coroutine_threadsafe(coro, loop)
            return task.result()
        else:
            # 在其他线程中，使用线程安全的方式运行
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
        """关闭事件循环管理器"""
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        if self._thread and self._thread.is_alive():
            self._shutdown_event.wait(timeout=5.0)
            
        logger.info("EventLoopManager shutdown")


# 全局事件循环管理器实例
event_loop_manager = EventLoopManager()


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