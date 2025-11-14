import unittest
import tempfile
import os
from datetime import datetime
from src.infrastructure.state.sqlite_history_manager import SQLiteHistoryManager
from src.infrastructure.state.interfaces import StateHistoryEntry


class TestSQLiteHistoryManager(unittest.TestCase):
    """测试SQLiteHistoryManager类"""

    def setUp(self):
        """测试前准备"""
        # 使用临时文件作为数据库，避免测试污染
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.history_manager = SQLiteHistoryManager(db_path=self.temp_db.name)
        self.agent_id = "test_agent_123"
        self.old_state = {"key1": "value1", "key2": "value2"}
        self.new_state = {"key1": "new_value1", "key3": "value3"}

    def tearDown(self):
        """测试后清理"""
        if self.history_manager._conn:
            self.history_manager.close()
        # 删除临时数据库文件
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_initialization(self):
        """测试初始化"""
        manager = SQLiteHistoryManager(db_path=self.temp_db.name, max_history_size=10)
        self.assertEqual(manager.max_history_size, 10)
        self.assertEqual(manager.db_path.name, os.path.basename(self.temp_db.name))
        manager.close()

    def test_record_state_change(self):
        """测试记录状态变化"""
        action = "test_action"
        
        # 记录状态变化
        history_id = self.history_manager.record_state_change(
            self.agent_id, self.old_state, self.new_state, action
        )
        
        # 验证返回了有效的历史ID
        self.assertIsInstance(history_id, str)
        self.assertTrue(len(history_id) > 0)
        
        # 验证数据库中存在记录
        history = self.history_manager.get_state_history(self.agent_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].agent_id, self.agent_id)
        self.assertEqual(history[0].action, action)

    def test_get_state_history(self):
        """测试获取状态历史"""
        # 记录几个状态变化
        history_ids = []
        for i in range(3):
            old_state = {"counter": i}
            new_state = {"counter": i + 1}
            history_id = self.history_manager.record_state_change(
                self.agent_id, old_state, new_state, f"action_{i}"
            )
            history_ids.append(history_id)
        
        # 获取历史记录
        history = self.history_manager.get_state_history(self.agent_id)
        
        # 验证返回了正确的数量
        self.assertEqual(len(history), 3)
        
        # 验证历史记录按时间倒序排列（最新的在前）
        for i, entry in enumerate(history):
            self.assertEqual(entry.action, f"action_{2 - i}")  # 最新的在前

    def test_get_state_history_with_limit(self):
        """测试带限制的历史获取"""
        # 记录超过限制数量的历史
        for i in range(10):
            old_state = {"counter": i}
            new_state = {"counter": i + 1}
            self.history_manager.record_state_change(
                self.agent_id, old_state, new_state, f"action_{i}"
            )
        
        # 获取带限制的历史记录
        history = self.history_manager.get_state_history(self.agent_id, limit=3)
        
        # 验证返回了正确的限制数量
        self.assertEqual(len(history), 3)

    def test_get_state_history_empty(self):
        """测试获取空的历史记录"""
        history = self.history_manager.get_state_history("nonexistent_agent")
        self.assertEqual(len(history), 0)

    def test_calculate_state_diff(self):
        """测试计算状态差异"""
        diff = self.history_manager._calculate_state_diff(self.old_state, self.new_state)
        
        # 验证添加的键
        self.assertIn("added_key3", diff)
        self.assertEqual(diff["added_key3"], "value3")
        
        # 验证修改的键
        self.assertIn("modified_key1", diff)
        self.assertEqual(diff["modified_key1"]["old"], "value1")
        self.assertEqual(diff["modified_key1"]["new"], "new_value1")
        
        # 验证删除的键
        self.assertIn("removed_key2", diff)
        self.assertEqual(diff["removed_key2"], "value2")

    def test_replay_history(self):
        """测试重放历史"""
        base_state = {"initial": "value"}
        
        # 创建一些状态变化
        state_changes = [
            ({"initial": "value"}, {"added_key": "added_value"}),
            ({"initial": "value", "added_key": "added_value"}, {"modified_key": "new_value", "initial": "modified"}),
            ({"added_key": "added_value", "modified_key": "new_value", "initial": "modified"}, {"removed_key": "to_be_removed", "final": "state"})
        ]
        
        for old_state, new_state in state_changes:
            self.history_manager.record_state_change(
                self.agent_id, old_state, new_state, "test_action"
            )
        
        # 重放历史
        replayed_state = self.history_manager.replay_history(self.agent_id, base_state)
        
        # 验证重放后的状态与最后一个状态一致
        expected_final_state = state_changes[-1][1]
        self.assertEqual(replayed_state, expected_final_state)

    def test_replay_history_with_timestamp(self):
        """测试带时间戳限制的重放历史"""
        base_state = {"initial": "value"}
        
        # 记录一些状态变化
        timestamps = []
        for i in range(3):
            old_state = {"counter": i}
            new_state = {"counter": i + 1}
            history_id = self.history_manager.record_state_change(
                self.agent_id, old_state, new_state, f"action_{i}"
            )
            # 获取对应的历史记录以获取时间戳
            history = self.history_manager.get_state_history(self.agent_id, limit=10)
            for entry in history:
                if entry.history_id == history_id:
                    timestamps.append(entry.timestamp)
                    break
        
        # 在第二个和第三个记录之间选择一个时间点
        if len(timestamps) > 1:
            until_timestamp = timestamps[1]  # 只应用到第二个记录
            
            # 重放历史到指定时间点
            replayed_state = self.history_manager.replay_history(
                self.agent_id, base_state, until_timestamp
            )
            
            # 验证只应用了到指定时间点的更改
            self.assertEqual(replayed_state["counter"], 2)  # action_1的结果

    def test_cleanup_old_entries(self):
        """测试清理旧记录"""
        agent_id = "cleanup_test_agent"
        max_history_size = 3
        
        # 创建一个具有较小历史大小限制的管理器
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        cleanup_manager = SQLiteHistoryManager(db_path=temp_db.name, max_history_size=max_history_size)
        
        try:
            # 记录超过最大限制的历史
            for i in range(6):  # 超过max_history_size=3
                old_state = {"counter": i}
                new_state = {"counter": i + 1}
                cleanup_manager.record_state_change(
                    agent_id, old_state, new_state, f"action_{i}"
                )
            
            # 获取历史记录
            history = cleanup_manager.get_state_history(agent_id)
            
            # 验证只保留了最大限制数量的记录
            self.assertLessEqual(len(history), max_history_size)
        finally:
            cleanup_manager.close()
            # 删除临时数据库文件
            if os.path.exists(temp_db.name):
                os.unlink(temp_db.name)

    def test_compress_decompress_diff(self):
        """测试差异数据的压缩和解压缩"""
        test_diff = {"key1": "value1", "key2": {"nested": "value"}}
        
        # 压缩差异数据
        compressed = self.history_manager._compress_diff(test_diff)
        self.assertIsInstance(compressed, bytes)
        
        # 解压缩差异数据
        decompressed = self.history_manager._decompress_diff(compressed)
        self.assertEqual(decompressed, test_diff)

    def test_generate_history_id(self):
        """测试生成历史ID"""
        history_id = self.history_manager._generate_history_id()
        self.assertIsInstance(history_id, str)
        self.assertTrue(len(history_id) > 0)

    def test_apply_state_diff(self):
        """测试应用状态差异"""
        current_state = {"key1": "value1", "key2": "value2"}
        diff = {
            "added_key3": "added_value",
            "modified_key1": {"old": "value1", "new": "new_value1"},
            "removed_key2": "value2"
        }
        
        new_state = self.history_manager._apply_state_diff(current_state, diff)
        
        # 验证添加的键
        self.assertIn("key3", new_state)
        self.assertEqual(new_state["key3"], "added_value")
        
        # 验证修改的键
        self.assertEqual(new_state["key1"], "new_value1")
        
        # 验证删除的键
        self.assertNotIn("key2", new_state)

    def test_get_statistics(self):
        """测试获取统计信息"""
        # 添加一些数据
        for i in range(5):
            old_state = {"counter": i}
            new_state = {"counter": i + 1}
            self.history_manager.record_state_change(
                f"agent_{i % 2}", old_state, new_state, "test_action"
            )
        
        # 获取统计信息
        stats = self.history_manager.get_statistics()
        
        # 验证统计信息包含必要的字段
        self.assertIn("total_records", stats)
        self.assertIn("agent_counts", stats)
        self.assertIn("action_counts", stats)
        self.assertIn("database_size_bytes", stats)
        self.assertIn("database_path", stats)
        self.assertIn("max_history_size", stats)
        
        # 验证总数
        self.assertEqual(stats["total_records"], 5)

    def test_delete_history(self):
        """测试删除历史记录"""
        agent_id = "delete_test_agent"
        
        # 添加一些历史记录
        for i in range(3):
            old_state = {"counter": i}
            new_state = {"counter": i + 1}
            self.history_manager.record_state_change(
                agent_id, old_state, new_state, f"action_{i}"
            )
        
        # 验证记录已添加
        history = self.history_manager.get_state_history(agent_id)
        self.assertEqual(len(history), 3)
        
        # 删除特定agent的所有历史
        deleted_count = self.history_manager.delete_history(agent_id)
        
        # 验证记录被删除
        self.assertEqual(deleted_count, 3)
        history_after = self.history_manager.get_state_history(agent_id)
        self.assertEqual(len(history_after), 0)


if __name__ == '__main__':
    unittest.main()