import unittest
from datetime import datetime
from src.infrastructure.state.snapshot_store import StateSnapshotStore
from src.infrastructure.state.interfaces import StateSnapshot


class TestStateSnapshotStore(unittest.TestCase):
    """测试StateSnapshotStore类"""

    def setUp(self):
        """测试前准备"""
        self.snapshot_store = StateSnapshotStore(storage_backend="memory")
        self.agent_id = "test_agent_123"
        self.domain_state = {"key1": "value1", "key2": "value2", "counter": 42}
        self.snapshot_name = "test_snapshot"

    def test_initialization(self):
        """测试初始化"""
        store = StateSnapshotStore()
        self.assertEqual(store.storage_backend, "memory")
        self.assertEqual(store.snapshots, {})
        self.assertEqual(store.agent_snapshots, {})

    def test_initialization_with_different_backends(self):
        """测试使用不同存储后端初始化"""
        # 测试内存存储
        store_memory = StateSnapshotStore(storage_backend="memory")
        self.assertEqual(store_memory.storage_backend, "memory")
        
        # 测试SQLite存储（实际使用内存存储作为占位实现）
        store_sqlite = StateSnapshotStore(storage_backend="sqlite")
        self.assertEqual(store_sqlite.storage_backend, "sqlite")
        
        # 测试文件存储（实际使用内存存储作为占位实现）
        store_file = StateSnapshotStore(storage_backend="file")
        self.assertEqual(store_file.storage_backend, "file")

    def test_save_snapshot(self):
        """测试保存快照"""
        snapshot = StateSnapshot(
            snapshot_id="test_snapshot_123",
            agent_id=self.agent_id,
            domain_state=self.domain_state,
            timestamp=datetime.now(),
            snapshot_name=self.snapshot_name
        )
        
        result = self.snapshot_store.save_snapshot(snapshot)
        
        # 验证保存成功
        self.assertTrue(result)
        
        # 验证快照被保存到存储中
        self.assertIn(snapshot.snapshot_id, self.snapshot_store.snapshots)
        
        # 验证Agent的快照列表被更新
        self.assertIn(self.agent_id, self.snapshot_store.agent_snapshots)
        self.assertIn(snapshot.snapshot_id, self.snapshot_store.agent_snapshots[self.agent_id])

    def test_load_snapshot(self):
        """测试加载快照"""
        snapshot = StateSnapshot(
            snapshot_id="test_snapshot_123",
            agent_id=self.agent_id,
            domain_state=self.domain_state,
            timestamp=datetime.now(),
            snapshot_name=self.snapshot_name
        )
        
        # 先保存快照
        self.snapshot_store.save_snapshot(snapshot)
        
        # 加载快照
        loaded_snapshot = self.snapshot_store.load_snapshot(snapshot.snapshot_id)
        
        # 验证加载的快照
        self.assertIsNotNone(loaded_snapshot)
        self.assertEqual(loaded_snapshot.snapshot_id, snapshot.snapshot_id)
        self.assertEqual(loaded_snapshot.agent_id, snapshot.agent_id)
        self.assertEqual(loaded_snapshot.domain_state, snapshot.domain_state)
        self.assertEqual(loaded_snapshot.snapshot_name, snapshot.snapshot_name)

    def test_load_nonexistent_snapshot(self):
        """测试加载不存在的快照"""
        loaded_snapshot = self.snapshot_store.load_snapshot("nonexistent_snapshot")
        self.assertIsNone(loaded_snapshot)

    def test_get_snapshots_by_agent(self):
        """测试按Agent获取快照"""
        agent_id_1 = "agent_1"
        agent_id_2 = "agent_2"
        
        # 为第一个Agent创建几个快照
        for i in range(3):
            snapshot = StateSnapshot(
                snapshot_id=f"snapshot_{i}",
                agent_id=agent_id_1,
                domain_state={"counter": i},
                timestamp=datetime.now(),
                snapshot_name=f"snapshot_{i}"
            )
            self.snapshot_store.save_snapshot(snapshot)
        
        # 为第二个Agent创建几个快照
        for i in range(2):
            snapshot = StateSnapshot(
                snapshot_id=f"snapshot_agent2_{i}",
                agent_id=agent_id_2,
                domain_state={"counter": i},
                timestamp=datetime.now(),
                snapshot_name=f"snapshot_agent2_{i}"
            )
            self.snapshot_store.save_snapshot(snapshot)
        
        # 获取第一个Agent的快照
        snapshots_agent_1 = self.snapshot_store.get_snapshots_by_agent(agent_id_1)
        snapshots_agent_2 = self.snapshot_store.get_snapshots_by_agent(agent_id_2)
        
        # 验证每个Agent的快照数量
        self.assertEqual(len(snapshots_agent_1), 3)
        self.assertEqual(len(snapshots_agent_2), 2)
        
        # 验证每个Agent只获取到自己的快照
        for snapshot in snapshots_agent_1:
            self.assertEqual(snapshot.agent_id, agent_id_1)
        
        for snapshot in snapshots_agent_2:
            self.assertEqual(snapshot.agent_id, agent_id_2)

    def test_get_snapshots_by_agent_with_limit(self):
        """测试带限制的按Agent获取快照"""
        # 创建超过限制的快照
        for i in range(10):
            snapshot = StateSnapshot(
                snapshot_id=f"snapshot_{i}",
                agent_id=self.agent_id,
                domain_state={"counter": i},
                timestamp=datetime.now(),
                snapshot_name=f"snapshot_{i}"
            )
            self.snapshot_store.save_snapshot(snapshot)
        
        # 获取带限制的快照
        snapshots = self.snapshot_store.get_snapshots_by_agent(self.agent_id, limit=3)
        
        # 验证返回了正确的限制数量
        self.assertEqual(len(snapshots), 3)

    def test_get_snapshots_by_agent_empty(self):
        """测试获取空的Agent快照列表"""
        snapshots = self.snapshot_store.get_snapshots_by_agent("nonexistent_agent")
        self.assertEqual(len(snapshots), 0)

    def test_serialize_deserialize_state(self):
        """测试状态的序列化和反序列化"""
        test_state = {"key1": "value1", "nested": {"key2": [1, 2, 3]}}
        
        # 序列化
        serialized = self.snapshot_store._serialize_state(test_state)
        self.assertIsInstance(serialized, bytes)
        
        # 反序列化
        deserialized = self.snapshot_store._deserialize_state(serialized)
        self.assertEqual(deserialized, test_state)

    def test_compress_decompress_data(self):
        """测试数据的压缩和解压缩"""
        test_data = b"test data that should be compressed"
        
        # 压缩
        compressed = self.snapshot_store._compress_data(test_data)
        self.assertIsInstance(compressed, bytes)
        self.assertLess(len(compressed), len(test_data) + 10)  # 压缩后应该更小（或几乎相同）
        
        # 解压缩
        decompressed = self.snapshot_store._decompress_data(compressed)
        self.assertEqual(decompressed, test_data)

    def test_cleanup_old_snapshots(self):
        """测试清理旧快照"""
        # 创建超过限制的快照
        for i in range(10):
            snapshot = StateSnapshot(
                snapshot_id=f"snapshot_{i}",
                agent_id=self.agent_id,
                domain_state={"counter": i},
                timestamp=datetime.now(),
                snapshot_name=f"snapshot_{i}"
            )
            self.snapshot_store.save_snapshot(snapshot)
        
        # 清理旧快照（保留最新的5个）
        self.snapshot_store._cleanup_old_snapshots(self.agent_id, max_snapshots=5)
        
        # 验证只保留了最新的快照
        snapshots = self.snapshot_store.get_snapshots_by_agent(self.agent_id)
        self.assertEqual(len(snapshots), 5)
        
        # 验证保留的是最新的快照（ID最大的）
        snapshot_ids = [s.snapshot_id for s in snapshots]
        expected_ids = [f"snapshot_{i}" for i in range(5, 10)]  # 最新的5个
        for expected_id in expected_ids:
            self.assertIn(expected_id, snapshot_ids)

    def test_save_snapshot_with_compression(self):
        """测试保存快照时的数据压缩"""
        snapshot = StateSnapshot(
            snapshot_id="test_snapshot_123",
            agent_id=self.agent_id,
            domain_state=self.domain_state,
            timestamp=datetime.now(),
            snapshot_name=self.snapshot_name
        )
        
        # 保存快照
        self.snapshot_store.save_snapshot(snapshot)
        
        # 验证快照被压缩存储
        saved_snapshot = self.snapshot_store.snapshots[snapshot.snapshot_id]
        self.assertIsNotNone(saved_snapshot.compressed_data)
        self.assertGreater(saved_snapshot.size_bytes, 0)

    def test_load_snapshot_with_compression(self):
        """测试加载快照时的数据解压缩"""
        snapshot = StateSnapshot(
            snapshot_id="test_snapshot_123",
            agent_id=self.agent_id,
            domain_state=self.domain_state,
            timestamp=datetime.now(),
            snapshot_name=self.snapshot_name
        )
        
        # 保存快照（会自动压缩）
        self.snapshot_store.save_snapshot(snapshot)
        
        # 清空原始状态以测试解压缩
        stored_snapshot = self.snapshot_store.snapshots[snapshot.snapshot_id]
        original_state = stored_snapshot.domain_state
        stored_snapshot.domain_state = {}  # 清空以测试解压缩
        
        # 加载快照（会自动解压缩）
        loaded_snapshot = self.snapshot_store.load_snapshot(snapshot.snapshot_id)
        
        # 验证状态被正确解压缩
        self.assertEqual(loaded_snapshot.domain_state, original_state)


if __name__ == '__main__':
    unittest.main()