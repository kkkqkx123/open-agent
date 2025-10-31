"""通用工作流加载器测试

测试通用工作流加载器的核心功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.application.workflow.universal_loader import (
    UniversalWorkflowLoader, 
    WorkflowInstance, 
    UniversalLoaderError,
    ConfigValidationError
)
from src.infrastructure.graph.function_registry import FunctionType
from src.infrastructure.graph.config import GraphConfig


class TestUniversalWorkflowLoader:
    """通用工作流加载器测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.loader = UniversalWorkflowLoader()
    
    def test_init(self):
        """测试初始化"""
        assert self.loader is not None
        assert self.loader.function_registry is not None
        assert self.loader.node_registry is not None
        assert self.loader.template_manager is not None
        assert self.loader.config_validator is not None
        assert self.loader.graph_builder is not None
    
    def test_register_function(self):
        """测试函数注册"""
        def test_function(state):
            return {"result": "test"}
        
        # 注册节点函数
        self.loader.register_function("test_node", test_function, FunctionType.NODE_FUNCTION)
        
        # 验证注册成功
        functions = self.loader.list_registered_functions()
        assert "test_node" in functions["nodes"]
        
        # 注册条件函数
        def test_condition(state):
            return "continue"
        
        self.loader.register_function("test_condition", test_condition, FunctionType.CONDITION_FUNCTION)
        
        # 验证注册成功
        functions = self.loader.list_registered_functions()
        assert "test_condition" in functions["conditions"]
    
    def test_register_function_invalid(self):
        """测试无效函数注册"""
        # 测试非可调用对象
        with pytest.raises(UniversalLoaderError):
            self.loader.register_function("invalid", "not_callable", FunctionType.NODE_FUNCTION)
        
        # 测试空名称
        def test_function(state):
            return {}
        
        with pytest.raises(UniversalLoaderError):
            self.loader.register_function("", test_function, FunctionType.NODE_FUNCTION)
    
    def test_get_function_info(self):
        """测试获取函数信息"""
        def test_function(state):
            """测试函数"""
            return {"result": "test"}
        
        self.loader.register_function("test_func", test_function, FunctionType.NODE_FUNCTION)
        
        info = self.loader.get_function_info("test_func", FunctionType.NODE_FUNCTION)
        assert info is not None
        assert info["name"] == "test_func"
        assert info["type"] == "node_function"
        assert "测试函数" in info["doc"]
    
    def test_get_function_info_not_found(self):
        """测试获取不存在的函数信息"""
        info = self.loader.get_function_info("nonexistent", FunctionType.NODE_FUNCTION)
        assert info is None
    
    def test_list_registered_functions(self):
        """测试列出已注册函数"""
        def test_node(state):
            return {}
        
        def test_condition(state):
            return "continue"
        
        self.loader.register_function("test_node", test_node, FunctionType.NODE_FUNCTION)
        self.loader.register_function("test_condition", test_condition, FunctionType.CONDITION_FUNCTION)
        
        functions = self.loader.list_registered_functions()
        assert "test_node" in functions["nodes"]
        assert "test_condition" in functions["conditions"]
        
        # 测试过滤
        node_functions = self.loader.list_registered_functions(FunctionType.NODE_FUNCTION)
        assert "test_node" in node_functions["nodes"]
        assert "conditions" not in node_functions
    
    def test_get_function_statistics(self):
        """测试获取函数统计"""
        def test_node(state):
            return {}
        
        def test_condition(state):
            return "continue"
        
        self.loader.register_function("test_node", test_node, FunctionType.NODE_FUNCTION)
        self.loader.register_function("test_condition", test_condition, FunctionType.CONDITION_FUNCTION)
        
        stats = self.loader.get_function_statistics()
        assert stats["total_node_functions"] >= 1
        assert stats["total_condition_functions"] >= 1
        assert "test_node" in stats["node_functions"]
        assert "test_condition" in stats["condition_functions"]
    
    def test_clear_cache(self):
        """测试清除缓存"""
        # 添加一些缓存数据
        self.loader._config_cache["test"] = "test_config"
        self.loader._graph_cache["test"] = "test_graph"
        
        # 清除缓存
        self.loader.clear_cache()
        
        # 验证缓存已清除
        assert len(self.loader._config_cache) == 0
        assert len(self.loader._graph_cache) == 0
    
    def test_load_from_dict(self):
        """测试从字典加载工作流"""
        config_dict = {
            "name": "test_workflow",
            "description": "测试工作流",
            "state_schema": {
                "name": "TestState",
                "fields": {
                    "messages": {
                        "type": "List[dict]",
                        "default": []
                    }
                }
            },
            "nodes": {
                "test_node": {
                    "type": "llm_node",
                    "config": {
                        "system_prompt": "测试提示"
                    }
                }
            },
            "edges": [],
            "entry_point": "test_node"
        }
        
        workflow = self.loader.load_from_dict(config_dict)
        
        assert workflow is not None
        assert isinstance(workflow, WorkflowInstance)
        assert workflow.config.name == "test_workflow"
    
    def test_load_from_dict_invalid(self):
        """测试从无效字典加载工作流"""
        # 缺少必需字段
        config_dict = {
            "name": "test_workflow"
            # 缺少 description, state_schema 等
        }
        
        with pytest.raises(ConfigValidationError):
            self.loader.load_from_dict(config_dict)
    
    @patch('builtins.open', create=True)
    @patch('yaml.safe_load')
    def test_load_from_file(self, mock_yaml_load, mock_open):
        """测试从文件加载工作流"""
        # 模拟文件内容
        config_data = {
            "name": "test_workflow",
            "description": "测试工作流",
            "state_schema": {
                "name": "TestState",
                "fields": {}
            },
            "nodes": {},
            "edges": []
        }
        mock_yaml_load.return_value = config_data
        
        # 模拟文件存在
        with patch('pathlib.Path.exists', return_value=True):
            workflow = self.loader.load_from_file("test_config.yaml")
        
        assert workflow is not None
        assert isinstance(workflow, WorkflowInstance)
    
    def test_load_from_file_not_found(self):
        """测试从不存在的文件加载工作流"""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                self.loader.load_from_file("nonexistent.yaml")
    
    def test_validate_config(self):
        """测试配置验证"""
        # 有效配置
        config_dict = {
            "name": "test_workflow",
            "description": "测试工作流",
            "state_schema": {
                "name": "TestState",
                "fields": {}
            },
            "nodes": {},
            "edges": []
        }
        
        result = self.loader.validate_config(config_dict)
        assert result.is_valid
        
        # 无效配置
        invalid_config = {
            "name": "",  # 空名称
            "description": "测试工作流",
            "state_schema": {
                "name": "TestState",
                "fields": {}
            },
            "nodes": {},
            "edges": []
        }
        
        result = self.loader.validate_config(invalid_config)
        assert not result.is_valid
        assert len(result.errors) > 0


