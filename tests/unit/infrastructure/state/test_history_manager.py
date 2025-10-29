"""测试历史管理功能"""

import pytest
from datetime import datetime
from src.infrastructure.state.history_manager import StateHistoryManager, StateHistoryEntry


class TestStateHistoryManager:
    """测试状态历史管理器"""
    
    def setup_method(self):
        """设置测试环境"""
        self.manager = StateHistoryManager(max_history_size=100)
    
    def test_record_and_get_state_change(self):
        """测试记录和获取状态变化"""
        # 记录状态变化
        old_state = {"messages": ["old message"], "data": "old_value"}
        new_state = {"messages": ["new message"], "data": "new_value", "new_field": "added"}
        
        history_id = self.manager.record_state_change(
            "test_agent", old_state, new_state, "test_action"
        )
        assert history_id is not None
        
        # 获取历史记录
        history = self.manager.get_state_history("test_agent")
        assert len(history) == 1
        assert history[0].action == "test_action"
        assert history[0].agent_id == "test_agent"
    
    def test_state_diff_calculation(self):
        """测试状态差异计算"""
        old_state = {
            "messages": ["message1", "message2"],
            "data": {"key1": "value1", "key2": "value2"},
            "removed_key": "removed_value"
        }
        
        new_state = {
            "messages": ["message1", "message2", "message3"],  # 添加了元素
            "data": {"key1": "value1", "key2": "modified_value"},  # 修改了值
            "added_key": "added_value" # 添加了键
        }
        
        # 记录状态变化以触发差异计算
        history_id = self.manager.record_state_change(
            "test_agent", old_state, new_state, "diff_test"
        )
        
        # 获取历史记录
        history = self.manager.get_state_history("test_agent")
        assert len(history) == 1
        entry = history[0]
        
        # 验证差异包含预期的更改
        diff = entry.state_diff
        assert "added_added_key" in diff  # 添加的键
        assert "modified_data" in diff  # 修改的值
        assert "removed_removed_key" in diff  # 删除的键
    
    def test_history_size_limit(self):
        """测试历史大小限制"""
        # 设置较小的历史大小限制
        manager = StateHistoryManager(max_history_size=3)
        
        # 添加超过限制的历史记录
        for i in range(5):
            old_state = {"counter": i}
            new_state = {"counter": i + 1}
            manager.record_state_change(
                "test_agent", old_state, new_state, f"action_{i}"
            )
        
        # 检查历史记录数量是否受限制
        history = manager.get_state_history("test_agent")
        assert len(history) <= 3  # 应该不超过限制
    
    def test_replay_history(self):
        """测试历史重放功能"""
        base_state = {"messages": [], "count": 0}
        
        # 添加一些状态变化
        step1_state = {"messages": ["message1"], "count": 1}
        step2_state = {"messages": ["message1", "message2"], "count": 2}
        step3_state = {"messages": ["message1", "message2", "message3"], "count": 3}
        
        self.manager.record_state_change("test_agent", base_state, step1_state, "step1")
        self.manager.record_state_change("test_agent", step1_state, step2_state, "step2")
        self.manager.record_state_change("test_agent", step2_state, step3_state, "step3")
        
        # 重放历史到第二步
        replayed_state = self.manager.replay_history("test_agent", base_state)
        # 由于我们没有特定的时间点限制，replay_history会应用所有历史记录
        # 所以最终状态应该与最新的状态相同


if __name__ == "__main__":
    pytest.main([__file__])