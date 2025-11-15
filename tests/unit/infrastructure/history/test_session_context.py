"""SessionContext单元测试"""

import pytest
from unittest.mock import patch
import threading
import time

from infrastructure.history.session_context import (
    SessionContext,
    get_current_session,
    set_current_session,
    clear_current_session,
    session_context,
    generate_session_id,
    SessionContextManager,
    get_session_context_manager
)


class TestSessionContext:
    """SessionContext测试"""

    def test_init(self) -> None:
        """测试初始化"""
        context = SessionContext()
        
        assert hasattr(context, '_local')
        assert hasattr(context._local, 'session_stack')
        assert context._local.session_stack == []

    def test_set_current_session(self) -> None:
        """测试设置当前会话ID"""
        context = SessionContext()
        
        context.set_current_session("session-1")
        
        assert context.get_current_session() == "session-1"
        assert context._local.session_stack == ["session-1"]

    def test_set_current_session_multiple_times(self) -> None:
        """测试多次设置当前会话ID"""
        context = SessionContext()
        
        context.set_current_session("session-1")
        context.set_current_session("session-2")
        
        # 应该保留所有会话ID，最新的在栈顶
        assert context.get_current_session() == "session-2"
        assert context._local.session_stack == ["session-1", "session-2"]

    def test_set_current_session_duplicate(self) -> None:
        """测试设置重复的会话ID"""
        context = SessionContext()
        
        context.set_current_session("session-1")
        context.set_current_session("session-2")
        context.set_current_session("session-1")  # 重复设置
        
        # 应该移除旧的并添加到栈顶
        assert context.get_current_session() == "session-1"
        assert context._local.session_stack == ["session-2", "session-1"]

    def test_get_current_session_empty(self) -> None:
        """测试获取当前会话ID（空栈）"""
        context = SessionContext()
        
        assert context.get_current_session() is None

    def test_get_current_session_with_stack(self) -> None:
        """测试获取当前会话ID（有栈）"""
        context = SessionContext()
        
        context.set_current_session("session-1")
        context.set_current_session("session-2")
        
        assert context.get_current_session() == "session-2"

    def test_clear_current_session(self) -> None:
        """测试清除当前会话ID"""
        context = SessionContext()
        
        context.set_current_session("session-1")
        context.clear_current_session()
        
        assert context.get_current_session() is None
        assert context._local.session_stack == []

    def test_clear_current_session_empty(self) -> None:
        """测试清除当前会话ID（空栈）"""
        context = SessionContext()
        
        # 不应该抛出异常
        context.clear_current_session()
        
        assert context.get_current_session() is None

    def test_session_context_manager(self) -> None:
        """测试会话上下文管理器"""
        context = SessionContext()
        
        # 设置初始会话
        context.set_current_session("initial-session")
        
        with context.session_context("temp-session"):
            assert context.get_current_session() == "temp-session"
        
        # 应该恢复到初始会话
        assert context.get_current_session() == "initial-session"

    def test_session_context_manager_nested(self) -> None:
        """测试嵌套会话上下文管理器"""
        context = SessionContext()
        
        with context.session_context("outer-session"):
            assert context.get_current_session() == "outer-session"
            
            with context.session_context("inner-session"):
                assert context.get_current_session() == "inner-session"
            
            # 应该恢复到外层会话
            assert context.get_current_session() == "outer-session"
        
        # 应该恢复到None
        assert context.get_current_session() is None

    def test_session_context_manager_exception(self) -> None:
        """测试会话上下文管理器异常处理"""
        context = SessionContext()
        
        context.set_current_session("initial-session")
        
        try:
            with context.session_context("temp-session"):
                assert context.get_current_session() == "temp-session"
                raise ValueError("测试异常")
        except ValueError:
            pass
        
        # 即使有异常，也应该恢复到初始会话
        assert context.get_current_session() == "initial-session"

    def test_generate_session_id(self) -> None:
        """测试生成会话ID"""
        context = SessionContext()
        
        with patch('src.application.history.session_context.uuid') as mock_uuid:
            mock_uuid.uuid4.return_value = "test-uuid"
            
            session_id = context.generate_session_id()
            
            assert session_id == "test-uuid"
            mock_uuid.uuid4.assert_called_once()

    def test_thread_safety(self) -> None:
        """测试线程安全性"""
        context = SessionContext()
        results = {}
        
        def worker(thread_id):
            context.set_current_session(f"session-{thread_id}")
            time.sleep(0.1)  # 模拟一些工作
            results[thread_id] = context.get_current_session()
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 每个线程应该有自己的会话ID
        for i in range(5):
            assert results[i] == f"session-{i}"


class TestGlobalFunctions:
    """全局函数测试"""

    def test_get_current_session_global(self) -> None:
        """测试全局获取当前会话ID"""
        assert get_current_session() is None

    def test_set_current_session_global(self) -> None:
        """测试全局设置当前会话ID"""
        set_current_session("global-session")
        
        assert get_current_session() == "global-session"
        
        # 清理
        clear_current_session()

    def test_clear_current_session_global(self) -> None:
        """测试全局清除当前会话ID"""
        set_current_session("global-session")
        clear_current_session()
        
        assert get_current_session() is None

    def test_session_context_global(self) -> None:
        """测试全局会话上下文管理器"""
        assert get_current_session() is None
        
        with session_context("global-temp-session"):
            assert get_current_session() == "global-temp-session"
        
        assert get_current_session() is None

    def test_generate_session_id_global(self) -> None:
        """测试全局生成会话ID"""
        with patch('src.application.history.session_context.uuid') as mock_uuid:
            mock_uuid.uuid4.return_value = "global-test-uuid"
            
            session_id = generate_session_id()
            
            assert session_id == "global-test-uuid"
            mock_uuid.uuid4.assert_called_once()


