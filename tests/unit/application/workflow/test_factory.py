"""工作流工厂测试

测试工作流工厂的功能。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import tempfile
import os

from src.application.workflow.factory import IWorkflowFactory, WorkflowFactory
from src.infrastructure.graph.config import WorkflowConfig
from src.infrastructure.graph.states import (
    WorkflowState, ReActState, PlanExecuteState
)
from src.infrastructure.container import IDependencyContainer
from src.infrastructure.graph.builder import GraphBuilder
from src.infrastructure.graph.registry import NodeRegistry


class TestIWorkflowFactoryInterface(unittest.TestCase):
    """测试工作流工厂接口"""

    def test_interface_methods(self):
        """测试接口方法存在"""
        # 检查接口方法
        self.assertTrue(hasattr(IWorkflowFactory, 'create_workflow'))
        self.assertTrue(hasattr(IWorkflowFactory, 'create_state'))
        self.assertTrue(hasattr(IWorkflowFactory, 'create_workflow_state'))
        self.assertTrue(hasattr(IWorkflowFactory, 'create_workflow_from_config'))
        self.assertTrue(hasattr(IWorkflowFactory, 'clone_workflow'))
        self.assertTrue(hasattr(IWorkflowFactory, 'graph_builder'))


class TestWorkflowFactory(unittest.TestCase):
    """测试工作流工厂实现"""

    def setUp(self):
        """设置测试环境"""
        self.mock_container = Mock(spec=IDependencyContainer)
        self.mock_node_registry = Mock(spec=NodeRegistry)
        self.factory = WorkflowFactory(
            container=self.mock_container,
            node_registry=self.mock_node_registry
        )
        
        # 创建测试配置
        self.test_config_dict = {
            "name": "test_workflow",
            "description": "测试工作流",
            "version": "1.0.0",
            "entry_point": "start",
            "nodes": {
                "start": {
                    "function": "test_function",
                    "type": "llm",
                    "config": {"model": "gpt-3.5-turbo"}
                }
            },
            "edges": []
        }
        self.test_config = WorkflowConfig.from_dict(self.test_config_dict)

    def test_init(self):
        """测试初始化"""
        factory = WorkflowFactory(
            container=self.mock_container,
            node_registry=self.mock_node_registry
        )
        self.assertEqual(factory.container, self.mock_container)
        self.assertEqual(factory.node_registry, self.mock_node_registry)

    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        factory = WorkflowFactory()
        self.assertIsNone(factory.container)
        self.assertIsNone(factory.node_registry)

    def test_graph_builder_property(self):
        """测试图构建器属性"""
        # 第一次访问应该创建构建器
        builder1 = self.factory.graph_builder
        self.assertIsInstance(builder1, GraphBuilder)
        
        # 后续访问应该返回同一个实例
        builder2 = self.factory.graph_builder
        self.assertEqual(builder1, builder2)

    def test_create_workflow(self):
        """测试创建工作流"""
        mock_workflow = Mock()
        
        # 直接mock GraphBuilder类而不是属性
        with patch('src.application.workflow.factory.GraphBuilder') as mock_builder_class:
            mock_builder_instance = Mock()
            mock_builder_instance.build_graph.return_value = mock_workflow
            mock_builder_class.return_value = mock_builder_instance
            
            # 重新创建工厂以使用mocked的GraphBuilder
            factory = WorkflowFactory(
                container=self.mock_container,
                node_registry=self.mock_node_registry
            )
            
            workflow = factory.create_workflow(self.test_config)
            self.assertEqual(workflow, mock_workflow)
            mock_builder_instance.build_graph.assert_called_once_with(self.test_config)

    def test_create_workflow_with_initial_state(self):
        """测试带初始状态创建工作流"""
        mock_workflow = Mock()
        
        # 直接mock GraphBuilder类而不是属性
        with patch('src.application.workflow.factory.GraphBuilder') as mock_builder_class:
            mock_builder_instance = Mock()
            mock_builder_instance.build_graph.return_value = mock_workflow
            mock_builder_class.return_value = mock_builder_instance
            
            # 重新创建工厂以使用mocked的GraphBuilder
            factory = WorkflowFactory(
                container=self.mock_container,
                node_registry=self.mock_node_registry
            )
            
            initial_state = {"test": "value"}
            workflow = factory.create_workflow(self.test_config, initial_state)
            self.assertEqual(workflow, mock_workflow)
            mock_builder_instance.build_graph.assert_called_once_with(self.test_config)

    def test_create_state(self):
        """测试创建状态"""
        from src.infrastructure.graph.states import StateFactory
        with patch.object(StateFactory, 'create_state_by_type') as mock_create:
            mock_state = {"test": "state"}
            mock_create.return_value = mock_state
            
            state = self.factory.create_state("test_type", param1="value1")
            self.assertEqual(state, dict(mock_state))
            mock_create.assert_called_once_with("test_type", param1="value1")

    def test_create_workflow_state(self):
        """测试创建工作流状态"""
        from src.infrastructure.graph.states import StateFactory
        with patch.object(StateFactory, 'create_workflow_state') as mock_create:
            mock_state = Mock(spec=WorkflowState)
            mock_create.return_value = mock_state
            
            state = self.factory.create_workflow_state(
                workflow_id="test_id",
                workflow_name="test_name",
                input_text="test input"
            )
            self.assertEqual(state, mock_state)
            mock_create.assert_called_once_with(
                workflow_id="test_id",
                workflow_name="test_name",
                input_text="test input",
                workflow_config=None,
                max_iterations=10
            )

    def test_create_react_state(self):
        """测试创建ReAct状态"""
        from src.infrastructure.graph.states import StateFactory
        with patch.object(StateFactory, 'create_react_state') as mock_create:
            mock_state = Mock(spec=ReActState)
            mock_create.return_value = mock_state
            
            state = self.factory.create_react_state(
                workflow_id="test_id",
                workflow_name="test_name",
                input_text="test input"
            )
            self.assertEqual(state, mock_state)
            mock_create.assert_called_once_with(
                workflow_id="test_id",
                workflow_name="test_name",
                input_text="test input",
                max_iterations=10,
                max_steps=10
            )

    def test_create_plan_execute_state(self):
        """测试创建计划执行状态"""
        from src.infrastructure.graph.states import StateFactory
        with patch.object(StateFactory, 'create_plan_execute_state') as mock_create:
            mock_state = Mock(spec=PlanExecuteState)
            mock_create.return_value = mock_state
            
            state = self.factory.create_plan_execute_state(
                workflow_id="test_id",
                workflow_name="test_name",
                input_text="test input"
            )
            self.assertEqual(state, mock_state)
            mock_create.assert_called_once_with(
                workflow_id="test_id",
                workflow_name="test_name",
                input_text="test input",
                max_iterations=10,
                max_steps=10
            )

    def test_create_workflow_from_config(self):
        """测试从配置文件创建工作流"""
        mock_workflow = Mock()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(self.test_config_dict, f)
            config_path = f.name
        
        try:
            # 直接mock GraphBuilder类而不是属性
            with patch('src.application.workflow.factory.GraphBuilder') as mock_builder_class:
                mock_builder_instance = Mock()
                mock_builder_instance.build_graph.return_value = mock_workflow
                mock_builder_instance.load_workflow_config.return_value = self.test_config
                mock_builder_class.return_value = mock_builder_instance
                
                # 重新创建工厂以使用mocked的GraphBuilder
                factory = WorkflowFactory(
                    container=self.mock_container,
                    node_registry=self.mock_node_registry
                )
                
                workflow = factory.create_workflow_from_config(config_path)
                self.assertEqual(workflow, mock_workflow)
                mock_builder_instance.load_workflow_config.assert_called_once_with(config_path)
                mock_builder_instance.build_graph.assert_called_once_with(self.test_config)
        finally:
            os.unlink(config_path)

    def test_validate_workflow_config(self):
        """测试验证工作流配置"""
        # 直接mock GraphBuilder类而不是属性
        with patch('src.application.workflow.factory.GraphBuilder') as mock_builder_class:
            mock_builder_instance = Mock()
            mock_builder_instance.validate_config.return_value = []
            mock_builder_class.return_value = mock_builder_instance
            
            # 重新创建工厂以使用mocked的GraphBuilder
            factory = WorkflowFactory(
                container=self.mock_container,
                node_registry=self.mock_node_registry
            )
            
            errors = factory.validate_workflow_config(self.test_config)
            self.assertEqual(errors, [])
            mock_builder_instance.validate_config.assert_called_once_with(self.test_config)

    def test_get_supported_state_types(self):
        """测试获取支持的状态类型"""
        supported_types = self.factory.get_supported_state_types()
        expected_types = ["base", "agent", "workflow", "react", "plan_execute"]
        self.assertEqual(supported_types, expected_types)

    def test_clone_workflow(self):
        """测试克隆工作流"""
        mock_workflow = Mock()
        cloned_workflow = self.factory.clone_workflow(mock_workflow)
        self.assertEqual(cloned_workflow, mock_workflow)

    def test_get_workflow_info(self):
        """测试获取工作流信息"""
        mock_workflow = Mock()
        mock_workflow.get_graph.return_value = Mock(nodes=[], edges=[])
        
        info = self.factory.get_workflow_info(mock_workflow)
        self.assertIn("type", info)
        self.assertIn("module", info)


if __name__ == '__main__':
    unittest.main()