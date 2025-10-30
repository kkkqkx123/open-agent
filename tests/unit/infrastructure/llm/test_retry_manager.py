"""重试管理器单元测试"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from concurrent.futures import TimeoutError

from src.infrastructure.llm.retry.retry_manager import (
    RetryManager,
    get_global_retry_manager,
    set_global_retry_manager,
    retry
)
from src.infrastructure.llm.retry.retry_config import RetryConfig
from src.infrastructure.llm.retry.interfaces import IRetryLogger


class TestRetryManager:
    """重试管理器测试"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return RetryConfig(
            enabled=True,
            max_attempts=3,
            base_delay=0.1,  # 减少测试时间
            max_delay=1.0,
            jitter=False
        )
    
    @pytest.fixture
    def logger(self):
        """创建模拟日志记录器"""
        return MagicMock(spec=IRetryLogger)
    
    @pytest.fixture
    def manager(self, config, logger):
        """创建重试管理器"""
        return RetryManager(config, logger)
    
    def test_execute_with_retry_success_first_attempt(self, manager):
        """测试第一次尝试成功"""
        func = MagicMock(return_value="success")
        
        result = manager.execute_with_retry(func, "arg1", kwarg1="value1")
        
        assert result == "success"
        func.assert_called_once_with("arg1", kwarg1="value1")
        assert len(manager._sessions) == 1
        assert manager._sessions[0].success == True
        assert manager._sessions[0].get_total_attempts() == 1
    
    def test_execute_with_retry_success_after_retry(self, manager):
        """测试重试后成功"""
        func = MagicMock(side_effect=[Exception("error"), "success"])
        
        result = manager.execute_with_retry(func)
        
        assert result == "success"
        assert func.call_count == 2
        assert len(manager._sessions) == 1
        assert manager._sessions[0].success == True
        assert manager._sessions[0].get_total_attempts() == 2
    
    def test_execute_with_retry_all_attempts_fail(self, manager):
        """测试所有尝试都失败"""
        func = MagicMock(side_effect=Exception("persistent error"))
        
        with pytest.raises(Exception, match="persistent error"):
            manager.execute_with_retry(func)
        
        assert func.call_count == 3  # max_attempts
        assert len(manager._sessions) == 1
        assert manager._sessions[0].success == False
        assert manager._sessions[0].get_total_attempts() == 3
    
    def test_execute_with_retry_disabled(self, manager):
        """测试重试禁用时直接执行"""
        manager.config.enabled = False
        func = MagicMock(side_effect=Exception("error"))
        
        with pytest.raises(Exception, match="error"):
            manager.execute_with_retry(func)
        
        func.assert_called_once()
        assert len(manager._sessions) == 0  # 不记录会话
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_async_success_first_attempt(self, manager):
        """测试异步函数第一次尝试成功"""
        func = AsyncMock(return_value="success")
        
        result = await manager.execute_with_retry_async(func, "arg1", kwarg1="value1")
        
        assert result == "success"
        func.assert_called_once_with("arg1", kwarg1="value1")
        assert len(manager._sessions) == 1
        assert manager._sessions[0].success == True
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_async_success_after_retry(self, manager):
        """测试异步函数重试后成功"""
        func = AsyncMock(side_effect=[Exception("error"), "success"])
        
        result = await manager.execute_with_retry_async(func)
        
        assert result == "success"
        assert func.call_count == 2
        assert len(manager._sessions) == 1
        assert manager._sessions[0].success == True
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_async_all_attempts_fail(self, manager):
        """测试异步函数所有尝试都失败"""
        func = AsyncMock(side_effect=Exception("persistent error"))
        
        with pytest.raises(Exception, match="persistent error"):
            await manager.execute_with_retry_async(func)
        
        assert func.call_count == 3
        assert len(manager._sessions) == 1
        assert manager._sessions[0].success == False
    
    def test_execute_with_timeout_success(self, manager):
        """测试带超时的成功执行"""
        manager.config.per_attempt_timeout = 1.0
        func = MagicMock(return_value="success")
        
        result = manager.execute_with_retry(func)
        
        assert result == "success"
    
    def test_execute_with_timeout_failure(self, manager):
        """测试带超时的失败执行"""
        manager.config.per_attempt_timeout = 0.1
        
        def slow_func():
            time.sleep(0.2)  # 超过超时时间
            return "success"
        
        with pytest.raises(TimeoutError):
            manager.execute_with_retry(slow_func)
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_async_success(self, manager):
        """测试异步函数带超时的成功执行"""
        manager.config.per_attempt_timeout = 1.0
        func = AsyncMock(return_value="success")
        
        result = await manager.execute_with_retry_async(func)
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_async_failure(self, manager):
        """测试异步函数带超时的失败执行"""
        manager.config.per_attempt_timeout = 0.1
        
        async def slow_func():
            await asyncio.sleep(0.2)  # 超过超时时间
            return "success"
        
        with pytest.raises(TimeoutError):
            await manager.execute_with_retry_async(slow_func)
    
    def test_retry_decorator_sync_function(self, manager):
        """测试同步函数装饰器"""
        func = MagicMock(side_effect=[Exception("error"), "success"])
        
        decorated_func = manager.retry(func)
        result = decorated_func()
        
        assert result == "success"
        assert func.call_count == 2
    
    def test_retry_decorator_async_function(self, manager):
        """测试异步函数装饰器"""
        func = AsyncMock(side_effect=[Exception("error"), "success"])
        
        decorated_func = manager.retry(func)
        
        async def test():
            result = await decorated_func()
            return result
        
        result = asyncio.run(test())
        assert result == "success"
        assert func.call_count == 2
    
    def test_retry_decorator_with_custom_config(self, manager):
        """测试带自定义配置的装饰器"""
        custom_config = RetryConfig(max_attempts=2, base_delay=0.05)
        func = MagicMock(side_effect=[Exception("error1"), Exception("error2"), "success"])
        
        decorated_func = manager.retry(func, config=custom_config)
        
        with pytest.raises(Exception, match="error2"):
            decorated_func()
        
        # 应该只尝试2次（自定义配置）
        assert func.call_count == 2
    
    def test_retry_decorator_without_function(self, manager):
        """测试不带函数参数的装饰器"""
        custom_config = RetryConfig(max_attempts=2)
        
        decorator = manager.retry(config=custom_config)
        
        func = MagicMock(return_value="success")
        decorated_func = decorator(func)
        
        result = decorated_func()
        
        assert result == "success"
        func.assert_called_once()
    
    def test_get_stats(self, manager):
        """测试获取统计信息"""
        # 模拟一些会话
        from src.infrastructure.llm.retry.retry_config import RetrySession
        
        # 成功会话
        success_session = RetrySession(func_name="test_func1", start_time=123.0)
        success_session.mark_success("result")
        manager._sessions.append(success_session)
        
        # 失败会话
        fail_session = RetrySession(func_name="test_func2", start_time=124.0)
        fail_session.mark_failure(Exception("failed"))
        manager._sessions.append(fail_session)
        
        stats = manager.get_stats()
        
        assert stats["total_sessions"] == 2
        assert "config" in stats
        assert "recent_sessions" in stats
        assert len(stats["recent_sessions"]) == 2
    
    def test_get_sessions_with_limit(self, manager):
        """测试获取限制数量的会话"""
        from src.infrastructure.llm.retry.retry_config import RetrySession
        
        # 添加多个会话
        for i in range(5):
            session = RetrySession(func_name=f"func{i}", start_time=123.0 + i)
            manager._sessions.append(session)
        
        # 获取限制数量的会话
        sessions = manager.get_sessions(limit=3)
        
        assert len(sessions) == 3
        # 应该是最后3个会话
        assert sessions[0].func_name == "func2"
        assert sessions[2].func_name == "func4"
    
    def test_clear_sessions(self, manager):
        """测试清空会话记录"""
        from src.infrastructure.llm.retry.retry_config import RetrySession
        
        # 添加会话
        session = RetrySession(func_name="test_func", start_time=123.0)
        manager._sessions.append(session)
        
        assert len(manager._sessions) == 1
        
        # 清空会话
        manager.clear_sessions()
        
        assert len(manager._sessions) == 0
        assert manager._stats.total_sessions == 0
    
    def test_reset_stats(self, manager):
        """测试重置统计信息"""
        # 添加一些统计数据
        manager._stats.total_sessions = 5
        manager._stats.successful_sessions = 3
        
        manager.reset_stats()
        
        assert manager._stats.total_sessions == 0
        assert manager._stats.successful_sessions == 0
    
    def test_is_enabled(self, manager):
        """测试检查是否启用"""
        assert manager.is_enabled() == True
        
        manager.config.enabled = False
        assert manager.is_enabled() == False
    
    def test_update_config(self, manager):
        """测试更新配置"""
        new_config = RetryConfig(
            enabled=False,
            max_attempts=5,
            base_delay=2.0
        )
        
        manager.update_config(new_config)
        
        assert manager.config == new_config
        assert manager.is_enabled() == False
    
    def test_delay_between_attempts(self, manager):
        """测试尝试之间的延迟"""
        func = MagicMock(side_effect=[Exception("error"), "success"])
        
        start_time = time.time()
        manager.execute_with_retry(func)
        end_time = time.time()
        
        # 应该有延迟（至少0.1秒，因为base_delay=0.1）
        elapsed = end_time - start_time
        assert elapsed >= 0.1
    
    def test_total_timeout(self, manager):
        """测试总超时时间"""
        manager.config.total_timeout = 0.2
        manager.config.base_delay = 0.1
        
        func = MagicMock(side_effect=Exception("error"))
        
        start_time = time.time()
        with pytest.raises(Exception):
            manager.execute_with_retry(func)
        end_time = time.time()
        
        # 应该在总超时时间内停止
        elapsed = end_time - start_time
        assert elapsed < 0.3  # 允许一些误差


