"""工作流可视化模块测试

测试工作流可视化和LangGraph Studio集成功能。
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
import json
from pathlib import Path
from typing import Dict, Any, Optional

from src.application.workflow.visualization import (
    IWorkflowVisualizer, LangGraphStudioVisualizer, SimpleVisualizer,
    create_visualizer
)
from src.application.workflow.builder_adapter import WorkflowBuilderAdapter


class TestIWorkflowVisualizer(unittest.TestCase):
    """测试工作流可视化器接口"""
    
    def test_interface_is_abstract(self):
        """测试接口是抽象的"""
        from abc import ABC
        self.assertTrue(issubclass(IWorkflowVisualizer, ABC))
        
        # 尝试实例化应该失败，因为这是一个抽象类
        with self.assertRaises(TypeError):
            IWorkflowVisualizer() # type: ignore
    
    def test_interface_methods_exist(self):
        """测试接口方法存在"""
        methods = [
            'visualize_workflow', 'export_to_langgraph_studio', 'generate_mermaid_diagram'
        ]
        
        for method in methods:
            self.assertTrue(hasattr(IWorkflowVisualizer, method))
    
    def test_concrete_implementation(self):
        """测试具体实现必须实现所有方法"""
        class ConcreteWorkflowVisualizer(IWorkflowVisualizer):
            def visualize_workflow(self, workflow: Any, output_path: Optional[str] = None) -> str:
                return "output_path"
            
            def export_to_langgraph_studio(self, workflow: Any, output_dir: str) -> str:
                return "output_dir"
            
            def generate_mermaid_diagram(self, workflow: Any) -> str:
                return "mermaid_diagram"
        
        # 应该能够实例化
        visualizer = ConcreteWorkflowVisualizer()
        self.assertIsInstance(visualizer, IWorkflowVisualizer)


class TestLangGraphStudioVisualizer(unittest.TestCase):
    """测试LangGraph Studio可视化器"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_workflow_builder = Mock(spec=WorkflowBuilderAdapter)
        self.visualizer = LangGraphStudioVisualizer(self.mock_workflow_builder)
        
        # 创建模拟的工作流
        self.mock_workflow = Mock()
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.visualizer.workflow_builder, self.mock_workflow_builder)
    
    def test_init_with_default_builder(self):
        """测试使用默认构建器初始化"""
        with patch('src.application.workflow.visualization.WorkflowBuilderAdapter') as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter
            
            visualizer = LangGraphStudioVisualizer()
            
            self.assertEqual(visualizer.workflow_builder, mock_adapter)
            mock_adapter_class.assert_called_once()
    
    @patch('src.application.workflow.visualization.time')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.application.workflow.visualization.json')
    def test_visualize_workflow(self, mock_json, mock_open_file, mock_time):
        """测试可视化工作流"""
        # 设置时间模拟
        mock_time.time.return_value = 1640995200  # 2022-01-01 00:00:00
        
        # 设置JSON模拟
        mock_json.dump = Mock()
        
        # 可视化工作流
        result = self.visualizer.visualize_workflow(self.mock_workflow)
        
        # 验证结果
        self.assertEqual(result, "workflow_visualization_1640995200.json")
        
        # 验证文件操作
        mock_open_file.assert_called_once_with("workflow_visualization_1640995200.json", 'w', encoding='utf-8')
        mock_json.dump.assert_called_once()
        
        # 验证可视化数据生成
        args, kwargs = mock_json.dump.call_args
        viz_data = args[0]
        self.assertIn("workflow_type", viz_data)
        self.assertIn("nodes", viz_data)
        self.assertIn("edges", viz_data)
        self.assertIn("metadata", viz_data)
    
    @patch('src.application.workflow.visualization.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.application.workflow.visualization.json')
    def test_export_to_langgraph_studio(self, mock_json, mock_open_file, mock_path_class):
        """测试导出到LangGraph Studio"""
        # 设置路径模拟
        mock_output_path = Mock(spec=Path)
        mock_path_class.return_value = mock_output_path
        mock_output_path.__str__ = Mock(return_value="/output/dir")  # 使str()返回正确的路径

        # 使模拟路径对象支持 / 操作符
        mock_config_file = Mock()
        mock_script_file = Mock()
        # 使用return_value而不是side_effect，因为我们需要多次调用
        mock_output_path.__truediv__ = Mock()
        mock_output_path.__truediv__.side_effect = lambda x: mock_config_file if x == "langgraph_studio_config.json" else mock_script_file

        # 设置JSON模拟
        mock_json.dump = Mock()

        # 导出到LangGraph Studio
        result = self.visualizer.export_to_langgraph_studio(self.mock_workflow, "/output/dir")

        # 验证结果
        self.assertEqual(result, "/output/dir")

        # 验证目录创建
        mock_output_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # 验证配置文件创建
        mock_config_file_call = mock_output_path.__truediv__.call_args_list[0]
        self.assertEqual(mock_config_file_call[0][0], "langgraph_studio_config.json")
        mock_open_file.assert_any_call(mock_config_file, 'w', encoding='utf-8')

        # 验证启动脚本创建
        mock_script_file_call = mock_output_path.__truediv__.call_args_list[1]
        self.assertEqual(mock_script_file_call[0][0], "start_studio.py")
        mock_open_file.assert_any_call(mock_script_file, 'w', encoding='utf-8')

        # 验证配置生成
        args, kwargs = mock_json.dump.call_args
        config = args[0]
        self.assertIn("graph", config)
        self.assertIn("ui", config)
        self.assertIn("debug", config)
    
    def test_generate_mermaid_diagram(self):
        """测试生成Mermaid图表"""
        # 生成Mermaid图表
        result = self.visualizer.generate_mermaid_diagram(self.mock_workflow)
        
        # 验证结果
        self.assertIn("graph TD", result)
        self.assertIn("A[开始]", result)
        self.assertIn("B[处理]", result)
        self.assertIn("C[结束]", result)
    
    def test_generate_visualization_data(self):
        """测试生成可视化数据"""
        # 生成可视化数据
        result = self.visualizer._generate_visualization_data(self.mock_workflow)
        
        # 验证结果结构
        self.assertIn("workflow_type", result)
        self.assertIn("nodes", result)
        self.assertIn("edges", result)
        self.assertIn("metadata", result)
        
        # 验证内容
        self.assertEqual(result["workflow_type"], "langgraph")
        self.assertEqual(len(result["nodes"]), 3)
        self.assertEqual(len(result["edges"]), 2)
        self.assertEqual(result["nodes"][0]["id"], "start")
        self.assertEqual(result["nodes"][0]["type"], "start")
        self.assertEqual(result["edges"][0]["from"], "start")
        self.assertEqual(result["edges"][0]["to"], "process")
    
    def test_generate_studio_config(self):
        """测试生成Studio配置"""
        # 生成Studio配置
        result = self.visualizer._generate_studio_config(self.mock_workflow)
        
        # 验证结果结构
        self.assertIn("graph", result)
        self.assertIn("ui", result)
        self.assertIn("debug", result)
        
        # 验证内容
        self.assertIn("nodes", result["graph"])
        self.assertIn("edges", result["graph"])
        self.assertEqual(result["ui"]["theme"], "light")
        self.assertEqual(result["ui"]["layout"], "horizontal")
        self.assertTrue(result["debug"]["enabled"])
        self.assertTrue(result["debug"]["show_state"])
    
    def test_generate_studio_script(self):
        """测试生成Studio启动脚本"""
        # 生成启动脚本
        result = self.visualizer._generate_studio_script()
        
        # 验证结果
        self.assertIn("#!/usr/bin/env python3", result)
        self.assertIn("LangGraph Studio启动脚本", result)
        self.assertIn("def main():", result)
        self.assertIn("if __name__ == \"__main__\":", result)
        self.assertIn("langgraph_studio_config.json", result)


