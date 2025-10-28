"""Thread分支管理器单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.domain.threads.models import ThreadBranch
from src.application.threads.branch_manager import BranchManager


class TestBranchManager:
    """BranchManager测试类"""
    
    @pytest.fixture
    def thread_manager_mock(self):
        """创建ThreadManager mock"""
        mock = AsyncMock()
        mock.get_thread_info.return_value = {
            "thread_id": "thread_123",
            "graph_id": "test_graph",
            "created_at": datetime.now().isoformat()
        }
        mock.create_thread.return_value = "thread_456"
        mock.update_thread_state.return_value = True
        mock.update_thread_metadata.return_value = True
        mock.thread_exists.return_value = True
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
    def branch_manager(self, thread_manager_mock, checkpoint_manager_mock):
        """创建BranchManager实例"""
        return BranchManager(thread_manager_mock, checkpoint_manager_mock)
    
    @pytest.mark.asyncio
    async def test_fork_thread_success(self, branch_manager, thread_manager_mock, checkpoint_manager_mock):
        """测试成功创建分支"""
        # 执行
        new_thread_id = await branch_manager.fork_thread(
            "thread_123",
            "checkpoint_123",
            "test_branch",
            {"test": "metadata"}
        )
        
        # 验证
        assert new_thread_id == "thread_456"
        thread_manager_mock.create_thread.assert_called_once()
        thread_manager_mock.update_thread_state.assert_called_once()
        checkpoint_manager_mock.get_checkpoint.assert_called_once_with("thread_123", "checkpoint_123")
    
    @pytest.mark.asyncio
    async def test_fork_thread_source_not_exists(self, branch_manager, thread_manager_mock):
        """测试源thread不存在"""
        thread_manager_mock.get_thread_info.return_value = None
        
        with pytest.raises(ValueError, match="源thread不存在"):
            await branch_manager.fork_thread("thread_999", "checkpoint_123", "test_branch")
    
    @pytest.mark.asyncio
    async def test_fork_thread_checkpoint_not_exists(self, branch_manager, checkpoint_manager_mock):
        """测试checkpoint不存在"""
        checkpoint_manager_mock.get_checkpoint.return_value = None
        
        with pytest.raises(ValueError, match="checkpoint不存在"):
            await branch_manager.fork_thread("thread_123", "checkpoint_999", "test_branch")
    
    @pytest.mark.asyncio
    async def test_get_thread_branches(self, branch_manager, thread_manager_mock):
        """测试获取thread分支"""
        thread_manager_mock.get_thread_info.return_value = {
            "thread_id": "thread_123",
            "branch_info": {
                "branch_id": "branch_123",
                "source_thread_id": "thread_000",
                "source_checkpoint_id": "checkpoint_000",
                "branch_name": "test_branch",
                "created_at": datetime.now().isoformat(),
                "metadata": {"test": "metadata"},
                "status": "active"
            }
        }
        
        branches = await branch_manager.get_thread_branches("thread_123")
        
        assert len(branches) == 1
        assert isinstance(branches[0], ThreadBranch)
        assert branches[0].branch_name == "test_branch"
    
    @pytest.mark.asyncio
    async def test_merge_branch_success(self, branch_manager, thread_manager_mock):
        """测试成功合并分支"""
        thread_manager_mock.get_thread_state.return_value = {"key": "value"}
        
        success = await branch_manager.merge_branch("thread_123", "thread_456", "latest")
        
        assert success is True
        thread_manager_mock.update_thread_state.assert_called_once()
        thread_manager_mock.update_thread_metadata.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_merge_branch_target_not_exists(self, branch_manager, thread_manager_mock):
        """测试目标thread不存在"""
        thread_manager_mock.thread_exists.side_effect = [False, True]
        
        success = await branch_manager.merge_branch("thread_999", "thread_456", "latest")
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_merge_branch_source_not_exists(self, branch_manager, thread_manager_mock):
        """测试源thread不存在"""
        thread_manager_mock.thread_exists.side_effect = [True, False]
        
        success = await branch_manager.merge_branch("thread_123", "thread_999", "latest")
        
        assert success is False