"""MetadataManager单元测试"""

from src.core.common.utils.metadata import MetadataManager


class TestMetadataManager:
    """MetadataManager测试类"""

    def test_normalize_metadata_none(self):
        """测试标准化None元数据"""
        result = MetadataManager.normalize_metadata(None)
        assert result == {}

    def test_normalize_metadata_dict(self):
        """测试标准化字典元数据"""
        original = {"key1": "value1", "key2": "value2"}
        result = MetadataManager.normalize_metadata(original)
        
        assert result == original
        assert isinstance(result, dict)

    def test_normalize_metadata_object_with_dict(self):
        """测试标准化具有__dict__属性的对象"""
        class TestObj:
            def __init__(self):
                self.attr1 = "value1"
                self.attr2 = "value2"
        
        obj = TestObj()
        result = MetadataManager.normalize_metadata(obj)
        
        assert result == {"attr1": "value1", "attr2": "value2"}

    def test_normalize_metadata_mapping_like(self):
        """测试标准化类映射对象"""
        class MappingLike:
            def __init__(self):
                self._data = {"key1": "value1", "key2": "value2"}
            
            def __getitem__(self, key):
                return self._data[key]
            
            def __iter__(self):
                return iter(self._data)
            
            def keys(self):
                return self._data.keys()
        
        mapping_obj = MappingLike()
        result = MetadataManager.normalize_metadata(mapping_obj)
        
        assert result == {"key1": "value1", "key2": "value2"}

    def test_normalize_metadata_mapping_like_without_keys(self):
        """测试没有keys方法的类映射对象"""
        class SimpleMapping:
            def __init__(self):
                self.data = {"key1": "value1", "key2": "value2"}
            
            def __getitem__(self, key):
                return self.data[key]
            
            def __iter__(self):
                return iter(self.data)
        
        mapping_obj = SimpleMapping()
        result = MetadataManager.normalize_metadata(mapping_obj)
        
        assert result == {"key1": "value1", "key2": "value2"}

    def test_normalize_metadata_other_types(self):
        """测试其他类型元数据"""
        # 测试字符串
        result = MetadataManager.normalize_metadata("string_value")
        assert result == {}

        # 测试数字
        result = MetadataManager.normalize_metadata(123)
        assert result == {}

        # 测试列表
        result = MetadataManager.normalize_metadata([1, 2, 3])
        assert result == {}

    def test_merge_metadata(self):
        """测试合并元数据"""
        base = {"key1": "base_value1", "key2": "base_value2"}
        override = {"key2": "override_value2", "key3": "new_value3"}
        
        result = MetadataManager.merge_metadata(base, override)
        
        expected = {
            "key1": "base_value1",  # 来自base
            "key2": "override_value2",  # 来自override（覆盖）
            "key3": "new_value3"  # 来自override（新增）
        }
        
        assert result == expected

    def test_validate_metadata_simple(self):
        """测试简单元数据验证"""
        metadata = {"name": "test", "version": "1.0"}
        schema = {"required": ["name"]}
        
        result = MetadataManager.validate_metadata(metadata, schema)
        assert result is True

    def test_validate_metadata_missing_required_field(self):
        """测试验证缺少必需字段的元数据"""
        metadata = {"version": "1.0"}  # 缺少name字段
        schema = {"required": ["name"]}
        
        result = MetadataManager.validate_metadata(metadata, schema)
        assert result is False

    def test_validate_metadata_multiple_required_fields(self):
        """测试验证多个必需字段"""
        # 包含所有必需字段
        metadata = {"name": "test", "version": "1.0", "type": "config"}
        schema = {"required": ["name", "version"]}
        
        result = MetadataManager.validate_metadata(metadata, schema)
        assert result is True

        # 缺少一个必需字段
        metadata_missing = {"name": "test", "type": "config"}  # 缺少version
        result = MetadataManager.validate_metadata(metadata_missing, schema)
        assert result is False

    def test_extract_field(self):
        """测试提取字段值"""
        metadata = {"key1": "value1", "key2": "value2", "nested": {"inner": "inner_value"}}

        # 提取存在的字段
        result = MetadataManager.extract_field(metadata, "key1")
        assert result == "value1"

        # 提取不存在的字段（无默认值）
        result = MetadataManager.extract_field(metadata, "nonexistent")
        assert result is None

        # 提取不存在的字段（有默认值）
        result = MetadataManager.extract_field(metadata, "nonexistent", "default_value")
        assert result == "default_value"

    def test_set_field(self):
        """测试设置字段值"""
        metadata = {"key1": "value1", "key2": "value2"}

        # 设置新字段
        result = MetadataManager.set_field(metadata, "key3", "value3")
        assert result["key3"] == "value3"
        assert "key3" not in metadata  # 原字典不应被修改

        # 更新现有字段
        result = MetadataManager.set_field(metadata, "key1", "new_value1")
        assert result["key1"] == "new_value1"
        assert metadata["key1"] == "value1"  # 原字典不应被修改

    def test_remove_field(self):
        """测试移除字段"""
        metadata = {"key1": "value1", "key2": "value2", "key3": "value3"}

        # 移除存在的字段
        result = MetadataManager.remove_field(metadata, "key2")
        assert "key2" not in result
        assert len(result) == 2
        assert metadata["key2"] == "value2"  # 原字典不应被修改

        # 移除不存在的字段
        result = MetadataManager.remove_field(metadata, "nonexistent")
        assert result == metadata  # 字典应保持不变

    def test_to_json(self):
        """测试转换为JSON字符串"""
        metadata = {"name": "test", "count": 42, "active": True, "tags": ["a", "b"]}
        
        json_str = MetadataManager.to_json(metadata)
        
        # 验证返回的是字符串
        assert isinstance(json_str, str)
        
        # 验证可以解析回相同的字典
        import json
        parsed = json.loads(json_str)
        assert parsed == metadata

    def test_from_json(self):
        """测试从JSON字符串解析"""
        json_str = '{"name": "test", "count": 42, "active": true, "tags": ["a", "b"]}'
        
        result = MetadataManager.from_json(json_str)
        
        expected = {"name": "test", "count": 42, "active": True, "tags": ["a", "b"]}
        assert result == expected

    def test_json_roundtrip(self):
        """测试JSON往返转换"""
        original = {"name": "test", "count": 42, "nested": {"inner": "value"}}
        
        # 转换为JSON再解析回来
        json_str = MetadataManager.to_json(original)
        result = MetadataManager.from_json(json_str)
        
        assert result == original

    def test_complex_metadata_operations(self):
        """测试复杂元数据操作"""
        # 创建复杂的元数据
        base_metadata = {
            "name": "app",
            "version": "1.0.0",
            "config": {
                "debug": True,
                "features": ["feature1", "feature2"]
            }
        }
        
        # 标准化（应该保持嵌套结构）
        normalized = MetadataManager.normalize_metadata(base_metadata)
        assert normalized == base_metadata
        
        # 合并元数据
        override_metadata = {
            "version": "1.0.1",  # 覆盖
            "author": "test"     # 新增
        }
        merged = MetadataManager.merge_metadata(normalized, override_metadata)
        assert merged["version"] == "1.0.1"
        assert merged["author"] == "test"
        assert merged["name"] == "app"  # 保留原始值
        
        # 提取嵌套值
        config = MetadataManager.extract_field(merged, "config")
        assert isinstance(config, dict)
        assert config["debug"] is True
        
        # 设置新字段
        updated = MetadataManager.set_field(merged, "timestamp", "2023-01-01")
        assert updated["timestamp"] == "2023-01-01"
        
        # 移除字段
        final = MetadataManager.remove_field(updated, "timestamp")
        assert "timestamp" not in final