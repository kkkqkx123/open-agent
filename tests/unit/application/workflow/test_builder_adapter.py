"""工作流构建器适配器测试

测试工作流构建器适配器的功能。
"""

import unittest
from unittest.mock import Mock, MagicMock, patch

from src.application.workflow.builder_adapter import WorkflowBuilderAdapter, WorkflowBuilder
from src.infrastructure.graph.config import WorkflowConfig
from src.infrastructure.graph.registry import NodeRegistry


class TestWorkflowBuilderAdapter(unittest.TestCase):
    """测试工作流构建器适配器"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_node_registry = Mock(spec=NodeRegistry)
        self.mock_template_registry = Mock()
        
        self.adapter = WorkflowBuilderAdapter(
            node_registry=self.mock_node_registry,
            template_registry=self.mock_template_registry
        )
        
        # 创建模拟的工作流配置
        self.mock_workflow_config = Mock(spec=WorkflowConfig)
        self.mock_workflow_config.name = "test_workflow"
        
        # 创建模拟的工作流实例
        self.mock_workflow = Mock()
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.adapter._node_registry, self.mock_node_registry)
        self.assertEqual(self.adapter._template_registry, self.mock_template_registry)
        self.assertIsNone(self.adapter._builder)
    
    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        adapter = WorkflowBuilderAdapter()
        self.assertIsNone(adapter._node_registry)
        self.assertIsNone(adapter._template_registry)
        self.assertIsNone(adapter._builder)
    
    def test_get_builder_lazy_initialization(self):
        """测试构建器的延迟初始化"""
        # 使用 patch.object 来 mock 内部导入
        with patch.object(self.adapter, '_get_builder') as mock_get_builder:
            mock_builder = Mock()
            mock_get_builder.return_value = mock_builder
            
            # 获取构建器
            builder = self.adapter._get_builder()
            
            # 验证结果
            self.assertEqual(builder, mock_builder)
            mock_get_builder.assert_called_once()
    
    def test_get_builder_with_default_registry(self):
        """测试使用默认注册表获取构建器"""
        # 创建没有指定注册表的适配器
        adapter = WorkflowBuilderAdapter()
        
        # 使用 patch.object 来 mock 内部导入
        with patch.object(adapter, '_get_builder') as mock_get_builder:
            mock_builder = Mock()
            mock_get_builder.return_value = mock_builder
            
            # 获取构建器
            builder = adapter._get_builder()
            
            # 验证结果
            self.assertEqual(builder, mock_builder)
            mock_get_builder.assert_called_once()
    
    def test_build_workflow(self):
        """测试构建工作流（向后兼容方法）"""
        # 使用 patch.object 来 mock _get_builder 方法
        with patch.object(self.adapter, '_get_builder') as mock_get_builder:
            mock_builder = Mock()
            mock_builder.build_graph.return_value = self.mock_workflow
            mock_get_builder.return_value = mock_builder
            
            # 构建工作流
            result = self.adapter.build_workflow(self.mock_workflow_config)
            
            # 验证结果
            self.assertEqual(result, self.mock_workflow)
            
            # 验证调用
            mock_builder.build_graph.assert_called_once_with(self.mock_workflow_config)
    
    def test_build_graph(self):
        """测试构建图"""
        # 使用 patch.object 来 mock _get_builder 方法
        with patch.object(self.adapter, '_get_builder') as mock_get_builder:
            mock_builder = Mock()
            mock_builder.build_graph.return_value = self.mock_workflow
            mock_get_builder.return_value = mock_builder
            
            # 构建图
            result = self.adapter.build_graph(self.mock_workflow_config)
            
            # 验证结果
            self.assertEqual(result, self.mock_workflow)
            
            # 验证调用
            mock_builder.build_graph.assert_called_once_with(self.mock_workflow_config)
    
    def test_load_workflow_config(self):
        """测试加载工作流配置"""
        # 使用 patch.object 来 mock _get_builder 方法
        with patch.object(self.adapter, '_get_builder') as mock_get_builder:
            mock_builder = Mock()
            mock_builder.load_workflow_config.return_value = self.mock_workflow_config
            mock_get_builder.return_value = mock_builder
            
            # 加载配置
            result = self.adapter.load_workflow_config("test_config.yaml")
            
            # 验证结果
            self.assertEqual(result, self.mock_workflow_config)
            
            # 验证调用
            mock_builder.load_workflow_config.assert_called_once_with("test_config.yaml")
    
    def test_validate_config(self):
        """测试验证配置"""
        # 使用 patch.object 来 mock _get_builder 方法
        with patch.object(self.adapter, '_get_builder') as mock_get_builder:
            mock_builder = Mock()
            mock_builder.validate_config.return_value = ["error1", "error2"]
            mock_get_builder.return_value = mock_builder
            
            # 验证配置
            result = self.adapter.validate_config(self.mock_workflow_config)
            
            # 验证结果
            self.assertEqual(result, ["error1", "error2"])
            
            # 验证调用
            mock_builder.validate_config.assert_called_once_with(self.mock_workflow_config)
    
    def test_build_from_yaml(self):
        """测试从YAML构建图"""
        # 使用 patch.object 来 mock _get_builder 方法
        with patch.object(self.adapter, '_get_builder') as mock_get_builder:
            mock_builder = Mock()
            mock_builder.build_from_yaml.return_value = self.mock_workflow
            mock_get_builder.return_value = mock_builder
            
            # 从YAML构建图
            result = self.adapter.build_from_yaml("test_config.yaml")
            
            # 验证结果
            self.assertEqual(result, self.mock_workflow)
            
            # 验证调用
            mock_builder.build_from_yaml.assert_called_once_with("test_config.yaml")
    
    def test_workflow_builder_alias(self):
        """测试WorkflowBuilder别名"""
        # 验证别名存在
        self.assertEqual(WorkflowBuilder, WorkflowBuilderAdapter)
        
        # 验证可以实例化
        builder = WorkflowBuilder()
        self.assertIsInstance(builder, WorkflowBuilderAdapter)
    
    def test_get_builder_internal_imports(self):
        """测试构建器内部导入逻辑"""
        # 测试实际的内部导入逻辑
        adapter = WorkflowBuilderAdapter()
        
        # Mock 内部导入的模块
        with patch('src.infrastructure.graph.builder.GraphBuilder') as mock_graph_builder_class, \
             patch('src.infrastructure.graph.registry.get_global_registry') as mock_get_global_registry:
            
            mock_global_registry = Mock(spec=NodeRegistry)
            mock_get_global_registry.return_value = mock_global_registry
            
            mock_builder = Mock()
            mock_graph_builder_class.return_value = mock_builder
            
            # 获取构建器
            builder = adapter._get_builder()
            
            # 验证构建器创建
            mock_graph_builder_class.assert_called_once_with(
                node_registry=mock_global_registry,
                template_registry=None
            )
            self.assertEqual(builder, mock_builder)
            
            # 第二次获取应该返回同一个实例
            builder2 = adapter._get_builder()
            self.assertEqual(builder, builder2)
            self.assertEqual(mock_graph_builder_class.call_count, 1)  # 仍然只调用一次


class TestWorkflowBuilderAdapterIntegration(unittest.TestCase):
    """测试工作流构建器适配器集成"""
    
    def setUp(self):
        """设置测试环境"""
        self.adapter = WorkflowBuilderAdapter()
    
    def test_multiple_method_calls_share_builder(self):
        """测试多个方法调用共享同一个构建器实例"""
        # 使用 patch.object 来 mock _get_builder 方法
        with patch.object(self.adapter, '_get_builder') as mock_get_builder:
            mock_builder = Mock()
            mock_builder.build_graph.return_value = Mock()
            mock_builder.load_workflow_config.return_value = Mock(spec=WorkflowConfig)
            mock_builder.validate_config.return_value = []
            mock_get_builder.return_value = mock_builder
            
            # 调用多个方法
            self.adapter.build_graph(Mock(spec=WorkflowConfig))
            self.adapter.load_workflow_config("test.yaml")
            self.adapter.validate_config(Mock(spec=WorkflowConfig))
            
            # 验证构建器只创建一次
            self.assertEqual(mock_get_builder.call_count, 3)  # 每次方法调用都会调用_get_builder
            
            # 验证所有方法都调用了构建器
            self.assertEqual(mock_builder.build_graph.call_count, 1)
            self.assertEqual(mock_builder.load_workflow_config.call_count, 1)
            self.assertEqual(mock_builder.validate_config.call_count, 1)
    
    def test_builder_initialization_error_handling(self):
        """测试构建器初始化错误处理"""
        # 使用 patch.object 来 mock _get_builder 方法，使其抛出异常
        with patch.object(self.adapter, '_get_builder') as mock_get_builder:
            mock_get_builder.side_effect = Exception("Builder initialization error")
            
            # 验证异常传播
            with self.assertRaises(Exception) as context:
                self.adapter.build_graph(Mock(spec=WorkflowConfig))
            
            self.assertIn("Builder initialization error", str(context.exception))
    
    def test_method_delegation(self):
        """测试方法委托"""
        # 使用 patch.object 来 mock _get_builder 方法
        with patch.object(self.adapter, '_get_builder') as mock_get_builder:
            mock_builder = Mock()
            mock_builder.build_graph.return_value = "workflow_result"
            mock_builder.load_workflow_config.return_value = "config_result"
            mock_builder.validate_config.return_value = "validation_result"
            mock_builder.build_from_yaml.return_value = "yaml_result"
            mock_get_builder.return_value = mock_builder
            
            # 测试所有方法都正确委托
            self.assertEqual(self.adapter.build_graph("config"), "workflow_result")
            self.assertEqual(self.adapter.load_workflow_config("path"), "config_result")
            self.assertEqual(self.adapter.validate_config("config"), "validation_result")
            self.assertEqual(self.adapter.build_from_yaml("path"), "yaml_result")
            
            # 验证所有方法都调用了构建器
            mock_builder.build_graph.assert_called_once_with("config")
            mock_builder.load_workflow_config.assert_called_once_with("path")
            mock_builder.validate_config.assert_called_once_with("config")
            mock_builder.build_from_yaml.assert_called_once_with("path")


if __name__ == '__main__':
    unittest.main()