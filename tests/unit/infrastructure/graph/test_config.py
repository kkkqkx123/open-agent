"""图配置单元测试"""

import pytest
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from src.infrastructure.graph.config import (
    EdgeType,
    StateFieldConfig,
    GraphStateConfig,
    NodeConfig,
    EdgeConfig,
    GraphConfig
)


class TestEdgeType:
    """边类型枚举测试"""

    def test_edge_type_values(self):
        """测试边类型枚举值"""
        assert EdgeType.SIMPLE.value == "simple"
        assert EdgeType.CONDITIONAL.value == "conditional"

    def test_edge_type_members(self):
        """测试边类型枚举成员"""
        assert EdgeType.SIMPLE.name == "SIMPLE"
        assert EdgeType.CONDITIONAL.name == "CONDITIONAL"


class TestStateFieldConfig:
    """状态字段配置测试"""

    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        config = StateFieldConfig(type="str")
        assert config.type == "str"
        assert config.default is None
        assert config.reducer is None
        assert config.description is None

    def test_init_with_all_params(self):
        """测试使用所有参数初始化"""
        config = StateFieldConfig(
            type="int",
            default=42,
            reducer="operator.add",
            description="测试字段"
        )
        assert config.type == "int"
        assert config.default == 42
        assert config.reducer == "operator.add"
        assert config.description == "测试字段"


class TestGraphStateConfig:
    """图状态配置测试"""

    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        config = GraphStateConfig(name="TestState")
        assert config.name == "TestState"
        assert config.fields == {}

    def test_init_with_fields(self):
        """测试使用字段初始化"""
        fields = {
            "test_field": StateFieldConfig(type="str", default="test")
        }
        config = GraphStateConfig(name="TestState", fields=fields)
        assert config.name == "TestState"
        assert config.fields == fields

    def test_to_typed_dict_class(self):
        """测试转换为TypedDict类"""
        fields = {
            "messages": StateFieldConfig(type="List[str]", reducer="operator.add"),
            "input": StateFieldConfig(type="str")
        }
        config = GraphStateConfig(name="TestState", fields=fields)
        
        typed_dict_class = config.to_typed_dict_class()
        assert typed_dict_class.__name__ == "TestState"
        assert hasattr(typed_dict_class, "__annotations__")

    def test_parse_type_string(self):
        """测试解析类型字符串"""
        config = GraphStateConfig(name="TestState")
        
        # 测试支持的类型
        assert config._parse_type_string("str") == str
        assert config._parse_type_string("int") == int
        assert config._parse_type_string("float") == float
        assert config._parse_type_string("bool") == bool
        assert config._parse_type_string("list") == list
        assert config._parse_type_string("dict") == dict
        assert config._parse_type_string("List[str]") == List[str]
        assert config._parse_type_string("List[int]") == List[int]
        assert config._parse_type_string("List[dict]") == List[Dict[str, Any]]
        assert config._parse_type_string("Dict[str, Any]") == Dict[str, Any]
        
        # 测试未知类型
        assert config._parse_type_string("unknown") == str

    def test_get_reducer_function(self):
        """测试获取reducer函数"""
        config = GraphStateConfig(name="TestState")
        
        # 测试支持的reducer
        import operator
        assert config._get_reducer_function("operator.add") == operator.add
        assert config._get_reducer_function("operator.or_") == operator.or_
        assert config._get_reducer_function("operator.and_") == operator.and_
        assert config._get_reducer_function("append") is not None
        assert config._get_reducer_function("extend") is not None
        assert config._get_reducer_function("replace") is not None
        
        # 测试未知reducer
        assert config._get_reducer_function("unknown") == operator.add


