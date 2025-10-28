"""Thread回滚功能集成测试"""

import pytest
import asyncio
from datetime import datetime

from src.infrastructure.container import get_global_container

container = get_global_container()
from src.domain.threads.interfaces import IThreadManager
from src.application.checkpoint.interfaces import ICheckpointManager


class TestThreadRollback:
    """Thread回滚集成测试"""
    
    @pytest.fixture
    def thread_manager(self):
        """获取ThreadManager实例"""
        return container.get(IThreadManager)
    
    @pytest.fixture
    def checkpoint_manager(self):
        """获取CheckpointManager实例"""
        return container.get(ICheckpointManager)
    
    @pytest.mark.asyncio
    async def test_thread_rollback_workflow(self, thread_manager, checkpoint_manager):
        """测试完整的thread回滚工作流"""
        # 1. 创建thread
        thread_id = await thread_manager.create_thread(
            "test_graph",
            {"test": "rollback_thread"}
        )
        
        # 2. 创建初始状态
        initial_state = {"step": 1, "data": "initial"}
        await thread_manager.update_thread_state(thread_id, initial_state)
        
        # 3. 获取初始checkpoint
        checkpoints = await checkpoint_manager.list_checkpoints(thread_id)
        assert len(checkpoints) > 0
        initial_checkpoint_id = checkpoints[0]["id"]
        
        # 4. 更新到新状态
        new_state = {"step": 2, "data": "new_state", "additional": "data"}
        await thread_manager.update_thread_state(thread_id, new_state)
        
        # 5. 验证当前状态
        current_state = await thread_manager.get_thread_state(thread_id)
        assert current_state == new_state
        
        # 6. 回滚到初始状态
        success = await thread_manager.rollback_thread(thread_id, initial_checkpoint_id)
        assert success is True
        
        # 7. 验证回滚后的状态
        rolled_back_state = await thread_manager.get_thread_state(thread_id)
        assert rolled_back_state == initial_state
        
        # 8. 验证回滚元数据
        thread_info = await thread_manager.get_thread_info(thread_id)
        assert "last_rollback" in thread_info
        assert thread_info["rollback_checkpoint"] == initial_checkpoint_id
        
        # 9. 清理
        await thread_manager.delete_thread(thread_id)
    
    @pytest.mark.asyncio
    async def test_rollback_nonexistent_checkpoint(self, thread_manager):
        """测试回滚到不存在的checkpoint"""
        # 1. 创建thread
        thread_id = await thread_manager.create_thread("test_graph")
        
        # 2. 尝试回滚到不存在的checkpoint
        success = await thread_manager.rollback_thread(thread_id, "nonexistent_checkpoint")
        assert success is False
        
        # 3. 清理
        await thread_manager.delete_thread(thread_id)
    
    @pytest.mark.asyncio
    async def test_rollback_nonexistent_thread(self, thread_manager):
        """测试回滚不存在的thread"""
        success = await thread_manager.rollback_thread("nonexistent_thread", "any_checkpoint")
        assert success is False