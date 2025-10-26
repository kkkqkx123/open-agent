"""工作流工厂测试"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import yaml

from src.application.workflow.factory import (
    UnifiedWorkflowFactory,
    get_global_factory,
    create_workflow_from_config,
    create_simple_workflow,
    create_react_workflow,
    create_plan_execute_workflow
)
from src.application.workflow.config import WorkflowConfig, NodeConfig, EdgeConfig, EdgeType
from src.infrastructure.graph.states import WorkflowState
from src.domain.prompts.interfaces import IPromptInjector


class TestUnifiedWorkflowFactory:
    """统一工作流工厂测试"""
    
    def test_init_with_default_components(self):
        """测试使用默认组件初始化"""
        factory = UnifiedWorkflowFactory()
        
        assert factory.node_registry is not None
        assert factory.workflow_builder is not None
        assert isinstance(factory._predefined_configs, dict)
    
    def test_init_with_custom_components(self):
        """测试使用自定义组件初始化"""
        mock_registry = Mock()
        mock_builder = Mock()
        
        factory = UnifiedWorkflowFactory(
            node_registry=mock_registry,
            workflow_builder=mock_builder
        )
        
        assert factory.node_registry is mock_registry
        assert factory.workflow_builder is mock_builder
    
    def test_create_from_config_success(self):
        """测试从配置成功创建工作流"""
        factory = UnifiedWorkflowFactory()
        
        # 创建模拟配置
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            nodes={
                "start": NodeConfig(type="mock_node")
            }
        )
        
        # 模拟构建器返回
        mock_workflow = Mock()
        factory.workflow_builder.build_workflow = Mock(return_value=mock_workflow)
        
        result = factory.create_from_config(config)
        
        assert result is mock_workflow
        factory.workflow_builder.build_workflow.assert_called_once_with(config)
    
    def test_create_from_config_failure(self):
        """测试从配置创建工作流失败"""
        factory = UnifiedWorkflowFactory()
        
        config = WorkflowConfig(name="test", description="测试")
        factory.workflow_builder.build_workflow = Mock(side_effect=Exception("构建失败"))
        
        with pytest.raises(Exception, match="构建失败"):
            factory.create_from_config(config)
    
    def test_create_simple_workflow(self):
        """测试创建简单工作流"""
        factory = UnifiedWorkflowFactory()
        mock_injector = Mock(spec=IPromptInjector)
        mock_injector.inject_prompts.return_value = WorkflowState()
        
        result = factory.create_simple(mock_injector)
        
        assert isinstance(result, dict)
        assert "run" in result
        assert "description" in result
        assert result["description"] == "简单提示词注入工作流"
        assert callable(result["run"])
    
    def test_create_simple_workflow_with_llm_client(self):
        """测试创建带LLM客户端的简单工作流"""
        factory = UnifiedWorkflowFactory()
        mock_injector = Mock(spec=IPromptInjector)
        mock_injector.inject_prompts.return_value = WorkflowState()
        mock_llm_client = Mock()
        mock_llm_client.generate.return_value = Mock()
        
        result = factory.create_simple(mock_injector, mock_llm_client)
        
        assert isinstance(result, dict)
        assert "run" in result
        
        # 测试运行工作流
        initial_state = WorkflowState()
        final_state = result["run"](initial_state)
        
        # 验证LLM被调用
        mock_llm_client.generate.assert_called_once()
    
    def test_create_react_workflow_with_config(self):
        """测试使用配置创建ReAct工作流"""
        factory = UnifiedWorkflowFactory()
        
        # 添加ReAct配置
        react_config = WorkflowConfig(
            name="react",
            description="ReAct工作流",
            nodes={"analyze": NodeConfig(type="analysis_node")}
        )
        factory.register_predefined_config("react", react_config)
        
        # 模拟构建器返回
        mock_workflow = Mock()
        factory.workflow_builder.build_workflow = Mock(return_value=mock_workflow)
        
        result = factory.create_react()
        
        assert result is mock_workflow
        factory.workflow_builder.build_workflow.assert_called_once_with(react_config)
    
    def test_create_react_workflow_no_config(self):
        """测试创建ReAct工作流但没有配置"""
        factory = UnifiedWorkflowFactory()
        
        with pytest.raises(ValueError, match="ReAct工作流配置未找到"):
            factory.create_react()
    
    def test_create_plan_execute_workflow(self):
        """测试创建Plan-Execute工作流"""
        factory = UnifiedWorkflowFactory()
        
        # 添加Plan-Execute配置
        plan_config = WorkflowConfig(
            name="plan_execute",
            description="Plan-Execute工作流",
            nodes={"plan": NodeConfig(type="llm_node")}
        )
        factory.register_predefined_config("plan_execute", plan_config)
        
        # 模拟构建器返回
        mock_workflow = Mock()
        factory.workflow_builder.build_workflow = Mock(return_value=mock_workflow)
        
        result = factory.create_plan_execute()
        
        assert result is mock_workflow
        factory.workflow_builder.build_workflow.assert_called_once_with(plan_config)
    
    def test_create_collaborative_workflow(self):
        """测试创建协作工作流"""
        factory = UnifiedWorkflowFactory()
        
        # 添加协作配置
        collab_config = WorkflowConfig(
            name="collaborative",
            description="协作工作流",
            nodes={"coordinator": NodeConfig(type="analysis_node")}
        )
        factory.register_predefined_config("collaborative", collab_config)
        
        # 模拟构建器返回
        mock_workflow = Mock()
        factory.workflow_builder.build_workflow = Mock(return_value=mock_workflow)
        
        result = factory.create_collaborative()
        
        assert result is mock_workflow
        factory.workflow_builder.build_workflow.assert_called_once_with(collab_config)
    
    def test_create_from_file(self):
        """测试从文件创建工作流"""
        factory = UnifiedWorkflowFactory()
        
        # 创建临时配置文件
        config_data = {
            "name": "file_workflow",
            "description": "从文件创建的工作流",
            "nodes": {
                "start": {"type": "mock_node"}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            # 模拟加载和构建
            mock_config = WorkflowConfig(
                name="file_workflow",
                description="从文件创建的工作流"
            )
            mock_workflow = Mock()
            
            factory.workflow_builder.load_workflow_config = Mock(return_value=mock_config)
            factory.workflow_builder.build_workflow = Mock(return_value=mock_workflow)
            
            result = factory.create_from_file(temp_path)
            
            assert result is mock_workflow
            factory.workflow_builder.load_workflow_config.assert_called_once_with(temp_path)
            factory.workflow_builder.build_workflow.assert_called_once_with(mock_config)
        finally:
            Path(temp_path).unlink()
    
    def test_list_predefined_workflows(self):
        """测试列出预定义工作流"""
        factory = UnifiedWorkflowFactory()
        
        # 添加一些配置
        factory.register_predefined_config("react", Mock())
        factory.register_predefined_config("plan_execute", Mock())
        
        workflows = factory.list_predefined_workflows()
        
        assert "react" in workflows
        assert "plan_execute" in workflows
        assert len(workflows) == 2
    
    def test_get_predefined_config(self):
        """测试获取预定义配置"""
        factory = UnifiedWorkflowFactory()
        
        config = WorkflowConfig(name="test", description="测试")
        factory.register_predefined_config("test", config)
        
        retrieved = factory.get_predefined_config("test")

        assert retrieved is not None
        assert retrieved is config
        assert retrieved.name == "test"
    
    def test_get_predefined_config_not_found(self):
        """测试获取不存在的预定义配置"""
        factory = UnifiedWorkflowFactory()
        
        result = factory.get_predefined_config("nonexistent")
        
        assert result is None
    
    def test_register_predefined_config(self):
        """测试注册预定义配置"""
        factory = UnifiedWorkflowFactory()
        
        config = WorkflowConfig(name="new_workflow", description="新工作流")
        factory.register_predefined_config("new_workflow", config)
        
        assert "new_workflow" in factory._predefined_configs
        assert factory._predefined_configs["new_workflow"] is config


class TestGlobalFactory:
    """全局工厂测试"""
    
    def test_get_global_factory_singleton(self):
        """测试全局工厂单例"""
        factory1 = get_global_factory()
        factory2 = get_global_factory()
        
        assert factory1 is factory2
        assert isinstance(factory1, UnifiedWorkflowFactory)
    
    @patch('src.application.workflow.factory.get_global_factory')
    def test_create_workflow_from_config(self, mock_get_factory):
        """测试从配置创建工作流的便捷函数"""
        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory
        
        config = WorkflowConfig(name="test", description="测试")
        mock_workflow = Mock()
        mock_factory.create_from_config.return_value = mock_workflow
        
        result = create_workflow_from_config(config)
        
        assert result is mock_workflow
        mock_factory.create_from_config.assert_called_once_with(config)
    
    @patch('src.application.workflow.factory.get_global_factory')
    def test_create_simple_workflow(self, mock_get_factory):
        """测试创建简单工作流的便捷函数"""
        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory
        
        mock_injector = Mock(spec=IPromptInjector)
        mock_workflow = {"run": Mock(), "description": "测试"}
        mock_factory.create_simple.return_value = mock_workflow
        
        result = create_simple_workflow(mock_injector)
        
        assert result is mock_workflow
        mock_factory.create_simple.assert_called_once_with(mock_injector, None)
    
    @patch('src.application.workflow.factory.get_global_factory')
    def test_create_react_workflow(self, mock_get_factory):
        """测试创建ReAct工作流的便捷函数"""
        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory
        
        mock_workflow = Mock()
        mock_factory.create_react.return_value = mock_workflow
        
        result = create_react_workflow()
        
        assert result is mock_workflow
        mock_factory.create_react.assert_called_once_with(None)
    
    @patch('src.application.workflow.factory.get_global_factory')
    def test_create_plan_execute_workflow(self, mock_get_factory):
        """测试创建Plan-Execute工作流的便捷函数"""
        mock_factory = Mock()
        mock_get_factory.return_value = mock_factory
        
        mock_workflow = Mock()
        mock_factory.create_plan_execute.return_value = mock_workflow
        
        result = create_plan_execute_workflow()
        
        assert result is mock_workflow
        mock_factory.create_plan_execute.assert_called_once_with(None)


class TestSimpleWorkflowExecution:
    """简单工作流执行测试"""
    
    def test_simple_workflow_run_without_initial_state(self):
        """测试简单工作流运行，无初始状态"""
        factory = UnifiedWorkflowFactory()
        mock_injector = Mock(spec=IPromptInjector)
        
        # 模拟注入器返回状态
        expected_state = WorkflowState()
        expected_state.current_step = "injected"
        mock_injector.inject_prompts.return_value = expected_state
        
        workflow = factory.create_simple(mock_injector)
        result = workflow["run"]()
        
        assert result is expected_state
        assert result.current_step == "injected"
        mock_injector.inject_prompts.assert_called_once()
    
    def test_simple_workflow_run_with_initial_state(self):
        """测试简单工作流运行，有初始状态"""
        factory = UnifiedWorkflowFactory()
        mock_injector = Mock(spec=IPromptInjector)
        
        # 创建初始状态
        initial_state = WorkflowState()
        initial_state.current_step = "initial"
        
        # 模拟注入器返回状态
        expected_state = WorkflowState()
        expected_state.current_step = "processed"
        mock_injector.inject_prompts.return_value = expected_state
        
        workflow = factory.create_simple(mock_injector)
        result = workflow["run"](initial_state)
        
        assert result is expected_state
        assert result.current_step == "processed"
        
        # 验证传入的是初始状态
        call_args = mock_injector.inject_prompts.call_args[0]
        assert call_args[0] is initial_state