class TestNodeConfig:
    """节点配置测试"""

    def test_init_with_required_params(self):
        """测试使用必需参数初始化"""
        config = NodeConfig(name="test_node", function_name="test_function")
        assert config.name == "test_node"
        assert config.function_name == "test_function"
        assert config.config == {}
        assert config.description is None
        assert config.input_state is None
        assert config.output_state is None

    def test_init_with_all_params(self):
        """测试使用所有参数初始化"""
        config = NodeConfig(
            name="test_node",
            function_name="test_function",
            config={"param": "value"},
            description="测试节点",
            input_state="InputState",
            output_state="OutputState"
        )
        assert config.name == "test_node"
        assert config.function_name == "test_function"
        assert config.config == {"param": "value"}
        assert config.description == "测试节点"
        assert config.input_state == "InputState"
        assert config.output_state == "OutputState"

    def test_from_dict_with_function_key(self):
        """测试从字典创建（使用function键）"""
        data = {
            "name": "test_node",
            "function": "test_function",
            "config": {"param": "value"},
            "description": "测试节点"
        }
        config = NodeConfig.from_dict(data)
        assert config.name == "test_node"
        assert config.function_name == "test_function"
        assert config.config == {"param": "value"}
        assert config.description == "测试节点"

    def test_from_dict_with_type_key(self):
        """测试从字典创建（使用type键）"""
        data = {
            "name": "test_node",
            "type": "test_function",
            "config": {"param": "value"}
        }
        config = NodeConfig.from_dict(data)
        assert config.name == "test_node"
        assert config.function_name == "test_function"
        assert config.config == {"param": "value"}


class TestEdgeConfig:
    """边配置测试"""

    def test_init_with_required_params(self):
        """测试使用必需参数初始化"""
        config = EdgeConfig(
            from_node="node1",
            to_node="node2",
            type=EdgeType.SIMPLE
        )
        assert config.from_node == "node1"
        assert config.to_node == "node2"
        assert config.type == EdgeType.SIMPLE
        assert config.condition is None
        assert config.description is None
        assert config.path_map is None

    def test_init_with_all_params(self):
        """测试使用所有参数初始化"""
        config = EdgeConfig(
            from_node="node1",
            to_node="node2",
            type=EdgeType.CONDITIONAL,
            condition="test_condition",
            description="测试边",
            path_map={"path1": "value1", "path2": "value2"}
        )
        assert config.from_node == "node1"
        assert config.to_node == "node2"
        assert config.type == EdgeType.CONDITIONAL
        assert config.condition == "test_condition"
        assert config.description == "测试边"
        assert config.path_map == {"path1": "value1", "path2": "value2"}

    def test_from_dict_with_simple_edge(self):
        """测试从字典创建简单边"""
        data = {
            "from": "node1",
            "to": "node2",
            "type": "simple"
        }
        config = EdgeConfig.from_dict(data)
        assert config.from_node == "node1"
        assert config.to_node == "node2"
        assert config.type == EdgeType.SIMPLE

    def test_from_dict_with_conditional_edge(self):
        """测试从字典创建条件边"""
        data = {
            "from": "node1",
            "to": "node2",
            "type": "conditional",
            "condition": "test_condition"
        }
        config = EdgeConfig.from_dict(data)
        assert config.from_node == "node1"
        assert config.to_node == "node2"
        assert config.type == EdgeType.CONDITIONAL
        assert config.condition == "test_condition"

    def test_to_dict(self):
        """测试转换为字典"""
        config = EdgeConfig(
            from_node="node1",
            to_node="node2",
            type=EdgeType.CONDITIONAL,
            condition="test_condition",
            description="测试边",
            path_map={"path1": "value1", "path2": "value2"}
        )
        result = config.to_dict()
        expected = {
            "from": "node1",
            "to": "node2",
            "type": "conditional",
            "condition": "test_condition",
            "description": "测试边",
            "path_map": {"path1": "value1", "path2": "value2"}
        }
        assert result == expected


