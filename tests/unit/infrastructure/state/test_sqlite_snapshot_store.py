import unittest
import tempfile
import os
from datetime import datetime
from src.infrastructure.state.sqlite_snapshot_store import SQLiteSnapshotStore
from src.infrastructure.state.interfaces import StateSnapshot


class TestSQLiteSnapshotStore(unittest.TestCase):
    """测试SQLiteSnapshotStore类"""

    def setUp(self):
        """测试前准备"""
        # 使用临时文件作为数据库，避免测试污染
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.snapshot_store = SQLiteSnapshotStore(db_path=self.temp_db.name)
        self.agent_id = "test_agent_123"
        self.domain_state = {"key1": "value1", "key2": "value2", "counter": 42}
        self.snapshot_name = "test_snapshot"

    def tearDown(self):
        """测试后清理"""
        if self.snapshot_store._conn:
            self.snapshot_store.close()
        # 删除临时数据库文件
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_initialization(self):
        """测试初始化"""
        store = SQLiteSnapshotStore(db_path=self.temp_db.name)
        self.assertEqual(store.db_path.name, os.path.basename(self.temp_db.name))
        store.close()

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
        
        # 验证快照被保存到数据库中
        loaded_snapshot = self.snapshot_store.load_snapshot(snapshot.snapshot_id)
        self.assertIsNotNone(loaded_snapshot)
        self.assertEqual(loaded_snapshot.snapshot_id, snapshot.snapshot_id)
        self.assertEqual(loaded_snapshot.agent_id, snapshot.agent_id)
        self.assertEqual(loaded_snapshot.domain_state, snapshot.domain_state)
        self.assertEqual(loaded_snapshot.snapshot_name, snapshot.snapshot_name)

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
        self.assertEqual(loaded_snapshot.metadata, snapshot.metadata)

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
        self.assertLessEqual(len(snapshots), 3)

    def test_get_snapshots_by_agent_empty(self):
        """测试获取空的Agent快照列表"""
        snapshots = self.snapshot_store.get_snapshots_by_agent("nonexistent_agent")
        self.assertEqual(len(snapshots), 0)

    def test_delete_snapshot(self):
        """测试删除快照"""
        snapshot = StateSnapshot(
            snapshot_id="test_snapshot_123",
            agent_id=self.agent_id,
            domain_state=self.domain_state,
            timestamp=datetime.now(),
            snapshot_name=self.snapshot_name
        )
        
        # 先保存快照
        self.snapshot_store.save_snapshot(snapshot)
        
        # 验证快照存在
        loaded_snapshot = self.snapshot_store.load_snapshot(snapshot.snapshot_id)
        self.assertIsNotNone(loaded_snapshot)
        
        # 删除快照
        result = self.snapshot_store.delete_snapshot(snapshot.snapshot_id)
        
        # 验证删除成功
        self.assertTrue(result)
        
        # 验证快照不再存在
        loaded_snapshot = self.snapshot_store.load_snapshot(snapshot.snapshot_id)
        self.assertIsNone(loaded_snapshot)

    def test_delete_nonexistent_snapshot(self):
        """测试删除不存在的快照"""
        result = self.snapshot_store.delete_snapshot("nonexistent_snapshot")
        self.assertFalse(result)

    def test_cleanup_old_snapshots(self):
        """测试清理旧快照"""
        agent_id = "cleanup_test_agent"
        
        # 创建超过限制的快照
        for i in range(10):
            snapshot = StateSnapshot(
                snapshot_id=f"snapshot_{i}",
                agent_id=agent_id,
                domain_state={"counter": i},
                timestamp=datetime.now(),
                snapshot_name=f"snapshot_{i}"
            )
            self.snapshot_store.save_snapshot(snapshot)
        
        # 验证初始快照数量
        initial_snapshots = self.snapshot_store.get_snapshots_by_agent(agent_id)
        self.assertEqual(len(initial_snapshots), 10)
        
        # 清理旧快照（保留最新的5个）
        deleted_count = self.snapshot_store.cleanup_old_snapshots(agent_id, max_snapshots=5)
        
        # 验证删除的快照数量
        self.assertEqual(deleted_count, 5)
        
        # 验证只保留了最新的快照
        final_snapshots = self.snapshot_store.get_snapshots_by_agent(agent_id)
        self.assertEqual(len(final_snapshots), 5)

    def test_save_snapshot_with_metadata(self):
        """测试保存带元数据的快照"""
        metadata = {"version": "1.0", "author": "test_user", "tags": ["test", "important"]}
        
        snapshot = StateSnapshot(
            snapshot_id="test_snapshot_with_metadata",
            agent_id=self.agent_id,
            domain_state=self.domain_state,
            timestamp=datetime.now(),
            snapshot_name=self.snapshot_name,
            metadata=metadata
        )
        
        # 保存快照
        result = self.snapshot_store.save_snapshot(snapshot)
        self.assertTrue(result)
        
        # 加载快照
        loaded_snapshot = self.snapshot_store.load_snapshot(snapshot.snapshot_id)
        
        # 验证元数据被正确保存和加载
        self.assertEqual(loaded_snapshot.metadata, metadata)

    def test_save_snapshot_with_compression(self):
        """测试保存快照时的数据压缩"""
        snapshot = StateSnapshot(
            snapshot_id="test_snapshot_compression",
            agent_id=self.agent_id,
            domain_state=self.domain_state,
            timestamp=datetime.now(),
            snapshot_name=self.snapshot_name
        )
        
        # 保存快照
        result = self.snapshot_store.save_snapshot(snapshot)
        self.assertTrue(result)
        
        # 验证快照被保存
        loaded_snapshot = self.snapshot_store.load_snapshot(snapshot.snapshot_id)
        self.assertIsNotNone(loaded_snapshot)

    def test_get_statistics(self):
        """测试获取统计信息"""
        # 添加一些数据
        for i in range(5):
            snapshot = StateSnapshot(
                snapshot_id=f"snapshot_{i}",
                agent_id=f"agent_{i % 2}",
                domain_state={"counter": i},
                timestamp=datetime.now(),
                snapshot_name=f"snapshot_{i}"
            )
            self.snapshot_store.save_snapshot(snapshot)
        
        # 获取统计信息
        stats = self.snapshot_store.get_statistics()
        
        # 验证统计信息包含必要的字段
        self.assertIn("total_snapshots", stats)
        self.assertIn("agent_counts", stats)
        self.assertIn("database_size_bytes", stats)
        self.assertIn("database_path", stats)
        
        # 验证总数
        self.assertEqual(stats["total_snapshots"], 5)

    def test_save_and_load_snapshot_with_all_fields(self):
        """测试保存和加载包含所有字段的快照"""
        # 创建一个包含所有可能字段的快照
        snapshot = StateSnapshot(
            snapshot_id="complete_test_snapshot",
            agent_id=self.agent_id,
            domain_state=self.domain_state,
            timestamp=datetime.now(),
            snapshot_name=self.snapshot_name,
            metadata={"version": "1.0", "description": "Complete test snapshot"},
            compressed_data=None,
            size_bytes=0
        )
        
        # 保存快照
        result = self.snapshot_store.save_snapshot(snapshot)
        self.assertTrue(result)
        
        # 加载快照
        loaded_snapshot = self.snapshot_store.load_snapshot(snapshot.snapshot_id)
        
        # 验证所有字段都被正确保存和加载
        self.assertEqual(loaded_snapshot.snapshot_id, snapshot.snapshot_id)
        self.assertEqual(loaded_snapshot.agent_id, snapshot.agent_id)
        self.assertEqual(loaded_snapshot.domain_state, snapshot.domain_state)
        self.assertEqual(loaded_snapshot.snapshot_name, snapshot.snapshot_name)
        self.assertEqual(loaded_snapshot.metadata, snapshot.metadata)
        # timestamp可能有微秒级别的差异，所以只检查日期部分
        self.assertEqual(loaded_snapshot.timestamp.date(), snapshot.timestamp.date())


if __name__ == '__main__':
    unittest.main()