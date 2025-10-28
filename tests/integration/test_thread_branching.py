"""Thread分支功能集成测试"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.domain.threads.interfaces import IThreadManager
from src.application.checkpoint.interfaces import ICheckpointManager
from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore
from src.application.checkpoint.manager import CheckpointManager
from src.domain.checkpoint.config import CheckpointConfig
from src.infrastructure.threads.metadata_store import MemoryThreadMetadataStore


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
        if info:
            # 添加分支信息
            if "branch_name" in info.get("metadata", {}):
                info["branch_name"] = info["metadata"]["branch_name"]
            if "source_thread_id" in info.get("metadata", {}):
                info["source_thread_id"] = info["metadata"]["source_thread_id"]
            if "source_checkpoint_id" in info.get("metadata", {}):
                info["source_checkpoint_id"] = info["metadata"]["source_checkpoint_id"]
            if "snapshots" in self._metadata.get(thread_id, {}):
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
            # 记录状态历史
            if thread_id not in self._metadata:
                self._metadata[thread_id] = {}
            history = self._metadata[thread_id].get("state_history", [])
            history.append({
                "timestamp": datetime.now().isoformat(),
                "state": state.copy()
            })
            self._metadata[thread_id]["state_history"] = history
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
        
        # 返回状态历史
        history = []
        if thread_id in self._metadata and "state_history" in self._metadata[thread_id]:
            state_history = self._metadata[thread_id]["state_history"]
            for i, state_record in enumerate(state_history):
                history.append({
                    "id": f"checkpoint_{thread_id}_{i}",
                    "thread_id": thread_id,
                    "created_at": state_record["timestamp"],
                    "state_data": state_record["state"]
                })
        
        if limit and len(history) > limit:
            history = history[:limit]
        
        return history


class TestThreadBranching:
    """Thread分支集成测试"""
    
    @pytest.fixture
    def thread_manager(self):
        """获取ThreadManager实例"""
        return MockThreadManager()
    
    @pytest.fixture
    def checkpoint_manager(self):
        """获取CheckpointManager实例"""
        checkpoint_store = MemoryCheckpointStore()
        config = CheckpointConfig(
            enabled=True,
            storage_type="memory",
            auto_save=True,
            save_interval=1,
            max_checkpoints=100
        )
        return CheckpointManager(checkpoint_store, config)
    
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
        
        # 3. 使用模拟的checkpoint ID（在真实实现中，这会由checkpoint_manager创建）
        checkpoint_id = f"checkpoint_{source_thread_id}_0"
        
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