"""Thread快照功能集成测试"""

import pytest
import asyncio
from datetime import datetime

from src.infrastructure.container import get_global_container
from src.domain.threads.interfaces import IThreadManager


class TestThreadSnapshots:
    """Thread快照集成测试"""
    
    @pytest.fixture
    def thread_manager(self):
        """获取ThreadManager实例"""
        return get_global_container().get(IThreadManager)
    
    @pytest.mark.asyncio
    async def test_thread_snapshot_workflow(self, thread_manager):
        """测试完整的thread快照工作流"""
        # 1. 创建thread
        thread_id = await thread_manager.create_thread(
            "test_graph",
            {"test": "snapshot_thread"}
        )
        
        # 2. 更新thread状态
        initial_state = {"step": 1, "data": "initial_state"}
        await thread_manager.update_thread_state(thread_id, initial_state)
        
        # 3. 创建快照
        snapshot_name = "test_snapshot"
        snapshot_id = await thread_manager.create_thread_snapshot(
            thread_id,
            snapshot_name,
            "Test snapshot description"
        )
        
        # 4. 验证快照创建成功
        assert snapshot_id.startswith("snapshot_")
        
        # 5. 更新thread到新状态
        new_state = {"step": 2, "data": "new_state", "additional": "data"}
        await thread_manager.update_thread_state(thread_id, new_state)
        
        # 6. 验证当前状态已更新
        current_state = await thread_manager.get_thread_state(thread_id)
        assert current_state == new_state
        
        # 7. 从快照恢复
        # 注意：在当前实现中，restore_snapshot是SnapshotManager的方法，
        # 但ThreadManager没有直接提供restore_snapshot方法
        # 所以我们验证快照信息被正确保存
        
        thread_info = await thread_manager.get_thread_info(thread_id)
        snapshots = thread_info.get("snapshots", [])
        assert len(snapshots) == 1
        assert snapshots[0]["snapshot_name"] == snapshot_name
        assert snapshots[0]["description"] == "Test snapshot description"
        
        # 8. 清理
        await thread_manager.delete_thread(thread_id)
    
    @pytest.mark.asyncio
    async def test_multiple_snapshots(self, thread_manager):
        """测试多个快照"""
        # 1. 创建thread
        thread_id = await thread_manager.create_thread("test_graph")
        
        # 2. 创建多个状态和快照
        states_and_snapshots = [
            ({"step": 1, "data": "state1"}, "snapshot1"),
            ({"step": 2, "data": "state2"}, "snapshot2"),
            ({"step": 3, "data": "state3"}, "snapshot3")
        ]
        
        for state, snapshot_name in states_and_snapshots:
            await thread_manager.update_thread_state(thread_id, state)
            await thread_manager.create_thread_snapshot(thread_id, snapshot_name)
        
        # 3. 验证所有快照都被保存
        thread_info = await thread_manager.get_thread_info(thread_id)
        snapshots = thread_info.get("snapshots", [])
        assert len(snapshots) == len(states_and_snapshots)
        
        # 4. 验证快照名称
        snapshot_names = [s["snapshot_name"] for s in snapshots]
        expected_names = [name for _, name in states_and_snapshots]
        assert set(snapshot_names) == set(expected_names)
        
        # 5. 清理
        await thread_manager.delete_thread(thread_id)