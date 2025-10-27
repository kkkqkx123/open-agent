"""工作流节点自动发现测试

测试工作流节点自动发现和注册功能。
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path
import importlib
from typing import List, Type, Dict, Any, Optional
import sys

from src.application.workflow.auto_discovery import (
    NodeDiscovery, auto_register_nodes, register_builtin_nodes
)
from src.infrastructure.graph.registry import BaseNode, NodeRegistry, NodeExecutionResult


class TestNodeDiscovery(unittest.TestCase):
    """测试节点发现器"""
    
    def setUp(self) -> None:
        """设置测试环境"""
        self.mock_registry = Mock(spec=NodeRegistry)
        self.discovery = NodeDiscovery(registry=self.mock_registry)
    
    def test_init(self) -> None:
        """测试初始化"""
        self.assertEqual(self.discovery.registry, self.mock_registry)
    
    def test_init_with_default_registry(self) -> None:
        """测试使用默认注册表初始化"""
        with patch('src.application.workflow.auto_discovery.get_global_registry') as mock_get_global:
            mock_global_registry = Mock(spec=NodeRegistry)
            mock_get_global.return_value = mock_global_registry
            
            discovery = NodeDiscovery()
            
            self.assertEqual(discovery.registry, mock_global_registry)
            mock_get_global.assert_called_once()
    
    @patch('src.application.workflow.auto_discovery.importlib.import_module')
    @patch('src.application.workflow.auto_discovery.Path')
    def test_discover_nodes_from_package_success(self, mock_path_class: Mock, mock_import_module: Mock) -> None:
        """测试成功从包中发现节点"""
        # 设置模拟
        mock_package = Mock()
        mock_package.__file__ = "/path/to/package/__init__.py"
        mock_import_module.return_value = mock_package
        
        mock_package_dir = Mock()
        mock_path_class.return_value = mock_package_dir
        
        # 模拟模块文件
        mock_module_file1 = Mock()
        mock_module_file1.name = "module1.py"
        mock_module_file1.stem = "module1"
        
        mock_module_file2 = Mock()
        mock_module_file2.name = "_internal.py"  # 以下划线开头，应该被跳过
        mock_module_file2.stem = "_internal"
        
        mock_package_dir.glob.return_value = [mock_module_file1, mock_module_file2]
        
        # 模拟模块
        mock_module1 = Mock()
        mock_module1.__name__ = "test_package.module1"
        
        # 模拟节点类
        class MockNode1(BaseNode):
            @property
            def node_type(self) -> str:
                return "test_node1"

            def execute(self, state: Any, config: Optional[Dict[str, Any]] = None) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)

            def get_config_schema(self) -> Dict[str, Any]:
                return {}
        
        class MockNode2(BaseNode):
            @property
            def node_type(self) -> str:
                return "test_node2"
            
            def execute(self, state: Any, config: Optional[Dict[str, Any]] = None) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> Dict[str, Any]:
                return {}
        
        class NotANode:
            """不是节点类"""
            pass
        
        # 设置模块成员
        mock_module1.__dict__.update({
            'MockNode1': MockNode1,
            'MockNode2': MockNode2,
            'NotANode': NotANode,
            'some_function': lambda: None
        })
        
        def mock_import_side_effect(module_name: str) -> Any:
            if module_name == "test_package":
                return mock_package
            elif module_name == "test_package.module1":
                return mock_module1
            else:
                raise ImportError(f"No module named '{module_name}'")
        
        mock_import_module.side_effect = mock_import_side_effect
        
        # 发现节点
        discovered_nodes = self.discovery.discover_nodes_from_package("test_package")
        
        # 验证结果
        self.assertEqual(len(discovered_nodes), 2)
        self.assertIn(MockNode1, discovered_nodes)
        self.assertIn(MockNode2, discovered_nodes)
        self.assertNotIn(NotANode, discovered_nodes)
        
        # 验证调用
        mock_import_module.assert_any_call("test_package")
        mock_import_module.assert_any_call("test_package.module1")
    
    @patch('src.application.workflow.auto_discovery.importlib.import_module')
    def test_discover_nodes_from_package_import_error(self, mock_import_module: Mock) -> None:
        """测试包导入错误"""
        # 设置模拟抛出异常
        mock_import_module.side_effect = ImportError("Package not found")
        
        # 发现节点
        discovered_nodes = self.discovery.discover_nodes_from_package("nonexistent_package")
        
        # 验证结果
        self.assertEqual(len(discovered_nodes), 0)
    
    @patch('src.application.workflow.auto_discovery.importlib.import_module')
    @patch('src.application.workflow.auto_discovery.Path')
    def test_discover_nodes_from_package_module_import_error(
        self, mock_path_class: Mock, mock_import_module: Mock
    ) -> None:
        """测试模块导入错误"""
        # 设置模拟
        mock_package = Mock()
        mock_package.__file__ = "/path/to/package/__init__.py"
        
        mock_package_dir = Mock()
        mock_path_class.return_value = mock_package_dir
        
        # 模拟模块文件
        mock_module_file = Mock()
        mock_module_file.name = "module1.py"
        mock_module_file.stem = "module1"
        
        mock_package_dir.glob.return_value = [mock_module_file]
        
        # 设置模块导入失败 - 使用条件函数来避免与 sys 模块冲突
        original_import = importlib.import_module
        
        def import_side_effect(module_name: str) -> Any:
            if module_name == "test_package":
                return mock_package
            elif module_name == "test_package.module1":
                raise ImportError("Module import failed")
            else:
                return original_import(module_name)
        
        mock_import_module.side_effect = import_side_effect
        
        # 发现节点
        with patch.object(sys, 'stdout') as mock_stdout:
            discovered_nodes = self.discovery.discover_nodes_from_package("test_package")
        
        # 验证结果
        self.assertEqual(len(discovered_nodes), 0)
    
    def test_register_discovered_nodes_success(self) -> None:
        """测试成功注册发现的节点"""
        # 创建模拟节点类
        class MockNode1(BaseNode):
            @property
            def node_type(self) -> str:
                return "test_node1"
            
            def execute(self, state: Any, config: Optional[Dict[str, Any]] = None) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
                
            def get_config_schema(self) -> Dict[str, Any]:
                return {}
        
        class MockNode2(BaseNode):
            @property
            def node_type(self) -> str:
                return "test_node2"
            
            def execute(self, state: Any, config: Optional[Dict[str, Any]] = None) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
                
            def get_config_schema(self) -> Dict[str, Any]:
                return {}
        
        nodes: List[Type[BaseNode]] = [MockNode1, MockNode2]
        
        # 注册节点
        results = self.discovery.register_discovered_nodes(nodes)
        
        # 验证结果
        self.assertEqual(len(results), 2)
        self.assertTrue(results["test_node1"])
        self.assertTrue(results["test_node2"])
        
        # 验证注册调用
        self.mock_registry.register_node.assert_any_call(MockNode1)
        self.mock_registry.register_node.assert_any_call(MockNode2)
    
    def test_register_discovered_nodes_without_node_type(self) -> None:
        """测试注册没有node_type属性的节点"""
        # 创建模拟节点类
        class MockNode(BaseNode):
            @property
            def node_type(self) -> str:
                # 没有定义node_type，返回默认值
                return "mock"
            
            def execute(self, state: Any, config: Optional[Dict[str, Any]] = None) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
                
            def get_config_schema(self) -> Dict[str, Any]:
                return {}
        
        nodes: List[Type[BaseNode]] = [MockNode]
        
        # 注册节点
        results = self.discovery.register_discovered_nodes(nodes)
        
        # 验证结果
        self.assertEqual(len(results), 1)
        self.assertTrue(results["mock"])  # 使用类名作为node_type
        
        # 验证注册调用
        self.mock_registry.register_node.assert_called_once_with(MockNode)
    
    def test_register_discovered_nodes_registration_error(self) -> None:
        """测试节点注册错误"""
        # 创建模拟节点类
        class MockNode(BaseNode):
            @property
            def node_type(self) -> str:
                return "test_node"
            
            def execute(self, state: Any, config: Optional[Dict[str, Any]] = None) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
                
            def get_config_schema(self) -> Dict[str, Any]:
                return {}
        
        nodes: List[Type[BaseNode]] = [MockNode]
        
        # 设置注册抛出异常
        self.mock_registry.register_node.side_effect = Exception("Registration failed")
        
        # 注册节点
        with patch.object(sys, 'stdout') as mock_stdout:
            results = self.discovery.register_discovered_nodes(nodes)
        
        # 验证结果
        self.assertEqual(len(results), 1)
        self.assertFalse(results["test_node"])
    
    @patch.object(NodeDiscovery, 'discover_nodes_from_package')
    @patch.object(NodeDiscovery, 'register_discovered_nodes')
    def test_auto_discover_and_register(self, mock_register: Mock, mock_discover: Mock) -> None:
        """测试自动发现并注册节点"""
        # 设置模拟
        class MockNode1(BaseNode):
            @property
            def node_type(self) -> str:
                return "test_node1"
            
            def execute(self, state: Any, config: Optional[Dict[str, Any]] = None) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> Dict[str, Any]:
                return {}
        
        class MockNode2(BaseNode):
            @property
            def node_type(self) -> str:
                return "test_node2"
            
            def execute(self, state: Any, config: Optional[Dict[str, Any]] = None) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> Dict[str, Any]:
                return {}
        
        mock_discover.side_effect = [
            [MockNode1],  # 第一个包发现的节点
            [MockNode2]   # 第二个包发现的节点
        ]
        
        mock_register.side_effect = [
            {"test_node1": True},  # 第一个包的注册结果
            {"test_node2": False}  # 第二个包的注册结果
        ]
        
        # 自动发现并注册
        results = self.discovery.auto_discover_and_register(["package1", "package2"])
        
        # 验证结果
        self.assertEqual(len(results), 3)  # discovered, registered, failed
        self.assertIn("discovered", results)
        self.assertIn("registered", results)
        self.assertIn("failed", results)
        
        # 验证发现的节点
        self.assertEqual(results["discovered"]["package1"], ["MockNode1"])
        self.assertEqual(results["discovered"]["package2"], ["MockNode2"])
        
        # 验证注册结果
        self.assertEqual(results["registered"]["package1"], {"test_node1": True})
        self.assertEqual(results["registered"]["package2"], {"test_node2": False})
        
        # 验证失败的注册
        self.assertEqual(len(results["failed"]), 1)
        self.assertEqual(results["failed"][0]["package"], "package2")
        self.assertEqual(results["failed"][0]["node_type"], "test_node2")
        
        # 验证调用
        mock_discover.assert_any_call("package1")
        mock_discover.assert_any_call("package2")
        mock_register.assert_any_call([MockNode1])
        mock_register.assert_any_call([MockNode2])


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""
    
    @patch('src.application.workflow.auto_discovery.NodeDiscovery')
    def test_auto_register_nodes_with_default_paths(self, mock_discovery_class: Mock) -> None:
        """测试使用默认路径自动注册节点"""
        # 设置模拟
        mock_discovery = Mock()
        mock_discovery_class.return_value = mock_discovery
        mock_discovery.auto_discover_and_register.return_value = {"result": "success"}
        
        # 自动注册节点
        result = auto_register_nodes()
        
        # 验证结果
        self.assertEqual(result, {"result": "success"})
        
        # 验证调用
        mock_discovery_class.assert_called_once()
        mock_discovery.auto_discover_and_register.assert_called_once_with(["src.workflow.nodes"])
    
    @patch('src.application.workflow.auto_discovery.NodeDiscovery')
    def test_auto_register_nodes_with_custom_paths(self, mock_discovery_class: Mock) -> None:
        """测试使用自定义路径自动注册节点"""
        # 设置模拟
        mock_discovery = Mock()
        mock_discovery_class.return_value = mock_discovery
        mock_discovery.auto_discover_and_register.return_value = {"result": "success"}
        
        custom_paths = ["custom.package1", "custom.package2"]
        
        # 自动注册节点
        result = auto_register_nodes(custom_paths)
        
        # 验证结果
        self.assertEqual(result, {"result": "success"})
        
        # 验证调用
        mock_discovery_class.assert_called_once()
        mock_discovery.auto_discover_and_register.assert_called_once_with(custom_paths)
    
    @patch('src.application.workflow.auto_discovery.importlib.import_module')
    def test_register_builtin_nodes_success(self, mock_import_module: Mock) -> None:
        """测试成功注册内置节点"""
        # 设置模拟
        mock_analysis_node = Mock()
        mock_tool_node = Mock()
        mock_llm_node = Mock()
        mock_condition_node = Mock()
        
        # 模拟成功导入
        def mock_import_side_effect(module_name: str) -> Any:
            if module_name == "src.infrastructure.graph.nodes.analysis_node":
                mock_module = Mock()
                mock_module.AnalysisNode = mock_analysis_node
                return mock_module
            elif module_name == "src.infrastructure.graph.nodes.tool_node":
                mock_module = Mock()
                mock_module.ToolNode = mock_tool_node
                return mock_module
            elif module_name == "src.infrastructure.graph.nodes.llm_node":
                mock_module = Mock()
                mock_module.LLMNode = mock_llm_node
                return mock_module
            elif module_name == "src.infrastructure.graph.nodes.condition_node":
                mock_module = Mock()
                mock_module.ConditionNode = mock_condition_node
                return mock_module
            else:
                # 对于其他模块，使用原始导入
                return importlib.import_module(module_name)
        
        mock_import_module.side_effect = mock_import_side_effect
        
        # 注册内置节点
        register_builtin_nodes()
        
        # 验证导入调用
        self.assertTrue(mock_import_module.called)
        # 验证特定的导入调用
        expected_calls = [
            "src.infrastructure.graph.nodes.analysis_node",
            "src.infrastructure.graph.nodes.tool_node",
            "src.infrastructure.graph.nodes.llm_node",
            "src.infrastructure.graph.nodes.condition_node"
        ]
        for call in expected_calls:
            mock_import_module.assert_any_call(call)
    
    @patch('src.application.workflow.auto_discovery.importlib.import_module')
    def test_register_builtin_nodes_import_error(self, mock_import_module: Mock) -> None:
        """测试注册内置节点时导入错误"""
        # 设置模拟抛出异常
        original_import = importlib.import_module
        
        def import_side_effect(module_name: str) -> Any:
            if module_name.startswith("src.infrastructure.graph.nodes"):
                raise ImportError("Module not found")
            else:
                return original_import(module_name)
        
        mock_import_module.side_effect = import_side_effect
        
        # 注册内置节点
        with patch.object(sys, 'stdout') as mock_stdout:
            register_builtin_nodes()
        
        # 验证错误打印
        self.assertTrue(mock_stdout.write.called)


if __name__ == '__main__':
    unittest.main()