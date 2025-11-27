"""配置管理器测试

测试统一配置管理器的功能。
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.config.config_manager import ConfigManager, DefaultConfigValidator
from src.interfaces.config.interfaces import IConfigValidator
from src.interfaces.configuration import ValidationResult


class TestConfigManager:
    """配置管理器测试类"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """临时配置目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """配置管理器实例"""
        return ConfigManager(base_path=temp_config_dir)
    
    @pytest.fixture
    def sample_config(self):
        """示例配置数据"""
        return {
            "name": "test_config",
            "type": "test",
            "version": "1.0.0",
            "settings": {
                "debug": True,
                "timeout": 30
            }
        }
    
    def test_init_config_manager(self, temp_config_dir):
        """测试配置管理器初始化"""
        manager = ConfigManager(base_path=temp_config_dir)
        
        assert manager.base_path == temp_config_dir
        assert manager.loader is not None
        assert manager.processor is not None
        assert manager.registry is not None
        assert manager._module_validators == {}
        assert manager._module_configs == {}
        assert manager._config_callbacks == {}
    
    def test_load_config_success(self, config_manager, temp_config_dir, sample_config):
        """测试成功加载配置"""
        # 创建配置文件
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_config, f)
        
        # 加载配置
        result = config_manager.load_config("test.yaml")
        
        assert result == sample_config
        assert "test.yaml:default" in config_manager._config_cache._cache
    
    def test_load_config_with_module_type(self, config_manager, temp_config_dir, sample_config):
        """测试带模块类型的配置加载"""
        # 创建配置文件
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_config, f)
        
        # 加载配置
        result = config_manager.load_config("test.yaml", module_type="test_module")
        
        assert result == sample_config
        assert "test_module" in config_manager._module_configs
        assert "test.yaml" in config_manager._module_configs["test_module"]
    
    def test_load_config_for_module(self, config_manager, temp_config_dir, sample_config):
        """测试模块特定配置加载"""
        # 创建配置文件
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_config, f)
        
        # 加载配置
        result = config_manager.load_config_for_module("test.yaml", "test_module")
        
        assert result == sample_config
        assert "test_module" in config_manager._module_configs
        assert "test.yaml" in config_manager._module_configs["test_module"]
    
    def test_register_module_validator(self, config_manager):
        """测试注册模块验证器"""
        mock_validator = Mock(spec=IConfigValidator)
        
        config_manager.register_module_validator("test_module", mock_validator)
        
        assert "test_module" in config_manager._module_validators
        assert config_manager._module_validators["test_module"] == mock_validator
    
    def test_get_module_config(self, config_manager):
        """测试获取模块配置"""
        # 添加模块配置
        config_manager._module_configs["test_module"] = {"key": "value"}
        
        result = config_manager.get_module_config("test_module")
        
        assert result == {"key": "value"}
        
        # 测试不存在的模块
        result = config_manager.get_module_config("nonexistent")
        assert result == {}
    
    def test_reload_module_configs(self, config_manager, temp_config_dir, sample_config):
        """测试重新加载模块配置"""
        # 创建配置文件
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_config, f)
        
        # 加载配置
        config_manager.load_config("test.yaml", module_type="test_module")
        
        # 验证配置已加载
        assert "test_module" in config_manager._module_configs
        assert "test.yaml" in config_manager._module_configs["test_module"]
        
        # 修改配置文件
        updated_config = sample_config.copy()
        updated_config["version"] = "2.0.0"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(updated_config, f)
        
        # 重新加载
        config_manager.reload_module_configs("test_module")
        
        # 验证配置已更新
        result = config_manager.get_module_config("test_module")
        assert result["test.yaml"]["version"] == "2.0.0"
    
    def test_invalidate_cache(self, config_manager, temp_config_dir, sample_config):
        """测试清除缓存"""
        # 创建配置文件
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_config, f)
        
        # 加载配置
        config_manager.load_config("test.yaml", module_type="test_module")
        
        # 验证缓存存在
        assert len(config_manager._config_cache._cache) > 0
        assert "test_module" in config_manager._module_configs
        assert "test.yaml" in config_manager._module_configs["test_module"]
        
        # 清除特定配置缓存
        config_manager.invalidate_cache("test.yaml")
        
        # 验证缓存已清除
        assert "test.yaml" not in config_manager._module_configs.get("test_module", {})
        
        # 清除所有缓存
        config_manager.invalidate_cache()
        
        assert len(config_manager._config_cache._cache) == 0
        assert len(config_manager._module_configs) == 0
    
    def test_get_config_status(self, config_manager):
        """测试获取配置状态"""
        # 添加一些测试数据
        config_manager._module_validators["test_module"] = Mock()
        config_manager._module_configs["test_module"] = {"test.yaml": {}}
        config_manager._config_callbacks["test.yaml"] = Mock()
        
        status = config_manager.get_config_status()
        
        assert status["loaded_modules"] == ["test_module"]
        assert status["module_configs_count"] == {"test_module": 1}
        assert status["registered_validators"] == ["test_module"]
        assert status["watched_files"] == ["test.yaml"]
        assert "cache_size" in status
        assert "auto_reload_enabled" in status
    
    def test_get_validator_with_module_type(self, config_manager):
        """测试获取模块特定验证器"""
        mock_validator = Mock(spec=IConfigValidator)
        config_manager.register_module_validator("test_module", mock_validator)
        
        # 获取模块特定验证器
        validator = config_manager._get_validator("test_module")
        assert validator == mock_validator
        
        # 获取默认验证器
        default_validator = config_manager._get_validator("nonexistent")
        assert isinstance(default_validator, DefaultConfigValidator)
    
    def test_validate_with_validator(self, config_manager):
        """测试使用验证器验证配置"""
        mock_validator = Mock(spec=IConfigValidator)
        mock_result = ValidationResult()
        mock_result.is_valid = True
        mock_validator.validate.return_value = mock_result
        
        config = {"test": "value"}
        result = config_manager._validate_with_validator(config, mock_validator)
        
        assert result == mock_result
        mock_validator.validate.assert_called_once_with(config)
    
    def test_validate_with_validator_exception(self, config_manager):
        """测试验证器异常处理"""
        mock_validator = Mock(spec=IConfigValidator)
        mock_validator.validate.side_effect = Exception("验证错误")
        
        config = {"test": "value"}
        result = config_manager._validate_with_validator(config, mock_validator)
        
        assert not result.is_valid
        assert "验证过程出错: 验证错误" in result.errors
    
    def test_get_nested_value(self, config_manager):
        """测试获取嵌套值"""
        data = {
            "level1": {
                "level2": {
                    "value": "test_value"
                }
            }
        }
        
        # 测试存在的路径
        result = config_manager._get_nested_value(data, "level1.level2.value")
        assert result == "test_value"
        
        # 测试不存在的路径
        result = config_manager._get_nested_value(data, "level1.level2.nonexistent", "default")
        assert result == "default"
        
        # 测试不存在的路径（无默认值）
        result = config_manager._get_nested_value(data, "level1.level2.nonexistent")
        assert result is None


