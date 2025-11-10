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
from unittest.mock import Mock, patch

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
        
        nodes = workflow.get_nodes()
        edges = workflow.get_edges()
        schema = workflow.get_state_schema()
        viz_data = workflow.get_visualization_data()
        
        assert len(nodes) == 2
        assert len(edges) == 1
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
                "type": "simple"
            }
        ]
        
        workflow = SimpleGraphWorkflow(
            name="simple_test",
            nodes=nodes,
            edges=edges,
            description="简单测试工作流"
        )
        
        assert workflow.name == "simple_test"
        assert workflow.description == "简单测试工作流"
        
        nodes_info = workflow.get_nodes()
        edges_info = workflow.get_edges()
        
        assert len(nodes_info) == 2
        assert len(edges_info) == 1
    
    @patch('src.application.workflow.universal_loader.WorkflowInstance')
    def test_workflow_instance_creation(self, mock_instance, simple_config):
        """测试工作流实例创建"""
        workflow = GraphWorkflow(simple_config)
        
        # 模拟 WorkflowInstance
        mock_instance.return_value = Mock(spec=WorkflowInstance)
        
        instance = workflow._create_instance()
        
        assert instance is not None
        mock_instance.assert_called_once()
    
    def test_error_handling_invalid_config(self):
        """测试无效配置的错误处理"""
        with pytest.raises(GraphWorkflowConfigError):
            GraphWorkflow({})  # 空配置
    
    def test_error_handling_invalid_file(self):
        """测试无效文件的错误处理"""
        with pytest.raises(GraphWorkflowError):
            GraphWorkflow("non_existent_file.yaml")
    
    def test_error_handling_invalid_file_format(self):
        """测试无效文件格式的错误处理"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("invalid content")
            temp_path = f.name
        
        try:
            with pytest.raises(GraphWorkflowError):
                GraphWorkflow(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_conditional_workflow_structure(self, conditional_config):
        """测试条件分支工作流结构"""
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
        workflow = GraphWorkflow(conditional_config)
        errors = workflow.validate()
        
        # 复杂但有效的配置应该没有错误
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_async_execution_interface(self, simple_config):
        """测试异步执行接口"""
        workflow = GraphWorkflow(simple_config)
        
        # 模拟异步执行
        with patch.object(workflow, '_create_instance') as mock_create:
            mock_instance = Mock()
            mock_instance.run_async = Mock(return_value=asyncio.Future())
            mock_instance.run_async.return_value.set_result({"result": "success"})
            mock_create.return_value = mock_instance
            
            result = await workflow.run_async({"messages": []})
            
            assert result == {"result": "success"}
            mock_instance.run_async.assert_called_once()
    
    def test_stream_execution_interface(self, simple_config):
        """测试流式执行接口"""
        workflow = GraphWorkflow(simple_config)
        
        # 模拟流式执行
        with patch.object(workflow, '_create_instance') as mock_create:
            mock_instance = Mock()
            mock_instance.stream = Mock(return_value=iter([{"step": 1}, {"step": 2}]))
            mock_create.return_value = mock_instance
            
            results = list(workflow.stream({"messages": []}))
            
            assert len(results) == 2
            assert results[0]["step"] == 1
            assert results[1]["step"] == 2
            mock_instance.stream.assert_called_once()
    
    def test_workflow_with_checkpoints(self):
        """测试带检查点的工作流"""
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