class TestSimpleVisualizer(unittest.TestCase):
    """测试简单可视化器"""
    
    def setUp(self):
        """设置测试环境"""
        self.visualizer = SimpleVisualizer()
        
        # 创建模拟的工作流
        self.mock_workflow = Mock()
    
    @patch('src.application.workflow.visualization.time')
    @patch('builtins.open', new_callable=mock_open)
    def test_visualize_workflow(self, mock_open_file, mock_time):
        """测试可视化工作流"""
        # 设置时间模拟
        mock_time.time.return_value = 1640995200  # 2022-01-01 00:00:00
        
        # 可视化工作流
        result = self.visualizer.visualize_workflow(self.mock_workflow)
        
        # 验证结果
        self.assertEqual(result, "simple_viz_1640995200.txt")
        
        # 验证文件操作
        mock_open_file.assert_called_once_with("simple_viz_1640995200.txt", 'w', encoding='utf-8')
        
        # 验证写入内容
        handle = mock_open_file()
        written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
        self.assertIn("工作流可视化", written_content)
        self.assertIn("工作流类型:", written_content)
        self.assertIn("创建时间:", written_content)
    
    @patch('src.application.workflow.visualization.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_export_to_langgraph_studio(self, mock_open_file, mock_path_class):
        """测试导出到LangGraph Studio"""
        # 设置路径模拟
        mock_output_path = Mock(spec=Path)
        mock_path_class.return_value = mock_output_path
        mock_output_path.__str__ = Mock(return_value="/output/dir")  # 使str()返回正确的路径
        
        # 使模拟路径对象支持 / 操作符
        mock_viz_file = Mock()
        mock_output_path.__truediv__ = Mock(return_value=mock_viz_file)
        
        # 导出到LangGraph Studio
        result = self.visualizer.export_to_langgraph_studio(self.mock_workflow, "/output/dir")
        
        # 验证结果
        self.assertEqual(result, "/output/dir")
        
        # 验证目录创建
        mock_output_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        # 验证文件创建
        mock_viz_file = mock_output_path / "workflow.txt"
        mock_open_file.assert_called_once()
        
        # 验证写入内容
        handle = mock_open_file()
        written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
        self.assertIn("简单工作流导出", written_content)
    
    def test_generate_mermaid_diagram(self):
        """测试生成Mermaid图表"""
        # 生成Mermaid图表
        result = self.visualizer.generate_mermaid_diagram(self.mock_workflow)
        
        # 验证结果
        self.assertIn("graph TD", result)
        self.assertIn("A[工作流]", result)
        self.assertIn("B[处理]", result)
        self.assertIn("C[完成]", result)


class TestCreateVisualizer(unittest.TestCase):
    """测试创建可视化器函数"""
    
    def test_create_langgraph_studio_visualizer(self):
        """测试创建LangGraph Studio可视化器"""
        # 创建可视化器
        visualizer = create_visualizer("langgraph_studio")
        
        # 验证结果
        self.assertIsInstance(visualizer, LangGraphStudioVisualizer)
    
    def test_create_simple_visualizer(self):
        """测试创建简单可视化器"""
        # 创建可视化器
        visualizer = create_visualizer("simple")
        
        # 验证结果
        self.assertIsInstance(visualizer, SimpleVisualizer)
    
    def test_create_visualizer_with_kwargs(self):
        """测试使用参数创建可视化器"""
        # 创建模拟构建器
        mock_builder = Mock(spec=WorkflowBuilderAdapter)
        
        # 创建可视化器
        visualizer = create_visualizer("langgraph_studio", workflow_builder=mock_builder)
        
        # 验证结果
        self.assertIsInstance(visualizer, LangGraphStudioVisualizer)
        # 验证workflow_builder属性被正确设置
        self.assertEqual(visualizer.workflow_builder, mock_builder) # type: ignore
    
    def test_create_visualizer_invalid_type(self):
        """测试创建无效类型的可视化器"""
        # 创建可视化器
        with self.assertRaises(ValueError) as context:
            create_visualizer("invalid_type")
        
        # 验证错误
        self.assertIn("未知的可视化器类型", str(context.exception))


class TestVisualizationIntegration(unittest.TestCase):
    """测试可视化集成"""
    
    def setUp(self):
        """设置测试环境"""
        self.mock_workflow = Mock()
        self.mock_workflow.__class__.__name__ = "TestWorkflow"
        self.mock_workflow.__class__.__module__ = "test.module"
    
    @patch('src.application.workflow.visualization.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.application.workflow.visualization.json')
    def test_full_export_workflow(self, mock_json, mock_open_file, mock_path_class):
        """测试完整导出工作流流程"""
        # 设置路径模拟
        mock_output_path = Mock(spec=Path)
        mock_path_class.return_value = mock_output_path
        mock_output_path.__str__ = Mock(return_value="/test/output")  # 使str()返回正确的路径
        
        # 使模拟路径对象支持 / 操作符
        mock_config_file = Mock()
        mock_script_file = Mock()
        mock_output_path.__truediv__ = Mock(side_effect=[mock_config_file, mock_script_file])
        
        # 设置JSON模拟
        mock_json.dump = Mock()
        
        # 创建可视化器
        visualizer = LangGraphStudioVisualizer()
        
        # 导出工作流
        output_dir = visualizer.export_to_langgraph_studio(self.mock_workflow, "/test/output")
        
        # 验证结果
        self.assertEqual(output_dir, "/test/output")
        
        # 验证目录创建
        mock_output_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        # 验证文件创建
        self.assertEqual(mock_open_file.call_count, 2)  # 配置文件和启动脚本
        
        # 验证JSON配置写入
        mock_json.dump.assert_called_once()
        args, kwargs = mock_json.dump.call_args
        config = args[0]
        self.assertIn("graph", config)
        self.assertIn("ui", config)
        self.assertIn("debug", config)
    
    def test_visualization_data_structure(self):
        """测试可视化数据结构"""
        # 创建可视化器
        visualizer = LangGraphStudioVisualizer()
        
        # 生成可视化数据
        viz_data = visualizer._generate_visualization_data(self.mock_workflow)
        
        # 验证必需字段
        required_fields = ["workflow_type", "nodes", "edges", "metadata"]
        for field in required_fields:
            self.assertIn(field, viz_data)
        
        # 验证节点结构
        nodes = viz_data["nodes"]
        self.assertIsInstance(nodes, list)
        if nodes:
            node = nodes[0]
            self.assertIn("id", node)
            self.assertIn("type", node)
            self.assertIn("label", node)
        
        # 验证边结构
        edges = viz_data["edges"]
        self.assertIsInstance(edges, list)
        if edges:
            edge = edges[0]
            self.assertIn("from", edge)
            self.assertIn("to", edge)
        
        # 验证元数据结构
        metadata = viz_data["metadata"]
        self.assertIn("created_at", metadata)
        self.assertIn("version", metadata)
    
    def test_mermaid_diagram_format(self):
        """测试Mermaid图表格式"""
        # 创建可视化器
        visualizer = LangGraphStudioVisualizer()
        
        # 生成Mermaid图表
        mermaid_code = visualizer.generate_mermaid_diagram(self.mock_workflow)
        
        # 验证Mermaid语法
        self.assertIn("graph TD", mermaid_code)
        self.assertIn("-->", mermaid_code)
        self.assertIn("[", mermaid_code)
        self.assertIn("]", mermaid_code)
        
        # 验证基本结构
        lines = mermaid_code.strip().split('\n')
        self.assertTrue(any("graph TD" in line for line in lines))
        self.assertTrue(any("A[" in line for line in lines))
        self.assertTrue(any("-->" in line for line in lines))


if __name__ == '__main__':
    unittest.main()