class TestGraphConfig:
    """图配置测试"""

    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        config = GraphConfig(
            name="test_graph",
            description="测试图"
        )
        assert config.name == "test_graph"
        assert config.description == "测试图"
        assert config.version == "1.0"
        assert isinstance(config.state_schema, GraphStateConfig)
        assert config.nodes == {}
        assert config.edges == []
        assert config.entry_point is None
        assert config.checkpointer is None
        assert config.interrupt_before is None
        assert config.interrupt_after is None
        assert config.additional_config == {}

    def test_init_with_all_params(self):
        """测试使用所有参数初始化"""
        state_schema = GraphStateConfig(name="TestState")
        nodes = {
            "node1": NodeConfig(name="node1", function_name="func1")
        }
        edges = [
            EdgeConfig(from_node="node1", to_node="node2", type=EdgeType.SIMPLE)
        ]
        
        config = GraphConfig(
            name="test_graph",
            description="测试图",
            version="2.0",
            state_schema=state_schema,
            nodes=nodes,
            edges=edges,
            entry_point="node1",
            checkpointer="memory",
            interrupt_before=["node1"],
            interrupt_after=["node2"],
            additional_config={"custom": "value"}
        )
        assert config.name == "test_graph"
        assert config.description == "测试图"
        assert config.version == "2.0"
        assert config.state_schema == state_schema
        assert config.nodes == nodes
        assert config.edges == edges
        assert config.entry_point == "node1"
        assert config.checkpointer == "memory"
        assert config.interrupt_before == ["node1"]
        assert config.interrupt_after == ["node2"]
        assert config.additional_config == {"custom": "value"}

    def test_from_dict_with_minimal_data(self):
        """测试从最小数据字典创建"""
        data = {
            "name": "test_graph",
            "description": "测试图"
        }
        config = GraphConfig.from_dict(data)
        assert config.name == "test_graph"
        assert config.description == "测试图"
        assert config.version == "1.0"
        assert isinstance(config.state_schema, GraphStateConfig)
        assert config.nodes == {}
        assert config.edges == []

    def test_from_dict_with_full_data(self):
        """测试从完整数据字典创建"""
        data = {
            "name": "test_graph",
            "description": "测试图",
            "version": "2.0",
            "state_schema": {
                "name": "TestState",
                "fields": {
                    "messages": {
                        "type": "List[str]",
                        "reducer": "operator.add"
                    }
                }
            },
            "nodes": {
                "node1": {
                    "function": "func1",
                    "config": {"param": "value"}
                }
            },
            "edges": [
                {
                    "from": "node1",
                    "to": "node2",
                    "type": "simple"
                }
            ],
            "entry_point": "node1",
            "checkpointer": "memory",
            "interrupt_before": ["node1"],
            "interrupt_after": ["node2"],
            "custom_field": "custom_value"
        }
        config = GraphConfig.from_dict(data)
        assert config.name == "test_graph"
        assert config.description == "测试图"
        assert config.version == "2.0"
        assert config.state_schema.name == "TestState"
        assert "messages" in config.state_schema.fields
        assert len(config.nodes) == 1
        assert "node1" in config.nodes
        assert len(config.edges) == 1
        assert config.entry_point == "node1"
        assert config.checkpointer == "memory"
        assert config.interrupt_before == ["node1"]
        assert config.interrupt_after == ["node2"]
        assert config.additional_config == {"custom_field": "custom_value"}

    def test_model_dump(self):
        """测试模型转储"""
        config = GraphConfig(
            name="test_graph",
            description="测试图"
        )
        result = config.model_dump()
        assert isinstance(result, dict)
        assert result["name"] == "test_graph"
        assert result["description"] == "测试图"

    def test_to_dict(self):
        """测试转换为字典"""
        config = GraphConfig(
            name="test_graph",
            description="测试图"
        )
        result = config.to_dict()
        assert isinstance(result, dict)
        assert result["name"] == "test_graph"
        assert result["description"] == "测试图"

    def test_validate_success(self):
        """测试验证成功"""
        state_schema = GraphStateConfig(
            name="TestState",
            fields={
                "messages": StateFieldConfig(type="List[str]", reducer="operator.add")
            }
        )
        nodes = {
            "node1": NodeConfig(name="node1", function_name="func1"),
            "node2": NodeConfig(name="node2", function_name="func2")
        }
        edges = [
            EdgeConfig(from_node="node1", to_node="node2", type=EdgeType.SIMPLE)
        ]
        
        config = GraphConfig(
            name="test_graph",
            description="测试图",
            state_schema=state_schema,
            nodes=nodes,
            edges=edges,
            entry_point="node1"
        )
        errors = config.validate()
        assert errors == []

    def test_validate_missing_name(self):
        """测试验证缺少名称"""
        config = GraphConfig(
            name="",
            description="测试图"
        )
        errors = config.validate()
        assert "图名称不能为空" in errors

    def test_validate_missing_description(self):
        """测试验证缺少描述"""
        config = GraphConfig(
            name="test_graph",
            description=""
        )
        errors = config.validate()
        assert "图描述不能为空" in errors

    def test_validate_no_nodes(self):
        """测试验证没有节点"""
        config = GraphConfig(
            name="test_graph",
            description="测试图"
        )
        errors = config.validate()
        assert "图必须至少包含一个节点" in errors

    def test_validate_missing_state_schema(self):
        """测试验证缺少状态模式"""
        config = GraphConfig(
            name="test_graph",
            description="测试图",
            nodes={
                "node1": NodeConfig(name="node1", function_name="func1")
            }
        )
        errors = config.validate()
        assert "图必须定义状态模式" in errors

    def test_validate_edge_from_node_not_exists(self):
        """测试验证边的起始节点不存在"""
        nodes = {
            "node1": NodeConfig(name="node1", function_name="func1")
        }
        edges = [
            EdgeConfig(from_node="node2", to_node="node1", type=EdgeType.SIMPLE)
        ]
        
        config = GraphConfig(
            name="test_graph",
            description="测试图",
            nodes=nodes,
            edges=edges
        )
        errors = config.validate()
        assert "边的起始节点 'node2' 不存在" in errors

    def test_validate_edge_to_node_not_exists(self):
        """测试验证边的目标节点不存在"""
        nodes = {
            "node1": NodeConfig(name="node1", function_name="func1")
        }
        edges = [
            EdgeConfig(from_node="node1", to_node="node2", type=EdgeType.SIMPLE)
        ]
        
        config = GraphConfig(
            name="test_graph",
            description="测试图",
            nodes=nodes,
            edges=edges
        )
        errors = config.validate()
        assert "边的目标节点 'node2' 不存在" in errors

    def test_validate_conditional_edge_missing_condition(self):
        """测试验证条件边缺少条件表达式"""
        nodes = {
            "node1": NodeConfig(name="node1", function_name="func1"),
            "node2": NodeConfig(name="node2", function_name="func2")
        }
        edges = [
            EdgeConfig(from_node="node1", to_node="node2", type=EdgeType.CONDITIONAL)
        ]
        
        config = GraphConfig(
            name="test_graph",
            description="测试图",
            nodes=nodes,
            edges=edges
        )
        errors = config.validate()
        assert "条件边 'node1' -> 'node2' 缺少条件表达式" in errors

    def test_validate_entry_point_not_exists(self):
        """测试验证入口节点不存在"""
        nodes = {
            "node1": NodeConfig(name="node1", function_name="func1")
        }
        
        config = GraphConfig(
            name="test_graph",
            description="测试图",
            nodes=nodes,
            entry_point="node2"
        )
        errors = config.validate()
        assert "入口节点 'node2' 不存在" in errors

    def test_get_state_class(self):
        """测试获取状态类"""
        state_schema = GraphStateConfig(name="TestState")
        config = GraphConfig(
            name="test_graph",
            description="测试图",
            state_schema=state_schema
        )
        state_class = config.get_state_class()
        assert state_class.__name__ == "TestState"