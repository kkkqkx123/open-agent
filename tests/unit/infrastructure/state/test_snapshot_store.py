"""测试快照存储功能"""

import pytest
from datetime import datetime
from src.infrastructure.state.snapshot_store import StateSnapshotStore, StateSnapshot


class TestStateSnapshotStore:
    """测试状态快照存储"""
    
    def setup_method(self):
        """设置测试环境"""
        self.store = StateSnapshotStore(storage_backend="memory")
    
    def test_save_and_load_snapshot(self):
        """测试保存和加载快照"""
        # 创建快照
        snapshot = StateSnapshot(
            snapshot_id="test_snapshot_id",
            agent_id="test_agent",
            domain_state={"messages": ["test message"], "data": {"key": "value"}},
            timestamp=datetime.now(),
            snapshot_name="test_snapshot"
        )
        
        # 保存快照
        success = self.store.save_snapshot(snapshot)
        assert success is True
        
        # 加载快照
        loaded_snapshot = self.store.load_snapshot("test_snapshot_id")
        assert loaded_snapshot is not None
        assert loaded_snapshot.agent_id == "test_agent"
        assert loaded_snapshot.snapshot_name == "test_snapshot"
        assert loaded_snapshot.domain_state["messages"] == ["test message"]
    
    def test_get_snapshots_by_agent(self):
        """测试按Agent获取快照"""
        # 创建多个快照
        snapshot1 = StateSnapshot(
            snapshot_id="snapshot1",
            agent_id="agent1",
            domain_state={"data": "value1"},
            timestamp=datetime.now(),
            snapshot_name="snapshot1"
        )
        
        snapshot2 = StateSnapshot(
            snapshot_id="snapshot2",
            agent_id="agent1",
            domain_state={"data": "value2"},
            timestamp=datetime.now(),
            snapshot_name="snapshot2"
        )
        
        snapshot3 = StateSnapshot(
            snapshot_id="snapshot3",
            agent_id="agent2",
            domain_state={"data": "value3"},
            timestamp=datetime.now(),
            snapshot_name="snapshot3"
        )
        
        # 保存快照
        self.store.save_snapshot(snapshot1)
        self.store.save_snapshot(snapshot2)
        self.store.save_snapshot(snapshot3)
        
        # 获取agent1的快照
        agent1_snapshots = self.store.get_snapshots_by_agent("agent1")
        assert len(agent1_snapshots) == 2
        snapshot_ids = [s.snapshot_id for s in agent1_snapshots]
        assert "snapshot1" in snapshot_ids
        assert "snapshot2" in snapshot_ids
        
        # 获取agent2的快照
        agent2_snapshots = self.store.get_snapshots_by_agent("agent2")
        assert len(agent2_snapshots) == 1
        assert agent2_snapshots[0].snapshot_id == "snapshot3"


if __name__ == "__main__":
    pytest.main([__file__])