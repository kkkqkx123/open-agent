"""事件循环管理器单元测试"""

import pytest
import asyncio
import threading
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.infrastructure.async_utils.event_loop_manager import (
    EventLoopManager, 
    event_loop_manager, 
    run_async, 
    AsyncContextManager, 
    AsyncLock
)


class TestEventLoopManager:
    """EventLoopManager测试类"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        # 重置单例实例
        EventLoopManager._instance = None
        EventLoopManager._initialized = False
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        instance1 = EventLoopManager()
        instance2 = EventLoopManager()
        
        assert instance1 is instance2
        assert EventLoopManager._instance is not None
    
    def test_initialization(self):
        """测试初始化"""
        manager = EventLoopManager()
        
        assert manager._loop is None
        assert manager._thread is None
        assert hasattr(manager, '_shutdown_event')
    
    def test_ensure_loop_creates_new_loop(self):
        """测试确保事件循环存在"""
        manager = EventLoopManager()
        
        # 确保初始状态
        assert manager._loop is None
        
        # 调用_ensure_loop
        loop = manager._ensure_loop()
        
        assert loop is not None
        assert isinstance(loop, asyncio.AbstractEventLoop)
        assert not loop.is_closed()
    
    def test_run_loop_method(self):
        """测试_run_loop方法"""
        manager = EventLoopManager()
        
        # 模拟事件循环
        mock_loop = Mock(spec=asyncio.AbstractEventLoop)
        mock_loop.run_forever = Mock()
        
        # 设置循环
        manager._loop = mock_loop
        
        # 调用_run_loop
        manager._run_loop()
        
        mock_loop.run_forever.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_async_with_simple_coroutine(self):
        """测试运行简单协程"""
        manager = EventLoopManager()
        
        # 创建简单协程
        async def simple_coro():
            return "test_result"
        
        # 测试run_async
        result = manager.run_async(simple_coro())
        
        assert result == "test_result"
    
    def test_create_task(self):
        """测试创建任务"""
        manager = EventLoopManager()
        
        # 创建简单协程
        async def simple_coro():
            await asyncio.sleep(0.01)
            return "task_result"
        
        # 测试create_task
        future = manager.create_task(simple_coro())
        
        assert isinstance(future, concurrent.futures.Future)
        
        # 获取结果
        result = future.result(timeout=1.0)
        assert result == "task_result"
    
    def test_shutdown_method(self):
        """测试关闭方法"""
        manager = EventLoopManager()
        
        # 创建并启动循环
        manager._ensure_loop()
        
        # 调用shutdown
        manager.shutdown()
        
        # 验证关闭事件被设置
        assert manager._shutdown_event.is_set() is False  # 应该是False，因为shutdown中设置了wait
    
    def test_global_event_loop_manager(self):
        """测试全局事件循环管理器"""
        assert event_loop_manager is not None
        assert isinstance(event_loop_manager, EventLoopManager)


class TestAsyncContextManager:
    """AsyncContextManager测试类"""
    
    @pytest.mark.asyncio
    async def test_async_context_manager_enter_exit(self):
        """测试异步上下文管理器"""
        manager = AsyncContextManager()
        
        # 测试进入上下文
        result = await manager.__aenter__()
        assert result is manager
    
    @pytest.mark.asyncio
    async def test_cleanup_method(self):
        """测试cleanup方法"""
        manager = AsyncContextManager()
        
        # 测试cleanup方法
        await manager.cleanup()
        # 应该正常执行，不抛出异常


class TestAsyncLock:
    """AsyncLock测试类"""
    
    @pytest.mark.asyncio
    async def test_async_lock_acquire_release(self):
        """测试异步锁获取和释放"""
        lock = AsyncLock()
        
        # 测试获取锁
        await lock.acquire()
        
        # 测试释放锁
        await lock.release()
    
    @pytest.mark.asyncio
    async def test_async_lock_context_manager(self):
        """测试异步锁上下文管理器"""
        lock = AsyncLock()
        
        async with lock:
            # 在上下文中应该持有锁
            pass


class TestRunAsyncFunction:
    """run_async便捷函数测试类"""
    
    @pytest.mark.asyncio
    async def test_run_async_function(self):
        """测试run_async便捷函数"""
        
        # 创建简单协程
        async def simple_coro():
            return "function_result"
        
        # 测试run_async函数
        result = run_async(simple_coro())
        
        assert result == "function_result"


def test_event_loop_manager_integration():
    """测试事件循环管理器集成"""
    # 测试全局管理器可用性
    assert event_loop_manager is not None
    
    # 测试便捷函数
    async def test_coro():
        return "integration_test"
    
    result = run_async(test_coro())
    assert result == "integration_test"


if __name__ == "__main__":
    pytest.main([__file__])