class TestSessionContextManager:
    """SessionContextManager测试"""

    def test_init(self) -> None:
        """测试初始化"""
        manager = SessionContextManager()
        
        assert manager._sessions == {}

    def test_create_session(self) -> None:
        """测试创建会话"""
        manager = SessionContextManager()
        
        with patch('src.application.history.session_context.generate_session_id', return_value="test-session-id"):
            session_id = manager.create_session({"key": "value"})
            
            assert session_id == "test-session-id"
            assert session_id in manager._sessions
            assert manager._sessions[session_id]["metadata"] == {"key": "value"}
            assert manager._sessions[session_id]["active"] is True

    def test_create_session_without_metadata(self) -> None:
        """测试创建会话（无元数据）"""
        manager = SessionContextManager()
        
        with patch('src.application.history.session_context.generate_session_id', return_value="test-session-id"):
            session_id = manager.create_session()
            
            assert session_id == "test-session-id"
            assert manager._sessions[session_id]["metadata"] == {}

    def test_get_session_metadata(self) -> None:
        """测试获取会话元数据"""
        manager = SessionContextManager()
        metadata = {"key": "value"}
        
        with patch('src.application.history.session_context.generate_session_id', return_value="test-session-id"):
            session_id = manager.create_session(metadata)
            
            result = manager.get_session_metadata(session_id)
            
            assert result == metadata

    def test_get_session_metadata_nonexistent(self) -> None:
        """测试获取不存在会话的元数据"""
        manager = SessionContextManager()
        
        result = manager.get_session_metadata("nonexistent-session")
        
        assert result is None

    def test_update_session_metadata(self) -> None:
        """测试更新会话元数据"""
        manager = SessionContextManager()
        initial_metadata = {"key1": "value1"}
        new_metadata = {"key2": "value2"}
        
        with patch('src.application.history.session_context.generate_session_id', return_value="test-session-id"):
            session_id = manager.create_session(initial_metadata)
            
            result = manager.update_session_metadata(session_id, new_metadata)
            
            assert result is True
            assert manager._sessions[session_id]["metadata"] == {
                "key1": "value1",
                "key2": "value2"
            }

    def test_update_session_metadata_nonexistent(self) -> None:
        """测试更新不存在会话的元数据"""
        manager = SessionContextManager()
        
        result = manager.update_session_metadata("nonexistent-session", {"key": "value"})
        
        assert result is False

    def test_deactivate_session(self) -> None:
        """测试停用会话"""
        manager = SessionContextManager()
        
        with patch('src.application.history.session_context.generate_session_id', return_value="test-session-id"):
            session_id = manager.create_session()
            
            result = manager.deactivate_session(session_id)
            
            assert result is True
            assert manager._sessions[session_id]["active"] is False

    def test_deactivate_session_nonexistent(self) -> None:
        """测试停用不存在会话"""
        manager = SessionContextManager()
        
        result = manager.deactivate_session("nonexistent-session")
        
        assert result is False

    def test_is_session_active(self) -> None:
        """测试检查会话是否活跃"""
        manager = SessionContextManager()
        
        with patch('src.application.history.session_context.generate_session_id', return_value="test-session-id"):
            session_id = manager.create_session()
            
            # 默认应该是活跃的
            assert manager.is_session_active(session_id) is True
            
            # 停用后应该不活跃
            manager.deactivate_session(session_id)
            assert manager.is_session_active(session_id) is False

    def test_is_session_active_nonexistent(self) -> None:
        """测试检查不存在会话是否活跃"""
        manager = SessionContextManager()
        
        assert manager.is_session_active("nonexistent-session") is False

    def test_get_active_sessions(self) -> None:
        """测试获取所有活跃会话"""
        manager = SessionContextManager()
        
        with patch('src.application.history.session_context.generate_session_id') as mock_uuid:
            mock_uuid.side_effect = ["session-1", "session-2", "session-3"]
            
            session1 = manager.create_session()
            session2 = manager.create_session()
            session3 = manager.create_session()
            
            # 停用一个会话
            manager.deactivate_session(session2)
            
            active_sessions = manager.get_active_sessions()
            
            assert len(active_sessions) == 2
            assert session1 in active_sessions
            assert session3 in active_sessions
            assert session2 not in active_sessions

    def test_get_active_sessions_empty(self) -> None:
        """测试获取所有活跃会话（空）"""
        manager = SessionContextManager()
        
        active_sessions = manager.get_active_sessions()
        
        assert active_sessions == {}


class TestGlobalSessionContextManager:
    """全局会话上下文管理器测试"""

    def test_get_session_context_manager_global(self) -> None:
        """测试获取全局会话上下文管理器"""
        manager = get_session_context_manager()
        
        assert isinstance(manager, SessionContextManager)
        
        # 应该返回同一个实例
        manager2 = get_session_context_manager()
        assert manager is manager2