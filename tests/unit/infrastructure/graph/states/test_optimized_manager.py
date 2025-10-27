"""优化状态管理器单元测试"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from src.infrastructure.graph.states.optimized_manager import (
    StateUpdate,
    OptimizedStateManager,
    create_optimized_state_manager
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


class TestOptimizedStateManager:
    """优化状态管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建优化状态管理器实例"""
        return OptimizedStateManager(
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
        manager = OptimizedStateManager(enable_pooling=False)
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
        
        updated_state = manager.update_state_incremental(state_id, sample_state, updates)
        
        # 验证更新
        assert updated_state["output"] == "新输出"
        assert updated_state["complete"] is True
        # 验证其他字段未改变
        assert updated_state["input"] == sample_state["input"]
        assert updated_state["messages"] == sample_state["messages"]

    def test_update_state_incremental_without_diff_tracking(self, sample_state):
        """测试增量更新状态（不使用差异跟踪）"""
        manager = OptimizedStateManager(enable_diff_tracking=False)
        state_id = "test_state"
        updates = {"output": "新输出"}
        
        updated_state = manager.update_state_incremental(state_id, sample_state, updates)
        
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
        manager.update_state_incremental(state_id, sample_state, updates)
        
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


class TestCreateOptimizedStateManager:
    """创建优化状态管理器函数测试"""

    def test_create_optimized_state_manager_with_defaults(self):
        """测试创建优化状态管理器（使用默认值）"""
        manager = create_optimized_state_manager()
        
        assert isinstance(manager, OptimizedStateManager)
        assert manager._enable_pooling is True
        assert manager._max_pool_size == 100
        assert manager._enable_diff_tracking is True

    def test_create_optimized_state_manager_with_custom_params(self):
        """测试创建优化状态管理器（使用自定义参数）"""
        manager = create_optimized_state_manager(
            enable_pooling=False,
            max_pool_size=10,
            enable_diff_tracking=False
        )
        
        assert isinstance(manager, OptimizedStateManager)
        assert manager._enable_pooling is False
        assert manager._max_pool_size == 10
        assert manager._enable_diff_tracking is False