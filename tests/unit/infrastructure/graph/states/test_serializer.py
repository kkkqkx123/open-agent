"""状态序列化器单元测试"""

import pytest
import json
import pickle
from unittest.mock import Mock, patch
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass

from src.infrastructure.graph.states.serializer import (
    CacheEntry,
    StateDiff,
    StateSerializer
)
from src.infrastructure.graph.states.base import BaseMessage, HumanMessage, AIMessage, ToolMessage


class TestCacheEntry:
    """缓存条目测试"""

    def test_init(self):
        """测试初始化"""
        entry = CacheEntry(
            serialized_data="序列化数据",
            state_hash="hash123",
            created_at=123456.789,
            access_count=5,
            last_accessed=123456.790
        )
        assert entry.serialized_data == "序列化数据"
        assert entry.state_hash == "hash123"
        assert entry.created_at == 123456.789
        assert entry.access_count == 5
        assert entry.last_accessed == 123456.790

    def test_is_expired_true(self):
        """测试是否过期（真）"""
        entry = CacheEntry(
            serialized_data="序列化数据",
            state_hash="hash123",
            created_at=123456.789  # 很久以前创建的
        )
        result = entry.is_expired(ttl_seconds=1)  # 1秒过期
        assert result is True

    def test_is_expired_false(self):
        """测试是否过期（假）"""
        entry = CacheEntry(
            serialized_data="序列化数据",
            state_hash="hash123",
            created_at=datetime.now().timestamp()  # 刚刚创建的
        )
        result = entry.is_expired(ttl_seconds=3600)  # 1小时过期
        assert result is False


class TestStateDiff:
    """状态差异测试"""

    def test_init(self):
        """测试初始化"""
        diff = StateDiff(
            added={"new_field": "新值"},
            modified={"existing_field": "修改值"},
            removed={"old_field"},
            timestamp=123456.789
        )
        assert diff.added == {"new_field": "新值"}
        assert diff.modified == {"existing_field": "修改值"}
        assert diff.removed == {"old_field"}
        assert diff.timestamp == 123456.789


