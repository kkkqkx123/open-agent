import unittest
from datetime import datetime
from src.infrastructure.state.interfaces import StateSnapshot, StateHistoryEntry


class TestStateSnapshot(unittest.TestCase):
    """测试StateSnapshot数据类"""

    def test_state_snapshot_creation(self):
        """测试StateSnapshot创建"""
        snapshot_id = "test_snapshot_123"
        agent_id = "test_agent_123"
        domain_state = {"key": "value", "number": 42}
        timestamp = datetime.now()
        snapshot_name = "test_snapshot"
        metadata = {"version": "1.0", "author": "test"}

        snapshot = StateSnapshot(
            snapshot_id=snapshot_id,
            agent_id=agent_id,
            domain_state=domain_state,
            timestamp=timestamp,
            snapshot_name=snapshot_name,
            metadata=metadata
        )

        self.assertEqual(snapshot.snapshot_id, snapshot_id)
        self.assertEqual(snapshot.agent_id, agent_id)
        self.assertEqual(snapshot.domain_state, domain_state)
        self.assertEqual(snapshot.timestamp, timestamp)
        self.assertEqual(snapshot.snapshot_name, snapshot_name)
        self.assertEqual(snapshot.metadata, metadata)
        self.assertIsNone(snapshot.compressed_data)
        self.assertEqual(snapshot.size_bytes, 0)

    def test_state_snapshot_default_values(self):
        """测试StateSnapshot默认值"""
        snapshot = StateSnapshot(
            snapshot_id="test_id",
            agent_id="test_agent",
            domain_state={"key": "value"},
            timestamp=datetime.now(),
            snapshot_name="test"
        )

        # 验证默认值
        self.assertEqual(snapshot.metadata, {})
        self.assertIsNone(snapshot.compressed_data)
        self.assertEqual(snapshot.size_bytes, 0)

    def test_state_snapshot_optional_compressed_data(self):
        """测试StateSnapshot压缩数据字段"""
        compressed_data = b"compressed_data_bytes"
        size_bytes = 100

        snapshot = StateSnapshot(
            snapshot_id="test_id",
            agent_id="test_agent",
            domain_state={"key": "value"},
            timestamp=datetime.now(),
            snapshot_name="test",
            compressed_data=compressed_data,
            size_bytes=size_bytes
        )

        self.assertEqual(snapshot.compressed_data, compressed_data)
        self.assertEqual(snapshot.size_bytes, size_bytes)


class TestStateHistoryEntry(unittest.TestCase):
    """测试StateHistoryEntry数据类"""

    def test_state_history_entry_creation(self):
        """测试StateHistoryEntry创建"""
        history_id = "test_history_123"
        agent_id = "test_agent_123"
        timestamp = datetime.now()
        action = "test_action"
        state_diff = {"added_key": "value", "modified_key": {"old": "old_val", "new": "new_val"}}
        metadata = {"version": "1.0", "source": "test"}

        entry = StateHistoryEntry(
            history_id=history_id,
            agent_id=agent_id,
            timestamp=timestamp,
            action=action,
            state_diff=state_diff,
            metadata=metadata
        )

        self.assertEqual(entry.history_id, history_id)
        self.assertEqual(entry.agent_id, agent_id)
        self.assertEqual(entry.timestamp, timestamp)
        self.assertEqual(entry.action, action)
        self.assertEqual(entry.state_diff, state_diff)
        self.assertEqual(entry.metadata, metadata)
        self.assertIsNone(entry.compressed_diff)

    def test_state_history_entry_default_values(self):
        """测试StateHistoryEntry默认值"""
        entry = StateHistoryEntry(
            history_id="test_id",
            agent_id="test_agent",
            timestamp=datetime.now(),
            action="test_action",
            state_diff={}
        )

        # 验证默认值
        self.assertEqual(entry.metadata, {})
        self.assertIsNone(entry.compressed_diff)

    def test_state_history_entry_optional_compressed_diff(self):
        """测试StateHistoryEntry压缩差异字段"""
        compressed_diff = b"compressed_diff_bytes"

        entry = StateHistoryEntry(
            history_id="test_id",
            agent_id="test_agent",
            timestamp=datetime.now(),
            action="test_action",
            state_diff={},
            compressed_diff=compressed_diff
        )

        self.assertEqual(entry.compressed_diff, compressed_diff)


if __name__ == '__main__':
    unittest.main()