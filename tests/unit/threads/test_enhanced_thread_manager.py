"""增强的ThreadManager单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.domain.threads.manager import ThreadManager


class TestEnhancedThreadManager:
    """增强的ThreadManager测试类"""
    
    @pytest.fixture
    def metadata_store_mock(self):
        """创建元数据存储mock"""
        mock = AsyncMock()
        mock.get_metadata.return_value = {
            "thread_id": "thread_123",
            "graph_id": "test_graph",
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        mock.save_metadata.return_value = True
        mock.delete_metadata.return_value = True
        mock.list_threads.return_value = []
        return mock
    
    @pytest.fixture
    def checkpoint_manager_mock(self):
        """创建CheckpointManager mock"""
        mock = AsyncMock()
        mock.get_checkpoint.return_value = {
            "id": "checkpoint_123",
            "state_data": {"key": "value"},
            "created_at": datetime.now().isoformat()
        }
        mock.list_checkpoints.return_value = [
            {"id": "checkpoint_123", "created_at": datetime.now().isoformat()}
        ]
        mock.restore_from_checkpoint.return_value = {"key": "value"}
        return mock
    
    @pytest.fixture
    def thread_manager(self, metadata_store_mock, checkpoint_manager_mock):
        """创建ThreadManager实例"""
        return ThreadManager(metadata_store_mock, checkpoint_manager_mock)
    
    @pytest.mark.asyncio
    async def test_fork_thread_success(self, thread_manager, metadata_store_mock, checkpoint_manager_mock):
        """测试成功创建thread分支"""
        # Mock create_thread to return a specific thread_id
        original_create_thread = thread_manager.create_thread
        thread_manager.create_thread = AsyncMock(return_value="thread_456")
        
        new_thread_id = await thread_manager.fork_thread(
            "thread_123",
            "checkpoint_123",
            "test_branch",
            {"test": "metadata"}
        )
        
        assert new_thread_id == "thread_456"
        thread_manager.create_thread.assert_called_once()
        thread_manager.update_thread_state.assert_called_once()
        checkpoint_manager_mock.get_checkpoint.assert_called_once_with("thread_123", "checkpoint_123")
    
    @pytest.mark.asyncio
    async def test_fork_thread_source_not_exists(self, thread_manager, metadata_store_mock):
        """测试源thread不存在"""
        metadata_store_mock.get_metadata.return_value = None
        
        with pytest.raises(ValueError, match="源thread不存在"):
            await thread_manager.fork_thread("thread_999", "checkpoint_123", "test_branch")
    
    @pytest.mark.asyncio
    async def test_create_thread_snapshot_success(self, thread_manager, metadata_store_mock, checkpoint_manager_mock):
        """测试成功创建thread快照"""
        metadata_store_mock.get_metadata.return_value = {
            "thread_id": "thread_123",
            "graph_id": "test_graph",
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "snapshots": []
        }
        
        snapshot_id = await thread_manager.create_thread_snapshot(
            "thread_123",
            "test_snapshot",
            "Test description"
        )
        
        assert snapshot_id.startswith("snapshot_")
        metadata_store_mock.save_metadata.assert_called_once()
        checkpoint_manager_mock.list_checkpoints.assert_called_once_with("thread_123")
    
    @pytest.mark.asyncio
    async def test_rollback_thread_success(self, thread_manager, checkpoint_manager_mock, metadata_store_mock):
        """测试成功回滚thread"""
        success = await thread_manager.rollback_thread("thread_123", "checkpoint_123")
        
        assert success is True
        checkpoint_manager_mock.restore_from_checkpoint.assert_called_once_with("thread_123", "checkpoint_123")
        metadata_store_mock.update_metadata.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rollback_thread_checkpoint_not_exists(self, thread_manager, checkpoint_manager_mock):
        """测试checkpoint不存在"""
        checkpoint_manager_mock.get_checkpoint.return_value = None
        
        success = await thread_manager.rollback_thread("thread_123", "checkpoint_999")
        
        assert success is False
        checkpoint_manager_mock.restore_from_checkpoint.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_thread_history_success(self, thread_manager, checkpoint_manager_mock):
        """测试成功获取thread历史"""
        history = await thread_manager.get_thread_history("thread_123", limit=10)
        
        assert len(history) == 1
        assert history[0]["id"] == "checkpoint_123"
        checkpoint_manager_mock.list_checkpoints.assert_called_once_with("thread_123")
    
    @pytest.mark.asyncio
    async def test_get_thread_history_thread_not_exists(self, thread_manager, metadata_store_mock):
        """测试thread不存在时获取历史"""
        metadata_store_mock.get_metadata.return_value = None
        
        history = await thread_manager.get_thread_history("thread_999")
        
        assert history == []