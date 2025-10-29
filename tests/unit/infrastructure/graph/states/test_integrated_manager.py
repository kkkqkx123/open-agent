"""整合状态管理器单元测试

整合PoolingStateManager和CompositeStateManager的测试用例，
提供完整的状态管理功能测试覆盖。
"""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from src.infrastructure.graph.states.pooling_manager import (
    StateUpdate,
    PoolingStateManager,
    create_optimized_state_manager
)
from src.infrastructure.graph.states.composite_manager import (
    CompositeStateManager,
    create_composite_state_manager
)
from src.infrastructure.graph.states.conflict_manager import (
    ConflictStateManager,
    Conflict
)
from src.infrastructure.graph.states.interface import (
    ConflictType,
    ConflictResolutionStrategy
)
from src.infrastructure.graph.states.base import BaseGraphState


class TestStateUpdate:
    """状态更新测试"""

    def test_init(self):
        """测试初始化"""
        update = StateUpdate(
            field_path="test.field",
            old_value="old",
            new_value="new",
            timestamp=123456.789
        )
        assert update.field_path == "test.field"
        assert update.old_value == "old"
        assert update.new_value == "new"
        assert update.timestamp == 123456.789


class TestPoolingStateManager:
    """对象池状态管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建对象池状态管理器实例"""
        return PoolingStateManager(
            enable_pooling=True,
            max_pool_size=5,
            enable_diff_tracking=True
        )

    @pytest.fixture
    def sample_state(self):
        """示例状态"""
        return {
            "messages": ["消息1", "消息2"],
            "input": "测试输入",
            "output": None,
            "tool_calls": [],
            "tool_results": [],
            "iteration_count": 0,
            "max_iterations": 10,
            "errors": [],
            "complete": False,
            "metadata": {"key": "value"}
        }

    def test_init(self, manager):
        """测试初始化"""
        assert manager._enable_pooling is True
        assert manager._max_pool_size == 5
        assert manager._enable_diff_tracking is True
        assert isinstance(manager._state_pool, dict)
        assert isinstance(manager._state_history, dict)
        assert manager._max_history_size == 50

    def test_create_state_with_pooling(self, manager, sample_state):
        """测试创建状态（使用对象池）"""
        state_id = "test_state"
        
        # 第一次创建
        state1 = manager.create_state(state_id, sample_state)
        assert state1 == sample_state
        
        # 第二次创建，应该重用对象
        state2 = manager.create_state(state_id, sample_state)
        assert state2 is state1  # 确保是同一个对象

    def test_create_state_without_pooling(self, sample_state):
        """测试创建状态（不使用对象池）"""
        manager = PoolingStateManager(enable_pooling=False)
        state_id = "test_state"
        
        state1 = manager.create_state(state_id, sample_state)
        state2 = manager.create_state(state_id, sample_state)
        
        assert state1 == sample_state
        assert state2 == sample_state
        assert state1 is not state2  # 确保是不同的对象

    def test_update_state_incremental_with_diff_tracking(self, manager, sample_state):
        """测试增量更新状态（使用差异跟踪）"""
        state_id = "test_state"
        updates = {"output": "新输出", "complete": True}
        
        updated_state = manager.update_state(state_id, sample_state, updates)
        
        # 验证更新
        assert updated_state["output"] == "新输出"
        assert updated_state["complete"] is True
        # 验证其他字段未改变
        assert updated_state["input"] == sample_state["input"]
        assert updated_state["messages"] == sample_state["messages"]

    def test_update_state_incremental_without_diff_tracking(self, sample_state):
        """测试增量更新状态（不使用差异跟踪）"""
        manager = PoolingStateManager(enable_diff_tracking=False)
        state_id = "test_state"
        updates = {"output": "新输出"}
        
        updated_state = manager.update_state(state_id, sample_state, updates)
        
        # 验证更新
        assert updated_state["output"] == "新输出"
        # 验证其他字段未改变
        assert updated_state["input"] == sample_state["input"]

    def test_apply_state_diff(self, manager, sample_state):
        """测试应用状态差异"""
        state_id = "test_state"
        # 简单的差异数据（实际应用中会是序列化的差异）
        diff_data = '{"added": {"output": "新输出"}, "modified": {}, "removed": []}'
        
        updated_state = manager.apply_state_diff(state_id, sample_state, diff_data)
        
        # 验证更新
        assert updated_state["output"] == "新输出"

    def test_compress_state(self, manager, sample_state):
        """测试压缩状态"""
        state_id = "test_state"
        
        compressed_state = manager.compress_state(state_id, sample_state)
        
        # 验证压缩后的状态
        assert isinstance(compressed_state, dict)
        assert compressed_state["input"] == sample_state["input"]

    def test_get_state_history(self, manager, sample_state):
        """测试获取状态更新历史"""
        state_id = "test_state"
        updates = {"output": "新输出"}
        
        # 执行更新以生成历史记录
        manager.update_state(state_id, sample_state, updates)
        
        # 获取历史记录
        history = manager.get_state_history(state_id, limit=5)
        
        assert isinstance(history, list)
        assert len(history) >= 1
        assert isinstance(history[0], StateUpdate)

    def test_get_state_history_empty(self, manager):
        """测试获取状态更新历史（空历史）"""
        history = manager.get_state_history("nonexistent_state", limit=5)
        assert history == []

    def test_get_memory_usage_stats(self, manager, sample_state):
        """测试获取内存使用统计"""
        state_id = "test_state"
        manager.create_state(state_id, sample_state)
        
        stats = manager.get_memory_usage_stats()
        
        assert isinstance(stats, dict)
        assert "pool_size" in stats
        assert "compressed_states_size" in stats
        assert "history_entries" in stats
        assert "pool_memory_bytes" in stats
        assert "compressed_memory_bytes" in stats
        assert "history_memory_bytes" in stats
        assert "total_memory_bytes" in stats
        assert "memory_saved_bytes" in stats

    def test_get_performance_stats(self, manager):
        """测试获取性能统计"""
        stats = manager.get_performance_stats()
        
        assert isinstance(stats, dict)
        assert "manager_stats" in stats
        assert "serializer_stats" in stats
        assert "pool_efficiency" in stats

    def test_cleanup_specific_state(self, manager, sample_state):
        """测试清理特定状态"""
        state_id = "test_state"
        manager.create_state(state_id, sample_state)
        
        # 验证状态存在
        assert state_id in manager._state_pool
        
        # 清理状态
        manager.cleanup(state_id)
        
        # 验证状态已被清理
        assert state_id not in manager._state_pool

    def test_cleanup_all_states(self, manager, sample_state):
        """测试清理所有状态"""
        state_id1 = "test_state_1"
        state_id2 = "test_state_2"
        manager.create_state(state_id1, sample_state)
        manager.create_state(state_id2, sample_state)
        
        # 验证状态存在
        assert state_id1 in manager._state_pool
        assert state_id2 in manager._state_pool
        
        # 清理所有状态
        manager.cleanup()
        
        # 验证所有状态已被清理
        assert len(manager._state_pool) == 0
        assert len(manager._state_history) == 0

    def test_apply_incremental_updates(self, manager, sample_state):
        """测试应用增量更新"""
        updates = {"output": "新输出", "new_field": "新字段"}
        
        updated_state = manager._apply_incremental_updates(sample_state, updates)
        
        # 验证更新
        assert updated_state["output"] == "新输出"
        assert updated_state["new_field"] == "新字段"
        # 验证其他字段未改变
        assert updated_state["input"] == sample_state["input"]

    def test_apply_incremental_updates_list_append(self, manager):
        """测试应用增量更新（列表追加）"""
        state = {"messages": ["消息1", "消息2"]}
        updates = {"messages": ["消息1", "消息2", "消息3"]}
        
        updated_state = manager._apply_incremental_updates(state, updates)
        
        # 验证更新
        assert updated_state["messages"] == ["消息1", "消息2", "消息3"]

    def test_record_updates(self, manager, sample_state):
        """测试记录更新"""
        state_id = "test_state"
        old_state = sample_state.copy()
        new_state = sample_state.copy()
        new_state["output"] = "新输出"
        
        manager._record_updates(state_id, old_state, new_state)
        
        # 验证历史记录
        assert state_id in manager._state_history
        assert len(manager._state_history[state_id]) >= 1

    def test_estimate_state_size(self, manager, sample_state):
        """测试估算状态大小"""
        size = manager._estimate_state_size(sample_state)
        assert isinstance(size, int)
        assert size > 0


