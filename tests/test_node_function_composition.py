"""
节点内部函数组合测试
"""

import unittest
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.infrastructure.graph.node_functions import (
    NodeFunctionManager,
    NodeFunctionRegistry,
    NodeFunctionConfig,
    NodeCompositionConfig
)
from src.infrastructure.graph.config import GraphConfig


class TestNodeFunctionComposition(unittest.TestCase):
    """节点函数组合测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.registry = NodeFunctionRegistry()
        self.manager = NodeFunctionManager(self.registry)
        
        # 创建测试函数
        def test_validator(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
            return {**state, "validated": True}
        
        def test_processor(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
            return {**state, "processed": True}
        
        # 注册测试函数
        validator_config = NodeFunctionConfig(
            name="test_validator",
            description="测试验证函数",
            function_type="validator",
            parameters={},
            implementation="builtin",
            metadata={},
            dependencies=[],
            return_schema={},
            input_schema={}
        )
        
        processor_config = NodeFunctionConfig(
            name="test_processor",
            description="测试处理函数",
            function_type="processor",
            parameters={},
            implementation="builtin",
            metadata={},
            dependencies=["test_validator"],
            return_schema={},
            input_schema={}
        )
        
        self.registry.register_function("test_validator", test_validator, validator_config)
        self.registry.register_function("test_processor", test_processor, processor_config)
        
        # 创建测试组合
        composition_config = NodeCompositionConfig(
            name="test_composition",
            description="测试组合",
            functions=[validator_config, processor_config],
            execution_order=["test_validator", "test_processor"],
            input_mapping={},
            output_mapping={},
            error_handling={},
            metadata={}
        )
        
        self.registry.register_composition(composition_config)
    
    def test_function_registration(self):
        """测试函数注册"""
        # 验证函数已注册
        self.assertTrue(self.registry.has_function("test_validator"))
        self.assertTrue(self.registry.has_function("test_processor"))
        
        # 验证函数可获取
        validator_func = self.registry.get_function("test_validator")
        self.assertIsNotNone(validator_func)
        
        processor_func = self.registry.get_function("test_processor")
        self.assertIsNotNone(processor_func)
    
    def test_composition_registration(self):
        """测试组合注册"""
        # 验证组合已注册
        self.assertTrue(self.registry.has_composition("test_composition"))
        
        # 验证组合可获取
        composition = self.registry.get_composition("test_composition")
        self.assertIsNotNone(composition)
        self.assertEqual(composition.name, "test_composition")
    
    def test_function_execution(self):
        """测试函数执行"""
        state = {"input": "test"}
        
        # 执行验证函数
        result = self.manager.execute_function("test_validator", state)
        self.assertTrue(result.get("validated"))
        
        # 执行处理函数
        result = self.manager.execute_function("test_processor", result)
        self.assertTrue(result.get("processed"))
    
    def test_composition_execution(self):
        """测试组合执行"""
        state = {"input": "test"}
        
        # 执行组合
        result = self.manager.execute_composition("test_composition", state)
        
        # 验证所有函数都已执行
        self.assertTrue(result.get("validated"))
        self.assertTrue(result.get("processed"))
    
    def test_list_functions(self):
        """测试函数列表"""
        functions = self.manager.list_functions()
        self.assertIn("test_validator", functions)
        self.assertIn("test_processor", functions)
        
        # 按类型列出函数
        validator_functions = self.manager.list_functions_by_type("validator")
        self.assertIn("test_validator", validator_functions)
    
    def test_list_compositions(self):
        """测试组合列表"""
        compositions = self.manager.list_compositions()
        self.assertIn("test_composition", compositions)


class TestNodeFunctionIntegration(unittest.TestCase):
    """节点函数集成测试类"""
    
    def setUp(self):
        """测试初始化"""
        # 使用配置目录加载函数
        self.manager = NodeFunctionManager()
        # 注意：在实际测试中，这里会加载配置文件中的函数
    
    def test_manager_initialization(self):
        """测试管理器初始化"""
        self.assertIsNotNone(self.manager.registry)
        self.assertIsNotNone(self.manager.loader)
        self.assertIsNotNone(self.manager.executor)
    
    def test_get_function_config(self):
        """测试获取函数配置"""
        # 对于内置函数，应该能获取到配置
        # 注意：这需要实际的配置文件支持
        pass


if __name__ == "__main__":
    unittest.main()