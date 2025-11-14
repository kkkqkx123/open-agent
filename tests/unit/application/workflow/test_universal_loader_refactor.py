"""测试UniversalWorkflowLoader重构后的功能"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.application.workflow.universal_loader import UniversalWorkflowLoader
from infrastructure.config.config_loader import IConfigLoader
from src.infrastructure.graph.config import GraphConfig
from src.infrastructure.graph.function_registry import FunctionType


class TestUniversalWorkflowLoaderRefactor:
    """测试UniversalWorkflowLoader重构后的功能"""

    @pytest.fixture
    def mock_config_loader(self):
        """模拟配置加载器"""
        mock_loader = Mock(spec=IConfigLoader)
        mock_loader.load.return_value = {
            "name": "test_workflow",
            "description": "Test workflow",
            "version": "1.0",
            "state_schema": {
                "name": "TestState",
                "fields": {
                    "messages": {
                        "type": "list",
                        "default": []
                    }
                }
            },
            "nodes": {
                "agent": {
                    "function": "test_agent_node",
                    "config": {}
                }
            },
            "edges": [
                {
                    "from": "__start__",
                    "to": "agent",
                    "type": "simple"
                }
            ],
            "entry_point": "agent"
        }
        return mock_loader

    @pytest.fixture
    def universal_loader(self, mock_config_loader):
        """创建UniversalWorkflowLoader实例"""
        return UniversalWorkflowLoader(
            config_loader=mock_config_loader,
            container=None,
            enable_auto_registration=False  # 禁用自动注册以简化测试
        )

    def test_init_with_config_loader(self, mock_config_loader):
        """测试使用配置加载器初始化"""
        loader = UniversalWorkflowLoader(
            config_loader=mock_config_loader,
            enable_auto_registration=False
        )
        
        assert loader.config_loader == mock_config_loader
        assert loader.enable_auto_registration is False

    def test_load_config_from_file_delegates_to_loader(self, universal_loader, mock_config_loader):
        """测试从文件加载配置委托给核心加载器"""
        config_path = "test_workflow.yaml"
        
        result = universal_loader._load_config_from_file(config_path)
        
        # 验证委托给了核心加载器
        mock_config_loader.load.assert_called_once_with(config_path)
        
        # 验证返回了GraphConfig对象
        assert isinstance(result, GraphConfig)
        assert result.name == "test_workflow"
        assert result.description == "Test workflow"

    def test_load_config_from_file_with_cache(self, universal_loader, mock_config_loader):
        """测试配置缓存功能"""
        config_path = "test_workflow.yaml"
        
        # 第一次加载
        result1 = universal_loader._load_config_from_file(config_path)
        
        # 第二次加载应该使用缓存
        result2 = universal_loader._load_config_from_file(config_path)
        
        # 验证只调用了一次加载器
        mock_config_loader.load.assert_called_once_with(config_path)
        
        # 验证返回了相同的对象
        assert result1 is result2

    def test_load_config_from_file_without_loader(self):
        """测试没有配置加载器时的错误处理"""
        loader = UniversalWorkflowLoader(
            config_loader=None,
            enable_auto_registration=False
        )
        
        # 模拟文件存在，但内容无效
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', side_effect=FileNotFoundError("No such file")):
                with pytest.raises(Exception) as exc_info:
                    loader._load_config_from_file("test.yaml")
        
        assert "加载配置文件失败" in str(exc_info.value)

    def test_load_from_file_uses_config_loader(self, universal_loader, mock_config_loader):
        """测试从文件加载工作流使用配置加载器"""
        config_path = "test_workflow.yaml"
        
        # 注册测试函数
        def test_agent_node(state):
            return {"result": "test"}
        
        universal_loader.register_function("test_agent_node", test_agent_node, FunctionType.NODE_FUNCTION)
        
        # 模拟文件存在
        with patch('pathlib.Path.exists', return_value=True):
            workflow_instance = universal_loader.load_from_file(config_path)
        
        # 验证配置加载器被调用
        mock_config_loader.load.assert_called_with(config_path)
        
        # 验证返回了工作流实例
        assert workflow_instance is not None
        assert hasattr(workflow_instance, 'config')
        assert hasattr(workflow_instance, 'graph')

    def test_load_from_dict_uses_config_loader(self, universal_loader):
        """测试从字典加载工作流"""
        # 注册测试函数
        def test_node(state):
            return {"result": "test"}
        
        universal_loader.register_function("test_node", test_node, FunctionType.NODE_FUNCTION)
        
        config_dict = {
            "name": "test_workflow",
            "description": "Test workflow",
            "version": "1.0",
            "state_schema": {
                "name": "TestState",
                "fields": {
                    "messages": {
                        "type": "list",
                        "default": []
                    }
                }
            },
            "nodes": {
                "test_node": {
                    "function": "test_node",
                    "config": {}
                }
            },
            "edges": [
                {
                    "from": "__start__",
                    "to": "test_node",
                    "type": "simple"
                }
            ],
            "entry_point": "test_node"
        }
        
        workflow_instance = universal_loader.load_from_dict(config_dict)
        
        # 验证返回了工作流实例
        assert workflow_instance is not None
        assert hasattr(workflow_instance, 'config')
        assert hasattr(workflow_instance, 'graph')

    def test_process_function_registrations_still_works(self, universal_loader):
        """测试函数注册处理功能仍然正常工作"""
        config_data = {
            "function_registrations": {
                "nodes": {
                    "test_node": "test.module.test_node"
                },
                "conditions": {
                    "test_condition": "test.module.test_condition"
                },
                "auto_discovery": {
                    "enabled": False
                }
            }
        }
        
        # 模拟模块导入
        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_module.test_node = Mock()
            mock_module.test_condition = Mock()
            mock_import.return_value = mock_module
            
            universal_loader._process_function_registrations(config_data)
            
            # 验证尝试注册了函数
            assert mock_import.call_count >= 2

    def test_validate_config_still_works(self, universal_loader):
        """测试配置验证功能仍然正常工作"""
        # 创建无效配置
        invalid_config = GraphConfig.from_dict({
            "name": "",  # 空名称应该导致验证失败
            "description": "Test",
            "version": "1.0",
            "state_schema": {"name": "State", "fields": {}},
            "nodes": {},
            "edges": []
        })
        
        result = universal_loader.validate_config(invalid_config)
        
        # 验证验证失败
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("名称不能为空" in error for error in result.errors)

    def test_error_handling_in_load_config_file(self, universal_loader, mock_config_loader):
        """测试加载配置文件时的错误处理"""
        # 模拟配置加载器抛出异常
        mock_config_loader.load.side_effect = Exception("Load failed")
        
        with pytest.raises(Exception) as exc_info:
            universal_loader._load_config_from_file("test.yaml")
        
        assert "加载配置文件失败" in str(exc_info.value)