class TestCompositeStateManager:
    """组合状态管理器测试"""
    
    def setup_method(self):
        """测试方法设置"""
        self.manager = create_composite_state_manager(
            enable_pooling=False,
            enable_diff_tracking=True,
            conflict_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
        )
        # 使用普通字典而不是AgentState对象
        self.state1 = {"input": "测试输入1", "messages": ["hello"]}
        self.state2 = {"input": "测试输入2", "messages": ["world"]}
    
    def test_create_composite_state_manager(self):
        """测试创建组合状态管理器"""
        manager = create_composite_state_manager()
        assert isinstance(manager, CompositeStateManager)
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

    def test_pooling_integration(self):
        """测试对象池集成功能"""
        # 创建启用对象池的组合管理器
        manager = create_composite_state_manager(
            enable_pooling=True,
            max_pool_size=5,
            enable_diff_tracking=True
        )
        
        state_id = "test_state"
        initial_state = {"input": "测试输入", "messages": []}
        
        # 创建状态
        state1 = manager.create_state(state_id, initial_state)
        
        # 更新状态
        updates = {"messages": ["消息1", "消息2"], "output": "测试输出"}
        state2 = manager.update_state(state_id, state1, updates)
        
        # 验证更新
        assert state2["messages"] == ["消息1", "消息2"]
        assert state2["output"] == "测试输出"
        
        # 测试内存统计
        stats = manager.get_memory_usage_stats()
        assert "pool_size" in stats
        assert stats["pool_size"] >= 1

    def test_version_management_integration(self):
        """测试版本管理集成功能"""
        state_id = "test_state"
        state = {"input": "测试输入", "messages": ["消息1"]}
        
        # 创建版本
        version_id = self.manager.create_state_version(state_id, state, {"tag": "v1"})
        
        # 获取版本
        version_state = self.manager.get_state_version(version_id)
        assert version_state is not None
        assert version_state["input"] == "测试输入"
        
        # 获取版本元数据
        metadata = self.manager.get_version_metadata(version_id)
        assert metadata is not None
        assert metadata["tag"] == "v1"
        
        # 获取状态的所有版本
        versions = self.manager.get_state_versions(state_id)
        assert len(versions) >= 1
        
        # 测试回滚
        success = self.manager.rollback_to_version(state_id, version_id)
        assert success is True


