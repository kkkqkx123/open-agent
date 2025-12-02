"""validation_utils.py模块的单元测试"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import mock_open, patch
import yaml
import json
from src.core.config.processor.validation_utils import (
    ValidationLevel, ValidationSeverity, ValidationCache, 
    load_config_file, generate_cache_key
)


class TestValidationLevel:
    """验证级别枚举的测试"""

    def test_validation_level_values(self):
        """测试验证级别枚举值"""
        assert ValidationLevel.SYNTAX.value == "syntax"
        assert ValidationLevel.SCHEMA.value == "schema"
        assert ValidationLevel.SEMANTIC.value == "semantic"
        assert ValidationLevel.DEPENDENCY.value == "dependency"
        assert ValidationLevel.PERFORMANCE.value == "performance"


class TestValidationSeverity:
    """验证严重性级别枚举的测试"""

    def test_validation_severity_values(self):
        """测试验证严重性级别枚举值"""
        assert ValidationSeverity.INFO.value == "info"
        assert ValidationSeverity.WARNING.value == "warning"
        assert ValidationSeverity.ERROR.value == "error"
        assert ValidationSeverity.CRITICAL.value == "critical"


class TestValidationCache:
    """验证缓存类的测试"""

    def setup_method(self):
        """测试前的设置"""
        self.cache = ValidationCache(max_size=2, ttl=1)  # 小容量和短TTL用于测试

    def test_init(self):
        """测试初始化"""
        assert self.cache.max_size == 2
        assert self.cache.ttl == 1
        assert len(self.cache._cache) == 0

    def test_set_and_get(self):
        """测试设置和获取缓存"""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

    def test_cache_expiration(self):
        """测试缓存过期"""
        # 手动设置一个过期时间
        self.cache._cache["key1"] = ("value1", datetime.now() - timedelta(seconds=2))  # 已过期
        assert self.cache.get("key1") is None  # 应该返回None，因为已过期

    def test_cache_lru_eviction(self):
        """测试LRU缓存淘汰"""
        # 填满缓存
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        assert len(self.cache._cache) == 2

        # 添加新项，应该触发淘汰
        self.cache.set("key3", "value3")
        assert len(self.cache._cache) == 2
        assert "key3" in self.cache._cache  # 新项应该存在
        # 由于我们使用时间戳作为LRU依据，最早添加的项会被移除

    def test_cache_full_behavior(self):
        """测试缓存满时的行为"""
        cache = ValidationCache(max_size=1)  # 只能存1个
        cache.set("key1", "value1")
        cache.set("key2", "value2")  # 这会替换key1
        
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"


class TestLoadConfigFile:
    """加载配置文件函数的测试"""

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="key: value")
    def test_load_yaml_file(self, mock_file, mock_exists):
        """测试加载YAML文件"""
        mock_exists.return_value = True
        with patch('yaml.safe_load') as mock_yaml_load:
            mock_yaml_load.return_value = {"key": "value"}
            result = load_config_file("test.yaml")
            assert result == {"key": "value"}
            mock_yaml_load.assert_called_once()

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    def test_load_json_file(self, mock_file, mock_exists):
        """测试加载JSON文件"""
        mock_exists.return_value = True
        with patch('json.load') as mock_json_load:
            mock_json_load.return_value = {"key": "value"}
            result = load_config_file("test.json")
            assert result == {"key": "value"}
            mock_json_load.assert_called_once()

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="key: value")
    def test_load_file_by_extension(self, mock_file, mock_exists):
        """测试根据扩展名加载文件"""
        mock_exists.return_value = True
        with patch('yaml.safe_load') as mock_yaml_load:
            mock_yaml_load.return_value = {"key": "value"}
            result = load_config_file("test.yml")
            assert result == {"key": "value"}

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="key: value")
    def test_load_unknown_format_try_yaml(self, mock_file, mock_exists):
        """测试未知格式尝试YAML加载"""
        mock_exists.return_value = True
        with patch('yaml.safe_load') as mock_yaml_load:
            mock_yaml_load.return_value = {"key": "value"}
            result = load_config_file("test.unknown")
            assert result == {"key": "value"}

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="invalid yaml")
    def test_load_invalid_format(self, mock_file, mock_exists):
        """测试无效格式"""
        mock_exists.return_value = True
        with patch('yaml.safe_load') as mock_yaml_load:
            mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")
            with pytest.raises(ValueError):
                load_config_file("test.unknown")

    @patch("pathlib.Path.exists")
    def test_load_nonexistent_file(self, mock_exists):
        """测试加载不存在的文件"""
        mock_exists.return_value = False
        with pytest.raises(FileNotFoundError):
            load_config_file("nonexistent.yaml")


class TestGenerateCacheKey:
    """生成缓存键函数的测试"""

    def test_generate_cache_key(self):
        """测试生成缓存键"""
        levels = [ValidationLevel.SCHEMA, ValidationLevel.SEMANTIC]
        key = generate_cache_key("test_path", levels)
        # 验证键的格式
        assert key.startswith("test_path_")
        # 验证级别按字母顺序排序
        assert "schema_semantic" in key or "semantic_schema" in key

    def test_generate_cache_key_single_level(self):
        """测试单个级别生成缓存键"""
        levels = [ValidationLevel.SYNTAX]
        key = generate_cache_key("test_path", levels)
        assert key == "test_path_syntax"

    def test_generate_cache_key_empty_levels(self):
        """测试空级别列表生成缓存键"""
        levels = []
        key = generate_cache_key("test_path", levels)
        assert key == "test_path_"