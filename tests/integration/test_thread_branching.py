"""Thread分支功能集成测试"""

import pytest
import asyncio
from datetime import datetime

from src.infrastructure.container import get_global_container

container = get_global_container()
from src.domain.threads.interfaces import IThreadManager
from src.application.checkpoint.interfaces import ICheckpointManager


class TestThreadBranching:
    """Thread分支集成测试"""
    
    @pytest.fixture
    def thread_manager(self):
        """获取ThreadManager实例"""
        return container.get(IThreadManager)
    
    @pytest.fixture
    def checkpoint_manager(self):
        """获取CheckpointManager实例"""
        return container.get(ICheckpointManager)
    
    @pytest.mark.asyncio
    async def test_thread_branching_workflow(self, thread_manager, checkpoint_manager):
        """测试完整的thread分支工作流"""
        # 1. 创建源thread
        source_thread_id = await thread_manager.create_thread(
            "test_graph",
            {"test": "source_thread"}
        )
        
        # 2. 更新thread状态并创建checkpoint
        initial_state = {"step": 1, "data": "initial"}
        await thread_manager.update_thread_state(source_thread_id, initial_state)
        
        # 3. 获取checkpoint ID
        checkpoints = await checkpoint_manager.list_checkpoints(source_thread_id)
        assert len(checkpoints) > 0
        checkpoint_id = checkpoints[0]["id"]
        
        # 4. 创建分支
        branch_name = "test_branch"
        new_thread_id = await thread_manager.fork_thread(
            source_thread_id,
            checkpoint_id,
            branch_name,
            {"test": "branch_metadata"}
        )
        
        # 5. 验证分支创建成功
        assert new_thread_id != source_thread_id
        
        # 6. 验证分支状态与源thread相同
        branch_state = await thread_manager.get_thread_state(new_thread_id)
        assert branch_state == initial_state
        
        # 7. 验证分支元数据
        branch_info = await thread_manager.get_thread_info(new_thread_id)
        assert branch_info["branch_name"] == branch_name
        assert branch_info["source_thread_id"] == source_thread_id
        assert branch_info["source_checkpoint_id"] == checkpoint_id
        
        # 8. 清理
        await thread_manager.delete_thread(source_thread_id)
        await thread_manager.delete_thread(new_thread_id)
    
    @pytest.mark.asyncio
    async def test_thread_branch_history(self, thread_manager, checkpoint_manager):
        """测试thread分支历史记录"""
        # 1. 创建thread
        thread_id = await thread_manager.create_thread("test_graph")
        
        # 2. 创建多个状态
        states = [
            {"step": 1, "data": "state1"},
            {"step": 2, "data": "state2"},
            {"step": 3, "data": "state3"}
        ]
        
        for state in states:
            await thread_manager.update_thread_state(thread_id, state)
        
        # 3. 获取历史记录
        history = await thread_manager.get_thread_history(thread_id)
        
        # 4. 验证历史记录
        assert len(history) == len(states)
        
        # 5. 清理
        await thread_manager.delete_thread(thread_id)