"""工作流工厂测试

测试工作流工厂的功能。
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, Optional, List

from src.application.workflow.factory import WorkflowFactory, IWorkflowFactory
from src.infrastructure.graph.config import WorkflowConfig
from src.infrastructure.graph.states import (
    BaseGraphState, AgentState, WorkflowState, 
    ReActState, PlanExecuteState, StateFactory
)
from src.infrastructure.graph.registry import NodeRegistry
from src.infrastructure.container import IDependencyContainer


class TestIWorkflowFactory(unittest.TestCase):
    """测试工作流工厂接口"""
    
    def test_interface_is_abstract(self):
        """测试接口是抽象的"""
        from abc import ABC
        self.assertTrue(issubclass(IWorkflowFactory, ABC))
        
        # 尝试实例化应该失败
        with self.assertRaises(TypeError):
            IWorkflowFactory()  # type: ignore
    
    def test_interface_methods_exist(self):
        """测试接口方法存在"""
        methods = ['create_workflow', 'create_state']
        
        for method in methods:
            self.assertTrue(hasattr(IWorkflowFactory, method))
    
    def test_concrete_implementation(self):
        """测试具体实现必须实现所有方法"""
        class ConcreteWorkflowFactory(IWorkflowFactory):
            def create_workflow(self, config: WorkflowConfig, initial_state: Optional[Dict[str, Any]] = None) -> Any:
                return Mock()
            
            def create_state(self, state_type: str, **kwargs) -> Dict[str, Any]:
                return {}
        
        # 应该能够实例化
        factory = ConcreteWorkflowFactory()
        self.assertIsInstance(factory, IWorkflowFactory)


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
        
        # 创建模拟的工作流配置
        self.mock_workflow_config = Mock(spec=WorkflowConfig)
        self.mock_workflow_config.name = "test_workflow"
        self.mock_workflow_config.description = "Test workflow"
        self.mock_workflow_config.version = "1.0.0"
        
        # 创建模拟的工作流实例
        self.mock_workflow = Mock()
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.factory.container, self.mock_container)
        self.assertEqual(self.factory.node_registry, self.mock_node_registry)
        self.assertIsNone(self.factory._builder_adapter)
    
    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        factory = WorkflowFactory()
        self.assertIsNone(factory.container)
        self.assertIsNone(factory.node_registry)
        self.assertIsNone(factory._builder_adapter)
    
    def test_builder_adapter_property(self):
        """测试构建器适配器属性（延迟初始化）"""
        # 第一次访问应该创建适配器
        with patch('src.application.workflow.factory.WorkflowBuilderAdapter') as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter
            
            adapter = self.factory.builder_adapter
            
            # 验证适配器创建
            mock_adapter_class.assert_called_once_with(node_registry=self.mock_node_registry)
            self.assertEqual(adapter, mock_adapter)
            
            # 第二次访问应该返回同一个实例
            adapter2 = self.factory.builder_adapter
            self.assertEqual(adapter, adapter2)
            mock_adapter_class.assert_called_once()  # 仍然只调用一次
    
    @patch('src.application.workflow.factory.WorkflowBuilderAdapter')
    def test_create_workflow(self, mock_adapter_class):
        """测试创建工作流"""
        # 设置模拟
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter
        mock_adapter.build_graph.return_value = self.mock_workflow
        
        # 创建工作流
        result = self.factory.create_workflow(self.mock_workflow_config)
        
        # 验证结果
        self.assertEqual(result, self.mock_workflow)
        
        # 验证调用
        mock_adapter.build_graph.assert_called_once_with(self.mock_workflow_config)
    
    @patch('src.application.workflow.factory.WorkflowBuilderAdapter')
    def test_create_workflow_with_initial_state(self, mock_adapter_class):
        """测试使用初始状态创建工作流"""
        # 设置模拟
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter
        mock_adapter.build_graph.return_value = self.mock_workflow
        
        # 创建初始状态
        initial_state = {"test": "value"}
        
        # 创建工作流
        result = self.factory.create_workflow(self.mock_workflow_config, initial_state)
        
        # 验证结果
        self.assertEqual(result, self.mock_workflow)
        
        # 验证调用
        mock_adapter.build_graph.assert_called_once_with(self.mock_workflow_config)
    
    @patch('src.application.workflow.factory.StateFactory')
    def test_create_state(self, mock_state_factory):
        """测试创建状态"""
        # 设置模拟
        mock_state = {"test": "state"}
        mock_state_factory.create_state_by_type.return_value = mock_state
        
        # 创建状态
        result = self.factory.create_state("workflow", test_param="value")
        
        # 验证结果
        self.assertEqual(result, mock_state)
        
        # 验证调用
        mock_state_factory.create_state_by_type.assert_called_once_with("workflow", test_param="value")
    
    @patch('src.application.workflow.factory.StateFactory')
    def test_create_workflow_state(self, mock_state_factory):
        """测试创建工作流状态"""
        # 设置模拟
        mock_state = Mock(spec=WorkflowState)
        mock_state_factory.create_workflow_state.return_value = mock_state
        
        # 创建工作流状态
        result = self.factory.create_workflow_state(
            workflow_id="test_id",
            workflow_name="test_workflow",
            input_text="test input",
            workflow_config={"test": "config"},
            max_iterations=20
        )
        
        # 验证结果
        self.assertEqual(result, mock_state)
        
        # 验证调用
        mock_state_factory.create_workflow_state.assert_called_once_with(
            workflow_id="test_id",
            workflow_name="test_workflow",
            input_text="test input",
            workflow_config={"test": "config"},
            max_iterations=20
        )
    
    @patch('src.application.workflow.factory.StateFactory')
    def test_create_agent_state(self, mock_state_factory):
        """测试创建Agent状态"""
        # 设置模拟
        mock_state = Mock(spec=AgentState)
        mock_state_factory.create_agent_state.return_value = mock_state
        
        # 创建Agent状态
        result = self.factory.create_agent_state(
            input_text="test input",
            agent_id="test_agent",
            agent_config={"test": "config"},
            max_iterations=15
        )
        
        # 验证结果
        self.assertEqual(result, mock_state)
        
        # 验证调用
        mock_state_factory.create_agent_state.assert_called_once_with(
            input_text="test input",
            agent_id="test_agent",
            agent_config={"test": "config"},
            max_iterations=15
        )
    
    @patch('src.application.workflow.factory.StateFactory')
    def test_create_react_state(self, mock_state_factory):
        """测试创建ReAct状态"""
        # 设置模拟
        mock_state = Mock(spec=ReActState)
        mock_state_factory.create_react_state.return_value = mock_state
        
        # 创建ReAct状态
        result = self.factory.create_react_state(
            workflow_id="test_id",
            workflow_name="test_workflow",
            input_text="test input",
            max_iterations=12,
            max_steps=8
        )
        
        # 验证结果
        self.assertEqual(result, mock_state)
        
        # 验证调用
        mock_state_factory.create_react_state.assert_called_once_with(
            workflow_id="test_id",
            workflow_name="test_workflow",
            input_text="test input",
            max_iterations=12,
            max_steps=8
        )
    
    @patch('src.application.workflow.factory.StateFactory')
    def test_create_plan_execute_state(self, mock_state_factory):
        """测试创建计划执行状态"""
        # 设置模拟
        mock_state = Mock(spec=PlanExecuteState)
        mock_state_factory.create_plan_execute_state.return_value = mock_state
        
        # 创建计划执行状态
        result = self.factory.create_plan_execute_state(
            workflow_id="test_id",
            workflow_name="test_workflow",
            input_text="test input",
            max_iterations=25,
            max_steps=15
        )
        
        # 验证结果
        self.assertEqual(result, mock_state)
        
        # 验证调用
        mock_state_factory.create_plan_execute_state.assert_called_once_with(
            workflow_id="test_id",
            workflow_name="test_workflow",
            input_text="test input",
            max_iterations=25,
            max_steps=15
        )
    
    @patch('src.application.workflow.factory.WorkflowBuilderAdapter')
    def test_create_workflow_from_config(self, mock_adapter_class):
        """测试从配置文件创建工作流"""
        # 设置模拟
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter
        mock_adapter.load_workflow_config.return_value = self.mock_workflow_config
        mock_adapter.build_graph.return_value = self.mock_workflow
        
        # 创建初始状态
        initial_state = {"test": "value"}
        
        # 从配置创建工作流
        result = self.factory.create_workflow_from_config(
            "test_config.yaml",
            initial_state
        )
        
        # 验证结果
        self.assertEqual(result, self.mock_workflow)
        
        # 验证调用
        mock_adapter.load_workflow_config.assert_called_once_with("test_config.yaml")
        mock_adapter.build_graph.assert_called_once_with(self.mock_workflow_config)
    
    @patch('src.application.workflow.factory.WorkflowBuilderAdapter')
    def test_validate_workflow_config(self, mock_adapter_class):
        """测试验证工作流配置"""
        # 设置模拟
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter
        mock_adapter.validate_config.return_value = ["error1", "error2"]
        
        # 验证配置
        result = self.factory.validate_workflow_config(self.mock_workflow_config)
        
        # 验证结果
        self.assertEqual(result, ["error1", "error2"])
        
        # 验证调用
        mock_adapter.validate_config.assert_called_once_with(self.mock_workflow_config)
    
    def test_initialize_workflow_with_state(self):
        """测试使用初始状态初始化工作流"""
        # 测试基本实现（目前直接返回工作流）
        result = self.factory._initialize_workflow_with_state(
            self.mock_workflow,
            {"test": "state"},
            self.mock_workflow_config
        )
        
        # 验证结果
        self.assertEqual(result, self.mock_workflow)
    
    def test_get_supported_state_types(self):
        """测试获取支持的状态类型"""
        result = self.factory.get_supported_state_types()
        
        # 验证结果
        expected_types = ["base", "agent", "workflow", "react", "plan_execute"]
        self.assertEqual(result, expected_types)
    
    def test_clone_workflow(self):
        """测试克隆工作流"""
        # 测试基本实现（目前直接返回原工作流）
        result = self.factory.clone_workflow(self.mock_workflow)
        
        # 验证结果
        self.assertEqual(result, self.mock_workflow)
    
    def test_get_workflow_info(self):
        """测试获取工作流信息"""
        # 创建模拟工作流
        mock_workflow = Mock()
        mock_workflow.__class__.__name__ = "TestWorkflow"
        mock_workflow.__class__.__module__ = "test.module"
        
        # 获取工作流信息
        result = self.factory.get_workflow_info(mock_workflow)
        
        # 验证结果
        expected_info = {
            "type": "TestWorkflow",
            "module": "test.module"
        }
        self.assertEqual(result, expected_info)
    
    def test_get_workflow_info_with_graph(self):
        """测试获取工作流信息（包含图信息）"""
        # 创建模拟工作流和图
        mock_graph = Mock()
        mock_graph.nodes = ["node1", "node2"]
        mock_graph.edges = ["edge1", "edge2"]
        
        mock_workflow = Mock()
        mock_workflow.__class__.__name__ = "TestWorkflow"
        mock_workflow.__class__.__module__ = "test.module"
        mock_workflow.get_graph.return_value = mock_graph
        
        # 获取工作流信息
        result = self.factory.get_workflow_info(mock_workflow)
        
        # 验证结果
        expected_info = {
            "type": "TestWorkflow",
            "module": "test.module",
            "node_count": "2",
            "edge_count": "2"
        }
        self.assertEqual(result, expected_info)
    
    def test_get_workflow_info_with_graph_error(self):
        """测试获取工作流信息（图访问出错）"""
        # 创建模拟工作流
        mock_workflow = Mock()
        mock_workflow.__class__.__name__ = "TestWorkflow"
        mock_workflow.__class__.__module__ = "test.module"
        mock_workflow.get_graph.side_effect = Exception("Graph access error")
        
        # 获取工作流信息
        result = self.factory.get_workflow_info(mock_workflow)
        
        # 验证结果（应该忽略错误）
        expected_info = {
            "type": "TestWorkflow",
            "module": "test.module"
        }
        self.assertEqual(result, expected_info)


if __name__ == '__main__':
    unittest.main()