class TestConflictResolutionStrategies:
    """冲突解决策略测试"""
    
    def setup_method(self):
        """测试方法设置"""
        self.state1 = {"input": "输入1", "messages": ["hello"]}
        self.state2 = {"input": "输入2", "messages": ["world"]}
        self.resolver = create_composite_state_manager().conflict_resolver
    
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
        assert result["custom_field"] == "新字段值"   # 新字段被添加
    
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


class TestCreateFunctions:
    """创建函数测试"""

    def test_create_optimized_state_manager_with_defaults(self):
        """测试创建对象池状态管理器（使用默认值）"""
        manager = create_optimized_state_manager()
        
        assert isinstance(manager, PoolingStateManager)
        assert manager._enable_pooling is True
        assert manager._max_pool_size == 10
        assert manager._enable_diff_tracking is True

    def test_create_optimized_state_manager_with_custom_params(self):
        """测试创建对象池状态管理器（使用自定义参数）"""
        manager = create_optimized_state_manager(
            enable_pooling=False,
            max_pool_size=10,
            enable_diff_tracking=False
        )
        
        assert isinstance(manager, PoolingStateManager)
        assert manager._enable_pooling is False
        assert manager._max_pool_size == 10
        assert manager._enable_diff_tracking is False

    def test_create_composite_state_manager_with_defaults(self):
        """测试创建组合状态管理器（使用默认值）"""
        manager = create_composite_state_manager()
        
        assert isinstance(manager, CompositeStateManager)
        assert manager._enable_pooling is True
        assert manager._max_pool_size == 100
        assert manager._enable_diff_tracking is True
        assert manager._conflict_strategy == ConflictResolutionStrategy.LAST_WRITE_WINS

    def test_create_composite_state_manager_with_custom_params(self):
        """测试创建组合状态管理器（使用自定义参数）"""
        manager = create_composite_state_manager(
            enable_pooling=False,
            max_pool_size=50,
            enable_diff_tracking=False,
            conflict_strategy=ConflictResolutionStrategy.MERGE_CHANGES
        )
        
        assert isinstance(manager, CompositeStateManager)
        assert manager._enable_pooling is False
        assert manager._max_pool_size == 50
        assert manager._enable_diff_tracking is False
        assert manager._conflict_strategy == ConflictResolutionStrategy.MERGE_CHANGES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])