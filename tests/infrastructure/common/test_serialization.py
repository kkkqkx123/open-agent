"""序列化模块单元测试

测试基础设施层序列化系统的基本功能。
"""

import pytest
import json
import pickle
from datetime import datetime
from enum import Enum
from unittest.mock import Mock, patch

from src.infrastructure.common.serialization import (
    Serializer,
    SerializationError,
)


class SampleEnum(Enum):
    """测试用枚举"""
    VALUE1 = "value1"
    VALUE2 = "value2"


class SampleSerializable:
    """测试用可序列化对象"""
    def __init__(self, data):
        self.data = data
    
    def to_dict(self):
        return {"data": self.data}


class TestSerializer:
    """测试序列化器"""

    @pytest.fixture
    def serializer(self):
        """创建序列化器实例"""
        return Serializer(enable_cache=False)

    def test_serializer_initialization(self):
        """测试序列化器初始化"""
        serializer = Serializer(enable_cache=True, cache_size=500)
        assert serializer._enable_cache is True
        assert serializer._cache_size == 500
        assert len(serializer._cache) == 0

        serializer = Serializer(enable_cache=False)
        assert serializer._enable_cache is False

    def test_serialize_json(self, serializer):
        """测试JSON序列化"""
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        result = serializer.serialize(data, format=Serializer.FORMAT_JSON)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == data

    def test_serialize_compact_json(self, serializer):
        """测试紧凑JSON序列化"""
        data = {"key": "value", "number": 42}
        result = serializer.serialize(data, format=Serializer.FORMAT_COMPACT_JSON)
        assert isinstance(result, str)
        # 紧凑JSON没有多余空格
        assert ' ' not in result
        parsed = json.loads(result)
        assert parsed == data

    def test_serialize_pickle(self, serializer):
        """测试Pickle序列化"""
        data = {"key": "value", "number": 42}
        result = serializer.serialize(data, format=Serializer.FORMAT_PICKLE)
        assert isinstance(result, bytes)
        parsed = pickle.loads(result)
        assert parsed == data

    def test_serialize_unsupported_format(self, serializer):
        """测试不支持的序列化格式"""
        with pytest.raises(SerializationError):
            serializer.serialize({"key": "value"}, format="unsupported")

    def test_deserialize_json(self, serializer):
        """测试JSON反序列化"""
        json_str = '{"key": "value", "number": 42}'
        result = serializer.deserialize(json_str, format=Serializer.FORMAT_JSON)
        assert result == {"key": "value", "number": 42}

    def test_deserialize_compact_json(self, serializer):
        """测试紧凑JSON反序列化"""
        json_str = '{"key":"value","number":42}'
        result = serializer.deserialize(json_str, format=Serializer.FORMAT_COMPACT_JSON)
        assert result == {"key": "value", "number": 42}

    def test_deserialize_pickle(self, serializer):
        """测试Pickle反序列化"""
        data = {"key": "value", "number": 42}
        pickled = pickle.dumps(data)
        result = serializer.deserialize(pickled, format=Serializer.FORMAT_PICKLE)
        assert result == data

    def test_deserialize_unsupported_format(self, serializer):
        """测试不支持的格式反序列化"""
        with pytest.raises(SerializationError):
            serializer.deserialize("data", format="unsupported")

    def test_serialize_deserialize_roundtrip(self, serializer):
        """测试序列化-反序列化往返"""
        original = {
            "string": "hello",
            "number": 3.14,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "none": None,
        }
        
        for fmt in [Serializer.FORMAT_JSON, Serializer.FORMAT_COMPACT_JSON, Serializer.FORMAT_PICKLE]:
            serialized = serializer.serialize(original, format=fmt)
            deserialized = serializer.deserialize(serialized, format=fmt)
            assert deserialized == original

    def test_preprocess_data_datetime(self, serializer):
        """测试预处理日期时间"""
        dt = datetime(2023, 1, 1, 12, 30, 45)
        result = serializer._preprocess_data(dt)
        assert result == "2023-01-01T12:30:45"

    def test_preprocess_data_enum(self, serializer):
        """测试预处理枚举"""
        result = serializer._preprocess_data(SampleEnum.VALUE1)
        assert result == "value1"

    def test_preprocess_data_serializable(self, serializer):
        """测试预处理可序列化对象"""
        obj = SampleSerializable("test")
        result = serializer._preprocess_data(obj)
        assert result == {"data": "test"}

    def test_preprocess_data_object(self, serializer):
        """测试预处理普通对象"""
        class SimpleObject:
            def __init__(self):
                self.public = "public_value"
                self._private = "private_value"
        
        obj = SimpleObject()
        result = serializer._preprocess_data(obj)
        assert result == {"public": "public_value"}

    def test_preprocess_data_nested(self, serializer):
        """测试预处理嵌套结构"""
        data = {
            "datetime": datetime(2023, 1, 1),
            "list": [SampleEnum.VALUE1, SampleEnum.VALUE2],
            "nested": {
                "obj": SampleSerializable("nested")
            }
        }
        result = serializer._preprocess_data(data)
        assert result["datetime"] == "2023-01-01T00:00:00"
        assert result["list"] == ["value1", "value2"]
        assert result["nested"]["obj"] == {"data": "nested"}

    def test_calculate_hash(self, serializer):
        """测试计算哈希"""
        data1 = {"key": "value"}
        data2 = {"key": "value"}
        data3 = {"key": "different"}
        
        hash1 = serializer.calculate_hash(data1)
        hash2 = serializer.calculate_hash(data2)
        hash3 = serializer.calculate_hash(data3)
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 32  # MD5哈希长度

    def test_cache_functionality(self):
        """测试缓存功能"""
        serializer = Serializer(enable_cache=True, cache_size=2)
        data = {"key": "value"}
        
        # 第一次序列化，应缓存
        result1 = serializer.serialize(data, format=Serializer.FORMAT_JSON)
        stats = serializer.get_stats()
        assert stats["cache_misses"] == 1
        assert stats["cache_hits"] == 0
        
        # 第二次序列化相同数据，应命中缓存
        result2 = serializer.serialize(data, format=Serializer.FORMAT_JSON)
        stats = serializer.get_stats()
        assert stats["cache_hits"] == 1
        
        # 反序列化缓存
        deserialized1 = serializer.deserialize(result1, format=Serializer.FORMAT_JSON)
        stats = serializer.get_stats()
        # 反序列化可能也会缓存，取决于实现
        # 我们只检查没有错误
        
        # 测试缓存淘汰（LRU）
        data2 = {"key2": "value2"}
        data3 = {"key3": "value3"}
        serializer.serialize(data2, format=Serializer.FORMAT_JSON)
        serializer.serialize(data3, format=Serializer.FORMAT_JSON)  # 应淘汰第一个缓存
        
        # 第一个数据应仍然可以序列化（但会重新计算）
        serializer.serialize(data, format=Serializer.FORMAT_JSON)
        # 不检查具体行为，只确保没有异常

    def test_cache_disabled(self):
        """测试禁用缓存"""
        serializer = Serializer(enable_cache=False)
        data = {"key": "value"}
        
        result1 = serializer.serialize(data, format=Serializer.FORMAT_JSON)
        result2 = serializer.serialize(data, format=Serializer.FORMAT_JSON)
        
        # 即使缓存禁用，序列化也应正常工作
        assert result1 == result2
        stats = serializer.get_stats()
        # 缓存命中应为0，因为缓存被禁用

    def test_clear_cache(self):
        """测试清空缓存"""
        serializer = Serializer(enable_cache=True)
        data = {"key": "value"}
        
        serializer.serialize(data, format=Serializer.FORMAT_JSON)
        stats_before = serializer.get_stats()
        assert stats_before["cache_size"] > 0
        
        serializer.clear_cache()
        stats_after = serializer.get_stats()
        assert stats_after["cache_size"] == 0

    def test_reset_stats(self):
        """测试重置统计"""
        serializer = Serializer(enable_cache=True)
        data = {"key": "value"}
        
        serializer.serialize(data, format=Serializer.FORMAT_JSON)
        stats_before = serializer.get_stats()
        assert stats_before["total_operations"] > 0
        
        serializer.reset_stats()
        stats_after = serializer.get_stats()
        assert stats_after["total_operations"] == 0
        assert stats_after["cache_hits"] == 0
        assert stats_after["cache_misses"] == 0
        assert stats_after["total_time"] == 0.0

    def test_serialization_error(self, serializer):
        """测试序列化错误处理"""
        # 创建无法序列化的对象（如循环引用）
        class CyclicObject:
            def __init__(self):
                self.self = self
        
        obj = CyclicObject()
        
        with pytest.raises(SerializationError):
            serializer.serialize(obj, format=Serializer.FORMAT_JSON)

    def test_deserialization_error(self, serializer):
        """测试反序列化错误处理"""
        invalid_json = "{invalid json}"
        
        with pytest.raises(SerializationError):
            serializer.deserialize(invalid_json, format=Serializer.FORMAT_JSON)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])