"""
工具检验管理器单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.infrastructure.tools.validation.manager import ToolValidationManager
from src.infrastructure.tools.validation.models import ValidationStatus


class TestToolValidationManager:
    """工具检验管理器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_config_loader = Mock()
        self.mock_config_loader.base_path = "configs"  # 添加base_path属性
        self.mock_logger = Mock()
        self.mock_tool_manager = Mock()
        
        # 创建验证器的Mock对象
        self.mock_config_validator = Mock()
        self.mock_loading_validator = Mock()
        self.mock_builtin_validator = Mock()
        self.mock_native_validator = Mock()
        self.mock_mcp_validator = Mock()
        
        self.manager = ToolValidationManager(
            self.mock_config_loader,
            self.mock_logger,
            self.mock_tool_manager
        )
        
        # 替换验证器为Mock对象
        self.manager.validators = {
            "config": self.mock_config_validator,
            "loading": self.mock_loading_validator,
            "builtin": self.mock_builtin_validator,
            "native": self.mock_native_validator,
            "mcp": self.mock_mcp_validator
        }
    
    def test_init_without_tool_manager(self):
        """测试不带工具管理器的初始化"""
        manager = ToolValidationManager(
            self.mock_config_loader, 
            self.mock_logger
        )
        
        # 验证加载验证器未注册
        assert "loading" not in manager.validators
    
    def test_validate_tool_success(self):
        """测试工具验证成功"""
        # 模拟配置验证结果
        mock_config_result = Mock()
        mock_config_result.is_successful.return_value = True
        mock_config_result.metadata = {
            "tool_type": "builtin",
            "config_data": {"name": "test_tool", "tool_type": "builtin"}
        }
        
        # 模拟类型验证结果
        mock_type_result = Mock()
        mock_type_result.is_successful.return_value = True
        
        # 模拟加载验证结果
        mock_loading_result = Mock()
        mock_loading_result.is_successful.return_value = True
        
        # 设置验证器返回值
        self.mock_config_validator.validate_config.return_value = mock_config_result
        self.mock_builtin_validator.validate_tool_type.return_value = mock_type_result
        self.mock_loading_validator.validate_loading.return_value = mock_loading_result
        
        results = self.manager.validate_tool("test_tool", "tools/test_tool.yaml")
        
        # 验证所有验证器都被调用
        self.mock_config_validator.validate_config.assert_called_once_with("tools/test_tool.yaml")
        self.mock_builtin_validator.validate_tool_type.assert_called_once_with(
            "builtin", {"name": "test_tool", "tool_type": "builtin"}
        )
        self.mock_loading_validator.validate_loading.assert_called_once_with("test_tool")
        
        # 验证返回结果
        assert "config" in results
        assert "type" in results
        assert "loading" in results
    
    def test_validate_tool_config_failure(self):
        """测试配置验证失败"""
        # 模拟配置验证失败
        mock_config_result = Mock()
        mock_config_result.is_successful.return_value = False
        mock_config_result.metadata = {}
        
        # 设置验证器返回值
        self.mock_config_validator.validate_config.return_value = mock_config_result
        
        results = self.manager.validate_tool("test_tool", "tools/test_tool.yaml")
        
        # 验证只有配置验证被调用
        self.mock_config_validator.validate_config.assert_called_once_with("tools/test_tool.yaml")
        self.mock_builtin_validator.validate_tool_type.assert_not_called()
        self.mock_loading_validator.validate_loading.assert_called_once_with("test_tool")
        
        # 验证返回结果
        assert "config" in results
        # 类型验证不应该被执行
        assert "type" not in results
    
    def test_validate_tool_unsupported_type(self):
        """测试不支持的工具类型"""
        # 模拟配置验证结果
        mock_config_result = Mock()
        mock_config_result.is_successful.return_value = True
        mock_config_result.metadata = {
            "tool_type": "unsupported",
            "config_data": {"name": "test_tool", "tool_type": "unsupported"}
        }
        
        # 设置验证器返回值
        self.mock_config_validator.validate_config.return_value = mock_config_result
        
        results = self.manager.validate_tool("test_tool", "tools/test_tool.yaml")
        
        # 验证类型验证未被调用（因为类型不支持）
        self.mock_config_validator.validate_config.assert_called_once_with("tools/test_tool.yaml")
        assert "unsupported" not in self.manager.validators
        self.mock_loading_validator.validate_loading.assert_called_once_with("test_tool")
        
        # 验证返回结果
        assert "config" in results
        assert "type" not in results
    
    def test_validate_all_tools_success(self):
       """测试验证所有工具成功"""
       # 模拟配置文件
       mock_config_files = [
           Path("tool1.yaml"),
           Path("tool2.yaml")
       ]
       
       # 模拟验证结果
       mock_results = {"config": Mock()}
       
       with patch.object(self.manager, '_get_tool_config_files', return_value=mock_config_files):
           with patch.object(self.manager, 'validate_tool', return_value=mock_results) as mock_validate_tool:
               all_results = self.manager.validate_all_tools("tools")
       
       # 验证validate_tool被调用两次
       assert mock_validate_tool.call_count == 2
       mock_validate_tool.assert_any_call("tool1", "tools/tool1.yaml")
       mock_validate_tool.assert_any_call("tool2", "tools/tool2.yaml")
       
       # 验证返回结果
       assert "tool1" in all_results
       assert "tool2" in all_results
    
    def test_validate_all_tools_exception(self):
        """测试验证所有工具时异常"""
        with patch.object(self.manager, '_get_tool_config_files', side_effect=Exception("获取文件失败")):
            all_results = self.manager.validate_all_tools("configs/tools")
        
        # 验证返回空结果
        assert all_results == {}
        # 验证记录了错误日志
        self.mock_logger.error.assert_called_once()
    
    def test_get_tool_config_files_success(self):
       """测试获取工具配置文件成功"""
       with patch.object(Path, "exists", return_value=True):
           with patch.object(Path, "glob", return_value=[Path("tool1.yaml"), Path("tool2.yaml")]):
               files = self.manager._get_tool_config_files("tools")
       
       assert len(files) == 2
       assert str(files[0]) == "tool1.yaml"
       assert str(files[1]) == "tool2.yaml"
    
    def test_get_tool_config_files_directory_not_exists(self):
       """测试配置目录不存在"""
       with patch.object(Path, "exists", return_value=False):
           files = self.manager._get_tool_config_files("tools")
       
       assert files == []
       # 验证记录了警告日志
       self.mock_logger.warning.assert_called_once()
    
    def test_generate_text_report(self):
        """测试生成文本报告"""
        # 模拟验证结果
        mock_config_result = Mock()
        mock_config_result.is_successful.return_value = True
        mock_config_result.status = ValidationStatus.SUCCESS
        mock_config_result.issues = []
        
        mock_loading_result = Mock()
        mock_loading_result.is_successful.return_value = True
        mock_loading_result.status = ValidationStatus.SUCCESS
        mock_loading_result.issues = []
        
        all_results = {
            "test_tool": {
                "config": mock_config_result,
                "loading": mock_loading_result
            }
        }
        
        report = self.manager.generate_report(all_results, "text")
        
        # 验证报告包含关键信息
        assert "工具检验报告" in report
        assert "工具: test_tool" in report
        assert "config: ✓" in report
        assert "loading: ✓" in report
        assert "总结:" in report
    
    def test_generate_json_report(self):
        """测试生成JSON报告"""
        # 模拟验证结果
        mock_config_result = Mock()
        mock_config_result.is_successful.return_value = True
        mock_config_result.status = ValidationStatus.SUCCESS
        mock_config_result.issues = []
        
        mock_loading_result = Mock()
        mock_loading_result.is_successful.return_value = True
        mock_loading_result.status = ValidationStatus.SUCCESS
        mock_loading_result.issues = []
        
        all_results = {
            "test_tool": {
                "config": mock_config_result,
                "loading": mock_loading_result
            }
        }
        
        report = self.manager.generate_report(all_results, "json")
        
        # 验证报告是有效的JSON
        import json
        report_data = json.loads(report)
        
        # 验证报告结构
        assert "summary" in report_data
        assert "tools" in report_data
        assert "test_tool" in report_data["tools"]
        assert report_data["summary"]["total_tools"] == 1
        assert report_data["summary"]["successful_tools"] == 1