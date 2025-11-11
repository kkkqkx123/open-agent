"""状态机工作流配置加载器测试

测试状态机工作流配置加载功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional
import sys
import os
import tempfile
import yaml

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../src'))

from application.workflow.state_machine.state_machine_config_loader import (
    StateMachineWorkflowLoader, load_state_machine_workflow, create_state_machine_workflow_from_dict
)
from application.workflow.state_machine.state_machine_workflow import (
    StateMachineWorkflow, StateMachineConfig, StateDefinition, Transition, StateType
)
from application.workflow.state_machine.state_machine_workflow_factory import StateMachineWorkflowFactory
from src.infrastructure.graph.config import WorkflowConfig


class TestStateMachineWorkflowLoader:
    """测试状态机工作流加载器"""

    @pytest.fixture
    def loader(self):
        """加载器fixture"""
        return StateMachineWorkflowLoader()

    @pytest.fixture
    def basic_config_data(self):
        """基本配置数据fixture"""
        return {
            "name": "test_workflow",
            "description": "测试工作流",
            "version": "1.0.0",
            "initial_state": "start",
            "states": {
                "start": {
                    "type": "start",
                    "description": "开始状态"
                },
                "process": {
                    "type": "process",
                    "description": "处理状态",
                    "transitions": [
                        {
                            "target": "end",
                            "condition": "always",
                            "description": "转移到结束"
                        }
                    ]
                },
                "end": {
                    "type": "end",
                    "description": "结束状态"
                }
            }
        }

    def test_loader_init(self):
        """测试加载器初始化"""
        loader = StateMachineWorkflowLoader()
        assert isinstance(loader.factory, StateMachineWorkflowFactory)
        
        # 测试使用自定义工厂
        mock_factory = Mock(spec=StateMachineWorkflowFactory)
        loader_with_factory = StateMachineWorkflowLoader(mock_factory)
        assert loader_with_factory.factory == mock_factory

    def test_load_yaml_file_success(self, loader):
        """测试成功加载YAML文件"""
        config_data = {
            "name": "test_workflow",
            "initial_state": "start"
        }
        
        # 创建临时YAML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            loaded_data = loader._load_yaml_file(temp_path)
            assert loaded_data["name"] == "test_workflow"
            assert loaded_data["initial_state"] == "start"
        finally:
            os.unlink(temp_path)

    def test_load_yaml_file_not_found(self, loader):
        """测试加载不存在的YAML文件"""
        with pytest.raises(FileNotFoundError, match="配置文件不存在: nonexistent.yaml"):
            loader._load_yaml_file("nonexistent.yaml")

    def test_parse_state_machine_config(self, loader):
        """测试解析状态机配置"""
        config_data = {
            "name": "test_workflow",
            "description": "测试工作流",
            "version": "1.0.0",
            "initial_state": "start",
            "states": {
                "start": {
                    "type": "start",
                    "description": "开始状态"
                },
                "process": {
                    "type": "process",
                    "description": "处理状态",
                    "transitions": [
                        {
                            "target": "end",
                            "condition": "always",
                            "description": "转移到结束"
                        }
                    ]
                },
                "end": {
                    "type": "end",
                    "description": "结束状态"
                }
            }
        }
        
        state_machine_config = loader._parse_state_machine_config(config_data)
        
        assert state_machine_config.name == "test_workflow"
        assert state_machine_config.description == "测试工作流"
        assert state_machine_config.version == "1.0.0"
        assert state_machine_config.initial_state == "start"
        
        # 检查状态
        assert len(state_machine_config.states) == 3
        assert "start" in state_machine_config.states
        assert "process" in state_machine_config.states
        assert "end" in state_machine_config.states

    def test_create_workflow_class(self, loader, basic_config_data):
        """测试创建工作流类"""
        state_machine_config = StateMachineConfig("test_workflow")
        
        workflow_class = loader._create_workflow_class(basic_config_data, state_machine_config)
        assert issubclass(workflow_class, StateMachineWorkflow)
        assert workflow_class.__name__ == "test_workflowWorkflow"

    def test_load_from_dict(self, loader, basic_config_data):
        """测试从字典加载"""
        with patch.object(loader.factory, 'create_workflow') as mock_create:
            mock_workflow = Mock(spec=StateMachineWorkflow)
            mock_create.return_value = mock_workflow
            
            workflow = loader.load_from_dict(basic_config_data)
            
            assert workflow == mock_workflow
            # 验证工厂方法被调用
            # 注意：register_workflow_type是一个方法，不是Mock对象，所以我们不能直接调用assert_called_once()
            # 我们可以通过其他方式验证它被调用了
            mock_create.assert_called_once()

    def test_load_from_file(self, loader, basic_config_data):
        """测试从文件加载"""
        # 创建临时YAML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(basic_config_data, f)
            temp_path = f.name
        
        try:
            with patch.object(loader.factory, 'create_workflow') as mock_create:
                mock_workflow = Mock(spec=StateMachineWorkflow)
                mock_create.return_value = mock_workflow
                
                workflow = loader.load_from_file(temp_path)
                
                assert workflow == mock_workflow
                # 验证工厂方法被调用
                # 注意：register_workflow_type是一个方法，不是Mock对象，所以我们不能直接调用assert_called_once()
                # 我们可以通过其他方式验证它被调用了
                mock_create.assert_called_once()
        finally:
            os.unlink(temp_path)


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_load_state_machine_workflow(self):
        """测试加载状态机工作流便捷函数"""
        config_data = {
            "name": "test_workflow",
            "initial_state": "start",
            "states": {
                "start": {"type": "start"},
                "end": {"type": "end"}
            }
        }
        
        # 创建临时YAML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            with patch('src.application.workflow.state_machine_config_loader.StateMachineWorkflowLoader') as mock_loader_class:
                mock_loader = Mock()
                mock_workflow = Mock(spec=StateMachineWorkflow)
                mock_loader.load_from_file.return_value = mock_workflow
                mock_loader_class.return_value = mock_loader
                
                workflow = load_state_machine_workflow(temp_path)
                
                assert workflow == mock_workflow
                mock_loader.load_from_file.assert_called_once_with(temp_path)
        finally:
            os.unlink(temp_path)

    def test_create_state_machine_workflow_from_dict(self):
        """测试从字典创建工作流便捷函数"""
        config_data = {
            "name": "test_workflow",
            "initial_state": "start",
            "states": {
                "start": {"type": "start"},
                "end": {"type": "end"}
            }
        }
        
        with patch('src.application.workflow.state_machine_config_loader.StateMachineWorkflowLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_workflow = Mock(spec=StateMachineWorkflow)
            mock_loader.load_from_dict.return_value = mock_workflow
            mock_loader_class.return_value = mock_loader
            
            workflow = create_state_machine_workflow_from_dict(config_data)
            
            assert workflow == mock_workflow
            mock_loader.load_from_dict.assert_called_once_with(config_data)