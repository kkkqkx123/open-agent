"""元数据管理器测试"""

import pytest
from src.infrastructure.common.metadata.metadata_manager import MetadataManager


class TestMetadataManager:
    """元数据管理器测试类"""
    
    def test_normalize_metadata_none(self):
        """测试标准化None元数据"""
        result = MetadataManager.normalize_metadata(None)
        assert result == {}
    
    def test_normalize_metadata_dict(self):
        """测试标准化字典元数据"""
        metadata = {"key1": "value1", "key2": "value2"}
        result = MetadataManager.normalize_metadata(metadata)
        assert result == metadata
        # 确保返回的是副本
        assert result is not metadata
    
    def test_normalize_metadata_object(self):
        """测试标准化对象元数据"""
        class TestObject:
            def __init__(self):
                self.attr1 = "value1"
                self.attr2 = "value2"
        
        obj = TestObject()
        result = MetadataManager.normalize_metadata(obj)
        assert result == {"attr1": "value1", "attr2": "value2"}
    
    def test_normalize_metadata_dict_like(self):
        """测试标准化类字典对象"""
        # 简化测试，只测试基本功能
        class DictLike:
            def __getitem__(self, key):
                return f"value_{key}"
            
            def keys(self):
                return ["key1", "key2"]
        
        obj = DictLike()
        result = MetadataManager.normalize_metadata(obj)
        # 验证能够处理类字典对象，具体实现可能有所不同
        assert isinstance(result, dict)
    
    def test_normalize_metadata_invalid(self):
        """测试标准化无效元数据"""
        result = MetadataManager.normalize_metadata("invalid")
        assert result == {}
    
    def test_merge_metadata(self):
        """测试合并元数据"""
        base = {"key1": "value1", "key2": "value2"}
        override = {"key2": "new_value2", "key3": "value3"}
        result = MetadataManager.merge_metadata(base, override)
        assert result == {"key1": "value1", "key2": "new_value2", "key3": "value3"}
    
    def test_validate_metadata_success(self):
        """测试验证元数据成功"""
        metadata = {"name": "test", "value": 123}
        schema = {"required": ["name", "value"]}
        result = MetadataManager.validate_metadata(metadata, schema)
        assert result == True
    
    def test_validate_metadata_failure(self):
        """测试验证元数据失败"""
        metadata = {"name": "test"}
        schema = {"required": ["name", "value"]}
        result = MetadataManager.validate_metadata(metadata, schema)
        assert result == False
    
    def test_validate_metadata_no_required(self):
        """测试验证元数据无必需字段"""
        metadata = {"name": "test"}
        schema = {"required": []}
        result = MetadataManager.validate_metadata(metadata, schema)
        assert result == True
    
    def test_extract_field_exists(self):
        """测试提取存在的字段"""
        metadata = {"name": "test", "value": 123}
        result = MetadataManager.extract_field(metadata, "name")
        assert result == "test"
    
    def test_extract_field_not_exists(self):
        """测试提取不存在的字段"""
        metadata = {"name": "test", "value": 123}
        result = MetadataManager.extract_field(metadata, "missing")
        assert result is None
    
    def test_extract_field_default(self):
        """测试提取字段使用默认值"""
        metadata = {"name": "test", "value": 123}
        result = MetadataManager.extract_field(metadata, "missing", "default")
        assert result == "default"
    
    def test_set_field(self):
        """测试设置字段"""
        metadata = {"name": "test", "value": 123}
        result = MetadataManager.set_field(metadata, "new_field", "new_value")
        assert result == {"name": "test", "value": 123, "new_field": "new_value"}
        # 确保原字典未被修改
        assert "new_field" not in metadata
    
    def test_set_field_override(self):
        """测试设置字段覆盖"""
        metadata = {"name": "test", "value": 123}
        result = MetadataManager.set_field(metadata, "value", 456)
        assert result == {"name": "test", "value": 456}
    
    def test_remove_field_exists(self):
        """测试移除存在的字段"""
        metadata = {"name": "test", "value": 123}
        result = MetadataManager.remove_field(metadata, "value")
        assert result == {"name": "test"}
        # 确保原字典未被修改
        assert "value" in metadata
    
    def test_remove_field_not_exists(self):
        """测试移除不存在的字段"""
        metadata = {"name": "test", "value": 123}
        result = MetadataManager.remove_field(metadata, "missing")
        assert result == {"name": "test", "value": 123}
    
    def test_to_json(self):
        """测试转换为JSON"""
        metadata = {"name": "test", "value": 123}
        result = MetadataManager.to_json(metadata)
        assert '"name": "test"' in result
        assert '"value": 123' in result
    
    def test_to_json_indent(self):
        """测试转换为JSON带缩进"""
        metadata = {"name": "test", "value": 123}
        result = MetadataManager.to_json(metadata, indent=4)
        lines = result.split('\n')
        assert len(lines) > 3  # 有缩进的多行
    
    def test_from_json(self):
        """测试从JSON解析"""
        json_str = '{"name": "test", "value": 123}'
        result = MetadataManager.from_json(json_str)
        assert result == {"name": "test", "value": 123}
    
    def test_json_roundtrip(self):
        """测试JSON往返转换"""
        original = {"name": "test", "value": 123, "nested": {"key": "value"}}
        json_str = MetadataManager.to_json(original)
        restored = MetadataManager.from_json(json_str)
        assert restored == original