class TestWorkflowInstance:
    """工作流实例测试类"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建模拟的图和配置
        self.mock_graph = Mock()
        self.mock_config = Mock()
        self.mock_config.name = "test_workflow"
        self.mock_config.additional_config = {}
        
        # 创建模拟的加载器
        self.mock_loader = Mock()
        self.mock_loader._template_manager = Mock()
        self.mock_loader._template_manager.create_state_from_config.return_value = {}
        
        # 创建工作流实例
        self.workflow = WorkflowInstance(self.mock_graph, self.mock_config, self.mock_loader)
    
    def test_init(self):
        """测试初始化"""
        assert self.workflow.graph == self.mock_graph
        assert self.workflow.config == self.mock_config
        assert self.workflow.loader == self.mock_loader
    
    def test_get_config(self):
        """测试获取配置"""
        config = self.workflow.get_config()
        assert config == self.mock_config
    
    def test_get_visualization(self):
        """测试获取可视化数据"""
        # 设置模拟配置
        self.mock_config.nodes = {
            "node1": Mock(function_name="test_node", config={}, description="测试节点")
        }
        self.mock_config.edges = [
            Mock(from_node="node1", to="node2", type=Mock(value="simple"), condition=None, description="测试边")
        ]
        self.mock_config.entry_point = "node1"
        
        viz = self.workflow.get_visualization()
        
        assert viz["name"] == "test_workflow"
        assert len(viz["nodes"]) == 1
        assert len(viz["edges"]) == 1
        assert viz["entry_point"] == "node1"
    
    def test_run(self):
        """测试运行工作流"""
        # 模拟图执行
        expected_result = {"status": "completed"}
        self.mock_graph.invoke.return_value = expected_result
        
        # 模拟状态创建
        self.mock_loader._template_manager.create_state_from_config.return_value = {"input": "test"}
        
        result = self.workflow.run({"input": "test"})
        
        assert result == expected_result
        self.mock_graph.invoke.assert_called_once()
    
    def test_run_with_error(self):
        """测试运行工作流出错"""
        # 模拟图执行错误
        self.mock_graph.invoke.side_effect = Exception("测试错误")
        
        # 模拟状态创建
        self.mock_loader._template_manager.create_state_from_config.return_value = {"input": "test"}
        
        with pytest.raises(UniversalLoaderError):
            self.workflow.run({"input": "test"})
    
    @pytest.mark.asyncio
    async def test_run_async(self):
        """测试异步运行工作流"""
        # 模拟异步图执行
        expected_result = {"status": "completed"}
        self.mock_graph.ainvoke.return_value = expected_result
        
        # 模拟状态创建
        self.mock_loader._template_manager.create_state_from_config.return_value = {"input": "test"}
        
        result = await self.workflow.run_async({"input": "test"})
        
        assert result == expected_result
        self.mock_graph.ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_async_fallback(self):
        """测试异步运行工作流回退到同步"""
        # 模拟图不支持异步
        del self.mock_graph.ainvoke
        
        expected_result = {"status": "completed"}
        self.mock_graph.invoke.return_value = expected_result
        
        # 模拟状态创建
        self.mock_loader._template_manager.create_state_from_config.return_value = {"input": "test"}
        
        result = await self.workflow.run_async({"input": "test"})
        
        assert result == expected_result
        self.mock_graph.invoke.assert_called_once()
    
    def test_stream(self):
        """测试流式运行工作流"""
        # 模拟流式执行
        chunks = [{"step": 1}, {"step": 2}, {"step": 3}]
        self.mock_graph.stream.return_value = iter(chunks)
        
        # 模拟状态创建
        self.mock_loader._template_manager.create_state_from_config.return_value = {"input": "test"}
        
        results = list(self.workflow.stream({"input": "test"}))
        
        assert results == chunks
        self.mock_graph.stream.assert_called_once()
    
    def test_stream_fallback(self):
        """测试流式运行工作流回退到同步"""
        # 模拟图不支持流式
        del self.mock_graph.stream
        
        expected_result = {"status": "completed"}
        self.mock_graph.invoke.return_value = expected_result
        
        # 模拟状态创建
        self.mock_loader._template_manager.create_state_from_config.return_value = {"input": "test"}
        
        results = list(self.workflow.stream({"input": "test"}))
        
        assert len(results) == 1
        assert results[0] == expected_result
        self.mock_graph.invoke.assert_called_once()
    
    def test_create_initial_state(self):
        """测试创建初始状态"""
        # 模拟模板管理器
        expected_state = {"input": "test", "messages": []}
        self.mock_loader._template_manager.create_state_from_config.return_value = expected_state
        
        state = self.workflow._create_initial_state({"input": "test"})
        
        assert state == expected_state
        self.mock_loader._template_manager.create_state_from_config.assert_called_once()


class TestIntegration:
    """集成测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.loader = UniversalWorkflowLoader()
    
    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        # 注册测试函数
        def test_node(state):
            return {"result": "test_result", "messages": state.get("messages", []) + [{"content": "test"}]}
        
        def test_condition(state):
            return "end" if state.get("result") else "continue"
        
        self.loader.register_function("test_node", test_node, FunctionType.NODE_FUNCTION)
        self.loader.register_function("test_condition", test_condition, FunctionType.CONDITION_FUNCTION)
        
        # 创建配置
        config_dict = {
            "name": "integration_test_workflow",
            "description": "集成测试工作流",
            "state_schema": {
                "name": "IntegrationTestState",
                "fields": {
                    "messages": {
                        "type": "List[dict]",
                        "default": []
                    },
                    "result": {
                        "type": "str",
                        "default": ""
                    }
                }
            },
            "nodes": {
                "test_node": {
                    "type": "test_node",
                    "config": {}
                }
            },
            "edges": [
                {
                    "from": "test_node",
                    "to": "__end__",
                    "type": "conditional",
                    "condition": "test_condition"
                }
            ],
            "entry_point": "test_node"
        }
        
        # 加载并运行工作流
        workflow = self.loader.load_from_dict(config_dict)
        result = workflow.run({"input": "test"})
        
        # 验证结果
        assert result is not None
        assert "result" in result
        assert result["result"] == "test_result"
    
    def test_function_registration_from_config(self):
        """测试从配置注册函数"""
        # 创建包含函数注册的配置
        config_data = {
            "name": "test_workflow",
            "description": "测试工作流",
            "state_schema": {
                "name": "TestState",
                "fields": {}
            },
            "nodes": {},
            "edges": [],
            "function_registrations": {
                "nodes": {
                    "test_node": "tests.unit.application.workflow.test_universal_loader.test_node_function"
                },
                "conditions": {
                    "test_condition": "tests.unit.application.workflow.test_universal_loader.test_condition_function"
                }
            }
        }
        
        # 模拟模块导入
        def test_node_function(state):
            return {"result": "from_module"}
        
        def test_condition_function(state):
            return "end"
        
        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_module.test_node_function = test_node_function
            mock_module.test_condition_function = test_condition_function
            mock_import.return_value = mock_module
            
            # 加载配置
            config = GraphConfig.from_dict(config_data)
            
            # 处理函数注册
            self.loader._process_function_registrations(config_data)
            
            # 验证函数已注册
            functions = self.loader.list_registered_functions()
            assert "test_node" in functions["nodes"]
            assert "test_condition" in functions["conditions"]


if __name__ == "__main__":
    pytest.main([__file__])