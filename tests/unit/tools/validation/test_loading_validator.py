"""
加载验证器单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.infrastructure.tools.validation.validators.loading_validator import LoadingValidator
from src.infrastructure.tools.validation.models import ValidationStatus


class TestLoadingValidator:
    """加载验证器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_tool_manager = Mock()
        self.mock_logger = Mock()
        self.validator = LoadingValidator(self.mock_tool_manager, self.mock_logger)
    
    def test_validate_loading_success(self):
        """测试加载验证成功"""
        # 模拟工具对象
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.tool_type = "builtin"
        mock_tool.description = "测试工具"
        mock_tool.get_schema.return_value = {"type": "object"}
        
        # 模拟工具管理器返回工具
        self.mock_tool_manager.get_tool.return_value = mock_tool
        
        result = self.validator.validate_loading("test_tool")
        
        assert result.is_successful()
        assert result.tool_name == "test_tool"
        assert result.tool_type == "builtin"
    
    def test_validate_loading_tool_not_found(self):
        """测试工具不存在"""
        # 模拟工具管理器抛出异常
        self.mock_tool_manager.get_tool.side_effect = ValueError("工具不存在")
        
        result = self.validator.validate_loading("nonexistent_tool")
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_loading_missing_attributes(self):
        """测试工具缺少必需属性"""
        # 模拟工具对象缺少必需属性
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        # 缺少description属性
        del mock_tool.description
        mock_tool.get_schema.return_value = {"type": "object"}
        
        # 模拟工具管理器返回工具
        self.mock_tool_manager.get_tool.return_value = mock_tool
        
        result = self.validator.validate_loading("test_tool")
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_loading_invalid_schema(self):
        """测试工具Schema无效"""
        # 模拟工具对象返回无效Schema
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.tool_type = "builtin"
        mock_tool.description = "测试工具"
        mock_tool.get_schema.return_value = "invalid_schema"  # 应该是字典
        
        # 模拟工具管理器返回工具
        self.mock_tool_manager.get_tool.return_value = mock_tool
        
        result = self.validator.validate_loading("test_tool")
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_loading_schema_exception(self):
        """测试获取Schema时抛出异常"""
        # 模拟工具对象获取Schema时抛出异常
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.tool_type = "builtin"
        mock_tool.description = "测试工具"
        mock_tool.get_schema.side_effect = Exception("获取Schema失败")
        
        # 模拟工具管理器返回工具
        self.mock_tool_manager.get_tool.return_value = mock_tool
        
        result = self.validator.validate_loading("test_tool")
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_get_supported_tool_types(self):
        """测试获取支持的工具类型"""
        supported_types = self.validator.get_supported_tool_types()
        assert set(supported_types) == {"builtin", "native", "mcp"}
    
    def test_validate_config_not_supported(self):
        """测试不支持的配置验证"""
        result = self.validator.validate_config("configs/tools/test.yaml")
        assert result.status == ValidationStatus.WARNING
    
    def test_validate_tool_type_not_supported(self):
        """测试不支持的类型验证"""
        result = self.validator.validate_tool_type("builtin", {"name": "test"})
        assert result.status == ValidationStatus.WARNING