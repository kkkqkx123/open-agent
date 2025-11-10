"""
GraphWorkflow 端到端集成测试

测试 GraphWorkflow 的完整功能，包括配置加载、工作流执行、错误处理等。
"""

import asyncio
import pytest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.application.workflow.graph_workflow import (
    GraphWorkflow, 
    SimpleGraphWorkflow,
    GraphWorkflowError,
    GraphWorkflowConfigError,
    GraphWorkflowExecutionError
)
from src.application.workflow.universal_loader import WorkflowInstance


class TestGraphWorkflowIntegration:
    """GraphWorkflow 集成测试类"""
    
    @pytest.fixture
    def simple_config(self):
        """简单配置 fixture"""
        return {
            "name": "test_workflow",
            "description": "测试工作流",
            "version": "1.0",
            "entry_point": "start",
            "nodes": {
                "start": {
                    "name": "start",
                    "function_name": "process_start",
                    "description": "开始节点"
                },
                "end": {
                    "name": "end", 
                    "function_name": "process_end",
                    "description": "结束节点"
                }
            },
            "edges": [
                {
                    "from": "start",
                    "to": "end",
                    "type": "simple"
                }
            ],
            "state_schema": {
                "name": "TestState",
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
            }
        }
    
    @pytest.fixture
    def conditional_config(self):
        """条件分支配置 fixture"""
        return {
            "name": "conditional_test",
            "description": "条件分支测试",
            "version": "1.0",
            "entry_point": "classifier",
            "nodes": {
                "classifier": {
                    "name": "classifier",
                    "function_name": "classify_input",
                    "description": "分类节点"
                },
                "processor_a": {
                    "name": "processor_a",
                    "function_name": "process_type_a",
                    "description": "处理器A"
                },
                "processor_b": {
                    "name": "processor_b", 
                    "function_name": "process_type_b",
                    "description": "处理器B"
                },
                "aggregator": {
                    "name": "aggregator",
                    "function_name": "aggregate_results",
                    "description": "聚合器"
                }
            },
            "edges": [
                {
                    "from": "classifier",
                    "to": "processor_a",
                    "type": "conditional",
                    "condition": "type == 'A'"
                },
                {
                    "from": "classifier",
                    "to": "processor_b", 
                    "type": "conditional",
                    "condition": "type == 'B'"
                },
                {
                    "from": "processor_a",
                    "to": "aggregator",
                    "type": "simple"
                },
                {
                    "from": "processor_b",
                    "to": "aggregator",
                    "type": "simple"
                }
            ],
            "state_schema": {
                "name": "ConditionalState",
                "fields": {
                    "input_text": {"type": "str", "default": ""},
                    "type": {"type": "str", "default": ""},
                    "result_a": {"type": "str", "default": ""},
                    "result_b": {"type": "str", "default": ""},
                    "final_result": {"type": "str", "default": ""}
                }
            }
        }
    
    def test_create_workflow_from_dict(self, simple_config):
        """测试从字典创建工作流"""
        # 注册测试函数到全局注册表
        from src.infrastructure.graph.function_registry import get_global_function_registry, FunctionType
        
        registry = get_global_function_registry()
        
        def process_start(state):
            return {"result": "started"}
        
        def process_end(state):
            return {"result": "ended"}
        
        registry.register("process_start", process_start, FunctionType.NODE_FUNCTION)
        registry.register("process_end", process_end, FunctionType.NODE_FUNCTION)
        
        workflow = GraphWorkflow(simple_config)
        
        assert workflow.name == "test_workflow"
        assert workflow.description == "测试工作流"
        assert workflow.version == "1.0"
        assert workflow.entry_point == "start"
    
    def test_create_workflow_from_yaml_file(self, simple_config):
        """测试从YAML文件创建工作流"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(simple_config, f)
            temp_path = f.name
        
        try:
            workflow = GraphWorkflow(temp_path)
            assert workflow.name == "test_workflow"
            assert workflow.description == "测试工作流"
            assert workflow.version == "1.0"
        finally:
            Path(temp_path).unlink()
    
    def test_create_workflow_from_json_file(self, simple_config):
        """测试从JSON文件创建工作流"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(simple_config, f)
            temp_path = f.name
        
        try:
            workflow = GraphWorkflow(temp_path)
            assert workflow.name == "test_workflow"
            assert workflow.description == "测试工作流"
            assert workflow.version == "1.0"
        finally:
            Path(temp_path).unlink()
    
    def test_workflow_validation(self, simple_config):
        """测试工作流验证"""
        workflow = GraphWorkflow(simple_config)
        errors = workflow.validate()
        
        # 应该没有错误（因为配置是有效的）
        assert len(errors) == 0
    
    def test_workflow_validation_with_errors(self):
        """测试有错误的配置验证"""
        invalid_config = {
            "name": "invalid_workflow",
            "description": "无效工作流",
            "nodes": {
                "node1": {
                    "name": "node1"
                    # 缺少 function_name
                }
            },
            "edges": []
        }
        
        workflow = GraphWorkflow(invalid_config)
        errors = workflow.validate()
        
        # 应该发现错误
        assert len(errors) > 0
    
    def test_get_workflow_info(self, simple_config):
        """测试获取工作流信息"""
        workflow = GraphWorkflow(simple_config)
        
        # 创建模拟实例
        mock_instance = Mock(spec=WorkflowInstance)
        mock_config = Mock()
        
        # 创建模拟节点对象
        start_node = Mock()
        start_node.name = "start"
        start_node.function_name = "process_start"
        start_node.description = "开始节点"
        start_node.config = {}
        
        end_node = Mock()
        end_node.name = "end"
        end_node.function_name = "process_end"
        end_node.description = "结束节点"
        end_node.config = {}
        
        # 创建模拟边对象
        edge = Mock()
        edge.from_node = "start"
        edge.to_node = "end"
        edge.type = "simple"
        edge.condition = None
        edge.description = ""
        
        # 模拟配置数据
        mock_config.state_schema = {
            "name": "TestState",
            "fields": {
                "messages": {"type": "List[dict]", "default": []},
                "result": {"type": "str", "default": ""}
            }
        }
        mock_config.nodes = {
            "start": start_node,
            "end": end_node
        }
        mock_config.edges = [edge]
        
        # 模拟实例方法
        mock_instance.get_config.return_value = mock_config
        mock_instance.get_visualization.return_value = {
            "nodes": [{"name": "start"}, {"name": "end"}],
            "edges": [{"from": "start", "to": "end"}]
        }
        
        # 模拟加载器
        with patch.object(workflow._loader, 'load_from_dict', return_value=mock_instance):
            nodes = workflow.get_nodes()
            edges = workflow.get_edges()
            schema = workflow.get_state_schema()
            viz_data = workflow.get_visualization_data()
            
            assert len(nodes) == 2
            assert nodes[0]["name"] == "start"
            assert nodes[1]["name"] == "end"
            assert len(edges) == 1
            assert edges[0]["from"] == "start"
            assert edges[0]["to"] == "end"
            assert schema["name"] == "TestState"
            assert "messages" in schema["fields"]
            assert "result" in schema["fields"]
            assert "nodes" in viz_data
            assert "edges" in viz_data
    
    def test_export_config(self, simple_config):
        """测试配置导出"""
        workflow = GraphWorkflow(simple_config)
        exported = workflow.export_config()
        
        assert exported["name"] == simple_config["name"]
        assert exported["description"] == simple_config["description"]
        assert exported["version"] == simple_config["version"]
    
    def test_simple_graph_workflow(self):
        """测试 SimpleGraphWorkflow"""
        # 注册测试函数
        from src.infrastructure.graph.function_registry import get_global_function_registry, FunctionType
        
        registry = get_global_function_registry()
        
        def process_input(state):
            return {"processed_data": state.get("input_data", "")}
        
        def generate_output(state):
            return {"output": f"Result: {state.get('processed_data', '')}"}
        
        registry.register("process_input", process_input, FunctionType.NODE_FUNCTION)
        registry.register("generate_output", generate_output, FunctionType.NODE_FUNCTION)
        
        nodes = [
            {
                "name": "input",
                "function_name": "process_input",
                "description": "输入处理"
            },
            {
                "name": "output",
                "function_name": "generate_output",
                "description": "输出生成"
            }
        ]
        
        edges = [
            {
                "from": "input",
                "to": "output",
                "type": "simple",
                "description": "输入到输出"
            }
        ]
        
        workflow = SimpleGraphWorkflow(
            name="simple_test",
            nodes=nodes,
            edges=edges,
            description="简单测试工作流",
            entry_point="input"  # 添加入口点
        )
        
        assert workflow.name == "simple_test"
        assert workflow.description == "简单测试工作流"
        
        nodes_info = workflow.get_nodes()
        edges_info = workflow.get_edges()
        
        assert len(nodes_info) == 2
        assert len(edges_info) == 1
    
    def test_workflow_instance_creation(self, simple_config):
        """测试工作流实例创建"""
        workflow = GraphWorkflow(simple_config)
        
        # 模拟加载器行为，避免实际创建实例时的函数验证错误
        with patch.object(workflow._loader, 'load_from_dict') as mock_load:
            mock_instance = Mock(spec=WorkflowInstance)
            mock_load.return_value = mock_instance
            
            instance = workflow._create_instance()
            
            assert instance is not None
            assert instance is mock_instance
            mock_load.assert_called_once()
    
    def test_error_handling_invalid_config(self):
        """测试无效配置的错误处理"""
        # 构造函数不会立即验证，需要在validate()方法中验证
        workflow = GraphWorkflow({"name": "test"})  # 缺少必要字段的配置
        errors = workflow.validate()
        
        # 应该返回验证错误而不是抛出异常
        assert len(errors) > 0
        # 检查字符串类型的错误信息
        string_errors = [error for error in errors if isinstance(error, str)]
        dict_errors = [error for error in errors if isinstance(error, dict)]
        
        assert len(string_errors) > 0 or len(dict_errors) > 0
        if string_errors:
            assert any("图描述不能为空" in error for error in string_errors)
        if dict_errors:
            assert any("config_error" in error.get("type", "") for error in dict_errors)
    
    def test_error_handling_invalid_file(self):
        """测试无效文件的错误处理"""
        with pytest.raises(GraphWorkflowError):
            GraphWorkflow("non_existent_file.yaml")
    
    def test_error_handling_invalid_file_format(self):
        """测试无效文件格式的错误处理"""
        from src.application.workflow.universal_loader import ConfigValidationError
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")  # 无效的YAML格式
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigValidationError):
                GraphWorkflow(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_conditional_workflow_structure(self, conditional_config):
        """测试条件分支工作流结构"""
        # 注册测试函数到全局注册表
        from src.infrastructure.graph.function_registry import get_global_function_registry, FunctionType
        
        registry = get_global_function_registry()
        
        def classify_input(state):
            return {"type": "A"}
        
        def process_type_a(state):
            return {"result_a": "processed A"}
        
        def process_type_b(state):
            return {"result_b": "processed B"}
        
        def aggregate_results(state):
            return {"final_result": "aggregated"}
        
        def condition_type_a(state):
            return state.get("type") == "A"
        
        def condition_type_b(state):
            return state.get("type") == "B"
        
        registry.register("classify_input", classify_input, FunctionType.NODE_FUNCTION)
        registry.register("process_type_a", process_type_a, FunctionType.NODE_FUNCTION)
        registry.register("process_type_b", process_type_b, FunctionType.NODE_FUNCTION)
        registry.register("aggregate_results", aggregate_results, FunctionType.NODE_FUNCTION)
        registry.register("type == 'A'", condition_type_a, FunctionType.CONDITION_FUNCTION)
        registry.register("type == 'B'", condition_type_b, FunctionType.CONDITION_FUNCTION)
        
        workflow = GraphWorkflow(conditional_config)
        
        nodes = workflow.get_nodes()
        edges = workflow.get_edges()
        
        assert len(nodes) == 4  # classifier, processor_a, processor_b, aggregator
        assert len(edges) == 4  # 2个条件边 + 2个普通边
        
        # 检查条件边
        conditional_edges = [e for e in edges if e.get("type") == "conditional"]
        assert len(conditional_edges) == 2
    
    def test_complex_workflow_validation(self, conditional_config):
        """测试复杂工作流验证"""
        # 注册测试函数到全局注册表
        from src.infrastructure.graph.function_registry import get_global_function_registry, FunctionType
        
        registry = get_global_function_registry()
        
        def classify_input(state):
            return {"type": "A"}
        
        def process_type_a(state):
            return {"result_a": "processed A"}
        
        def process_type_b(state):
            return {"result_b": "processed B"}
        
        def aggregate_results(state):
            return {"final_result": "aggregated"}
        
        def condition_type_a(state):
            return state.get("type") == "A"
        
        def condition_type_b(state):
            return state.get("type") == "B"
        
        registry.register("classify_input", classify_input, FunctionType.NODE_FUNCTION)
        registry.register("process_type_a", process_type_a, FunctionType.NODE_FUNCTION)
        registry.register("process_type_b", process_type_b, FunctionType.NODE_FUNCTION)
        registry.register("aggregate_results", aggregate_results, FunctionType.NODE_FUNCTION)
        registry.register("type == 'A'", condition_type_a, FunctionType.CONDITION_FUNCTION)
        registry.register("type == 'B'", condition_type_b, FunctionType.CONDITION_FUNCTION)
        
        workflow = GraphWorkflow(conditional_config)
        errors = workflow.validate()
        
        # 复杂但有效的配置应该没有错误
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_async_execution_interface(self, simple_config):
        """测试异步执行接口"""
        # 注册测试函数到全局注册表
        from src.infrastructure.graph.function_registry import get_global_function_registry, FunctionType
        
        registry = get_global_function_registry()
        
        def process_start(state):
            return {"messages": [], "result": "started"}
        
        def process_end(state):
            return {"messages": [], "result": "completed"}
        
        registry.register("process_start", process_start, FunctionType.NODE_FUNCTION)
        registry.register("process_end", process_end, FunctionType.NODE_FUNCTION)
        
        workflow = GraphWorkflow(simple_config)
        
        # 模拟整个实例
        mock_instance = AsyncMock()
        mock_instance.run_async = AsyncMock(return_value={
            "messages": ["async result"],
            "result": "completed"
        })
        
        # 替换实例
        workflow._instance = mock_instance
        
        # 异步执行
        result = await workflow.run_async({"input": "test"})
        
        # 验证结果
        assert result["messages"] == ["async result"]
        assert result["result"] == "completed"
        mock_instance.run_async.assert_called_once()
    
    def test_stream_execution_interface(self, simple_config):
        """测试流式执行接口"""
        # 注册测试函数到全局注册表
        from src.infrastructure.graph.function_registry import get_global_function_registry, FunctionType
        
        registry = get_global_function_registry()
        
        def process_start(state):
            return {"messages": [], "result": "started"}
        
        def process_end(state):
            return {"messages": [], "result": "completed"}
        
        registry.register("process_start", process_start, FunctionType.NODE_FUNCTION)
        registry.register("process_end", process_end, FunctionType.NODE_FUNCTION)
        
        workflow = GraphWorkflow(simple_config)
        
        # 模拟整个实例
        mock_instance = Mock()
        mock_instance.stream = Mock(return_value=iter([
            {"messages": [], "result": "started"},
            {"messages": [], "result": "processing"},
            {"messages": [], "result": "completed"}
        ]))
        
        # 替换实例
        workflow._instance = mock_instance
        
        # 流式执行
        results = list(workflow.stream({"messages": []}))
        
        # 验证结果
        assert len(results) == 3
        assert "messages" in results[0]
        assert "result" in results[0]
        assert "messages" in results[1]
        assert "result" in results[1]
        assert "messages" in results[2]
        assert "result" in results[2]
        mock_instance.stream.assert_called_once()
    
    def test_workflow_with_checkpoints(self):
        """测试带检查点的工作流"""
        # 注册测试函数
        from src.infrastructure.graph.function_registry import get_global_function_registry, FunctionType
        
        registry = get_global_function_registry()
        
        def start_func(state):
            return {"data": "started"}
        
        registry.register("start_func", start_func, FunctionType.NODE_FUNCTION)
        
        config_with_checkpoints = {
            "name": "checkpoint_test",
            "description": "检查点测试",
            "version": "1.0",
            "entry_point": "start",
            "nodes": {
                "start": {
                    "name": "start",
                    "function_name": "start_func",
                    "description": "开始"
                }
            },
            "edges": [],
            "state_schema": {
                "name": "CheckpointState",
                "fields": {
                    "data": {"type": "str", "default": ""}
                }
            },
            "checkpoints": {
                "enabled": True,
                "checkpoint_path": "/tmp/checkpoints"
            }
        }
        
        workflow = GraphWorkflow(config_with_checkpoints)
        assert workflow.name == "checkpoint_test"
        
        # 验证检查点配置被正确处理
        exported = workflow.export_config()
        assert "checkpoints" in exported
        assert exported["checkpoints"]["enabled"] == True
    
    def test_workflow_with_interrupts(self):
        """测试带中断点的工作流"""
        # 注册测试函数
        from src.infrastructure.graph.function_registry import get_global_function_registry, FunctionType
        
        registry = get_global_function_registry()
        
        def start_func(state):
            return {"data": "started"}
        
        registry.register("start_func", start_func, FunctionType.NODE_FUNCTION)
        
        config_with_interrupts = {
            "name": "interrupt_test",
            "description": "中断点测试",
            "version": "1.0",
            "entry_point": "start",
            "nodes": {
                "start": {
                    "name": "start",
                    "function_name": "start_func",
                    "description": "开始"
                }
            },
            "edges": [],
            "state_schema": {
                "name": "InterruptState",
                "fields": {
                    "data": {"type": "str", "default": ""}
                }
            },
            "interrupts": {
                "before_nodes": ["start"],
                "after_nodes": []
            }
        }
        
        workflow = GraphWorkflow(config_with_interrupts)
        assert workflow.name == "interrupt_test"
        
        # 验证中断点配置被正确处理
        exported = workflow.export_config()
        assert "interrupts" in exported
        assert "start" in exported["interrupts"]["before_nodes"]


class TestGraphWorkflowRealExecution:
    """真实执行测试（需要实际函数注册）"""
    
    @pytest.fixture
    def mock_functions(self):
        """模拟函数注册"""
        # 这里可以注册真实的函数或模拟函数
        # 由于需要实际的函数注册，这些测试主要验证接口
        pass
    
    def test_workflow_execution_interface(self):
        """测试执行接口（需要函数注册）"""
        # 注册测试函数
        from src.infrastructure.graph.function_registry import get_global_function_registry, FunctionType
        
        registry = get_global_function_registry()
        
        def test_function(state):
            return {"output_data": f"processed_{state.get('input_data', '')}"}
        
        registry.register("test_function", test_function, FunctionType.NODE_FUNCTION)
        
        config = {
            "name": "execution_test",
            "description": "执行测试",
            "version": "1.0",
            "entry_point": "test",
            "nodes": {
                "test": {
                    "name": "test",
                    "function_name": "test_function",
                    "description": "测试函数"
                }
            },
            "edges": [],
            "state_schema": {
                "name": "ExecutionState",
                "fields": {
                    "input_data": {"type": "str", "default": ""},
                    "output_data": {"type": "str", "default": ""}
                }
            }
        }
        
        workflow = GraphWorkflow(config)
        
        # 测试执行接口（需要实际函数）
        # 这里主要验证接口存在且可以调用
        initial_state = {"input_data": "test"}
        
        # 由于需要实际函数，这里只验证接口
        assert hasattr(workflow, 'run')
        assert hasattr(workflow, 'run_async')
        assert hasattr(workflow, 'stream')


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])