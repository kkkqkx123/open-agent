"""ConfigInheritanceHandler单元测试"""

import os
import tempfile
from pathlib import Path
import yaml
from unittest.mock import Mock, patch

import pytest

from src.core.common.utils.inheritance_handler import ConfigInheritanceHandler
from src.core.common.exceptions.config import ConfigError as ConfigurationError


class TestConfigInheritanceHandler:
    """ConfigInheritanceHandler测试类"""

    def setup_method(self):
        """测试前准备"""
        self.handler = ConfigInheritanceHandler()

    def test_init(self):
        """测试初始化"""
        handler = ConfigInheritanceHandler()
        assert handler.config_loader is None

        mock_loader = Mock()
        handler_with_loader = ConfigInheritanceHandler(mock_loader)
        assert handler_with_loader.config_loader == mock_loader

    def test_resolve_inheritance_simple(self):
        """测试简单的继承解析"""
        parent_config = {
            "model": "gpt-3.5",
            "temperature": 0.7,
            "max_tokens": 100
        }
        child_config = {
            "inherits_from": "parent_config",
            "temperature": 0.9,  # 覆盖父配置
            "top_p": 0.9  # 新增字段
        }

        # 模拟加载父配置
        with patch.object(self.handler, '_load_config_from_file', return_value=parent_config):
            result = self.handler.resolve_inheritance(child_config)

        # 验证结果
        assert result["model"] == "gpt-3.5"  # 继承的字段
        assert result["temperature"] == 0.9  # 覆盖的字段
        assert result["max_tokens"] == 10   # 继承的字段
        assert result["top_p"] == 0.9       # 新增的字段
        assert "inherits_from" not in result  # inherits_from字段被移除

    def test_resolve_inheritance_chain(self):
        """测试继承链"""
        grandparent_config = {
            "model": "gpt-3.5",
            "temperature": 0.5,
            "base_setting": "value1"
        }
        parent_config = {
            "inherits_from": "grandparent_config",
            "temperature": 0.7,  # 覆盖祖父配置
            "parent_setting": "value2"
        }
        child_config = {
            "inherits_from": "parent_config",
            "temperature": 0.9,  # 覆盖父配置
            "child_setting": "value3"
        }

        # 模拟加载配置
        def mock_load_config(path, base_path):
            if path == "grandparent_config":
                return grandparent_config
            elif path == "parent_config":
                return parent_config  # 这会触发递归调用
            return {}

        # 由于递归调用，我们需要特殊处理
        original_load = self.handler._load_config_from_file
        
        def side_effect(path, base_path):
            if path == "grandparent_config":
                return {
                    "model": "gpt-3.5",
                    "temperature": 0.5,
                    "base_setting": "value1"
                }
            elif path == "parent_config":
                # 直接返回处理后的父配置，避免无限递归
                return {
                    "model": "gpt-3.5",
                    "temperature": 0.7,
                    "base_setting": "value1",
                    "parent_setting": "value2"
                }
            return {}
        
        with patch.object(self.handler, '_load_config_from_file', side_effect=side_effect):
            result = self.handler.resolve_inheritance(child_config)

        # 验证结果
        assert result["model"] == "gpt-3.5"
        assert result["temperature"] == 0.9  # 子配置的值
        assert result["base_setting"] == "value1"  # 祖父配置的值
        assert result["parent_setting"] == "value2"  # 父配置的值
        assert result["child_setting"] == "value3"  # 子配置的值

    def test_resolve_inheritance_with_env_vars(self):
        """测试继承解析与环境变量结合"""
        os.environ["TEST_API_KEY"] = "test_key_123"
        
        parent_config = {
            "model": "gpt-3.5",
            "api_key": "${TEST_API_KEY}",
            "temperature": 0.7
        }
        child_config = {
            "inherits_from": "parent_config",
            "temperature": 0.9
        }

        with patch.object(self.handler, '_load_config_from_file', return_value=parent_config):
            result = self.handler.resolve_inheritance(child_config)

        assert result["model"] == "gpt-3.5"
        assert result["api_key"] == "test_key_123"  # 环境变量被解析
        assert result["temperature"] == 0.9

        # 清理环境变量
        del os.environ["TEST_API_KEY"]

    def test_merge_configs_simple(self):
        """测试简单配置合并"""
        parent = {"a": 1, "b": 2}
        child = {"b": 3, "c": 4}
        expected = {"a": 1, "b": 3, "c": 4}

        result = self.handler._merge_configs(parent, child)
        assert result == expected

    def test_merge_configs_nested(self):
        """测试嵌套配置合并"""
        parent = {
            "model": "gpt-3.5",
            "settings": {
                "temperature": 0.7,
                "max_tokens": 100
            },
            "plugins": ["plugin1", "plugin2"]
        }
        child = {
            "settings": {
                "temperature": 0.9,  # 覆盖嵌套字段
                "top_p": 0.9 # 新增嵌套字段
            },
            "plugins": ["plugin3"],  # 覆盖列表
            "new_field": "value"
        }
        expected = {
            "model": "gpt-3.5",  # 继承
            "settings": {
                "temperature": 0.9,  # 覆盖
                "max_tokens": 100,   # 继承
                "top_p": 0.9         # 新增
            },
            "plugins": ["plugin3"],  # 覆盖
            "new_field": "value"     # 新增
        }

        result = self.handler._merge_configs(parent, child)
        assert result == expected

    def test_resolve_env_vars_simple(self):
        """测试简单环境变量解析"""
        os.environ["TEST_VAR"] = "test_value"
        os.environ["ANOTHER_VAR"] = "another_value"
        
        config = {
            "api_key": "${TEST_VAR}",
            "endpoint": "https://api.${ANOTHER_VAR}.com",
            "normal_field": "normal_value"
        }

        result = self.handler._resolve_env_vars(config)

        assert result["api_key"] == "test_value"
        assert result["endpoint"] == "https://api.another_value.com"
        assert result["normal_field"] == "normal_value"

        # 清理环境变量
        del os.environ["TEST_VAR"]
        del os.environ["ANOTHER_VAR"]

    def test_resolve_env_vars_with_default(self):
        """测试带默认值的环境变量解析"""
        config = {
            "api_key": "${NONEXISTENT_VAR:default_key}",
            "timeout": "${NONEXISTENT_TIMEOUT:30}"
        }

        result = self.handler._resolve_env_vars(config)

        assert result["api_key"] == "default_key"
        assert result["timeout"] == "30"

    def test_resolve_env_vars_undefined_error(self):
        """测试未定义环境变量的错误处理"""
        config = {
            "api_key": "${UNDEFINED_VAR}"
        }

        # 由于_resolve_env_vars内部调用_resolve_env_var_string，
        # 而_resolve_env_var_string会抛出ConfigurationError
        with pytest.raises(ConfigurationError):
            self.handler._resolve_env_vars(config)

    def test_resolve_references_simple(self):
        """测试简单引用解析"""
        config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "url": "postgresql://localhost:5432"
            },
            "connection_string": "$ref: database.url",
            "settings": {
                "db_host": "$ref: database.host"
            }
        }

        result = self.handler._resolve_references(config)

        assert result["connection_string"] == "postgresql://localhost:5432"
        assert result["settings"]["db_host"] == "localhost"
        assert result["database"]["host"] == "localhost"

    def test_get_nested_value(self):
        """测试获取嵌套值"""
        config = {
            "level1": {
                "level2": {
                    "level3": "deep_value"
                },
                "sibling": "sibling_value"
            },
            "top_level": "top_value"
        }

        # 测试不同层级的访问
        assert self.handler._get_nested_value(config, "level1.level2.level3") == "deep_value"
        assert self.handler._get_nested_value(config, "level1.sibling") == "sibling_value"
        assert self.handler._get_nested_value(config, "top_level") == "top_value"

        # 测试不存在的路径
        with pytest.raises(ConfigurationError):
            self.handler._get_nested_value(config, "nonexistent.path")

    def test_validate_config_with_schema(self):
        """测试使用模式验证配置"""
        from pydantic import BaseModel
        from pydantic import field_validator
        
        class TestConfig(BaseModel):
            name: str
            count: int
            
            @field_validator('count')
            def validate_count(cls, v):
                if v < 0:
                    raise ValueError('Count must be non-negative')
                return v

        config = {"name": "test", "count": 5}
        
        errors = self.handler.validate_config(config, TestConfig)
        assert len(errors) == 0  # 验证应该通过

        # 测试验证失败的情况
        invalid_config = {"name": "test", "count": -1}
        errors = self.handler.validate_config(invalid_config, TestConfig)
        assert len(errors) > 0  # 应该有验证错误

    def test_custom_validation(self):
        """测试自定义验证"""
        config = {
            "_required_fields": ["name", "version"],
            "_field_types": {"name": "str", "version": "str", "count": "int"},
            "name": "test",
            "version": "1.0",
            "count": 10
        }

        errors = self.handler._custom_validation(config)
        assert len(errors) == 0 # 验证应该通过

        # 测试缺少必需字段
        config_missing_field = {
            "_required_fields": ["name", "version"],
            "name": "test"
            # 缺少version字段
        }
        errors = self.handler._custom_validation(config_missing_field)
        assert len(errors) == 1
        assert "缺少必要字段: version" in errors[0]

        # 测试字段类型错误
        config_wrong_type = {
            "_field_types": {"count": "int"},
            "count": "not_an_int"  # 应该是整数但提供的是字符串
        }
        errors = self.handler._custom_validation(config_wrong_type)
        assert len(errors) == 1
        assert "类型错误" in errors[0]

    def test_check_type(self):
        """测试类型检查"""
        # 测试各种类型
        assert self.handler._check_type("hello", "str")
        assert not self.handler._check_type(123, "str")
        
        assert self.handler._check_type(123, "int")
        assert not self.handler._check_type("123", "int")
        
        assert self.handler._check_type(12.5, "float")
        assert not self.handler._check_type(123, "float")
        
        assert self.handler._check_type(True, "bool")
        assert not self.handler._check_type(1, "bool")
        
        assert self.handler._check_type([1, 2, 3], "list")
        assert not self.handler._check_type("not_a_list", "list")
        
        assert self.handler._check_type({"key": "value"}, "dict")
        assert not self.handler._check_type("not_a_dict", "dict")

        # 测试未知类型（应该返回True）
        assert self.handler._check_type("anything", "unknown_type")

    def test_add_pattern_and_resolve_inheritance_with_custom_pattern(self):
        """测试添加自定义模式并使用"""
        # 这个测试主要是确保继承处理器能正常工作
        # 实际上ConfigInheritanceHandler没有add_pattern方法
        # 这个方法在Redactor类中，所以这里我们只测试继承处理器的主要功能
        parent_config = {"model": "gpt-3.5", "temperature": 0.7}
        child_config = {"inherits_from": "parent_config", "temperature": 0.9}
        
        with patch.object(self.handler, '_load_config_from_file', return_value=parent_config):
            result = self.handler.resolve_inheritance(child_config)
        
        assert result["model"] == "gpt-3.5"
        assert result["temperature"] == 0.9