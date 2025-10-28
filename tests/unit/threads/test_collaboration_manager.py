"""Thread协作管理器单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.application.threads.collaboration_manager import CollaborationManager


class TestCollaborationManager:
    """CollaborationManager测试类"""
    
    @pytest.fixture
    def thread_manager_mock(self):
        """创建ThreadManager mock"""
        mock = AsyncMock()
        mock.thread_exists.return_value = True
        mock.get_thread_state.return_value = {"key": "value"}
        mock.update_thread_state.return_value = True
        mock.get_thread_info.return_value = {
            "thread_id": "thread_123",
            "collaborations": []
        }
        mock.update_thread_metadata.return_value = True
        return mock
    
    @pytest.fixture
    def checkpoint_manager_mock(self):
        """创建CheckpointManager mock"""
        mock = AsyncMock()
        mock.get_checkpoint.return_value = {
            "id": "checkpoint_123",
            "state_data": {"key": "value"}
        }
        return mock
    
    @pytest.fixture
    def collaboration_manager(self, thread_manager_mock, checkpoint_manager_mock):
        """创建CollaborationManager实例"""
        return CollaborationManager(thread_manager_mock, checkpoint_manager_mock)
    
    @pytest.mark.asyncio
    async def test_share_thread_state_read_only(self, collaboration_manager, thread_manager_mock, checkpoint_manager_mock):
        """测试只读共享thread状态"""
        success = await collaboration_manager.share_thread_state(
            "thread_123",
            "thread_456",
            "checkpoint_123",
            {"read": True, "write": False}
        )
        
        assert success is True
        thread_manager_mock.update_thread_state.assert_not_called()
        thread_manager_mock.update_thread_metadata.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_share_thread_state_write(self, collaboration_manager, thread_manager_mock, checkpoint_manager_mock):
        """测试写入共享thread状态"""
        success = await collaboration_manager.share_thread_state(
            "thread_123",
            "thread_456",
            "checkpoint_123",
            {"read": True, "write": True}
        )
        
        assert success is True
        thread_manager_mock.update_thread_state.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_share_thread_state_source_not_exists(self, collaboration_manager, thread_manager_mock):
        """测试源thread不存在"""
        thread_manager_mock.thread_exists.side_effect = [False, True]
        
        success = await collaboration_manager.share_thread_state(
            "thread_999",
            "thread_456",
            "checkpoint_123"
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_share_thread_state_target_not_exists(self, collaboration_manager, thread_manager_mock):
        """测试目标thread不存在"""
        thread_manager_mock.thread_exists.side_effect = [True, False]
        
        success = await collaboration_manager.share_thread_state(
            "thread_123",
            "thread_999",
            "checkpoint_123"
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_create_shared_session_success(self, collaboration_manager, thread_manager_mock):
        """测试成功创建共享会话"""
        thread_manager_mock.get_thread_info.return_value = {
            "thread_id": "thread_123",
            "collaborations": []
        }
        
        collaboration_id = await collaboration_manager.create_shared_session(
            ["thread_123", "thread_456"],
            {"permissions": {"read": True, "write": True}}
        )
        
        assert collaboration_id.startswith("collab_")
        assert thread_manager_mock.update_thread_metadata.call_count == 2
    
    @pytest.mark.asyncio
    async def test_create_shared_session_thread_not_exists(self, collaboration_manager, thread_manager_mock):
        """测试thread不存在"""
        thread_manager_mock.thread_exists.return_value = False
        
        with pytest.raises(ValueError, match="Thread不存在"):
            await collaboration_manager.create_shared_session(["thread_999"], {})
    
    @pytest.mark.asyncio
    async def test_sync_thread_states_bidirectional(self, collaboration_manager, thread_manager_mock):
        """测试双向同步thread状态"""
        thread_manager_mock.get_thread_state.side_effect = [
            {"key1": "value1"},
            {"key2": "value2"}
        ]
        
        success = await collaboration_manager.sync_thread_states(
            ["thread_123", "thread_456"],
            "bidirectional"
        )
        
        assert success is True
        assert thread_manager_mock.update_thread_state.call_count == 2
    
    @pytest.mark.asyncio
    async def test_sync_thread_states_master_slave(self, collaboration_manager, thread_manager_mock):
        """测试主从同步thread状态"""
        thread_manager_mock.get_thread_state.side_effect = [
            {"key1": "value1"},
            {"key2": "value2"}
        ]
        
        success = await collaboration_manager.sync_thread_states(
            ["thread_123", "thread_456"],
            "master_slave"
        )
        
        assert success is True
        thread_manager_mock.update_thread_state.assert_called_once_with(
            "thread_456", {"key1": "value1"}
        )
    
    @pytest.mark.asyncio
    async def test_sync_thread_states_insufficient_threads(self, collaboration_manager):
        """测试thread数量不足"""
        success = await collaboration_manager.sync_thread_states(["thread_123"])
        
        assert success is False