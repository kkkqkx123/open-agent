"""工作流可视化测试

测试工作流可视化功能。
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import os
from pathlib import Path

from src.application.workflow.visualization import (
    IWorkflowVisualizer,
    LangGraphStudioVisualizer,
    SimpleVisualizer,
    create_visualizer
)
from src.infrastructure.graph.builder import GraphBuilder


class TestVisualizationInterfaces(unittest.TestCase):
    """测试可视化接口"""

    def test_visualizer_interface(self):
        """测试可视化器接口"""
        # 确保接口方法存在
        self.assertTrue(hasattr(IWorkflowVisualizer, 'visualize_workflow'))
        self.assertTrue(hasattr(IWorkflowVisualizer, 'export_to_langgraph_studio'))
        self.assertTrue(hasattr(IWorkflowVisualizer, 'generate_mermaid_diagram'))


class TestLangGraphStudioVisualizer(unittest.TestCase):
    """测试LangGraph Studio可视化器"""

    def setUp(self):
        """设置测试环境"""
        self.mock_workflow_builder = Mock(spec=GraphBuilder)
        self.visualizer = LangGraphStudioVisualizer(self.mock_workflow_builder)

    def test_init_with_default_builder(self):
        """测试使用默认构建器初始化"""
        with patch('src.application.workflow.visualization.GraphBuilder') as mock_builder_class:
            mock_builder = Mock()
            mock_builder_class.return_value = mock_builder
            visualizer = LangGraphStudioVisualizer()
            self.assertEqual(visualizer.graph_builder, mock_builder)

    def test_visualize_workflow(self):
        """测试工作流可视化"""
        mock_workflow = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_viz.json")
            result_path = self.visualizer.visualize_workflow(mock_workflow, output_path)
            
            # 验证输出路径
            self.assertEqual(result_path, output_path)
            
            # 验证文件已创建
            self.assertTrue(os.path.exists(output_path))

    def test_export_to_langgraph_studio(self):
        """测试导出到LangGraph Studio"""
        mock_workflow = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = self.visualizer.export_to_langgraph_studio(mock_workflow, temp_dir)
            
            # 验证输出路径
            self.assertEqual(result_path, temp_dir)
            
            # 验证配置文件已创建
            config_file = os.path.join(temp_dir, "langgraph_studio_config.json")
            self.assertTrue(os.path.exists(config_file))
            
            # 验证脚本文件已创建
            script_file = os.path.join(temp_dir, "start_studio.py")
            self.assertTrue(os.path.exists(script_file))

    def test_generate_mermaid_diagram(self):
        """测试生成Mermaid图表"""
        mock_workflow = Mock()
        diagram = self.visualizer.generate_mermaid_diagram(mock_workflow)
        
        # 验证返回的是字符串
        self.assertIsInstance(diagram, str)
        
        # 验证包含基本的Mermaid语法
        self.assertIn("graph TD", diagram)


class TestSimpleVisualizer(unittest.TestCase):
    """测试简单可视化器"""

    def setUp(self):
        """设置测试环境"""
        self.visualizer = SimpleVisualizer()

    def test_visualize_workflow(self):
        """测试工作流可视化"""
        mock_workflow = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_simple_viz.txt")
            result_path = self.visualizer.visualize_workflow(mock_workflow, output_path)
            
            # 验证输出路径
            self.assertEqual(result_path, output_path)
            
            # 验证文件已创建
            self.assertTrue(os.path.exists(output_path))

    def test_export_to_langgraph_studio(self):
        """测试导出到LangGraph Studio"""
        mock_workflow = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = self.visualizer.export_to_langgraph_studio(mock_workflow, temp_dir)
            
            # 验证输出路径
            self.assertEqual(result_path, temp_dir)
            
            # 验证文件已创建
            viz_file = os.path.join(temp_dir, "workflow.txt")
            self.assertTrue(os.path.exists(viz_file))

    def test_generate_mermaid_diagram(self):
        """测试生成Mermaid图表"""
        mock_workflow = Mock()
        diagram = self.visualizer.generate_mermaid_diagram(mock_workflow)
        
        # 验证返回的是字符串
        self.assertIsInstance(diagram, str)
        
        # 验证包含基本的Mermaid语法
        self.assertIn("graph TD", diagram)


class TestCreateVisualizer(unittest.TestCase):
    """测试创建可视化器函数"""

    def test_create_simple_visualizer(self):
        """测试创建简单可视化器"""
        visualizer = create_visualizer("simple")
        self.assertIsInstance(visualizer, SimpleVisualizer)

    def test_create_langgraph_studio_visualizer(self):
        """测试创建LangGraph Studio可视化器"""
        visualizer = create_visualizer("langgraph_studio")
        self.assertIsInstance(visualizer, LangGraphStudioVisualizer)

    def test_create_unknown_visualizer(self):
        """测试创建未知类型的可视化器"""
        with self.assertRaises(ValueError):
            create_visualizer("unknown_type")

    def test_create_visualizer_with_kwargs(self):
        """测试创建可视化器并传递参数"""
        mock_builder = Mock()
        visualizer = create_visualizer("langgraph_studio", graph_builder=mock_builder)
        self.assertIsInstance(visualizer, LangGraphStudioVisualizer)


if __name__ == '__main__':
    unittest.main()