"""
配置验证器单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.infrastructure.tools.validation.validators.config_validator import ConfigValidator
from src.infrastructure.tools.validation.models import ValidationStatus


class TestConfigValidator:
    """配置验证器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_config_loader = Mock()
        self.mock_logger = Mock()
        self.validator = ConfigValidator(self.mock_config_loader, self.mock_logger)
    
    def test_validate_config_success(self):
        """测试配置验证成功"""
        # 模拟配置数据
        config_data = {
            "name": "test_tool",
            "tool_type": "builtin",
            "description": "测试工具",
            "function_path": "test.module:test_function",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            }
        }
        
        # 模拟配置文件存在
        with patch.object(Path, "exists", return_value=True):
            with patch.object(self.validator.config_loader, "load", return_value=config_data):
                result = self.validator.validate_config("configs/tools/test_tool.yaml")
        
        assert result.is_successful()
        assert result.tool_name == "test_tool"
        assert result.tool_type == "builtin"
    
    def test_validate_config_missing_required_fields(self):
        """测试配置缺少必需字段"""
        # 模拟配置数据缺少必需字段
        invalid_config_data = {
            "name": "test_tool",
            # 缺少tool_type字段
            "description": "测试工具",
            "function_path": "test.module:test_function"
        }
        
        with patch.object(Path, "exists", return_value=True):
            with patch.object(self.validator.config_loader, "load", return_value=invalid_config_data):
                result = self.validator.validate_config("configs/tools/invalid.yaml")
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_config_invalid_tool_type(self):
        """测试配置工具类型无效"""
        # 模拟配置数据工具类型无效
        invalid_config_data = {
            "name": "test_tool",
            "tool_type": "invalid_type",
            "description": "测试工具",
            "function_path": "test.module:test_function"
        }
        
        with patch.object(Path, "exists", return_value=True):
            with patch.object(self.validator.config_loader, "load", return_value=invalid_config_data):
                result = self.validator.validate_config("configs/tools/invalid.yaml")
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_config_invalid_schema(self):
        """测试配置Schema无效"""
        # 模拟配置数据Schema无效
        invalid_config_data = {
            "name": "test_tool",
            "tool_type": "builtin",
            "description": "测试工具",
            "function_path": "test.module:test_function",
            "parameters_schema": "invalid_schema"  # 应该是字典
        }
        
        with patch.object(Path, "exists", return_value=True):
            with patch.object(self.validator.config_loader, "load", return_value=invalid_config_data):
                result = self.validator.validate_config("configs/tools/invalid.yaml")
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_config_load_failure(self):
        """测试配置加载失败"""
        with patch.object(Path, "exists", return_value=True):
            with patch.object(self.validator.config_loader, "load", side_effect=Exception("加载失败")):
                result = self.validator.validate_config("configs/tools/nonexistent.yaml")
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_get_supported_tool_types(self):
        """测试获取支持的工具类型"""
        supported_types = self.validator.get_supported_tool_types()
        assert set(supported_types) == {"builtin", "native", "mcp"}
    
    def test_validate_loading_not_supported(self):
        """测试不支持的加载验证"""
        result = self.validator.validate_loading("test_tool")
        assert result.status == ValidationStatus.WARNING
    
    def test_validate_tool_type_not_supported(self):
        """测试不支持的类型验证"""
        result = self.validator.validate_tool_type("builtin", {"name": "test"})
        assert result.status == ValidationStatus.WARNING