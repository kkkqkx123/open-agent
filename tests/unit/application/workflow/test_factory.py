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
from src.infrastructure.container import IDependencyContainer


class TestIWorkflowFactoryInterface(unittest.TestCase):
    """测试工作流工厂接口"""

    def test_interface_methods(self):
        """测试接口方法存在"""
        # 检查接口方法
        self.assertTrue(hasattr(IWorkflowFactory, 'create_workflow'))
        self.assertTrue(hasattr(IWorkflowFactory, 'register_workflow_type'))
        self.assertTrue(hasattr(IWorkflowFactory, 'get_supported_types'))
        self.assertTrue(hasattr(IWorkflowFactory, 'load_workflow_config'))


class TestWorkflowFactory(unittest.TestCase):
    """测试工作流工厂实现"""

    def setUp(self):
        """设置测试环境"""
        self.mock_container = Mock(spec=IDependencyContainer)
        self.mock_config_loader = Mock()
        self.factory = WorkflowFactory(
            container=self.mock_container,
            config_loader=self.mock_config_loader
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
            config_loader=self.mock_config_loader
        )
        self.assertEqual(factory.container, self.mock_container)
        self.assertEqual(factory.config_loader, self.mock_config_loader)

    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        factory = WorkflowFactory()
        self.assertIsNone(factory.container)
        self.assertIsNone(factory.config_loader)

    def test_create_workflow(self):
        """测试创建工作流"""
        # 使用基础工作流类型（默认）
        workflow = self.factory.create_workflow(self.test_config)
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.config, self.test_config)
        self.assertEqual(workflow.config_loader, self.mock_config_loader)
        self.assertEqual(workflow.container, self.mock_container)

    def test_create_workflow_with_react_type(self):
        """测试创建ReAct工作流"""
        config_dict = self.test_config_dict.copy()
        config_dict['name'] = 'react_workflow'
        config = WorkflowConfig.from_dict(config_dict)
        
        workflow = self.factory.create_workflow(config)
        self.assertIsNotNone(workflow)

    def test_create_workflow_with_plan_execute_type(self):
        """测试创建计划执行工作流"""
        config_dict = self.test_config_dict.copy()
        config_dict['name'] = 'plan_execute_workflow'
        config = WorkflowConfig.from_dict(config_dict)
        
        workflow = self.factory.create_workflow(config)
        self.assertIsNotNone(workflow)

    def test_register_workflow_type(self):
        """测试注册工作流类型"""
        from src.application.workflow.factory import BaseWorkflow
        
        factory = WorkflowFactory()
        factory.register_workflow_type('custom', BaseWorkflow)
        
        supported = factory.get_supported_types()
        self.assertIn('custom', supported)

    def test_get_supported_types(self):
        """测试获取支持的工作流类型"""
        supported_types = self.factory.get_supported_types()
        # 应该至少包含内置的三种工作流类型
        self.assertIn('base', supported_types)
        self.assertIn('react', supported_types)
        self.assertIn('plan_execute', supported_types)

    def test_load_workflow_config(self):
        """测试加载工作流配置"""
        from infrastructure.config.core.loader import IConfigLoader
        
        mock_loader = Mock(spec=IConfigLoader)
        factory = WorkflowFactory(config_loader=mock_loader)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(self.test_config_dict, f)
            config_path = f.name
        
        try:
            config = factory.load_workflow_config(config_path)
            self.assertEqual(config.name, 'test_workflow')
            self.assertEqual(config.version, '1.0.0')
        finally:
            os.unlink(config_path)

    def test_load_workflow_config_without_loader(self):
        """测试不配置加载器时加载配置会失败"""
        factory = WorkflowFactory()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(self.test_config_dict, f)
            config_path = f.name
        
        try:
            # 虽然没有设置config_loader，但load_workflow_config方法会手动加载YAML
            config = factory.load_workflow_config(config_path)
            self.assertEqual(config.name, 'test_workflow')
        finally:
            os.unlink(config_path)

    def test_load_workflow_config_file_not_found(self):
        """测试加载不存在的配置文件"""
        factory = WorkflowFactory()
        
        with self.assertRaises(FileNotFoundError):
            factory.load_workflow_config('/nonexistent/path/config.yaml')

    def test_create_workflow_unknown_type(self):
        """测试创建未知类型的工作流"""
        config_dict = self.test_config_dict.copy()
        config_dict['additional_config'] = {'workflow_type': 'unknown'}
        config = WorkflowConfig.from_dict(config_dict)
        
        with self.assertRaises(ValueError):
            self.factory.create_workflow(config)


if __name__ == '__main__':
    unittest.main()
