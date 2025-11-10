"""
GraphWorkflow 配置测试

测试各种配置场景下的 GraphWorkflow 行为。
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path

from src.application.workflow.graph_workflow import (
    GraphWorkflow,
    GraphWorkflowConfigError
)


class TestGraphWorkflowConfig:
    """GraphWorkflow 配置测试类"""
    
    def test_minimal_valid_config(self):
        """测试最小有效配置"""
        minimal_config = {
            "name": "minimal",
            "nodes": {
                "start": {
                    "name": "start",
                    "function_name": "start_func"
                }
            },
            "edges": [],
            "state_schema": {
                "name": "MinimalState",
                "fields": {
                    "data": {"type": "str", "default": ""}
                }
            }
        }
        
        workflow = GraphWorkflow(minimal_config)
        assert workflow.name == "minimal"
        assert workflow.description == ""  # 默认空描述
        assert workflow.version == "1.0"  # 默认版本
        assert workflow.entry_point == "start"  # 默认入口点
    
    def test_complete_config(self):
        """测试完整配置"""
        complete_config = {
            "name": "complete_workflow",
            "description": "完整配置工作流",
            "version": "2.0",
            "entry_point": "main",
            "nodes": {
                "main": {
                    "name": "main",
                    "function_name": "main_function",
                    "description": "主节点",
                    "config": {"param": "value"}
                }
            },
            "edges": [],
            "state_schema": {
                "name": "CompleteState",
                "fields": {
                    "input": {"type": "str", "default": ""},
                    "output": {"type": "str", "default": ""},
                    "metadata": {"type": "dict", "default": {}}
                }
            },
            "checkpoints": {
                "enabled": True,
                "checkpoint_path": "/tmp/checkpoints"
            },
            "interrupts": {
                "before_nodes": ["main"],
                "after_nodes": []
            },
            "config": {
                "recursive_limit": 100,
                "timeout": 300
            }
        }
        
        workflow = GraphWorkflow(complete_config)
        assert workflow.name == "complete_workflow"
        assert workflow.description == "完整配置工作流"
        assert workflow.version == "2.0"
        assert workflow.entry_point == "main"
        
        # 验证导出的配置包含所有字段
        exported = workflow.export_config()
        assert exported["checkpoints"]["enabled"] == True
        assert exported["interrupts"]["before_nodes"] == ["main"]
        assert exported["config"]["recursive_limit"] == 100
    
    def test_config_with_complex_state(self):
        """测试复杂状态模式配置"""
        complex_config = {
            "name": "complex_state_workflow",
            "nodes": {
                "processor": {
                    "name": "processor",
                    "function_name": "process_data"
                }
            },
            "edges": [],
            "state_schema": {
                "name": "ComplexState",
                "fields": {
                    "messages": {"type": "List[dict]", "default": []},
                    "nested_data": {
                        "type": "dict",
                        "default": {"key": "value"}
                    },
                    "optional_field": {"type": "str", "default": None},
                    "counter": {"type": "int", "default": 0},
                    "flag": {"type": "bool", "default": False}
                }
            }
        }
        
        workflow = GraphWorkflow(complex_config)
        schema = workflow.get_state_schema()
        
        assert schema["name"] == "ComplexState"
        assert len(schema["fields"]) == 5
        assert schema["fields"]["messages"]["type"] == "List[dict]"
        assert schema["fields"]["counter"]["default"] == 0
        assert schema["fields"]["flag"]["default"] is False
    
    def test_config_with_multiple_nodes_and_edges(self):
        """测试多节点多边的配置"""
        multi_config = {
            "name": "multi_node_workflow",
            "nodes": {
                "input": {
                    "name": "input",
                    "function_name": "input_func"
                },
                "processor1": {
                    "name": "processor1",
                    "function_name": "process1_func"
                },
                "processor2": {
                    "name": "processor2",
                    "function_name": "process2_func"
                },
                "aggregator": {
                    "name": "aggregator",
                    "function_name": "aggregate_func"
                }
            },
            "edges": [
                {
                    "from": "input",
                    "to": "processor1",
                    "type": "simple"
                },
                {
                    "from": "input",
                    "to": "processor2",
                    "type": "simple"
                },
                {
                    "from": "processor1",
                    "to": "aggregator",
                    "type": "simple"
                },
                {
                    "from": "processor2",
                    "to": "aggregator",
                    "type": "simple"
                }
            ],
            "state_schema": {
                "name": "MultiNodeState",
                "fields": {
                    "input_data": {"type": "str", "default": ""},
                    "result1": {"type": "str", "default": ""},
                    "result2": {"type": "str", "default": ""},
                    "final_result": {"type": "str", "default": ""}
                }
            }
        }
        
        workflow = GraphWorkflow(multi_config)
        nodes = workflow.get_nodes()
        edges = workflow.get_edges()
        
        assert len(nodes) == 4
        assert len(edges) == 4
        
        # 验证边的结构
        input_edges = [e for e in edges if e["from"] == "input"]
        assert len(input_edges) == 2
        
        aggregator_edges = [e for e in edges if e["to"] == "aggregator"]
        assert len(aggregator_edges) == 2
    
    def test_config_with_conditional_edges(self):
        """测试条件边配置"""
        conditional_config = {
            "name": "conditional_workflow",
            "nodes": {
                "classifier": {
                    "name": "classifier",
                    "function_name": "classify"
                },
                "type_a_processor": {
                    "name": "type_a_processor",
                    "function_name": "process_type_a"
                },
                "type_b_processor": {
                    "name": "type_b_processor",
                    "function_name": "process_type_b"
                }
            },
            "edges": [
                {
                    "from": "classifier",
                    "to": "type_a_processor",
                    "type": "conditional",
                    "condition": "type == 'A'"
                },
                {
                    "from": "classifier",
                    "to": "type_b_processor",
                    "type": "conditional",
                    "condition": "type == 'B'"
                }
            ],
            "state_schema": {
                "name": "ConditionalState",
                "fields": {
                    "input": {"type": "str", "default": ""},
                    "type": {"type": "str", "default": ""}
                }
            }
        }
        
        workflow = GraphWorkflow(conditional_config)
        edges = workflow.get_edges()
        
        conditional_edges = [e for e in edges if e.get("type") == "conditional"]
        assert len(conditional_edges) == 2
        
        # 验证条件表达式
        assert conditional_edges[0]["condition"] == "type == 'A'"
        assert conditional_edges[1]["condition"] == "type == 'B'"
    
    def test_config_validation_errors(self):
        """测试配置验证错误"""
        # 缺少必要字段
        with pytest.raises(GraphWorkflowConfigError):
            GraphWorkflow({"name": "invalid"})
        
        # 空的节点配置
        with pytest.raises(GraphWorkflowConfigError):
            GraphWorkflow({
                "name": "invalid",
                "nodes": {},
                "edges": [],
                "state_schema": {"name": "State", "fields": {}}
            })
        
        # 无效的状态模式
        with pytest.raises(GraphWorkflowConfigError):
            GraphWorkflow({
                "name": "invalid",
                "nodes": {"node": {"name": "node", "function_name": "func"}},
                "edges": [],
                "state_schema": {"name": "State"}  # 缺少 fields
            })
    
    def test_file_config_loading(self):
        """测试文件配置加载"""
        config = {
            "name": "file_test",
            "nodes": {
                "test": {
                    "name": "test",
                    "function_name": "test_func"
                }
            },
            "edges": [],
            "state_schema": {
                "name": "FileTestState",
                "fields": {
                    "data": {"type": "str", "default": ""}
                }
            }
        }
        
        # 测试 YAML 文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            yaml_path = f.name
        
        try:
            workflow_yaml = GraphWorkflow(yaml_path)
            assert workflow_yaml.name == "file_test"
        finally:
            Path(yaml_path).unlink()
        
        # 测试 JSON 文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            json_path = f.name
        
        try:
            workflow_json = GraphWorkflow(json_path)
            assert workflow_json.name == "file_test"
        finally:
            Path(json_path).unlink()
    
    def test_config_with_cycles(self):
        """测试循环配置"""
        cycle_config = {
            "name": "cycle_workflow",
            "nodes": {
                "start": {
                    "name": "start",
                    "function_name": "start_func"
                },
                "processor": {
                    "name": "processor",
                    "function_name": "process_func"
                },
                "checker": {
                    "name": "checker",
                    "function_name": "check_func"
                }
            },
            "edges": [
                {
                    "from": "start",
                    "to": "processor",
                    "type": "simple"
                },
                {
                    "from": "processor",
                    "to": "checker",
                    "type": "simple"
                },
                {
                    "from": "checker",
                    "to": "processor",
                    "type": "conditional",
                    "condition": "continue == true"
                }
            ],
            "state_schema": {
                "name": "CycleState",
                "fields": {
                    "data": {"type": "str", "default": ""},
                    "continue": {"type": "bool", "default": True}
                }
            }
        }
        
        workflow = GraphWorkflow(cycle_config)
        edges = workflow.get_edges()
        
        # 验证循环边
        cycle_edges = [e for e in edges if e["from"] == "checker" and e["to"] == "processor"]
        assert len(cycle_edges) == 1
        assert cycle_edges[0]["type"] == "conditional"
    
    def test_config_with_parallel_structure(self):
        """测试并行结构配置"""
        parallel_config = {
            "name": "parallel_workflow",
            "nodes": {
                "splitter": {
                    "name": "splitter",
                    "function_name": "split_func"
                },
                "worker_a": {
                    "name": "worker_a",
                    "function_name": "work_a_func"
                },
                "worker_b": {
                    "name": "worker_b",
                    "function_name": "work_b_func"
                },
                "worker_c": {
                    "name": "worker_c",
                    "function_name": "work_c_func"
                },
                "aggregator": {
                    "name": "aggregator",
                    "function_name": "aggregate_func"
                }
            },
            "edges": [
                {
                    "from": "splitter",
                    "to": "worker_a",
                    "type": "simple"
                },
                {
                    "from": "splitter",
                    "to": "worker_b",
                    "type": "simple"
                },
                {
                    "from": "splitter",
                    "to": "worker_c",
                    "type": "simple"
                },
                {
                    "from": "worker_a",
                    "to": "aggregator",
                    "type": "simple"
                },
                {
                    "from": "worker_b",
                    "to": "aggregator",
                    "type": "simple"
                },
                {
                    "from": "worker_c",
                    "to": "aggregator",
                    "type": "simple"
                }
            ],
            "state_schema": {
                "name": "ParallelState",
                "fields": {
                    "input_data": {"type": "str", "default": ""},
                    "result_a": {"type": "str", "default": ""},
                    "result_b": {"type": "str", "default": ""},
                    "result_c": {"type": "str", "default": ""},
                    "final_result": {"type": "str", "default": ""}
                }
            }
        }
        
        workflow = GraphWorkflow(parallel_config)
        edges = workflow.get_edges()
        
        # 验证并行边
        splitter_edges = [e for e in edges if e["from"] == "splitter"]
        assert len(splitter_edges) == 3
        
        aggregator_edges = [e for e in edges if e["to"] == "aggregator"]
        assert len(aggregator_edges) == 3
    
    def test_config_export_import_consistency(self):
        """测试配置导出导入一致性"""
        original_config = {
            "name": "consistency_test",
            "description": "一致性测试",
            "version": "1.5",
            "entry_point": "main",
            "nodes": {
                "main": {
                    "name": "main",
                    "function_name": "main_func",
                    "config": {"param": "value"}
                }
            },
            "edges": [],
            "state_schema": {
                "name": "ConsistencyState",
                "fields": {
                    "data": {"type": "str", "default": "test"}
                }
            },
            "checkpoints": {
                "enabled": True,
                "checkpoint_path": "/tmp/check"
            }
        }
        
        # 创建工作流
        workflow1 = GraphWorkflow(original_config)
        
        # 导出配置
        exported_config = workflow1.export_config()
        
        # 从导出的配置创建新工作流
        workflow2 = GraphWorkflow(exported_config)
        
        # 验证一致性
        assert workflow1.name == workflow2.name
        assert workflow1.description == workflow2.description
        assert workflow1.version == workflow2.version
        
        # 验证状态模式一致性
        schema1 = workflow1.get_state_schema()
        schema2 = workflow2.get_state_schema()
        assert schema1["name"] == schema2["name"]
        assert schema1["fields"] == schema2["fields"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])