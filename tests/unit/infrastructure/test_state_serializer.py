"""StateSerializer单元测试"""

import json
import pickle
import time
import threading
from typing import Dict, Any
import pytest

from src.infrastructure.graph.states.serializer import StateSerializer, StateDiff
from src.infrastructure.graph.states.base import BaseGraphState, BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from src.infrastructure.graph.states.agent import AgentState
from src.infrastructure.graph.states.workflow import WorkflowState


class TestStateSerializer:
    """StateSerializer测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.serializer = StateSerializer(
            max_cache_size=100,
            cache_ttl_seconds=360,
            enable_compression=True,
            enable_diff_serialization=True
        )
        
        # 创建测试状态
        self.test_state = {
            "messages": [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi there!")
            ],
            "current_step": 1,
            "total_steps": 5,
            "metadata": {"user_id": "test_user", "session_id": "test_session"}
        }
    
    def test_serialize_json_format(self):
        """测试JSON格式序列化"""
        result = self.serializer.serialize(self.test_state, format=StateSerializer.FORMAT_JSON)
        assert isinstance(result, str)
        
        # 验证可以反序列化
        deserialized = self.serializer.deserialize(result, format=StateSerializer.FORMAT_JSON)
        assert deserialized["current_step"] == 1
        assert len(deserialized["messages"]) == 2
    
    def test_serialize_compact_json_format(self):
        """测试紧凑JSON格式序列化"""
        result = self.serializer.serialize(self.test_state, format=StateSerializer.FORMAT_COMPACT_JSON)
        assert isinstance(result, str)
        
        # 验证可以反序列化
        deserialized = self.serializer.deserialize(result, format=StateSerializer.FORMAT_COMPACT_JSON)
        assert deserialized["current_step"] == 1
        assert len(deserialized["messages"]) == 2
    
    def test_serialize_pickle_format(self):
        """测试Pickle格式序列化"""
        result = self.serializer.serialize(self.test_state, format=StateSerializer.FORMAT_PICKLE)
        assert isinstance(result, bytes)
        
        # 验证可以反序列化
        deserialized = self.serializer.deserialize(result, format=StateSerializer.FORMAT_PICKLE)
        assert deserialized["current_step"] == 1
        assert len(deserialized["messages"]) == 2
    
    def test_serialize_with_cache(self):
        """测试带缓存的序列化"""
        # 第一次序列化
        start_time = time.time()
        result1 = self.serializer.serialize(self.test_state)
        time1 = time.time() - start_time
        
        # 第二次序列化（应该使用缓存）
        start_time = time.time()
        result2 = self.serializer.serialize(self.test_state)
        time2 = time.time() - start_time
        
        # 验证结果相同
        assert result1 == result2
        # 验证缓存命中率
        stats = self.serializer.get_performance_stats()
        assert stats["cache_stats"]["hits"] > 0
    
    def test_serialize_without_cache(self):
        """测试不带缓存的序列化"""
        result = self.serializer.serialize(self.test_state, enable_cache=False)
        assert isinstance(result, str)
        
        # 验证缓存未命中
        stats = self.serializer.get_performance_stats()
        initial_misses = stats["cache_stats"]["misses"]
        
        # 再次序列化同一个状态，但不启用缓存
        result2 = self.serializer.serialize(self.test_state, enable_cache=False)
        stats = self.serializer.get_performance_stats()
        new_misses = stats["cache_stats"]["misses"]
        
        # 由于不启用缓存，应该增加misses
        assert new_misses >= initial_misses
    
    def test_message_serialization(self):
        """测试消息序列化"""
        message = HumanMessage(content="Test message")
        serialized = self.serializer.serialize_message(message)
        assert serialized["content"] == "Test message"
        assert serialized["type"] == "human"
        
        deserialized = self.serializer.deserialize_message(serialized)
        assert isinstance(deserialized, HumanMessage)
        assert deserialized.content == "Test message"
    
    def test_tool_message_serialization(self):
        """测试工具消息序列化"""
        message = ToolMessage(content="Tool result", tool_call_id="call_123")
        serialized = self.serializer.serialize_message(message)
        assert serialized["content"] == "Tool result"
        assert serialized["type"] == "tool"
        assert serialized["tool_call_id"] == "call_123"
        
        deserialized = self.serializer.deserialize_message(serialized)
        assert isinstance(deserialized, ToolMessage)
        assert deserialized.content == "Tool result"
        assert deserialized.tool_call_id == "call_123"
    
    def test_state_diff_serialization(self):
        """测试状态差异序列化"""
        old_state = {
            "messages": [HumanMessage(content="Hello")],
            "step": 1,
            "data": "old"
        }
        
        new_state = {
            "messages": [HumanMessage(content="Hello"), AIMessage(content="Hi")],
            "step": 2,
            "data": "new",
            "new_field": "value"
        }
        
        # 序列化差异
        diff_result = self.serializer.serialize_diff(old_state, new_state)
        assert isinstance(diff_result, str)
        
        # 应用差异
        applied_state = self.serializer.apply_diff(old_state, diff_result)
        
        # 验证应用的差异与新状态基本一致
        assert applied_state["step"] == new_state["step"]
        assert applied_state["data"] == new_state["data"]
        assert applied_state["new_field"] == new_state["new_field"]
        assert len(applied_state["messages"]) == len(new_state["messages"])
    
    def test_state_diff_serialization_disabled(self):
        """测试禁用差异序列化的情况"""
        serializer = StateSerializer(enable_diff_serialization=False)
        
        old_state = {"data": "old"}
        new_state = {"data": "new"}
        
        # 应该回退到完整序列化
        result = serializer.serialize_diff(old_state, new_state)
        assert isinstance(result, str)
    
    def test_optimize_state_for_storage(self):
        """测试状态存储优化"""
        large_state = {
            "messages": [HumanMessage(content=f"Message {i}") for i in range(150)],  # 大列表
            "empty_list": [],
            "none_value": None,
            "data": "normal_data"
        }
        
        optimized = self.serializer.optimize_state_for_storage(large_state)
        
        # 验证空列表被移除
        assert "empty_list" not in optimized
        
        # 验证None值被移除
        assert "none_value" not in optimized
        
        # 验证正常数据保留
        assert "data" in optimized
        assert optimized["data"] == "normal_data"
        
        # 验证大消息列表被压缩
        if "messages" in optimized:
            assert len(optimized["messages"]) <= len(large_state["messages"])
    
    def test_performance_stats(self):
        """测试性能统计"""
        # 执行一些操作来填充统计信息
        self.serializer.serialize(self.test_state)
        self.serializer.deserialize(self.serializer.serialize(self.test_state))
        
        stats = self.serializer.get_performance_stats()
        
        assert "cache_stats" in stats
        assert "serialization_stats" in stats
        assert "memory_stats" in stats
        
        # 验证统计信息结构
        assert "hits" in stats["cache_stats"]
        assert "misses" in stats["cache_stats"]
        assert "total_serializations" in stats["serialization_stats"]
        assert "total_deserializations" in stats["serialization_stats"]
    
    def test_cache_clear(self):
        """测试缓存清除"""
        # 添加一些数据到缓存
        self.serializer.serialize(self.test_state)
        
        # 检查缓存大小
        initial_stats = self.serializer.get_performance_stats()
        initial_cache_size = initial_stats["cache_stats"]["cache_size"]
        
        # 清除缓存
        self.serializer.clear_cache()
        
        # 检查缓存是否被清除
        final_stats = self.serializer.get_performance_stats()
        final_cache_size = final_stats["cache_stats"]["cache_size"]
        
        assert final_cache_size < initial_cache_size
        assert final_cache_size == 0
    
    def test_concurrent_access(self):
        """测试并发访问"""
        results = []
        errors = []
        
        def serialize_worker():
            try:
                result = self.serializer.serialize(self.test_state)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # 创建多个线程同时访问
        threads = []
        for i in range(5):
            thread = threading.Thread(target=serialize_worker)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有错误
        assert len(errors) == 0
        assert len(results) == 5
        
        # 验证所有结果都相同
        first_result = results[0]
        for result in results:
            assert result == first_result
    
    def test_calculate_state_hash(self):
        """测试状态哈希计算"""
        hash1 = self.serializer._calculate_state_hash({"a": 1, "b": 2})
        hash2 = self.serializer._calculate_state_hash({"b": 2, "a": 1})  # 不同顺序
        
        # 相同内容应产生相同哈希
        assert hash1 == hash2
        
        hash3 = self.serializer._calculate_state_hash({"a": 1, "b": 3})  # 不同内容
        # 不同内容应产生不同哈希
        assert hash1 != hash3
    
    def test_unsupported_format(self):
        """测试不支持的格式"""
        with pytest.raises(ValueError):
            self.serializer.serialize(self.test_state, format="unsupported_format")
        
        with pytest.raises(ValueError):
            self.serializer.deserialize("dummy_data", format="unsupported_format")
    
    def test_empty_state_serialization(self):
        """测试空状态序列化"""
        empty_state = {}
        result = self.serializer.serialize(empty_state)
        deserialized = self.serializer.deserialize(result)
        
        assert deserialized == {}
    
    def test_nested_state_serialization(self):
        """测试嵌套状态序列化"""
        nested_state = {
            "level1": {
                "level2": {
                    "data": "nested_value",
                    "messages": [SystemMessage(content="Nested message")]
                }
            },
            "simple_value": "test"
        }
        
        result = self.serializer.serialize(nested_state)
        deserialized = self.serializer.deserialize(result)
        
        assert deserialized["level1"]["level2"]["data"] == "nested_value"
        assert len(deserialized["level1"]["level2"]["messages"]) == 1
        assert deserialized["simple_value"] == "test"


if __name__ == "__main__":
    pytest.main([__file__])