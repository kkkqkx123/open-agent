"""
Native工具验证器单元测试
"""

import pytest
from unittest.mock import Mock

from src.infrastructure.tools.validation.validators.native_validator import NativeToolValidator
from src.infrastructure.tools.validation.models import ValidationStatus


class TestNativeToolValidator:
    """Native工具验证器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_logger = Mock()
        self.validator = NativeToolValidator(self.mock_logger)
    
    def test_validate_tool_type_success(self):
        """测试Native工具类型验证成功"""
        config = {
            "name": "weather_tool",
            "api_url": "https://api.weather.com/v1/weather",
            "method": "GET",
            "auth_method": "api_key",
            "api_key": "test_key"
        }
        
        result = self.validator.validate_tool_type("native", config)
        
        assert result.is_successful()
        assert result.tool_name == "weather_tool"
        assert result.tool_type == "native"
    
    def test_validate_tool_type_missing_api_url(self):
        """测试缺少API URL"""
        config = {
            "name": "weather_tool",
            # 缺少api_url
            "method": "GET",
            "auth_method": "api_key"
        }
        
        result = self.validator.validate_tool_type("native", config)
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_tool_type_invalid_api_url_type(self):
        """测试API URL类型无效"""
        config = {
            "name": "weather_tool",
            "api_url": 123,  # 应该是字符串
            "method": "GET",
            "auth_method": "api_key"
        }
        
        result = self.validator.validate_tool_type("native", config)
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_tool_type_invalid_method(self):
        """测试无效的HTTP方法"""
        config = {
            "name": "weather_tool",
            "api_url": "https://api.weather.com/v1/weather",
            "method": "INVALID",  # 无效方法
            "auth_method": "api_key"
        }
        
        result = self.validator.validate_tool_type("native", config)
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_tool_type_invalid_auth_method(self):
        """测试无效的认证方法"""
        config = {
            "name": "weather_tool",
            "api_url": "https://api.weather.com/v1/weather",
            "method": "GET",
            "auth_method": "invalid_auth"  # 无效认证方法
        }
        
        result = self.validator.validate_tool_type("native", config)
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_tool_type_missing_api_key(self):
        """测试缺少API密钥"""
        config = {
            "name": "weather_tool",
            "api_url": "https://api.weather.com/v1/weather",
            "method": "GET",
            "auth_method": "api_key"
            # 缺少api_key
        }
        
        result = self.validator.validate_tool_type("native", config)
        
        assert not result.is_successful()  # 应该是失败，因为有警告
        assert result.has_warnings()
    
    def test_validate_tool_type_invalid_timeout(self):
        """测试无效的超时配置"""
        config = {
            "name": "weather_tool",
            "api_url": "https://api.weather.com/v1/weather",
            "method": "GET",
            "auth_method": "none",
            "timeout": "invalid"  # 应该是整数
        }
        
        result = self.validator.validate_tool_type("native", config)
        
        assert not result.is_successful()  # 应该是失败，因为有警告
        assert result.has_warnings()
    
    def test_get_supported_tool_types(self):
        """测试获取支持的工具类型"""
        supported_types = self.validator.get_supported_tool_types()
        assert supported_types == ["native"]
    
    def test_validate_config_not_supported(self):
        """测试不支持的配置验证"""
        result = self.validator.validate_config("configs/tools/test.yaml")
        assert result.status == ValidationStatus.WARNING
    
    def test_validate_loading_not_supported(self):
        """测试不支持的加载验证"""
        result = self.validator.validate_loading("test_tool")
        assert result.status == ValidationStatus.WARNING