class TestStateSerializer:
    """状态序列化器测试"""

    @pytest.fixture
    def serializer(self) -> StateSerializer:
        """创建状态序列化器实例"""
        return StateSerializer(
            max_cache_size=10,
            cache_ttl_seconds=3600,
            enable_compression=True,
            enable_diff_serialization=True
        )

    @pytest.fixture
    def sample_state(self) -> dict:
        """示例状态"""
        return {
            "messages": [
                HumanMessage(content="用户输入"),
                AIMessage(content="AI响应")
            ],
            "input": "测试输入",
            "output": "测试输出",
            "tool_calls": [{"name": "tool1", "arguments": {}}],
            "tool_results": [{"result": "工具结果"}],
            "iteration_count": 1,
            "max_iterations": 10,
            "errors": [],
            "complete": False,
            "metadata": {"key": "value"}
        }

    def test_init(self, serializer):
        """测试初始化"""
        assert serializer._max_cache_size == 10
        assert serializer._cache_ttl_seconds == 3600
        assert serializer._enable_compression is True
        assert serializer._enable_diff_serialization is True
        assert isinstance(serializer._serialization_cache, dict)
        assert isinstance(serializer._diff_cache, dict)
        assert isinstance(serializer._message_cache, dict)

    def test_serialize_message(self, serializer):
        """测试序列化消息"""
        message = HumanMessage(content="测试消息")
        serialized = StateSerializer.serialize_message(message)
        
        assert isinstance(serialized, dict)
        assert serialized["content"] == "测试消息"
        assert serialized["type"] == "human"

    def test_serialize_message_tool(self, serializer) -> None:
        """测试序列化工具消息"""
        message = ToolMessage(content='工具消息', tool_call_id='tool_123')

        serialized = StateSerializer.serialize_message(message)
        
        assert isinstance(serialized, dict)
        assert serialized["content"] == "工具消息"
        assert serialized["type"] == "tool"
        assert serialized["tool_call_id"] == "tool_123"

    def test_deserialize_message_human(self, serializer):
        """测试反序列化人类消息"""
        message_data = {"content": "测试消息", "type": "human"}
        message = StateSerializer.deserialize_message(message_data)
        
        assert isinstance(message, HumanMessage)
        assert message.content == "测试消息"

    def test_deserialize_message_ai(self, serializer):
        """测试反序列化AI消息"""
        message_data = {"content": "AI响应", "type": "ai"}
        message = StateSerializer.deserialize_message(message_data)
        
        assert isinstance(message, AIMessage)
        assert message.content == "AI响应"

    def test_deserialize_message_tool(self, serializer):
        """测试反序列化工具消息"""
        message_data = {
            "content": "工具消息", 
            "type": "tool", 
            "tool_call_id": "tool_123"
        }
        message = StateSerializer.deserialize_message(message_data)
        
        assert isinstance(message, ToolMessage)
        assert message.content == "工具消息"
        assert message.type == "tool"
        assert message.tool_call_id == "tool_123"

    def test_serialize_json(self, serializer, sample_state):
        """测试JSON序列化"""
        serialized = serializer.serialize(sample_state, format=StateSerializer.FORMAT_JSON)
        
        assert isinstance(serialized, str)
        # 验证可以解析回JSON
        parsed = json.loads(serialized)
        assert "input" in parsed
        assert parsed["input"] == "测试输入"

    def test_serialize_compact_json(self, serializer, sample_state):
        """测试紧凑JSON序列化"""
        serialized = serializer.serialize(sample_state, format=StateSerializer.FORMAT_COMPACT_JSON)
        
        assert isinstance(serialized, str)
        # 验证可以解析回JSON
        parsed = json.loads(serialized)
        assert "input" in parsed
        assert parsed["input"] == "测试输入"

    def test_serialize_pickle(self, serializer, sample_state):
        """测试Pickle序列化"""
        serialized = serializer.serialize(sample_state, format=StateSerializer.FORMAT_PICKLE)
        
        assert isinstance(serialized, bytes)
        # 验证可以反序列化回对象
        deserialized = pickle.loads(serialized)
        assert "input" in deserialized
        assert deserialized["input"] == "测试输入"

    def test_serialize_with_cache(self, serializer, sample_state):
        """测试序列化（使用缓存）"""
        # 第一次序列化
        serialized1 = serializer.serialize(sample_state, format=StateSerializer.FORMAT_COMPACT_JSON)
        
        # 第二次序列化，应该使用缓存
        serialized2 = serializer.serialize(sample_state, format=StateSerializer.FORMAT_COMPACT_JSON)
        
        assert serialized1 == serialized2
        assert serializer._stats["cache_hits"] == 1
        assert serializer._stats["cache_misses"] == 1

    def test_deserialize_json(self, serializer, sample_state):
        """测试JSON反序列化"""
        # 先序列化
        serialized = serializer.serialize(sample_state, format=StateSerializer.FORMAT_JSON)
        
        # 再反序列化
        deserialized = serializer.deserialize(serialized, format=StateSerializer.FORMAT_JSON)
        
        assert isinstance(deserialized, dict)
        assert deserialized["input"] == "测试输入"
        assert len(deserialized["messages"]) == 2
        assert isinstance(deserialized["messages"][0], HumanMessage)
        assert isinstance(deserialized["messages"][1], AIMessage)

    def test_deserialize_compact_json(self, serializer, sample_state):
        """测试紧凑JSON反序列化"""
        # 先序列化
        serialized = serializer.serialize(sample_state, format=StateSerializer.FORMAT_COMPACT_JSON)
        
        # 再反序列化
        deserialized = serializer.deserialize(serialized, format=StateSerializer.FORMAT_COMPACT_JSON)
        
        assert isinstance(deserialized, dict)
        assert deserialized["input"] == "测试输入"

    def test_deserialize_pickle(self, serializer, sample_state):
        """测试Pickle反序列化"""
        # 先序列化
        serialized = serializer.serialize(sample_state, format=StateSerializer.FORMAT_PICKLE)
        
        # 再反序列化
        deserialized = serializer.deserialize(serialized, format=StateSerializer.FORMAT_PICKLE)
        
        assert isinstance(deserialized, dict)
        assert deserialized["input"] == "测试输入"

    def test_serialize_diff(self, serializer, sample_state):
        """测试序列化状态差异"""
        old_state = sample_state.copy()
        new_state = sample_state.copy()
        new_state["output"] = "新输出"
        new_state["new_field"] = "新字段"
        
        diff_data = serializer.serialize_diff(
            old_state, 
            new_state, 
            format=StateSerializer.FORMAT_COMPACT_JSON
        )
        
        assert isinstance(diff_data, str)
        # 验证可以解析回JSON
        parsed = json.loads(diff_data)
        assert "added" in parsed
        assert "modified" in parsed
        assert "removed" in parsed

    def test_apply_diff(self, serializer, sample_state):
        """测试应用状态差异"""
        # 创建差异数据
        diff_data = {
            "added": {"new_field": "新字段"},
            "modified": {"output": "新输出"},
            "removed": [],
            "timestamp": datetime.now().timestamp()
        }
        diff_json = json.dumps(diff_data, separators=(',', ':'))
        
        # 应用差异
        updated_state = serializer.apply_diff(
            sample_state, 
            diff_json, 
            format=StateSerializer.FORMAT_COMPACT_JSON
        )
        
        # 验证更新
        assert updated_state["new_field"] == "新字段"
        assert updated_state["output"] == "新输出"

    def test_optimize_state_for_storage(self, serializer, sample_state):
        """测试优化状态用于存储"""
        # 添加一些空字段
        sample_state["empty_list"] = []
        sample_state["none_value"] = None
        
        optimized = serializer.optimize_state_for_storage(sample_state)
        
        # 验证优化结果
        assert isinstance(optimized, dict)
        # 空列表和None值应该被移除
        assert "empty_list" not in optimized
        assert "none_value" not in optimized
        # 其他字段应该保留
        assert optimized["input"] == "测试输入"

    def test_get_performance_stats(self, serializer):
        """测试获取性能统计"""
        stats = serializer.get_performance_stats()
        
        assert isinstance(stats, dict)
        assert "cache_stats" in stats
        assert "serialization_stats" in stats
        assert "memory_stats" in stats
        
        cache_stats = stats["cache_stats"]
        assert "hits" in cache_stats
        assert "misses" in cache_stats
        assert "hit_rate" in cache_stats

    def test_clear_cache(self, serializer, sample_state):
        """测试清除缓存"""
        # 先序列化以填充缓存
        serializer.serialize(sample_state, format=StateSerializer.FORMAT_COMPACT_JSON)
        
        # 验证缓存不为空
        assert len(serializer._serialization_cache) > 0
        
        # 清除缓存
        serializer.clear_cache()
        
        # 验证缓存已清空
        assert len(serializer._serialization_cache) == 0
        assert serializer._stats["cache_hits"] == 0
        assert serializer._stats["cache_misses"] == 0

    def test_calculate_state_hash(self, serializer, sample_state):
        """测试计算状态哈希"""
        hash1 = serializer._calculate_state_hash(sample_state)
        hash2 = serializer._calculate_state_hash(sample_state.copy())  # 相同内容
        
        assert isinstance(hash1, str)
        assert len(hash1) == 32  # MD5哈希长度
        assert hash1 == hash2  # 相同内容应该产生相同哈希

    def test_prepare_state_for_serialization(self, serializer, sample_state):
        """测试准备状态用于序列化"""
        prepared = serializer._prepare_state_for_serialization(sample_state, include_metadata=True)
        
        assert isinstance(prepared, dict)
        assert "input" in prepared
        assert "messages" in prepared
        assert "_serialization_metadata" in prepared

    def test_process_value_for_serialization_message(self, serializer):
        """测试处理值用于序列化（消息对象）"""
        message = HumanMessage(content="测试消息")
        processed = serializer._process_value_for_serialization(message)
        
        assert isinstance(processed, dict)
        assert processed["content"] == "测试消息"
        assert processed["type"] == "human"

    def test_process_value_for_serialization_list(self, serializer):
        """测试处理值用于序列化（列表）"""
        messages = [HumanMessage(content="消息1"), AIMessage(content="消息2")]
        processed = serializer._process_value_for_serialization(messages)
        
        assert isinstance(processed, list)
        assert len(processed) == 2
        assert isinstance(processed[0], dict)
        assert isinstance(processed[1], dict)

    def test_process_value_for_serialization_dict(self, serializer):
        """测试处理值用于序列化（字典）"""
        state = {"message": HumanMessage(content="测试消息")}
        processed = serializer._process_value_for_serialization(state)
        
        assert isinstance(processed, dict)
        assert isinstance(processed["message"], dict)
        assert processed["message"]["content"] == "测试消息"

    def test_restore_state_from_serialization(self, serializer, sample_state):
        """测试从序列化数据恢复状态"""
        # 准备序列化数据
        prepared = serializer._prepare_state_for_serialization(sample_state, include_metadata=False)
        serialized = json.dumps(prepared, separators=(',', ':'))
        parsed = json.loads(serialized)
        
        # 恢复状态
        restored = serializer._restore_state_from_serialization(parsed)
        
        assert isinstance(restored, dict)
        assert restored["input"] == "测试输入"
        assert len(restored["messages"]) == 2
        assert isinstance(restored["messages"][0], HumanMessage)
        assert isinstance(restored["messages"][1], AIMessage)

    def test_compute_state_diff(self, serializer, sample_state):
        """测试计算状态差异"""
        import copy
        old_state = copy.deepcopy(sample_state)
        new_state = copy.deepcopy(sample_state)
        new_state["output"] = "新输出"
        new_state["new_field"] = "新字段"
        new_state["messages"].append(AIMessage(content="新消息"))
        
        diff = serializer._compute_state_diff(old_state, new_state)
        
        assert isinstance(diff, StateDiff)
        assert "new_field" in diff.added
        assert "output" in diff.modified
        # messages字段已存在，只是内容发生变化，应该在modified中
        assert "messages" in diff.modified
        assert len(diff.modified["messages"]) == 3  # 从2条增加到3条

    def test_deep_equal_true(self, serializer):
        """测试深度比较（真）"""
        obj1 = {"messages": [HumanMessage(content="消息1")], "input": "输入"}
        obj2 = {"messages": [HumanMessage(content="消息1")], "input": "输入"}
        
        result = serializer._deep_equal(obj1, obj2)
        assert result is True

    def test_deep_equal_false(self, serializer):
        """测试深度比较（假）"""
        obj1 = {"messages": [HumanMessage(content="消息1")], "input": "输入"}
        obj2 = {"messages": [HumanMessage(content="消息2")], "input": "输入"}
        
        result = serializer._deep_equal(obj1, obj2)
        assert result is False

    def test_apply_state_diff(self, serializer, sample_state):
        """测试应用状态差异"""
        diff = StateDiff(
            added={"new_field": "新字段"},
            modified={"output": "新输出"},
            removed=set(),
            timestamp=datetime.now().timestamp()
        )
        
        updated_state = serializer._apply_state_diff(sample_state, diff)
        
        assert updated_state["new_field"] == "新字段"
        assert updated_state["output"] == "新输出"

    def test_get_from_cache_hit(self, serializer, sample_state):
        """测试从缓存获取（命中）"""
        state_hash = "test_hash"
        cached_data = "缓存数据"
        
        # 添加到缓存
        serializer._add_to_cache(state_hash, cached_data)
        
        # 从缓存获取
        result = serializer._get_from_cache(state_hash)
        
        assert result == cached_data

    def test_get_from_cache_miss(self, serializer):
        """测试从缓存获取（未命中）"""
        result = serializer._get_from_cache("nonexistent_hash")
        assert result is None

    def test_add_to_cache(self, serializer):
        """测试添加到缓存"""
        state_hash = "test_hash"
        serialized_data = "序列化数据"
        
        serializer._add_to_cache(state_hash, serialized_data)
        
        assert state_hash in serializer._serialization_cache
        assert serializer._serialization_cache[state_hash].serialized_data == serialized_data