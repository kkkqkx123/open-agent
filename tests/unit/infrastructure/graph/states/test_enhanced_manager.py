"""EnhancedStateManager单元测试"""

import pytest
from datetime import datetime
from src.infrastructure.graph.states.composite_manager import (
    CompositeStateManager as EnhancedStateManager,
    create_composite_state_manager as create_enhanced_state_manager,
)
from src.infrastructure.graph.states.interface import (
    ConflictType,
    ConflictResolutionStrategy
)


class TestEnhancedStateManager:
    """EnhancedStateManager测试类"""
    
    def setup_method(self):
        """测试方法设置"""
        self.manager = create_enhanced_state_manager(
            enable_pooling=False,
            enable_diff_tracking=True,
            conflict_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
        )
        # 使用普通字典而不是AgentState对象
        self.state1 = {"input": "测试输入1", "messages": ["hello"]}
        self.state2 = {"input": "测试输入2", "messages": ["world"]}
    
    def test_create_enhanced_state_manager(self):
        """测试创建增强的状态管理器"""
        manager = create_enhanced_state_manager()
        assert isinstance(manager, EnhancedStateManager)
        assert manager.conflict_resolver.strategy == ConflictResolutionStrategy.LAST_WRITE_WINS
    
    def test_create_state_version(self):
        """测试创建状态版本"""
        version_id = self.manager.create_state_version("test_state", self.state1, {"description": "测试版本"})
        assert version_id.startswith("test_state_v")
        
        # 验证版本存在
        version_state = self.manager.get_state_version(version_id)
        assert version_state is not None
        assert version_state["input"] == "测试输入1"
    
    def test_get_nonexistent_state_version(self):
        """测试获取不存在的状态版本"""
        version_state = self.manager.get_state_version("nonexistent")
        assert version_state is None
    
    def test_compare_states_no_differences(self):
        """测试比较相同状态"""
        differences = self.manager.compare_states(self.state1, self.state1)
        assert len(differences) == 0
    
    def test_compare_states_with_differences(self):
        """测试比较不同状态"""
        # 创建普通字典状态用于测试
        state1 = {"input": "测试输入1", "field1": "value1"}
        state2 = {"input": "修改后的输入", "field1": "value1", "output": "测试输出"}
        
        differences = self.manager.compare_states(state1, state2)
        assert len(differences) >= 2
        assert "input" in differences
        assert "output" in differences
        assert differences["input"]["old_value"] == "测试输入1"
        assert differences["input"]["new_value"] == "修改后的输入"
    
    def test_detect_conflicts_no_conflicts(self):
        """测试检测无冲突状态"""
        conflicts = self.manager.detect_conflicts(self.state1, self.state1)
        assert len(conflicts) == 0
    
    def test_detect_conflicts_with_field_modification(self):
        """测试检测字段修改冲突"""
        # 创建相同的状态，只修改一个字段
        state1 = {"input": "测试输入", "messages": ["hello"]}
        state2 = {"input": "修改后的输入", "messages": ["hello"]}
        
        conflicts = self.manager.detect_conflicts(state1, state2)
        # 应该只检测到input字段的冲突
        input_conflicts = [c for c in conflicts if c.field_path == "input"]
        assert len(input_conflicts) == 1
        conflict = input_conflicts[0]
        assert conflict.conflict_type == ConflictType.FIELD_MODIFICATION
        assert conflict.field_path == "input"
        assert conflict.current_value == "测试输入"
        assert conflict.new_value == "修改后的输入"
    
    def test_detect_conflicts_with_list_operation(self):
        """测试检测列表操作冲突"""
        # 创建相同的状态，只修改列表字段
        state1 = {"input": "测试输入", "messages": ["hello"]}
        state2 = {"input": "测试输入", "messages": ["hello", "world"]}
        
        conflicts = self.manager.detect_conflicts(state1, state2)
        # 应该检测到messages字段的冲突
        messages_conflicts = [c for c in conflicts if c.field_path == "messages"]
        assert len(messages_conflicts) == 1
        conflict = messages_conflicts[0]
        assert conflict.conflict_type == ConflictType.LIST_OPERATION
        assert conflict.field_path == "messages"
    
    def test_update_state_with_conflict_resolution_no_conflicts(self):
        """测试无冲突状态更新"""
        resolved_state, unresolved = self.manager.update_state_with_conflict_resolution(
            self.state1, self.state1
        )
        assert len(unresolved) == 0
        assert resolved_state["input"] == "测试输入1"
    
    def test_update_state_with_conflict_resolution_last_write_wins(self):
        """测试最后写入获胜策略"""
        self.manager.conflict_resolver.strategy = ConflictResolutionStrategy.LAST_WRITE_WINS
        self.state2["input"] = "新输入值"
        
        resolved_state, unresolved = self.manager.update_state_with_conflict_resolution(
            self.state1, self.state2
        )
        assert len(unresolved) == 0
        assert resolved_state["input"] == "新输入值"
    
    def test_update_state_with_conflict_resolution_first_write_wins(self):
        """测试首次写入获胜策略"""
        self.manager.conflict_resolver.strategy = ConflictResolutionStrategy.FIRST_WRITE_WINS
        # 创建相同的状态，只修改特定字段
        state1 = {"input": "原始输入", "messages": ["hello"]}
        state2 = {"input": "冲突输入", "messages": ["hello"]}
        # 添加一个新字段到state2，测试新字段的添加
        state2["custom_field"] = "新字段值"
        
        resolved_state, unresolved = self.manager.update_state_with_conflict_resolution(
            state1, state2
        )
        # 冲突字段保留原始值，新字段被添加
        assert resolved_state["input"] == "原始输入"
        assert resolved_state["custom_field"] == "新字段值"
    
    def test_update_state_with_conflict_resolution_merge_changes(self):
        """测试合并变更策略"""
        self.manager.conflict_resolver.strategy = ConflictResolutionStrategy.MERGE_CHANGES
        self.state1["input"] = "原始值"
        self.state1["metadata"] = {"key1": "value1"}
        self.state2["input"] = "新值"
        self.state2["metadata"] = {"key2": "value2"}
        self.state2["output"] = "新输出"
        
        resolved_state, unresolved = self.manager.update_state_with_conflict_resolution(
            self.state1, self.state2
        )
        # 合并后的状态应包含所有字段
        assert resolved_state["input"] == "新值"  # 简单字段使用新值
        assert "key1" in resolved_state["metadata"]  # 字典被合并
        assert "key2" in resolved_state["metadata"]
        assert resolved_state["output"] == "新输出"  # 新字段被添加
    
    def test_get_conflict_history(self):
        """测试获取冲突历史"""
        # 创建一些冲突
        state1 = {"input": "原始输入", "messages": ["hello"]}
        state2 = {"input": "冲突输入", "messages": ["hello"]}
        state2["input"] = "冲突值"
        
        resolved_state, unresolved = self.manager.update_state_with_conflict_resolution(state1, state2)
        history = self.manager.get_conflict_history()
        
        # 检查是否有input字段的冲突
        input_conflicts = [c for c in history if c.field_path == "input"]
        assert len(input_conflicts) >= 1
        assert input_conflicts[0].field_path == "input"
    
    def test_clear_conflict_history(self):
        """测试清空冲突历史"""
        # 创建冲突
        self.state2["input"] = "冲突值"
        self.manager.update_state_with_conflict_resolution(self.state1, self.state2)
        
        # 清空历史
        self.manager.clear_conflict_history()
        history = self.manager.get_conflict_history()
        assert len(history) == 0
    
    def test_can_auto_resolve(self):
        """测试自动解决判断"""
        # 创建字段修改冲突
        self.state2["input"] = "冲突值"
        conflicts = self.manager.detect_conflicts(self.state1, self.state2)
        
        for conflict in conflicts:
            can_resolve = self.manager._can_auto_resolve(conflict)
            assert can_resolve is True
    
    def test_determine_conflict_type(self):
        """测试冲突类型判断"""
        # 测试字段修改
        diff_info = {
            "old_value": "旧值",
            "new_value": "新值",
            "type_changed": False
        }
        conflict_type = self.manager._determine_conflict_type("test_field", diff_info)
        assert conflict_type == ConflictType.FIELD_MODIFICATION
        
        # 测试类型变化
        diff_info["type_changed"] = True
        conflict_type = self.manager._determine_conflict_type("test_field", diff_info)
        assert conflict_type == ConflictType.STRUCTURE_CHANGE
        
        # 测试列表操作
        diff_info = {
            "old_value": [1, 2],
            "new_value": [1, 2, 3],
            "type_changed": False
        }
        conflict_type = self.manager._determine_conflict_type("test_list", diff_info)
        assert conflict_type == ConflictType.LIST_OPERATION


