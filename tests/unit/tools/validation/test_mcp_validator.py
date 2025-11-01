"""
MCP工具验证器单元测试
"""

import pytest
from unittest.mock import Mock

from src.infrastructure.tools.validation.validators.mcp_validator import MCPToolValidator
from src.infrastructure.tools.validation.models import ValidationStatus


class TestMCPToolValidator:
    """MCP工具验证器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_logger = Mock()
        self.validator = MCPToolValidator(self.mock_logger)
    
    def test_validate_tool_type_success(self):
        """测试MCP工具类型验证成功"""
        config = {
            "name": "database_tool",
            "mcp_server_url": "http://localhost:8080/mcp",
            "dynamic_schema": True,
            "refresh_interval": 300
        }
        
        result = self.validator.validate_tool_type("mcp", config)
        
        assert result.is_successful()
        assert result.tool_name == "database_tool"
        assert result.tool_type == "mcp"
    
    def test_validate_tool_type_missing_server_url(self):
        """测试缺少服务器URL"""
        config = {
            "name": "database_tool",
            # 缺少mcp_server_url
            "dynamic_schema": True
        }
        
        result = self.validator.validate_tool_type("mcp", config)
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_tool_type_invalid_server_url_type(self):
        """测试服务器URL类型无效"""
        config = {
            "name": "database_tool",
            "mcp_server_url": 123,  # 应该是字符串
            "dynamic_schema": True
        }
        
        result = self.validator.validate_tool_type("mcp", config)
        
        assert not result.is_successful()
        assert result.has_errors()
    
    def test_validate_tool_type_invalid_dynamic_schema(self):
        """测试动态Schema配置无效"""
        config = {
            "name": "database_tool",
            "mcp_server_url": "http://localhost:8080/mcp",
            "dynamic_schema": "invalid"  # 应该是布尔值
        }
        
        result = self.validator.validate_tool_type("mcp", config)
        
        assert not result.is_successful()  # 应该是失败，因为有警告
        assert result.has_warnings()
    
    def test_validate_tool_type_invalid_refresh_interval(self):
        """测试刷新间隔配置无效"""
        config = {
            "name": "database_tool",
            "mcp_server_url": "http://localhost:8080/mcp",
            "refresh_interval": "invalid"  # 应该是整数
        }
        
        result = self.validator.validate_tool_type("mcp", config)
        
        assert not result.is_successful()  # 应该是失败，因为有警告
        assert result.has_warnings()
    
    def test_validate_tool_type_invalid_timeout(self):
        """测试无效的超时配置"""
        config = {
            "name": "database_tool",
            "mcp_server_url": "http://localhost:8080/mcp",
            "timeout": "invalid"  # 应该是整数
        }
        
        result = self.validator.validate_tool_type("mcp", config)
        
        assert not result.is_successful()  # 应该是失败，因为有警告
        assert result.has_warnings()
    
    def test_get_supported_tool_types(self):
        """测试获取支持的工具类型"""
        supported_types = self.validator.get_supported_tool_types()
        assert supported_types == ["mcp"]
    
    def test_validate_config_not_supported(self):
        """测试不支持的配置验证"""
        result = self.validator.validate_config("configs/tools/test.yaml")
        assert result.status == ValidationStatus.WARNING
    
    def test_validate_loading_not_supported(self):
        """测试不支持的加载验证"""
        result = self.validator.validate_loading("test_tool")
        assert result.status == ValidationStatus.WARNING