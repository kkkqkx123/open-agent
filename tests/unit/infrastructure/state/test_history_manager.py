import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from src.infrastructure.state.history_manager import StateHistoryManager
from src.infrastructure.state.interfaces import StateHistoryEntry


class TestStateHistoryManager(unittest.TestCase):
    """测试StateHistoryManager类"""

    def setUp(self):
        """测试前准备"""
        self.history_manager = StateHistoryManager(max_history_size=5)
        self.agent_id = "test_agent_123"
        self.old_state = {"key1": "value1", "key2": "value2"}
        self.new_state = {"key1": "new_value1", "key3": "value3"}

    def test_initialization(self):
        """测试初始化"""
        manager = StateHistoryManager(max_history_size=10)
        self.assertEqual(manager.max_history_size, 10)
        self.assertEqual(len(manager.history_entries), 0)
        self.assertEqual(len(manager.agent_history), 0)
        self.assertEqual(len(manager.history_index), 0)

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
        
        # 验证历史记录被保存
        self.assertEqual(len(self.history_manager.history_entries), 1)
        self.assertIn(self.agent_id, self.history_manager.agent_history)
        self.assertIn(history_id, self.history_manager.history_index)

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
            self.assertEqual(entry.history_id, history_ids[2 - i])  # 最新的在前

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

    def test_cleanup_old_entries(self):
        """测试清理旧记录"""
        # 记录超过最大限制的历史
        for i in range(10):  # 超过max_history_size=5
            old_state = {"counter": i}
            new_state = {"counter": i + 1}
            self.history_manager.record_state_change(
                self.agent_id, old_state, new_state, f"action_{i}"
            )
        
        # 获取历史记录
        history = self.history_manager.get_state_history(self.agent_id)
        
        # 验证只保留了最大限制数量的记录
        self.assertEqual(len(history), 5)
        
        # 验证保留的是最新的记录
        self.assertEqual(history[0].action, "action_9")  # 最新的
        self.assertEqual(history[4].action, "action_5")  # 最旧的保留记录

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
        
        # 记录一些状态变化并保存时间戳
        timestamps = []
        for i in range(3):
            old_state = {"counter": i}
            new_state = {"counter": i + 1}
            history_id = self.history_manager.record_state_change(
                self.agent_id, old_state, new_state, f"action_{i}"
            )
            # 获取对应的历史记录并保存时间戳
            entry = self.history_manager.history_index[history_id]
            timestamps.append(entry.timestamp)
        
        # 在第二个和第三个记录之间选择一个时间点
        until_timestamp = timestamps[1]  # 只应用到第二个记录
        
        # 重放历史到指定时间点
        replayed_state = self.history_manager.replay_history(
            self.agent_id, base_state, until_timestamp
        )
        
        # 验证只应用了到指定时间点的更改
        self.assertEqual(replayed_state["counter"], 2)  # action_1的结果

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


if __name__ == '__main__':
    unittest.main()