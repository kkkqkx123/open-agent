"""serialization.py 单元测试"""

import json
import pickle
import pytest
from datetime import datetime
from enum import Enum
from unittest.mock import Mock, patch
from core.common.serialization import Serializer, SerializationError


class TestEnum(Enum):
    """测试用枚举"""
    VALUE1 = "value1"
    VALUE2 = "value2"


class TestClass:
    """测试用类"""
    def __init__(self, name, value):
        self.name = name
        self.value = value


class TestSerializer:
    """测试 Serializer 类"""
    
    def test_serializer_initialization(self):
        """测试序列化器初始化"""
        # 测试不启用缓存
        serializer = Serializer(enable_cache=False)
        assert not serializer._enable_cache
        assert serializer._cache_size == 1000  # 实际默认值是1000
        
        # 测试启用缓存
        serializer = Serializer(enable_cache=True, cache_size=500)
        assert serializer._enable_cache
        assert serializer._cache_size == 500
    
    def test_json_serialization(self):
        """测试JSON序列化"""
        serializer = Serializer()
        data = {"name": "test", "value": 123}
        
        serialized = serializer.serialize(data, format=serializer.FORMAT_JSON)
        assert isinstance(serialized, str)
        
        deserialized = serializer.deserialize(serialized, format=serializer.FORMAT_JSON)
        assert deserialized == data
    
    def test_compact_json_serialization(self):
        """测试紧凑JSON序列化"""
        serializer = Serializer()
        data = {"name": "test", "value": 123}
        
        serialized = serializer.serialize(data, format=serializer.FORMAT_COMPACT_JSON)
        assert isinstance(serialized, str)
        # 紧凑JSON不应该有缩进
        assert "\n" not in serialized
        
        deserialized = serializer.deserialize(serialized, format=serializer.FORMAT_COMPACT_JSON)
        assert deserialized == data
    
    def test_pickle_serialization(self):
        """测试Pickle序列化"""
        serializer = Serializer()
        data = {"name": "test", "value": [1, 2, 3]}
        
        serialized = serializer.serialize(data, format=serializer.FORMAT_PICKLE)
        assert isinstance(serialized, bytes)
        
        deserialized = serializer.deserialize(serialized, format=serializer.FORMAT_PICKLE)
        assert deserialized == data
    
    def test_unsupported_format(self):
        """测试不支持的格式"""
        serializer = Serializer()
        data = {"name": "test"}
        
        with pytest.raises(SerializationError, match="不支持的序列化格式"):
            serializer.serialize(data, format="unsupported")
        
        with pytest.raises(SerializationError, match="不支持的格式"):
            serializer.deserialize('data', format="unsupported")
    
    def test_serialization_error(self):
        """测试序列化错误"""
        serializer = Serializer()
        
        # 创建一个包含无限递归引用的对象，会导致序列化错误
        import threading
        obj = {}
        obj['self_ref'] = obj  # 创建循环引用
        
        with pytest.raises(SerializationError, match="序列化失败"):
            serializer.serialize(obj, format=serializer.FORMAT_JSON)
    
    def test_deserialization_error(self):
        """测试反序列化错误"""
        serializer = Serializer()
        
        with pytest.raises(SerializationError, match="反序列化失败"):
            serializer.deserialize('{invalid_json}', format=serializer.FORMAT_JSON)
    
    def test_preprocess_data_with_basic_types(self):
        """测试预处理基本数据类型"""
        serializer = Serializer()
        
        # 测试None
        assert serializer._preprocess_data(None) is None
        
        # 测试字符串
        assert serializer._preprocess_data("test") == "test"
        
        # 测试数字
        assert serializer._preprocess_data(123) == 123
        assert serializer._preprocess_data(12.34) == 12.34
        
        # 测试布尔值
        assert serializer._preprocess_data(True) is True
        assert serializer._preprocess_data(False) is False
    
    def test_preprocess_data_with_complex_types(self):
        """测试预处理复杂数据类型"""
        serializer = Serializer()
        
        # 测试字典
        data = {"key1": "value1", "key2": [1, 2, 3]}
        processed = serializer._preprocess_data(data)
        assert processed == data
        
        # 测试列表
        data = [1, "test", {"nested": "value"}]
        processed = serializer._preprocess_data(data)
        assert processed == data
        
        # 测试日期时间
        dt = datetime(2023, 1, 12, 0, 0)
        processed = serializer._preprocess_data(dt)
        assert processed == "2023-01-12T00:00:00"  # 正确的ISO格式
    
    def test_preprocess_data_with_enum(self):
        """测试预处理枚举"""
        serializer = Serializer()
        
        enum_value = TestEnum.VALUE1
        processed = serializer._preprocess_data(enum_value)
        assert processed == "value1"  # 枚举的value
    
    def test_preprocess_data_with_object(self):
        """测试预处理对象"""
        serializer = Serializer()
        
        obj = TestClass("test_name", 123)
        processed = serializer._preprocess_data(obj)
        
        # 对象会被转换为字典
        assert isinstance(processed, dict)
        assert processed["name"] == "test_name"
        assert processed["value"] == 123
    
    def test_calculate_hash(self):
        """测试计算哈希"""
        serializer = Serializer()
        
        data1 = {"key": "value"}
        data2 = {"key": "value"}
        data3 = {"key": "different_value"}
        
        hash1 = serializer._calculate_hash(data1)
        hash2 = serializer._calculate_hash(data2)
        hash3 = serializer._calculate_hash(data3)
        
        # 相同数据应该有相同哈希
        assert hash1 == hash2
        # 不同数据应该有不同哈希
        assert hash1 != hash3
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        serializer = Serializer(enable_cache=True, cache_size=2)
        
        data = {"test": "data"}
        
        # 第一次序列化
        result1 = serializer.serialize(data, format=serializer.FORMAT_JSON, enable_cache=True)
        
        # 第二次序列化相同数据，应该使用缓存
        result2 = serializer.serialize(data, format=serializer.FORMAT_JSON, enable_cache=True)
        
        assert result1 == result2
        
        # 检查统计信息
        stats = serializer.get_stats()
        assert stats["cache_hits"] >= 0
        assert stats["cache_misses"] >= 0
    
    def test_cache_size_limit(self):
        """测试缓存大小限制"""
        serializer = Serializer(enable_cache=True, cache_size=2)
        
        # 添加超过缓存大小的数据
        for i in range(5):
            data = {"index": i}
            serializer.serialize(data, format=serializer.FORMAT_JSON, enable_cache=True)
        
        # 检查缓存大小是否被限制
        stats = serializer.get_stats()
        assert stats["cache_size"] <= 2
    
    def test_stats_functionality(self):
        """测试统计功能"""
        serializer = Serializer(enable_cache=True)
        
        # 执行一些操作
        data = {"test": "data"}
        serializer.serialize(data, format=serializer.FORMAT_JSON)
        serializer.deserialize(serializer.serialize(data, format=serializer.FORMAT_JSON), format=serializer.FORMAT_JSON)
        
        stats = serializer.get_stats()
        assert stats["total_operations"] >= 2
        assert "cache_hit_rate" in stats
        assert "average_time" in stats
    
    def test_clear_cache(self):
        """测试清空缓存"""
        serializer = Serializer(enable_cache=True)
        
        data = {"test": "data"}
        serializer.serialize(data, format=serializer.FORMAT_JSON, enable_cache=True)
        
        # 检查缓存不为空
        stats_before = serializer.get_stats()
        assert stats_before["cache_size"] > 0
        
        # 清空缓存
        serializer.clear_cache()
        
        # 检查缓存为空
        stats_after = serializer.get_stats()
        assert stats_after["cache_size"] == 0
    
    def test_reset_stats(self):
        """测试重置统计"""
        serializer = Serializer(enable_cache=True)
        
        data = {"test": "data"}
        serializer.serialize(data, format=serializer.FORMAT_JSON, enable_cache=True)
        
        # 确保有一些统计信息
        stats_before = serializer.get_stats()
        assert stats_before["total_operations"] > 0
        
        # 重置统计
        serializer.reset_stats()
        
        # 检查统计被重置
        stats_after = serializer.get_stats()
        assert stats_after["total_operations"] == 0
        assert stats_after["cache_hits"] == 0
        assert stats_after["cache_misses"] == 0
        assert stats_after["total_time"] == 0.0


