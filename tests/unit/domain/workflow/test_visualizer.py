"""工作流可视化器测试

测试WorkflowVisualizer的功能。
"""

import unittest
from unittest.mock import Mock

from src.domain.workflow.visualizer import WorkflowVisualizer
from src.infrastructure.graph.config import WorkflowConfig


class TestWorkflowVisualizer(unittest.TestCase):
    """测试工作流可视化器"""
    
    def setUp(self):
        """设置测试环境"""
        self.visualizer = WorkflowVisualizer()
        
        # 创建模拟的工作流配置
        self.mock_workflow_config = Mock(spec=WorkflowConfig)
        self.mock_workflow_config.name = "test_workflow"
        self.mock_workflow_config.description = "Test workflow"
        self.mock_workflow_config.version = "1.0.0"
        self.mock_workflow_config.entry_point = "node1"
        
        # 创建模拟的节点配置
        mock_node_config = Mock()
        mock_node_config.function_name = "llm_node"
        mock_node_config.description = "Test LLM node"
        mock_node_config.config = {"model": "gpt-4"}
        
        self.mock_workflow_config.nodes = {"node1": mock_node_config}
        
        # 创建模拟的边配置 - 确保from_node和to_node都在nodes中
        mock_edge_config = Mock()
        mock_edge_config.from_node = "node1"
        mock_edge_config.to_node = "node1"  # 改为node1，确保节点存在
        mock_edge_config.type.value = "normal"
        mock_edge_config.description = "Test edge"
        mock_edge_config.condition = None
        
        self.mock_workflow_config.edges = [mock_edge_config]
    
    def test_init(self):
        """测试初始化"""
        self.assertIn("hierarchical", self.visualizer.layout_engines)
        self.assertIn("force_directed", self.visualizer.layout_engines)
        self.assertIn("circular", self.visualizer.layout_engines)
    
    def test_generate_visualization(self):
        """测试生成可视化数据"""
        # 生成可视化数据
        visualization = self.visualizer.generate_visualization(self.mock_workflow_config)
        
        # 验证结果
        self.assertEqual(visualization["workflow_id"], "test_workflow")
        self.assertEqual(visualization["name"], "test_workflow")
        self.assertEqual(visualization["description"], "Test workflow")
        self.assertEqual(visualization["version"], "1.0.0")
        self.assertEqual(visualization["layout"], "hierarchical")
        self.assertIn("nodes", visualization)
        self.assertIn("edges", visualization)
        self.assertEqual(visualization["entry_point"], "node1")
        self.assertIn("generated_at", visualization)
        self.assertIn("statistics", visualization)
        
        # 验证节点数据
        nodes = visualization["nodes"]
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["id"], "node1")
        self.assertEqual(nodes[0]["type"], "llm_node")
        self.assertEqual(nodes[0]["label"], "Test LLM node")
        self.assertIn("position", nodes[0])
        self.assertIn("size", nodes[0])
        self.assertIn("style", nodes[0])
        self.assertIn("metadata", nodes[0])
        
        # 验证边数据
        edges = visualization["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["from"], "node1")
        self.assertEqual(edges[0]["to"], "node1")  # 由于我们修改了边的to_node为node1
        self.assertEqual(edges[0]["type"], "normal")
        self.assertEqual(edges[0]["label"], "Test edge")
        self.assertIsNone(edges[0]["condition"])
        self.assertIn("style", edges[0])
        self.assertIn("metadata", edges[0])
    
    def test_generate_visualization_with_layout(self):
        """测试使用指定布局生成可视化数据"""
        # 生成可视化数据
        visualization = self.visualizer.generate_visualization(self.mock_workflow_config, layout="force_directed")
        
        # 验证结果
        self.assertEqual(visualization["layout"], "force_directed")
    
    def test_generate_visualization_invalid_layout(self):
        """测试使用无效布局生成可视化数据"""
        # 生成可视化数据
        visualization = self.visualizer.generate_visualization(self.mock_workflow_config, layout="invalid_layout")
        
        # 验证结果 - 应该使用默认的层次布局
        self.assertEqual(visualization["layout"], "hierarchical")
    
    def test_export_diagram_json(self):
        """测试导出JSON格式图表"""
        # 导出图表
        data = self.visualizer.export_diagram(self.mock_workflow_config, format="json")
        
        # 验证结果
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)
        
        # 解码并验证JSON格式
        import json
        json_data = json.loads(data.decode('utf-8'))
        self.assertEqual(json_data["workflow_id"], "test_workflow")
    
    def test_export_diagram_mermaid(self):
        """测试导出Mermaid格式图表"""
        # 导出图表
        data = self.visualizer.export_diagram(self.mock_workflow_config, format="mermaid")
        
        # 验证结果
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)
        
        # 解码并验证Mermaid格式
        mermaid_data = data.decode('utf-8')
        self.assertIn("graph TD", mermaid_data)
    
    def test_export_diagram_svg(self):
        """测试导出SVG格式图表"""
        # 导出图表
        data = self.visualizer.export_diagram(self.mock_workflow_config, format="svg")
        
        # 验证结果
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)
    
    def test_export_diagram_png(self):
        """测试导出PNG格式图表"""
        # 导出图表
        data = self.visualizer.export_diagram(self.mock_workflow_config, format="png")
        
        # 验证结果
        self.assertIsInstance(data, bytes)
    
    def test_export_diagram_invalid_format(self):
        """测试导出无效格式图表"""
        # 执行测试并验证异常
        with self.assertRaises(ValueError) as context:
            self.visualizer.export_diagram(self.mock_workflow_config, format="invalid_format")
        
        self.assertIn("不支持的导出格式", str(context.exception))
    
    def test_get_node_size(self):
        """测试获取节点大小"""
        # 测试已知节点类型
        size = self.visualizer._get_node_size("llm_node")
        self.assertEqual(size, {"width": 120, "height": 80})
        
        # 测试未知节点类型
        size = self.visualizer._get_node_size("unknown_node")
        self.assertEqual(size, {"width": 100, "height": 60})
    
    def test_get_node_style(self):
        """测试获取节点样式"""
        # 测试已知节点类型
        style = self.visualizer._get_node_style("llm_node")
        self.assertEqual(style["fill"], "#e1f5fe")
        self.assertEqual(style["stroke"], "#0288d1")
        self.assertEqual(style["stroke_width"], 2)
        
        # 测试未知节点类型
        style = self.visualizer._get_node_style("unknown_node")
        self.assertEqual(style["fill"], "#f5f5f5")
        self.assertEqual(style["stroke"], "#9e9e9e")
        self.assertEqual(style["stroke_width"], 1)
    
    def test_get_edge_style(self):
        """测试获取边样式"""
        # 测试已知边类型
        style = self.visualizer._get_edge_style("normal")
        self.assertEqual(style["stroke"], "#666")
        self.assertEqual(style["stroke_width"], 2)
        self.assertTrue(style["arrow"])
        
        # 测试未知边类型
        style = self.visualizer._get_edge_style("unknown_type")
        self.assertEqual(style["stroke"], "#666")
        self.assertEqual(style["stroke_width"], 2)
        self.assertTrue(style["arrow"])
    
    def test_get_node_category(self):
        """测试获取节点分类"""
        # 测试已知节点类型
        category = self.visualizer._get_node_category("llm_node")
        self.assertEqual(category, "ai")
        
        # 测试未知节点类型
        category = self.visualizer._get_node_category("unknown_node")
        self.assertEqual(category, "unknown")
    
    def test_count_node_types(self):
        """测试统计节点类型"""
        # 创建测试节点数据
        nodes = [
            {"type": "llm_node"},
            {"type": "tool_node"},
            {"type": "llm_node"},
            {"type": "unknown_node"}
        ]
        
        # 统计节点类型
        counts = self.visualizer._count_node_types(nodes)
        
        # 验证结果
        self.assertEqual(counts["llm_node"], 2)
        self.assertEqual(counts["tool_node"], 1)
        self.assertEqual(counts["unknown_node"], 1)
    
    def test_count_edge_types(self):
        """测试统计边类型"""
        # 创建测试边数据
        edges = [
            {"type": "normal"},
            {"type": "conditional"},
            {"type": "normal"},
            {"type": "unknown_type"}
        ]
        
        # 统计边类型
        counts = self.visualizer._count_edge_types(edges)
        
        # 验证结果
        self.assertEqual(counts["normal"], 2)
        self.assertEqual(counts["conditional"], 1)
        self.assertEqual(counts["unknown_type"], 1)


if __name__ == '__main__':
    unittest.main()