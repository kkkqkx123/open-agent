"""
Builtin工具验证器单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.infrastructure.tools.validation.validators.builtin_validator import BuiltinToolValidator
from src.infrastructure.tools.validation.models import ValidationStatus


class TestBuiltinToolValidator:
    """Builtin工具验证器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_logger = Mock()
        self.validator = BuiltinToolValidator(self.mock_logger)
    
    def test_validate_tool_type_success(self):
        """测试Builtin工具类型验证成功"""
        config = {
            "name": "test_tool",
            "function_path": "defination.tools.calculator:calculate"
        }
        
        with patch.object(self.validator, '_load_function_from_path'):
            result = self.validator.validate_tool_type("builtin", config)
        
        assert result.is_successful()
        assert result.tool_name == "test_tool"
        assert result.tool_type == "builtin"
    
    def test_validate_tool_type_missing_function_path(self):
        """测试缺少函数路径"""
        config = {
            "name": "test_tool"
            # 缺少function_path
        }
        
        result = self.validator.validate_tool_type("builtin", config)
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_tool_type_invalid_function_path(self):
        """测试无效的函数路径格式"""
        config = {
            "name": "test_tool",
            "function_path": "invalid_path"  # 无效格式
        }
        
        result = self.validator.validate_tool_type("builtin", config)
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_tool_type_function_load_failure(self):
        """测试函数加载失败"""
        config = {
            "name": "test_tool",
            "function_path": "defination.tools.calculator:calculate"
        }
        
        with patch.object(self.validator, '_load_function_from_path', side_effect=Exception("加载失败")):
            result = self.validator.validate_tool_type("builtin", config)
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_function_path_valid(self):
        """测试有效的函数路径格式"""
        valid_paths = [
            "module:function",
            "package.module:function",
            "package.subpackage.module:function_name",
            "module123:func456"
        ]
        
        for path in valid_paths:
            assert self.validator._validate_function_path(path)
    
    def test_validate_function_path_invalid(self):
        """测试无效的函数路径格式"""
        invalid_paths = [
            "module",  # 缺少冒号
            ":function",  # 缺少模块名
            "module:",  # 缺少函数名
            "123module:function",  # 模块名以数字开头
            "module:123function",  # 函数名以数字开头
            "module.function:function:name"  # 多个冒号
        ]
        
        for path in invalid_paths:
            assert not self.validator._validate_function_path(path)
    
    def test_load_function_from_path_success(self):
        """测试成功加载函数"""
        with patch('importlib.import_module') as mock_import_module:
            mock_module = Mock()
            mock_module.calculate = Mock()
            mock_import_module.return_value = mock_module
            
            func = self.validator._load_function_from_path("defination.tools.calculator:calculate")
            
            assert func == mock_module.calculate
            mock_import_module.assert_called_once_with("defination.tools.calculator")
    
    def test_load_function_from_path_module_not_found(self):
        """测试模块未找到"""
        with patch('importlib.import_module', side_effect=ImportError("模块未找到")):
            with pytest.raises(ValueError, match="加载函数失败"):
                self.validator._load_function_from_path("nonexistent.module:function")
    
    def test_load_function_from_path_function_not_found(self):
        """测试函数未找到"""
        with patch('importlib.import_module') as mock_import_module:
            mock_module = Mock()
            # 模块中没有指定的函数
            del mock_module.nonexistent_function
            mock_import_module.return_value = mock_module
            
            with pytest.raises(ValueError, match="加载函数失败"):
                self.validator._load_function_from_path("module:nonexistent_function")
    
    def test_load_function_from_path_not_callable(self):
        """测试函数不可调用"""
        with patch('importlib.import_module') as mock_import_module:
            mock_module = Mock()
            mock_module.not_a_function = "not callable"  # 不是可调用对象
            mock_import_module.return_value = mock_module
            
            with pytest.raises(ValueError, match="指定路径不是可调用对象"):
                self.validator._load_function_from_path("module:not_a_function")
    
    def test_get_supported_tool_types(self):
        """测试获取支持的工具类型"""
        supported_types = self.validator.get_supported_tool_types()
        assert supported_types == ["builtin"]
    
    def test_validate_config_not_supported(self):
        """测试不支持的配置验证"""
        result = self.validator.validate_config("configs/tools/test.yaml")
        assert result.status == ValidationStatus.WARNING
    
    def test_validate_loading_not_supported(self):
        """测试不支持的加载验证"""
        result = self.validator.validate_loading("test_tool")
        assert result.status == ValidationStatus.WARNING