class TestConflictResolutionStrategies:
    """冲突解决策略测试"""
    
    def setup_method(self):
        """测试方法设置"""
        self.state1 = {"input": "输入1", "messages": ["hello"]}
        self.state2 = {"input": "输入2", "messages": ["world"]}
        self.resolver = create_enhanced_state_manager().conflict_resolver
    
    def test_last_write_wins_strategy(self):
        """测试最后写入获胜策略"""
        self.state2["input"] = "新输入"
        result = self.resolver._last_write_wins(self.state1, self.state2)
        assert result["input"] == "新输入"
    
    def test_first_write_wins_strategy(self):
        """测试首次写入获胜策略"""
        state1 = {"input": "原始输入", "messages": ["hello"]}
        state2 = {"input": "冲突输入", "messages": ["hello"]}
        # 添加一个新字段到state2，测试新字段的添加
        state2["custom_field"] = "新字段值"
        
        result = self.resolver._first_write_wins(state1, state2)
        assert result["input"] == "原始输入"  # 冲突字段保留原始值
        assert result["custom_field"] == "新字段值"   # 新字段被添加"
    
    def test_merge_changes_strategy(self):
        """测试合并变更策略"""
        state1 = {"input": "原始输入", "metadata": {"key1": "value1"}, "messages": ["hello"]}
        state2 = {"input": "新输入", "metadata": {"key2": "value2"}, "output": "新输出", "messages": ["hello", "world"]}
        
        result = self.resolver._merge_changes(state1, state2)
        assert result["input"] == "新输入"
        assert result["metadata"]["key1"] == "value1"
        assert result["metadata"]["key2"] == "value2"
        assert result["output"] == "新输出"
    
    def test_merge_dicts_recursive(self):
        """测试递归字典合并"""
        dict1 = {"a": 1, "b": {"x": 10, "y": 20}}
        dict2 = {"b": {"y": 30, "z": 40}, "c": 3}
        
        result = self.resolver._merge_dicts(dict1, dict2)
        assert result["a"] == 1
        assert result["b"]["x"] == 10
        assert result["b"]["y"] == 30  # 被覆盖
        assert result["b"]["z"] == 40  # 被添加
        assert result["c"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])