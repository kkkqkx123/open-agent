"""模块注册管理器单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.infrastructure.registry.module_registry_manager import (
    ModuleRegistryManager,
    RegistryInfo,
    TypeInfo
)
from src.infrastructure.registry.config_validator import ValidationResult


class TestRegistryInfo:
    """测试RegistryInfo类"""
    
    def test_init(self):
        """测试初始化"""
        info = RegistryInfo(
            name="test_registry",
            config_path="test/path.yaml"
        )
        
        assert info.name == "test_registry"
        assert info.config_path == "test/path.yaml"
        assert info.config == {}
        assert info.validation_result is None
        assert info.loaded is False
        assert info.enabled is True


class TestTypeInfo:
    """测试TypeInfo类"""
    
    def test_init(self):
        """测试初始化"""
        info = TypeInfo(
            name="test_type",
            class_path="module.TestClass",
            description="Test type",
            enabled=True
        )
        
        assert info.name == "test_type"
        assert info.class_path == "module.TestClass"
        assert info.description == "Test type"
        assert info.enabled is True
        assert info.config_files == []
        assert info.class_instance is None
        assert info.loaded is False


class TestModuleRegistryManager:
    """测试ModuleRegistryManager类"""
    
    @pytest.fixture
    def registry_manager(self):
        """创建注册管理器实例"""
        return ModuleRegistryManager(base_path="test/configs")
    
    def test_init(self, registry_manager):
        """测试初始化"""
        assert registry_manager.base_path == Path("test/configs")
        assert registry_manager.initialized is False
        assert len(registry_manager.workflow_types) == 0
        assert len(registry_manager.tool_types) == 0
        assert len(registry_manager.state_machine_configs) == 0
        assert len(registry_manager.tool_sets) == 0
    
    @patch('src.infrastructure.registry.module_registry_manager.ConfigParser')
    def test_initialize_success(self, mock_config_parser, registry_manager):
        """测试成功初始化"""
        # 模拟配置解析器
        mock_parser = Mock()
        mock_config_parser.return_value = mock_parser
        
        # 模拟工作流注册表配置
        workflow_registry_config = {
            "workflow_types": {
                "test_workflow": {
                    "class_path": "module.TestWorkflow",
                    "description": "Test workflow",
                    "enabled": True,
                    "config_files": ["test.yaml"]
                }
            }
        }
        
        # 模拟工具注册表配置
        tool_registry_config = {
            "tool_types": {
                "test_tool": {
                    "class_path": "module.TestTool",
                    "description": "Test tool",
                    "enabled": True,
                    "config_files": ["tool.yaml"]
                }
            },
            "tool_sets": {
                "basic_tools": {
                    "description": "Basic tools",
                    "enabled": True,
                    "tools": ["test_tool"]
                }
            }
        }
        
        # 模拟状态机注册表配置
        state_machine_registry_config = {
            "config_files": {
                "test_state_machine": {
                    "file_path": "state_machine.yaml",
                    "description": "Test state machine",
                    "enabled": True
                }
            }
        }
        
        # 设置模拟返回值
        mock_parser.parse_registry_config.side_effect = [
            workflow_registry_config,
            tool_registry_config,
            state_machine_registry_config
        ]
        mock_parser.get_validation_result.return_value = ValidationResult()
        
        # 初始化
        registry_manager.config_parser = mock_parser
        registry_manager.initialize()
        
        # 验证结果
        assert registry_manager.initialized is True
        assert len(registry_manager.workflow_types) == 1
        assert len(registry_manager.tool_types) == 1
        assert len(registry_manager.state_machine_configs) == 1
        assert len(registry_manager.tool_sets) == 1
        
        # 验证工作流类型
        workflow_type = registry_manager.get_workflow_type("test_workflow")
        assert workflow_type is not None
        assert workflow_type.name == "test_workflow"
        assert workflow_type.class_path == "module.TestWorkflow"
        assert workflow_type.enabled is True
        
        # 验证工具类型
        tool_type = registry_manager.get_tool_type("test_tool")
        assert tool_type is not None
        assert tool_type.name == "test_tool"
        assert tool_type.class_path == "module.TestTool"
        assert tool_type.enabled is True
        
        # 验证工具集
        tool_set = registry_manager.get_tool_set("basic_tools")
        assert tool_set is not None
        assert tool_set["description"] == "Basic tools"
        assert tool_set["enabled"] is True
        assert "test_tool" in tool_set["tools"]
    
    @patch('src.infrastructure.registry.module_registry_manager.ConfigParser')
    def test_initialize_failure(self, mock_config_parser, registry_manager):
        """测试初始化失败"""
        # 模拟配置解析器抛出异常
        mock_parser = Mock()
        mock_config_parser.return_value = mock_parser
        mock_parser.parse_registry_config.side_effect = Exception("Parse error")
        
        registry_manager.config_parser = mock_parser
        
        # 初始化应该失败但不抛出异常
        registry_manager.initialize()
        
        # 验证状态
        assert registry_manager.initialized is False
        assert len(registry_manager.workflow_types) == 0
        assert len(registry_manager.tool_types) == 0
    
    def test_get_workflow_type_not_found(self, registry_manager):
        """测试获取不存在的工作流类型"""
        workflow_type = registry_manager.get_workflow_type("nonexistent")
        assert workflow_type is None
    
    def test_get_tool_type_not_found(self, registry_manager):
        """测试获取不存在的工具类型"""
        tool_type = registry_manager.get_tool_type("nonexistent")
        assert tool_type is None
    
    def test_get_tool_set_not_found(self, registry_manager):
        """测试获取不存在的工具集"""
        tool_set = registry_manager.get_tool_set("nonexistent")
        assert tool_set is None
    
    def test_get_workflow_types_empty(self, registry_manager):
        """测试获取空的工作流类型列表"""
        workflow_types = registry_manager.get_workflow_types()
        assert workflow_types == {}
    
    def test_get_tool_types_empty(self, registry_manager):
        """测试获取空的工具类型列表"""
        tool_types = registry_manager.get_tool_types()
        assert tool_types == {}
    
    def test_get_state_machine_configs_empty(self, registry_manager):
        """测试获取空的状态机配置列表"""
        state_machine_configs = registry_manager.get_state_machine_configs()
        assert state_machine_configs == {}
    
    @patch('src.infrastructure.registry.module_registry_manager.ConfigParser')
    def test_reload_registry(self, mock_config_parser, registry_manager):
        """测试重新加载注册表"""
        # 模拟配置解析器
        mock_parser = Mock()
        mock_config_parser.return_value = mock_parser
        
        # 模拟注册表配置
        registry_config = {
            "workflow_types": {
                "test_workflow": {
                    "class_path": "module.TestWorkflow",
                    "description": "Test workflow",
                    "enabled": True,
                    "config_files": ["test.yaml"]
                }
            }
        }
        
        mock_parser.parse_registry_config.return_value = registry_config
        mock_parser.get_validation_result.return_value = ValidationResult()
        
        registry_manager.config_parser = mock_parser
        
        # 初始化
        registry_manager.initialize()
        assert len(registry_manager.workflow_types) == 1
        
        # 重新加载
        registry_manager.reload_registry("workflows")
        
        # 验证重新加载后仍然有数据
        assert len(registry_manager.workflow_types) == 1
    
    def test_clear_cache(self, registry_manager):
        """测试清除缓存"""
        # 添加一些缓存数据
        registry_manager.config_cache["test"] = {"data": "test"}
        
        # 清除缓存
        registry_manager.clear_cache()
        
        # 验证缓存已清除
        assert len(registry_manager.config_cache) == 0
    
    def test_get_registry_info(self, registry_manager):
        """测试获取注册表信息"""
        info = registry_manager.get_registry_info()
        
        expected_keys = {
            "initialized",
            "registries",
            "workflow_types",
            "tool_types",
            "state_machine_configs",
            "tool_sets",
            "cache_size"
        }
        
        for key in expected_keys:
            assert key in info
        
        assert info["initialized"] is False
        assert info["workflow_types"] == 0
        assert info["tool_types"] == 0
        assert info["state_machine_configs"] == 0
        assert info["tool_sets"] == 0
        assert info["cache_size"] == 0


if __name__ == "__main__":
    pytest.main([__file__])