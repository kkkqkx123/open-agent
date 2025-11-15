"""状态机工作流工厂测试

测试状态机工作流工厂的功能。
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

from src.application.workflow.state_machine.state_machine_workflow_factory import (
    StateMachineWorkflowFactory, StateMachineConfigLoader,
    StateMachineWorkflow, StateMachineConfig, StateDefinition, Transition, StateType
)
from src.infrastructure.graph.config import WorkflowConfig
from infrastructure.config.loader.file_config_loader import IConfigLoader
from src.infrastructure.container import IDependencyContainer


class TestStateMachineWorkflowFactory:
    """测试状态机工作流工厂"""

    @pytest.fixture
    def factory(self):
        """工厂fixture"""
        return StateMachineWorkflowFactory()

    @pytest.fixture
    def basic_workflow_config(self):
        """基本工作流配置fixture"""
        return WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            version="1.0.0",
            nodes={},
            edges=[],
            entry_point="start"
        )

    def test_factory_init(self):
        """测试工厂初始化"""
        factory = StateMachineWorkflowFactory()
        assert factory.config_loader is None
        assert factory.container is None
        assert factory._workflow_classes == {}

    def test_factory_init_with_params(self):
        """测试带参数的工厂初始化"""
        mock_config_loader = Mock(spec=IConfigLoader)
        mock_container = Mock(spec=IDependencyContainer)
        
        factory = StateMachineWorkflowFactory(mock_config_loader, mock_container)
        assert factory.config_loader == mock_config_loader
        assert factory.container == mock_container

    def test_register_workflow_type(self, factory):
        """测试注册工作流类型"""
        class TestWorkflow(StateMachineWorkflow):
            pass
        
        factory.register_workflow_type("test_workflow", TestWorkflow)
        assert "test_workflow" in factory._workflow_classes
        assert factory._workflow_classes["test_workflow"] == TestWorkflow

    def test_get_supported_types(self, factory):
        """测试获取支持的工作流类型"""
        class TestWorkflow(StateMachineWorkflow):
            pass
            
        factory.register_workflow_type("test_workflow", TestWorkflow)
        supported_types = factory.get_supported_types()
        assert "test_workflow" in supported_types
        assert len(supported_types) == 1

    def test_create_workflow_success(self, factory, basic_workflow_config):
        """测试成功创建工作流"""
        class TestWorkflow(StateMachineWorkflow):
            def __init__(self, config, state_machine_config=None, config_loader=None, container=None):
                super().__init__(config, state_machine_config, config_loader, container)
        
        factory.register_workflow_type("test_workflow", TestWorkflow)
        
        workflow = factory.create_workflow(basic_workflow_config)
        assert isinstance(workflow, TestWorkflow)

    def test_create_workflow_not_registered(self, factory, basic_workflow_config):
        """测试创建未注册的工作流"""
        basic_workflow_config.name = "unregistered_workflow"
        
        with pytest.raises(ValueError, match="未注册的工作流: unregistered_workflow"):
            factory.create_workflow(basic_workflow_config)

    def test_register_workflow(self, factory):
        """测试注册工作流"""
        class TestWorkflow(StateMachineWorkflow):
            pass
            
        factory.register_workflow("test_workflow", TestWorkflow)
        assert "test_workflow" in factory._workflow_classes
        assert factory._workflow_classes["test_workflow"] == TestWorkflow

    def test_unregister_workflow(self, factory):
        """测试注销工作流"""
        class TestWorkflow(StateMachineWorkflow):
            pass
            
        factory.register_workflow("test_workflow", TestWorkflow)
        assert "test_workflow" in factory._workflow_classes
        
        factory.unregister_workflow("test_workflow")
        assert "test_workflow" not in factory._workflow_classes

    def test_get_registered_workflows(self, factory):
        """测试获取已注册的工作流"""
        class TestWorkflow(StateMachineWorkflow):
            pass
            
        factory.register_workflow("test_workflow", TestWorkflow)
        registered = factory.get_registered_workflows()
        
        assert isinstance(registered, dict)
        assert "test_workflow" in registered
        assert registered["test_workflow"] == TestWorkflow


    def test_create_state_machine_config_default(self, factory):
        """测试创建默认状态机配置"""
        config = factory._create_state_machine_config("unknown_workflow", None)
        assert config.name == "unknown_workflow"
        assert config.initial_state == "start"

    def test_create_state_machine_config_deep_thinking(self, factory):
        """测试创建深度思考状态机配置"""
        config = factory._create_state_machine_config("deep_thinking", None)
        assert config.name == "deep_thinking_workflow"
        assert config.initial_state == "initial"
    
    def test_create_state_machine_config_ultra_thinking(self, factory):
        """测试创建超思考状态机配置"""
        config = factory._create_state_machine_config("ultra_thinking", None)
        assert config.name == "ultra_thinking_workflow"
        assert config.initial_state == "initial"


class TestStateMachineConfigLoader:
    """测试状态机配置加载器"""

    def test_parse_config_basic(self):
        """测试解析基本配置"""
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
        
        config = StateMachineConfigLoader._parse_config(config_data)
        
        assert config.name == "test_workflow"
        assert config.description == "测试工作流"
        assert config.version == "1.0.0"
        assert config.initial_state == "start"
        
        # 检查状态
        assert len(config.states) == 3
        assert "start" in config.states
        assert "process" in config.states
        assert "end" in config.states
        
        # 检查状态类型
        assert config.states["start"].state_type == StateType.START
        assert config.states["process"].state_type == StateType.PROCESS
        assert config.states["end"].state_type == StateType.END
        
        # 检查转移
        process_state = config.states["process"]
        assert len(process_state.transitions) == 1
        transition = process_state.transitions[0]
        assert transition.target_state == "end"
        assert transition.condition == "always"
        assert transition.description == "转移到结束"

    def test_load_from_yaml(self):
        """测试从YAML文件加载配置"""
        config_data = {
            "name": "test_workflow",
            "description": "测试工作流",
            "version": "1.0.0",
            "initial_state": "start",
            "states": {
                "start": {
                    "type": "start"
                },
                "end": {
                    "type": "end"
                }
            }
        }
        
        # 创建临时YAML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = StateMachineConfigLoader.load_from_yaml(temp_path)
            assert config.name == "test_workflow"
            assert config.initial_state == "start"
            assert len(config.states) == 2
        finally:
            os.unlink(temp_path)


class TestGlobalFunctions:
    """测试全局函数"""

    def test_get_state_machine_factory(self):
        """测试获取状态机工厂"""
        from src.application.workflow.state_machine.state_machine_workflow_factory import get_state_machine_factory, _state_machine_factory
        
        # 重置全局工厂
        _state_machine_factory = None
        with patch('src.application.workflow.state_machine.state_machine_workflow_factory._state_machine_factory', _state_machine_factory):
            factory1 = get_state_machine_factory()
            factory2 = get_state_machine_factory()
            
            assert factory1 is not None
            assert factory2 is not None
            assert factory1 == factory2

    def test_register_state_machine_workflow(self):
        """测试注册状态机工作流"""
        from src.application.workflow.state_machine.state_machine_workflow_factory import (
            register_state_machine_workflow, get_state_machine_factory
        )
        
        class TestWorkflow(StateMachineWorkflow):
            pass
        
        # 重置工厂
        with patch('src.application.workflow.state_machine.state_machine_workflow_factory._state_machine_factory', None):
            register_state_machine_workflow("test_workflow", TestWorkflow)
            
            factory = get_state_machine_factory()
            assert "test_workflow" in factory._workflow_classes
            assert factory._workflow_classes["test_workflow"] == TestWorkflow

    def test_create_state_machine_workflow(self):
        """测试创建状态机工作流"""
        from src.application.workflow.state_machine.state_machine_workflow_factory import (
            create_state_machine_workflow, register_state_machine_workflow
        )
        
        class TestWorkflow(StateMachineWorkflow):
            def __init__(self, config, state_machine_config=None, **kwargs):
                # 简化初始化以避免依赖
                self.config = config
                self.state_machine_config = state_machine_config
        
        # 重置工厂
        with patch('src.application.workflow.state_machine.state_machine_workflow_factory._state_machine_factory', None):
            register_state_machine_workflow("test_workflow", TestWorkflow)
            
            workflow_config = WorkflowConfig(
                name="test_workflow",
                description="测试工作流",
                version="1.0.0",
                nodes={},
                edges=[],
                entry_point="start"
            )
            
            workflow = create_state_machine_workflow(workflow_config)
            assert isinstance(workflow, TestWorkflow)
            assert workflow.config == workflow_config