"""
工具检验模块集成测试
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import shutil

from src.infrastructure.tools.validation import ToolValidationManager
from src.infrastructure.tools.validation.models import ValidationStatus


class TestValidationIntegration:
    """集成测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_config_loader = Mock()
        self.mock_logger = Mock()
        self.mock_tool_manager = Mock()
    
    def test_complete_validation_workflow(self):
        """测试完整验证工作流"""
        # 创建检验管理器
        validation_manager = ToolValidationManager(
            self.mock_config_loader,
            self.mock_logger,
            self.mock_tool_manager
        )
        
        # 验证管理器是否正确初始化了验证器
        assert "config" in validation_manager.validators
        assert "loading" in validation_manager.validators
        assert "builtin" in validation_manager.validators
        assert "native" in validation_manager.validators
        assert "mcp" in validation_manager.validators
    
    def test_validate_hash_convert_tool(self):
        """测试Hash转换工具完整验证流程"""
        # 模拟配置数据
        hash_convert_config = {
            "name": "hash_convert",
            "tool_type": "builtin",
            "description": "将文本转换为各种哈希值的工具",
            "function_path": "defination.tools.hash_convert:hash_convert",
            "enabled": True,
            "timeout": 10,
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要转换为哈希值的文本"
                    },
                    "algorithm": {
                        "type": "string",
                        "description": "哈希算法",
                        "enum": ["md5", "sha1", "sha256", "sha512"],
                        "default": "sha256"
                    }
                },
                "required": ["text"]
            }
        }
        
        # 模拟工具对象
        mock_tool = Mock()
        mock_tool.name = "hash_convert"
        mock_tool.tool_type = "builtin"
        mock_tool.description = "将文本转换为各种哈希值的工具"
        mock_tool.get_schema.return_value = hash_convert_config["parameters_schema"]
        
        # 设置模拟
        self.mock_config_loader.load.return_value = hash_convert_config
        self.mock_tool_manager.get_tool.return_value = mock_tool
        
        # 创建检验管理器
        validation_manager = ToolValidationManager(
            self.mock_config_loader,
            self.mock_logger,
            self.mock_tool_manager
        )
        
        # 验证工具
        results = validation_manager.validate_tool(
            "hash_convert", 
            "configs/tools/hash_convert.yaml"
        )
        
        # 验证结果
        assert "config" in results
        assert "loading" in results
        assert results["config"].is_successful()
        assert results["loading"].is_successful()
        
        # 只有在配置验证成功时，才会执行类型特定验证
        if results["config"].is_successful():
            tool_type = results["config"].metadata.get("tool_type")
            if tool_type in ["builtin", "native", "mcp"]:
                assert "type" in results
                assert results["type"].is_successful()
    
    def test_validate_weather_tool(self):
        """测试天气工具完整验证流程"""
        # 模拟配置数据
        weather_config = {
            "name": "weather",
            "tool_type": "native",
            "description": "查询指定城市的天气信息",
            "enabled": True,
            "timeout": 15,
            "api_url": "https://api.openweathermap.org/data/2.5/weather",
            "method": "GET",
            "auth_method": "api_key",
            "api_key": "test_key",
            "headers": {
                "User-Agent": "ModularAgent/1.0",
                "Content-Type": "application/json"
            },
            "retry_count": 3,
            "retry_delay": 1.0,
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "q": {
                        "type": "string",
                        "description": "城市名称"
                    },
                    "units": {
                        "type": "string",
                        "description": "温度单位",
                        "enum": ["metric", "imperial", "kelvin"],
                        "default": "metric"
                    }
                },
                "required": ["q"]
            }
        }
        
        # 模拟工具对象
        mock_tool = Mock()
        mock_tool.name = "weather"
        mock_tool.tool_type = "native"
        mock_tool.description = "查询指定城市的天气信息"
        mock_tool.get_schema.return_value = weather_config["parameters_schema"]
        
        # 设置模拟
        self.mock_config_loader.load.return_value = weather_config
        self.mock_tool_manager.get_tool.return_value = mock_tool
        
        # 创建检验管理器
        validation_manager = ToolValidationManager(
            self.mock_config_loader,
            self.mock_logger,
            self.mock_tool_manager
        )
        
        # 验证工具
        results = validation_manager.validate_tool(
            "weather", 
            "configs/tools/weather.yaml"
        )
        
        # 验证结果
        assert "config" in results
        assert "loading" in results
        assert results["config"].is_successful()
        assert results["loading"].is_successful()
        
        # 只有在配置验证成功时，才会执行类型特定验证
        if results["config"].is_successful():
            tool_type = results["config"].metadata.get("tool_type")
            if tool_type in ["builtin", "native", "mcp"]:
                assert "type" in results
                assert results["type"].is_successful()
    
    def test_validate_all_tools_in_real_config_dir(self):
        """测试在真实配置目录中验证所有工具"""
        # 由于我们无法访问真实的配置目录，我们模拟这个过程
        # 模拟配置文件列表
        mock_config_files = [
            Path("configs/tools/hash_convert.yaml"),
            Path("configs/tools/calculator.yaml")
        ]
        
        # 模拟配置数据
        hash_convert_config = {
            "name": "hash_convert",
            "tool_type": "builtin",
            "description": "将文本转换为各种哈希值的工具",
            "function_path": "defination.tools.hash_convert:hash_convert",
            "enabled": True,
            "timeout": 10,
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要转换为哈希值的文本"}
                },
                "required": ["text"]
            }
        }
        
        calculator_config = {
            "name": "calculator",
            "tool_type": "builtin",
            "description": "执行基本数学计算的工具",
            "function_path": "defination.tools.calculator:calculate",
            "enabled": True,
            "timeout": 10,
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "要计算的数学表达式"}
                },
                "required": ["expression"]
            }
        }
        
        # 模拟工具对象
        mock_hash_tool = Mock()
        mock_hash_tool.name = "hash_convert"
        mock_hash_tool.tool_type = "builtin"
        mock_hash_tool.get_schema.return_value = hash_convert_config["parameters_schema"]
        
        mock_calc_tool = Mock()
        mock_calc_tool.name = "calculator"
        mock_calc_tool.tool_type = "builtin"
        mock_calc_tool.get_schema.return_value = calculator_config["parameters_schema"]
        
        # 设置模拟
        def mock_load(path):
            if "hash_convert" in path:
                return hash_convert_config
            elif "calculator" in path:
                return calculator_config
            else:
                return {}
        
        self.mock_config_loader.load.side_effect = mock_load
        self.mock_tool_manager.get_tool.side_effect = lambda name: {
            "hash_convert": mock_hash_tool,
            "calculator": mock_calc_tool
        }[name]
        
        # 创建检验管理器
        validation_manager = ToolValidationManager(
            self.mock_config_loader,
            self.mock_logger,
            self.mock_tool_manager
        )
        
        # 模拟获取配置文件
        with patch.object(validation_manager, '_get_tool_config_files', return_value=mock_config_files):
            all_results = validation_manager.validate_all_tools()
        
        # 验证结果
        assert len(all_results) == 2
        assert "hash_convert" in all_results
        assert "calculator" in all_results
        
        # 验证每个工具的验证结果
        for tool_name, tool_results in all_results.items():
            assert "config" in tool_results
            assert "loading" in tool_results
            
            # 只有在配置验证成功时，才会执行类型特定验证
            if tool_results["config"].is_successful():
                tool_type = tool_results["config"].metadata.get("tool_type")
                if tool_type in ["builtin", "native", "mcp"]:
                    assert "type" in tool_results
                    assert tool_results["type"].is_successful()
            
            # 验证所有阶段都成功
            assert tool_results["config"].is_successful()
            assert tool_results["loading"].is_successful()
    
    def test_generate_report(self):
        """测试报告生成"""
        # 创建检验管理器
        validation_manager = ToolValidationManager(
            self.mock_config_loader,
            self.mock_logger,
            self.mock_tool_manager
        )
        
        # 模拟验证结果
        mock_config_result = Mock()
        mock_config_result.is_successful.return_value = True
        mock_config_result.status = ValidationStatus.SUCCESS
        mock_config_result.issues = []
        mock_config_result.tool_name = "test_tool"
        mock_config_result.tool_type = "builtin"
        
        mock_loading_result = Mock()
        mock_loading_result.is_successful.return_value = True
        mock_loading_result.status = ValidationStatus.SUCCESS
        mock_loading_result.issues = []
        mock_loading_result.tool_name = "test_tool"
        mock_loading_result.tool_type = "builtin"
        
        all_results = {
            "test_tool": {
                "config": mock_config_result,
                "loading": mock_loading_result
            }
        }
        
        # 生成文本报告
        text_report = validation_manager.generate_report(all_results, "text")
        assert "工具检验报告" in text_report
        assert "test_tool" in text_report
        
        # 生成JSON报告
        json_report = validation_manager.generate_report(all_results, "json")
        import json
        report_data = json.loads(json_report)
        assert "summary" in report_data
        assert report_data["summary"]["total_tools"] == 1