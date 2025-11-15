"""通用序列化器测试"""

import pytest
import json
import pickle
from datetime import datetime
from enum import Enum
from src.infrastructure.common.serialization.universal_serializer import UniversalSerializer, SerializationError
from src.infrastructure.common.interfaces import ISerializable


class TestEnum(Enum):
    """测试枚举"""
    VALUE1 = "value1"
    VALUE2 = "value2"


class TestSerializable(ISerializable):
    """测试可序列化类"""
    
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value
    
    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value}
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TestSerializable':
        return cls(data["name"], data["value"])


class TestUniversalSerializer:
    """通用序列化器测试类"""
    
    def setup_method(self):
        """设置测试环境"""
        self.serializer = UniversalSerializer()
    
    def test_serialize_json(self):
        """测试JSON序列化"""
        data = {"name": "test", "value": 123}
        result = self.serializer.serialize(data, "json")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == data
    
    def test_serialize_compact_json(self):
        """测试紧凑JSON序列化"""
        data = {"name": "test", "value": 123}
        result = self.serializer.serialize(data, "compact_json")
        assert isinstance(result, str)
        assert ":" in result  # 紧凑格式包含冒号
        # 确保没有缩进
        assert "\n" not in result
    
    def test_serialize_pickle(self):
        """测试Pickle序列化"""
        data = {"name": "test", "value": 123}
        result = self.serializer.serialize(data, "pickle")
        assert isinstance(result, bytes)
    
    def test_deserialize_json(self):
        """测试JSON反序列化"""
        data = {"name": "test", "value": 123}
        serialized = json.dumps(data)
        result = self.serializer.deserialize(serialized, "json")
        assert result == data
    
    def test_deserialize_compact_json(self):
        """测试紧凑JSON反序列化"""
        data = {"name": "test", "value": 123}
        serialized = json.dumps(data, separators=(',', ':'))
        result = self.serializer.deserialize(serialized, "compact_json")
        assert result == data
    
    def test_deserialize_pickle(self):
        """测试Pickle反序列化"""
        data = {"name": "test", "value": 123}
        serialized = pickle.dumps(data)
        result = self.serializer.deserialize(serialized, "pickle")
        assert result == data
    
    def test_serialize_datetime(self):
        """测试日期时间序列化"""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        data = {"timestamp": dt}
        result = self.serializer.serialize(data, "json")
        parsed = json.loads(result)
        assert parsed["timestamp"] == dt.isoformat()
    
    def test_serialize_enum(self):
        """测试枚举序列化"""
        data = {"enum_value": TestEnum.VALUE1}
        result = self.serializer.serialize(data, "json")
        parsed = json.loads(result)
        assert "TestEnum" in parsed["enum_value"]
        assert "VALUE1" in parsed["enum_value"]
    
    def test_serialize_serializable(self):
        """测试可序列化对象"""
        obj = TestSerializable("test", 123)
        data = {"object": obj}
        result = self.serializer.serialize(data, "json")
        parsed = json.loads(result)
        
        # 检查序列化后的结构
        assert "__type__" in parsed["object"]
        assert parsed["object"]["__type__"] == "TestSerializable"
        assert "data" in parsed["object"]
        assert parsed["object"]["data"]["name"] == "test"
        assert parsed["object"]["data"]["value"] == 123
    
    def test_serialize_nested_structures(self):
        """测试嵌套结构序列化"""
        data = {
            "level1": {
                "level2": {
                    "datetime": datetime(2023, 1, 1, 12, 0, 0),
                    "enum": TestEnum.VALUE1,
                    "serializable": TestSerializable("nested", 456)
                }
            }
        }
        result = self.serializer.serialize(data, "json")
        parsed = json.loads(result)
        assert parsed["level1"]["level2"]["datetime"] == datetime(2023, 1, 1, 12, 0, 0).isoformat()
        assert "TestEnum" in parsed["level1"]["level2"]["enum"]
        assert parsed["level1"]["level2"]["serializable"]["data"]["name"] == "nested"
    
    def test_serialize_list(self):
        """测试列表序列化"""
        data = [
            {"name": "item1", "value": 1},
            {"name": "item2", "value": 2},
            datetime(2023, 1, 1, 12, 0, 0)
        ]
        result = self.serializer.serialize(data, "json")
        parsed = json.loads(result)
        assert len(parsed) == 3
        assert parsed[0]["name"] == "item1"
        assert parsed[2] == datetime(2023, 1, 1, 12, 0, 0).isoformat()
    
    def test_serialize_error_invalid_format(self):
        """测试序列化错误 - 无效格式"""
        data = {"name": "test", "value": 123}
        with pytest.raises(SerializationError):
            self.serializer.serialize(data, "invalid_format")
    
    def test_deserialize_error_invalid_format(self):
        """测试反序列化错误 - 无效格式"""
        data = "test"
        with pytest.raises(SerializationError):
            self.serializer.deserialize(data, "invalid_format")
    
    def test_deserialize_error_invalid_json(self):
        """测试反序列化错误 - 无效JSON"""
        data = "invalid json"
        with pytest.raises(SerializationError):
            self.serializer.deserialize(data, "json")
    
    def test_deserialize_error_invalid_pickle(self):
        """测试反序列化错误 - 无效Pickle"""
        data = b"invalid pickle"
        with pytest.raises(SerializationError):
            self.serializer.deserialize(data, "pickle")
    
    def test_roundtrip_json(self):
        """测试JSON往返序列化"""
        original = {
            "string": "test",
            "number": 123,
            "boolean": True,
            "null": None,
            "datetime": datetime(2023, 1, 1, 12, 0, 0),
            "enum": TestEnum.VALUE1,
            "serializable": TestSerializable("roundtrip", 789),
            "nested": {
                "list": [1, 2, 3],
                "dict": {"key": "value"}
            }
        }
        serialized = self.serializer.serialize(original, "json")
        deserialized = self.serializer.deserialize(serialized, "json")
        
        # 验证基本类型
        assert deserialized["string"] == original["string"]
        assert deserialized["number"] == original["number"]
        assert deserialized["boolean"] == original["boolean"]
        assert deserialized["null"] == original["null"]
        
        # 验证特殊类型
        assert deserialized["datetime"] == original["datetime"].isoformat()
        assert "TestEnum" in deserialized["enum"]
        assert deserialized["serializable"]["data"]["name"] == original["serializable"].name
        assert deserialized["nested"]["list"] == original["nested"]["list"]
    
    def test_roundtrip_pickle(self):
        """测试Pickle往返序列化"""
        original = {
            "string": "test",
            "number": 123,
            "datetime": datetime(2023, 1, 1, 12, 0, 0),
            "enum": TestEnum.VALUE1,
            "serializable": TestSerializable("roundtrip", 789)
        }
        serialized = self.serializer.serialize(original, "pickle")
        deserialized = self.serializer.deserialize(serialized, "pickle")
        
        # Pickle会预处理数据，所以验证预处理后的结构
        assert deserialized["string"] == original["string"]
        assert deserialized["number"] == original["number"]
        # datetime会被转换为ISO字符串
        assert deserialized["datetime"] == original["datetime"].isoformat()
        # enum会被转换为字符串
        assert deserialized["enum"] == "TestEnum.VALUE1"
        # serializable会被转换为字典结构
        assert deserialized["serializable"]["__type__"] == "TestSerializable"
        assert deserialized["serializable"]["data"]["name"] == original["serializable"].name
        assert deserialized["serializable"]["data"]["value"] == original["serializable"].value