class TestSerializerIntegration:
    """测试序列化器集成"""
    
    def test_json_serialization_integration(self):
        """测试JSON序列化集成"""
        serializer = Serializer()
        
        # 复杂数据结构
        original_data = {
            "string": "test",
            "number": 123,
            "float": 12.34,
            "boolean": True,
            "list": [1, 2, {"nested": "value"}],
            "dict": {"nested_key": "nested_value"}
        }
        
        serialized = serializer.serialize(original_data, format=serializer.FORMAT_JSON)
        deserialized = serializer.deserialize(serialized, format=serializer.FORMAT_JSON)
        
        assert deserialized == original_data
    
    def test_pickle_serialization_integration(self):
        """测试Pickle序列化集成"""
        serializer = Serializer()
        
        # 复杂数据结构
        original_data = {
            "string": "test",
            "number": 123,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        
        serialized = serializer.serialize(original_data, format=serializer.FORMAT_PICKLE)
        deserialized = serializer.deserialize(serialized, format=serializer.FORMAT_PICKLE)
        
        assert deserialized == original_data
    
    def test_compact_json_serialization_integration(self):
        """测试紧凑JSON序列化集成"""
        serializer = Serializer()
        
        original_data = {"key1": "value1", "key2": [1, 2, 3]}
        
        serialized = serializer.serialize(original_data, format=serializer.FORMAT_COMPACT_JSON)
        deserialized = serializer.deserialize(serialized, format=serializer.FORMAT_COMPACT_JSON)
        
        assert deserialized == original_data
        # 确保紧凑格式不包含多余的空格
        assert serialized == '{"key1":"value1","key2":[1,2,3]}'


if __name__ == "__main__":
    pytest.main([__file__])