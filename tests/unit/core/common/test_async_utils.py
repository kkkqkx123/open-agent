"""async_tuils.py 单元测试"""

import asyncio
import pytest
import threading
from unittest.mock import Mock, patch
from core.common.async_utils import AsyncUtils, run_async, AsyncContextManager, AsyncLock


class TestAsyncUtils:
    """测试 AsyncUtils 类"""
    
    def setup_method(self):
        """测试前设置"""
        # 重置单例实例
        AsyncUtils._instance = None
        AsyncUtils._initialized = False
    
    def teardown_method(self):
        """测试后清理"""
        if AsyncUtils._instance:
            AsyncUtils._instance.shutdown()
            AsyncUtils._instance = None
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        instance1 = AsyncUtils()
        instance2 = AsyncUtils()
        assert instance1 is instance2
    
    def test_run_async_with_simple_coroutine(self):
        """测试运行简单协程"""
        async def simple_coroutine():
            return "test_result"
        
        manager = AsyncUtils()
        result = manager.run_async(simple_coroutine())
        assert result == "test_result"
    
    def test_run_async_with_asyncio_sleep(self):
        """测试运行包含异步操作的协程"""
        async def sleep_coroutine():
            await asyncio.sleep(0.01) # 短暂延迟
            return "sleep_completed"
        
        manager = AsyncUtils()
        result = manager.run_async(sleep_coroutine())
        assert result == "sleep_completed"
    
    def test_run_async_exception_handling(self):
        """测试异常处理"""
        async def error_coroutine():
            raise ValueError("Test error")
        
        manager = AsyncUtils()
        with pytest.raises(ValueError, match="Test error"):
            manager.run_async(error_coroutine())
    
    def test_create_task(self):
        """测试创建任务"""
        async def task_coroutine():
            await asyncio.sleep(0.01)
            return "task_completed"
        
        manager = AsyncUtils()
        future = manager.create_task(task_coroutine())
        result = future.result(timeout=1)  # 设置超时
        assert result == "task_completed"
    
    def test_run_async_function(self):
        """测试便捷函数 run_async"""
        async def test_coroutine():
            return "run_async_test"
        
        result = run_async(test_coroutine())
        assert result == "run_async_test"


class TestAsyncContextManager:
    """测试 AsyncContextManager 类"""
    
    class TestContextManagerClass(AsyncContextManager):
        """测试用的上下文管理器"""
        def __init__(self):
            super().__init__()
            self.cleanup_called = False
        
        async def cleanup(self):
            self.cleanup_called = True
    
    async def test_async_context_manager(self):
        """测试异步上下文管理器"""
        context_manager = self.TestContextManagerClass()
        
        async with context_manager:
            # 在上下文中做一些操作
            pass
        
        # 确保cleanup被调用
        assert context_manager.cleanup_called


class TestAsyncLock:
    """测试 AsyncLock 类"""
    
    def test_async_lock_basic_usage(self):
        """测试异步锁基本用法"""
        async def test_lock():
            lock = AsyncLock()
            
            async with lock:
                # 在锁内做一些操作
                pass
            
            # 测试直接使用 acquire/release
            await lock.acquire()
            await lock.release()
        
        run_async(test_lock())
    
    def test_async_lock_concurrent_access(self):
        """测试异步锁并发访问"""
        shared_resource = 0
        lock = AsyncLock()
        
        async def modify_resource():
            nonlocal shared_resource
            async with lock:
                current_value = shared_resource
                await asyncio.sleep(0.01)  # 模拟一些处理时间
                shared_resource = current_value + 1
        
        async def run_concurrent_modifications():
            tasks = [modify_resource() for _ in range(5)]
            await asyncio.gather(*tasks)
            return shared_resource
        
        final_value = run_async(run_concurrent_modifications())
        assert final_value == 5  # 确保没有竞态条件


if __name__ == "__main__":
    pytest.main([__file__])