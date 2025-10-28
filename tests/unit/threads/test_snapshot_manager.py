"""Thread快照管理器单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.application.threads.snapshot_manager import SnapshotManager


class TestSnapshotManager:
    """SnapshotManager测试类"""
    
    @pytest.fixture
    def thread_manager_mock(self):
        """创建ThreadManager mock"""
        mock = AsyncMock()
        mock.get_thread_info.return_value = {
            "thread_id": "thread_123",
            "graph_id": "test_graph",
            "created_at": datetime.now().isoformat(),
            "snapshots": []
        }
        mock.thread_exists.return_value = True
        mock.update_thread_metadata.return_value = True
        return mock
    
    @pytest.fixture
    def checkpoint_manager_mock(self):
        """创建CheckpointManager mock"""
        mock = AsyncMock()
        mock.list_checkpoints.return_value = [
            {"id": "checkpoint_123", "created_at": datetime.now().isoformat()},
            {"id": "checkpoint_456", "created_at": datetime.now().isoformat()}
        ]
        mock.get_checkpoint.return_value = {
            "id": "checkpoint_123",
            "state_data": {"key": "value"}
        }
        return mock
    
    @pytest.fixture
    def snapshot_manager(self, thread_manager_mock, checkpoint_manager_mock):
        """创建SnapshotManager实例"""
        return SnapshotManager(thread_manager_mock, checkpoint_manager_mock)
    
    @pytest.mark.asyncio
    async def test_create_snapshot_success(self, snapshot_manager, thread_manager_mock, checkpoint_manager_mock):
        """测试成功创建快照"""
        snapshot_id = await snapshot_manager.create_snapshot(
            "thread_123",
            "test_snapshot",
            "Test snapshot description"
        )
        
        assert snapshot_id.startswith("snapshot_")
        thread_manager_mock.update_thread_metadata.assert_called_once()
        checkpoint_manager_mock.list_checkpoints.assert_called_once_with("thread_123")
    
    @pytest.mark.asyncio
    async def test_create_snapshot_thread_not_exists(self, snapshot_manager, thread_manager_mock):
        """测试thread不存在"""
        thread_manager_mock.thread_exists.return_value = False
        
        with pytest.raises(ValueError, match="Thread不存在"):
            await snapshot_manager.create_snapshot("thread_999", "test_snapshot")
    
    @pytest.mark.asyncio
    async def test_restore_snapshot_success(self, snapshot_manager, thread_manager_mock, checkpoint_manager_mock):
        """测试成功恢复快照"""
        # 设置包含快照的thread信息
        thread_manager_mock.get_thread_info.return_value = {
            "thread_id": "thread_123",
            "snapshots": [{
                "snapshot_id": "snapshot_123",
                "checkpoint_ids": ["checkpoint_123"]
            }]
        }
        
        # Mock update_thread_state 返回 True
        thread_manager_mock.update_thread_state.return_value = True
        
        success = await snapshot_manager.restore_snapshot("thread_123", "snapshot_123")
        
        assert success is True
        thread_manager_mock.update_thread_state.assert_called_once()
        thread_manager_mock.update_thread_metadata.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_restore_snapshot_not_found(self, snapshot_manager, thread_manager_mock):
        """测试快照不存在"""
        thread_manager_mock.get_thread_info.return_value = {
            "thread_id": "thread_123",
            "snapshots": []
        }
        
        success = await snapshot_manager.restore_snapshot("thread_123", "snapshot_999")
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_delete_snapshot_success(self, snapshot_manager, thread_manager_mock):
        """测试成功删除快照"""
        thread_manager_mock.list_threads.return_value = [{
            "thread_id": "thread_123",
            "snapshots": [{
                "snapshot_id": "snapshot_123",
                "snapshot_name": "test_snapshot"
            }]
        }]
        
        success = await snapshot_manager.delete_snapshot("snapshot_123")
        
        assert success is True
        thread_manager_mock.update_thread_metadata.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_snapshot_not_found(self, snapshot_manager, thread_manager_mock):
        """测试快照不存在"""
        thread_manager_mock.list_threads.return_value = [{
            "thread_id": "thread_123",
            "snapshots": []
        }]
        
        success = await snapshot_manager.delete_snapshot("snapshot_999")
        
        assert success is False