class TestGlobalRetryManager:
    """全局重试管理器测试"""
    
    def test_get_global_retry_manager_singleton(self):
        """测试全局重试管理器单例"""
        manager1 = get_global_retry_manager()
        manager2 = get_global_retry_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, RetryManager)
    
    def test_set_global_retry_manager(self):
        """测试设置全局重试管理器"""
        custom_manager = RetryManager(RetryConfig(max_attempts=5))
        
        set_global_retry_manager(custom_manager)
        
        retrieved_manager = get_global_retry_manager()
        assert retrieved_manager is custom_manager
    
    def test_retry_decorator_global(self):
        """测试全局重试装饰器"""
        func = MagicMock(side_effect=[Exception("error"), "success"])
        
        decorated_func = retry()(func)
        result = decorated_func()
        
        assert result == "success"
        assert func.call_count == 2
    
    def test_retry_decorator_global_with_config(self):
        """测试带配置的全局重试装饰器"""
        custom_config = RetryConfig(max_attempts=2)
        func = MagicMock(side_effect=[Exception("error1"), Exception("error2"), "success"])
        
        decorated_func = retry(custom_config)(func)
        
        with pytest.raises(Exception, match="error2"):
            decorated_func()
        
        # 应该只尝试2次
        assert func.call_count == 2