class TestDefaultConfigValidator:
    """默认配置验证器测试类"""
    
    @pytest.fixture
    def validator(self):
        """默认验证器实例"""
        return DefaultConfigValidator()
    
    def test_validate_valid_config(self, validator):
        """测试验证有效配置"""
        config = {
            "name": "test",
            "type": "test_type",
            "value": "test_value"
        }
        
        result = validator.validate(config)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_config_without_name(self, validator):
        """测试验证没有name字段的配置"""
        config = {
            "type": "test_type",
            "value": "test_value"
        }
        
        result = validator.validate(config)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert "建议包含 'name' 字段" in result.warnings[0]
    
    def test_validate_empty_config(self, validator):
        """测试验证空配置"""
        config = {}
        
        result = validator.validate(config)
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert "配置不能为空" in result.errors[0]
    
    def test_validate_non_dict_config(self, validator):
        """测试验证非字典配置"""
        config = "not a dict"
        
        result = validator.validate(config)
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert "必须是字典类型" in result.errors[0]
    
    def test_validate_with_exception(self, validator):
        """测试验证过程中的异常"""
        # 直接测试异常情况，不使用mock因为会导致递归调用
        config = None  # 传入None会导致异常
        
        result = validator.validate(config)
        
        assert not result.is_valid
        assert len(result.errors) == 1
        # None会被当作非字典类型，所以错误信息是"配置必须是字典类型"
        assert "配置必须是字典类型" in result.errors[0]
    
    def test_supports_module_type(self, validator):
        """测试支持模块类型"""
        assert validator.supports_module_type("any_module") is True
        assert validator.supports_module_type("") is True
        assert validator.supports_module_type(None) is True