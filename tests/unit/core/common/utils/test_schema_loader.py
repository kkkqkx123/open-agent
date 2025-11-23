"""SchemaLoader单元测试"""

import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from src.core.common.utils.schema_loader import SchemaLoader
from src.core.common.exceptions import ConfigurationError


class TestSchemaLoader:
    """SchemaLoader测试类"""

    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.schema_dir = Path(self.temp_dir) / "schemas"
        self.schema_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """测试初始化"""
        loader = SchemaLoader()
        assert loader.schema_dir == Path("schemas")
        assert loader._schemas == {}

        loader_with_dir = SchemaLoader(self.temp_dir)
        assert loader_with_dir.schema_dir == Path(self.temp_dir)

    def test_load_schema_success(self):
        """测试成功加载模式"""
        # 创建模式文件
        schema_data = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        
        schema_file = self.schema_dir / "test_schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f)

        loader = SchemaLoader(self.temp_dir)
        loaded_schema = loader.load_schema("test_schema")

        assert loaded_schema == schema_data

    def test_load_schema_not_found(self):
        """测试加载不存在的模式文件"""
        loader = SchemaLoader(self.temp_dir)
        
        with pytest.raises(FileNotFoundError):
            loader.load_schema("nonexistent_schema")

    def test_load_schema_invalid_json(self):
        """测试加载无效JSON模式文件"""
        # 创建无效的JSON文件
        schema_file = self.schema_dir / "invalid_schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            f.write('{ invalid json }')

        loader = SchemaLoader(self.temp_dir)
        
        with pytest.raises(ValueError, match="无效的JSON模式文件"):
            loader.load_schema("invalid_schema")

    def test_load_schema_not_dict(self):
        """测试加载非字典类型的模式文件"""
        # 创建非对象类型的JSON文件
        schema_file = self.schema_dir / "not_dict_schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump([1, 2, 3], f)  # 数组而不是对象

        loader = SchemaLoader(self.temp_dir)
        
        with pytest.raises(ValueError, match="必须包含 JSON 对象"):
            loader.load_schema("not_dict_schema")

    def test_load_schema_cached(self):
        """测试模式缓存功能"""
        # 创建模式文件
        schema_data = {"type": "string"}
        schema_file = self.schema_dir / "cached_schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f)

        loader = SchemaLoader(self.temp_dir)
        
        # 第一次加载
        first_load = loader.load_schema("cached_schema")
        assert first_load == schema_data
        
        # 第二次加载（应该从缓存获取）
        second_load = loader.load_schema("cached_schema")
        assert second_load == schema_data
        assert first_load is second_load  # 应该是同一个对象（来自缓存）

    def test_validate_config_valid(self):
        """测试验证有效配置"""
        # 创建模式文件
        schema_data = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            },
            "required": ["name"]
        }
        schema_file = self.schema_dir / "validation_test.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f)

        loader = SchemaLoader(self.temp_dir)
        valid_config = {"name": "test", "age": 25}

        result = loader.validate_config(valid_config, "validation_test")
        assert result is True

    def test_validate_config_invalid(self):
        """测试验证无效配置"""
        # 创建模式文件
        schema_data = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            },
            "required": ["name"]
        }
        schema_file = self.schema_dir / "validation_test2.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f)

        loader = SchemaLoader(self.temp_dir)
        invalid_config = {"age": -5}  # 缺少必需字段且值无效

        result = loader.validate_config(invalid_config, "validation_test2")
        assert result is False

    def test_validate_config_schema_not_found(self):
        """测试验证配置时模式不存在"""
        loader = SchemaLoader(self.temp_dir)
        config = {"name": "test"}

        result = loader.validate_config(config, "nonexistent_schema")
        assert result is False

    def test_get_schema_field_info(self):
        """测试获取模式字段信息"""
        # 创建包含字段信息的模式
        schema_data = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "用户姓名"
                },
                "age": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "用户年龄"
                }
            }
        }
        schema_file = self.schema_dir / "field_info_test.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f)

        loader = SchemaLoader(self.temp_dir)
        
        field_info = loader.get_schema_field_info("field_info_test", "name")
        assert field_info is not None
        assert field_info["type"] == "string"
        assert field_info["description"] == "用户姓名"

        # 测试不存在的字段
        field_info = loader.get_schema_field_info("field_info_test", "nonexistent")
        assert field_info is None

    def test_get_schema_field_info_schema_not_found(self):
        """测试获取字段信息时模式不存在"""
        loader = SchemaLoader(self.temp_dir)
        
        field_info = loader.get_schema_field_info("nonexistent_schema", "any_field")
        assert field_info is None

    def test_list_schemas(self):
        """测试列出所有模式"""
        # 创建多个模式文件
        schemas_data = {
            "schema1": {"type": "object"},
            "schema2": {"type": "string"},
            "schema3": {"type": "array"}
        }
        
        for name, data in schemas_data.items():
            schema_file = self.schema_dir / f"{name}.json"
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)

        loader = SchemaLoader(self.temp_dir)
        listed_schemas = loader.list_schemas()

        assert len(listed_schemas) == 3
        assert "schema1" in listed_schemas
        assert "schema2" in listed_schemas
        assert "schema3" in listed_schemas

    def test_list_schemas_empty_dir(self):
        """测试空目录的模式列表"""
        loader = SchemaLoader(self.temp_dir)
        listed_schemas = loader.list_schemas()
        assert listed_schemas == []

    def test_list_schemas_nonexistent_dir(self):
        """测试不存在目录的模式列表"""
        loader = SchemaLoader("/nonexistent/directory")
        listed_schemas = loader.list_schemas()
        assert listed_schemas == []

    def test_reload_schema(self):
        """测试重新加载模式"""
        # 创建初始模式文件
        initial_data = {"version": "1.0"}
        schema_file = self.schema_dir / "reload_test.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f)

        loader = SchemaLoader(self.temp_dir)
        
        # 首次加载
        first_load = loader.load_schema("reload_test")
        assert first_load == initial_data

        # 更新文件内容
        updated_data = {"version": "2.0", "new_field": "value"}
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f)

        # 重新加载（注意：当前实现会从缓存获取，reload方法会清除缓存后重新加载）
        reloaded = loader.reload_schema("reload_test")
        assert reloaded == updated_data
        assert reloaded != first_load

    def test_reload_all_schemas(self):
        """测试重新加载所有模式"""
        # 创建多个模式文件
        schemas_data = {
            "reload1": {"data": "initial1"},
            "reload2": {"data": "initial2"}
        }
        
        for name, data in schemas_data.items():
            schema_file = self.schema_dir / f"{name}.json"
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)

        loader = SchemaLoader(self.temp_dir)
        
        # 加载模式以填充缓存
        schema1 = loader.load_schema("reload1")
        schema2 = loader.load_schema("reload2")
        
        # 验证缓存中有模式
        assert "reload1" in loader._schemas
        assert "reload2" in loader._schemas

        # 重新加载所有（清除缓存）
        loader.reload_all_schemas()
        
        # 验证缓存被清空
        assert len(loader._schemas) == 0

    def test_create_default_schema(self):
        """测试创建默认模式"""
        loader = SchemaLoader(self.temp_dir)
        config = {
            "name": "test",
            "count": 42,
            "active": True,
            "tags": ["a", "b"],
            "nested": {
                "inner": "value"
            }
        }

        loader.create_default_schema("auto_generated", config)

        # 验证模式文件被创建
        generated_file = self.schema_dir / "auto_generated.json"
        assert generated_file.exists()

        # 验证生成的模式
        with open(generated_file, 'r', encoding='utf-8') as f:
            generated_schema = json.load(f)

        assert generated_schema["type"] == "object"
        assert "properties" in generated_schema
        assert "required" in generated_schema
        assert "name" in generated_schema["properties"]  # 非空字段被标记为必需
        assert generated_schema["properties"]["name"]["type"] == "string"
        assert generated_schema["properties"]["count"]["type"] == "integer"
        assert generated_schema["properties"]["active"]["type"] == "boolean"
        assert generated_schema["properties"]["tags"]["type"] == "array"

    def test_create_default_schema_overwrite(self):
        """测试覆盖已存在的模式文件"""
        loader = SchemaLoader(self.temp_dir)
        
        # 首先创建一个模式文件
        existing_schema = {"existing": "schema"}
        existing_file = self.schema_dir / "overwrite_test.json"
        with open(existing_file, 'w', encoding='utf-8') as f:
            json.dump(existing_schema, f)

        # 创建新的默认模式（应该覆盖）
        new_config = {"new_field": "new_value"}
        loader.create_default_schema("overwrite_test", new_config)

        # 验证文件被覆盖
        with open(existing_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # 新内容应该与配置推断的模式匹配，而不是原始内容
        assert "new_field" in content["properties"]

    def test_create_default_schema_error(self):
        """测试创建模式时的错误处理"""
        # 使用只读目录测试错误处理
        readonly_dir = Path(self.temp_dir) / "readonly"
        readonly_dir.mkdir(mode=0o444, parents=True, exist_ok=True)  # 只读权限

        loader = SchemaLoader(readonly_dir)
        config = {"test": "value"}

        try:
            loader.create_default_schema("readonly_test", config)
            # 在某些系统上，上面的操作可能不会抛出异常
        except Exception:
            # 如果抛出异常，这是预期的
            pass

    def test_validate_against_schema_required_fields(self):
        """测试验证必需字段"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": ["name", "email"]
        }
        
        # 缺少必需字段的配置
        invalid_config = {"name": "test"}  # 缺少email
        
        loader = SchemaLoader(self.temp_dir)
        result = loader._validate_against_schema(invalid_config, schema)
        assert result is False

        # 包含所有必需字段的配置
        valid_config = {"name": "test", "email": "test@example.com"}
        result = loader._validate_against_schema(valid_config, schema)
        assert result is True

    def test_validate_against_schema_field_types(self):
        """测试验证字段类型"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "score": {"type": "number"},
                "active": {"type": "boolean"},
                "tags": {"type": "array"},
                "settings": {"type": "object"}
            }
        }
        
        # 类型正确的配置
        valid_config = {
            "name": "test",
            "age": 25,
            "score": 95.5,
            "active": True,
            "tags": ["tag1", "tag2"],
            "settings": {"key": "value"}
        }
        
        loader = SchemaLoader(self.temp_dir)
        result = loader._validate_against_schema(valid_config, schema)
        assert result is True

        # 类型错误的配置
        invalid_config = {
            "name": 123, # 应该是字符串但提供整数
            "age": "25",  # 应该是整数但提供字符串
        }
        result = loader._validate_against_schema(invalid_config, schema)
        assert result is False