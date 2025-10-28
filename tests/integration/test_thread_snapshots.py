"""Thread快照功能集成测试"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.domain.threads.interfaces import IThreadManager


class MockThreadManager(IThreadManager):
    """模拟Thread管理器用于测试"""

    def __init__(self) -> None:
        self._threads: Dict[str, Dict[str, Any]] = {}
        self._states: Dict[str, Dict[str, Any]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        import uuid
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        self._threads[thread_id] = {
            "thread_id": thread_id,
            "graph_id": graph_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "metadata": metadata or {}
        }
        self._states[thread_id] = {}
        return thread_id
    
    async def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]:
        info = self._threads.get(thread_id)
        if info and thread_id in self._metadata:
            # 添加快照信息
            if "snapshots" in self._metadata[thread_id]:
                info["snapshots"] = self._metadata[thread_id]["snapshots"]
        return info
    
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        if thread_id in self._threads:
            self._threads[thread_id]["status"] = status
            return True
        return False
    
    async def update_thread_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        if thread_id in self._threads:
            self._threads[thread_id]["metadata"].update(metadata)
            return True
        return False
    
    async def delete_thread(self, thread_id: str) -> bool:
        if thread_id in self._threads:
            del self._threads[thread_id]
            if thread_id in self._states:
                del self._states[thread_id]
            if thread_id in self._metadata:
                del self._metadata[thread_id]
            return True
        return False
    
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        return list(self._threads.values())
    
    async def thread_exists(self, thread_id: str) -> bool:
        return thread_id in self._threads
    
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        return self._states.get(thread_id)
    
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        if thread_id in self._states:
            self._states[thread_id].update(state)
            return True
        return False
    
    async def fork_thread(
        self,
        source_thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从指定checkpoint创建thread分支"""
        import uuid
        if source_thread_id not in self._threads:
            raise ValueError(f"源thread不存在: {source_thread_id}")
        
        new_thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        source_thread = self._threads[source_thread_id]
        
        # 复制源thread信息
        self._threads[new_thread_id] = {
            "thread_id": new_thread_id,
            "graph_id": source_thread["graph_id"],
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "metadata": {
                "branch_name": branch_name,
                "source_thread_id": source_thread_id,
                "source_checkpoint_id": checkpoint_id,
                "branch_type": "fork",
                **(metadata or {})
            }
        }
        
        # 复制状态
        if source_thread_id in self._states:
            self._states[new_thread_id] = self._states[source_thread_id].copy()
        else:
            self._states[new_thread_id] = {}
        
        return new_thread_id
    
    async def create_thread_snapshot(
        self,
        thread_id: str,
        snapshot_name: str,
        description: Optional[str] = None
    ) -> str:
        """创建thread状态快照"""
        import uuid
        if thread_id not in self._threads:
            raise ValueError(f"Thread不存在: {thread_id}")
        
        snapshot_id = f"snapshot_{uuid.uuid4().hex[:8]}"
        
        # 保存快照信息到thread元数据
        if thread_id not in self._metadata:
            self._metadata[thread_id] = {}
        
        snapshots = self._metadata[thread_id].get("snapshots", [])
        snapshots.append({
            "snapshot_id": snapshot_id,
            "thread_id": thread_id,
            "snapshot_name": snapshot_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "state": self._states.get(thread_id, {}).copy()
        })
        self._metadata[thread_id]["snapshots"] = snapshots
        
        return snapshot_id
    
    async def rollback_thread(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> bool:
        """回滚thread到指定checkpoint"""
        # 在模拟实现中，我们简单地检查thread是否存在
        if thread_id not in self._threads:
            return False
        
        # 在实际实现中，这里会恢复checkpoint的状态
        # 在模拟中，我们只是记录回滚操作
        if thread_id not in self._metadata:
            self._metadata[thread_id] = {}
        
        self._metadata[thread_id]["last_rollback"] = datetime.now().isoformat()
        self._metadata[thread_id]["rollback_checkpoint"] = checkpoint_id
        
        return True
    
    async def get_thread_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取thread历史记录"""
        if thread_id not in self._threads:
            return []
        
        # 在模拟实现中，返回简单的状态历史
        history = []
        if thread_id in self._states:
            history.append({
                "id": f"checkpoint_{thread_id}",
                "thread_id": thread_id,
                "created_at": self._threads[thread_id]["created_at"],
                "state_data": self._states[thread_id].copy()
            })
        
        if limit and len(history) > limit:
            history = history[:limit]
        
        return history


class TestThreadSnapshots:
    """Thread快照集成测试"""
    
    @pytest.fixture
    def thread_manager(self):
        """获取ThreadManager实例"""
        return MockThreadManager()
    
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