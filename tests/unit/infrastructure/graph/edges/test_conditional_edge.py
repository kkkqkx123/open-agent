"""条件边单元测试"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

from src.infrastructure.graph.edges.conditional_edge import (
    ConditionType,
    ConditionalEdge
)
from src.infrastructure.graph.config import EdgeConfig, EdgeType
from src.domain.agent.state import AgentState


class TestConditionType:
    """条件类型枚举测试"""

    def test_condition_type_values(self):
        """测试条件类型枚举值"""
        assert ConditionType.HAS_TOOL_CALLS.value == "has_tool_calls"
        assert ConditionType.NO_TOOL_CALLS.value == "no_tool_calls"
        assert ConditionType.HAS_TOOL_RESULTS.value == "has_tool_results"
        assert ConditionType.MAX_ITERATIONS_REACHED.value == "max_iterations_reached"
        assert ConditionType.HAS_ERRORS.value == "has_errors"
        assert ConditionType.NO_ERRORS.value == "no_errors"
        assert ConditionType.MESSAGE_CONTAINS.value == "message_contains"
        assert ConditionType.ITERATION_COUNT_EQUALS.value == "iteration_count_equals"
        assert ConditionType.ITERATION_COUNT_GREATER_THAN.value == "iteration_count_greater_than"
        assert ConditionType.CUSTOM.value == "custom"

    def test_condition_type_members(self):
        """测试条件类型枚举成员"""
        assert ConditionType.HAS_TOOL_CALLS.name == "HAS_TOOL_CALLS"
        assert ConditionType.NO_TOOL_CALLS.name == "NO_TOOL_CALLS"
        assert ConditionType.HAS_TOOL_RESULTS.name == "HAS_TOOL_RESULTS"
        assert ConditionType.MAX_ITERATIONS_REACHED.name == "MAX_ITERATIONS_REACHED"
        assert ConditionType.HAS_ERRORS.name == "HAS_ERRORS"
        assert ConditionType.NO_ERRORS.name == "NO_ERRORS"
        assert ConditionType.MESSAGE_CONTAINS.name == "MESSAGE_CONTAINS"
        assert ConditionType.ITERATION_COUNT_EQUALS.name == "ITERATION_COUNT_EQUALS"
        assert ConditionType.ITERATION_COUNT_GREATER_THAN.name == "ITERATION_COUNT_GREATER_THAN"
        assert ConditionType.CUSTOM.name == "CUSTOM"


class TestConditionalEdge:
    """条件边测试"""

    def test_init(self):
        """测试初始化"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="has_tool_calls",
            condition_type=ConditionType.HAS_TOOL_CALLS,
            condition_parameters={}
        )
        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.condition == "has_tool_calls"
        assert edge.condition_type == ConditionType.HAS_TOOL_CALLS
        assert edge.condition_parameters == {}
        assert edge.description is None

    def test_init_with_description(self):
        """测试带描述初始化"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="has_tool_calls",
            condition_type=ConditionType.HAS_TOOL_CALLS,
            condition_parameters={},
            description="测试条件边"
        )
        assert edge.description == "测试条件边"

    def test_from_config_success(self):
        """测试从配置创建成功"""
        config = EdgeConfig(
            from_node="node1",
            to_node="node2",
            type=EdgeType.CONDITIONAL,
            condition="has_tool_calls",
            description="测试条件边"
        )
        
        edge = ConditionalEdge.from_config(config)
        
        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.condition == "has_tool_calls"
        assert edge.condition_type == ConditionType.HAS_TOOL_CALLS
        assert edge.condition_parameters == {}
        assert edge.description == "测试条件边"

    def test_from_config_wrong_type(self):
        """测试从错误类型的配置创建"""
        config = EdgeConfig(
            from_node="node1",
            to_node="node2",
            type=EdgeType.SIMPLE
        )
        
        with pytest.raises(ValueError, match="配置类型不匹配"):
            ConditionalEdge.from_config(config)

    def test_from_config_missing_condition(self):
        """测试从缺少条件的配置创建"""
        config = EdgeConfig(
            from_node="node1",
            to_node="node2",
            type=EdgeType.CONDITIONAL
        )
        
        with pytest.raises(ValueError, match="条件边必须指定条件表达式"):
            ConditionalEdge.from_config(config)

    def test_to_config(self):
        """测试转换为配置"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="has_tool_calls",
            condition_type=ConditionType.HAS_TOOL_CALLS,
            condition_parameters={}
        )
        
        config = edge.to_config()
        
        assert isinstance(config, EdgeConfig)
        assert config.from_node == "node1"
        assert config.to_node == "node2"
        assert config.type == EdgeType.CONDITIONAL
        assert config.condition == "has_tool_calls"

    def test_evaluate_has_tool_calls_true(self):
        """测试评估有工具调用（真）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="has_tool_calls",
            condition_type=ConditionType.HAS_TOOL_CALLS,
            condition_parameters={}
        )
        
        # 创建包含工具调用的状态
        state = Mock(spec=AgentState)
        state.messages = [Mock()]
        state.messages[-1].tool_calls = [{"name": "test_tool"}]
        
        result = edge.evaluate(state)
        assert result is True

    def test_evaluate_has_tool_calls_false(self):
        """测试评估有工具调用（假）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="has_tool_calls",
            condition_type=ConditionType.HAS_TOOL_CALLS,
            condition_parameters={}
        )
        
        # 创建不包含工具调用的状态
        state = Mock(spec=AgentState)
        state.messages = [Mock()]
        state.messages[-1].tool_calls = []
        
        result = edge.evaluate(state)
        assert result is False

    def test_evaluate_no_tool_calls_true(self):
        """测试评估无工具调用（真）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="no_tool_calls",
            condition_type=ConditionType.NO_TOOL_CALLS,
            condition_parameters={}
        )
        
        # 创建不包含工具调用的状态
        state = Mock(spec=AgentState)
        state.messages = [Mock()]
        state.messages[-1].tool_calls = []
        
        result = edge.evaluate(state)
        assert result is True

    def test_evaluate_no_tool_calls_false(self):
        """测试评估无工具调用（假）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="no_tool_calls",
            condition_type=ConditionType.NO_TOOL_CALLS,
            condition_parameters={}
        )
        
        # 创建包含工具调用的状态
        state = Mock(spec=AgentState)
        state.messages = [Mock()]
        state.messages[-1].tool_calls = [{"name": "test_tool"}]
        
        result = edge.evaluate(state)
        assert result is False

    def test_evaluate_has_tool_results_true(self):
        """测试评估有工具结果（真）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="has_tool_results",
            condition_type=ConditionType.HAS_TOOL_RESULTS,
            condition_parameters={}
        )
        
        # 创建包含工具结果的状态
        state = Mock(spec=AgentState)
        state.tool_results = [{"result": "test_result"}]
        
        result = edge.evaluate(state)
        assert result is True

    def test_evaluate_has_tool_results_false(self):
        """测试评估有工具结果（假）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="has_tool_results",
            condition_type=ConditionType.HAS_TOOL_RESULTS,
            condition_parameters={}
        )
        
        # 创建不包含工具结果的状态
        state = Mock(spec=AgentState)
        state.tool_results = []
        
        result = edge.evaluate(state)
        assert result is False

    def test_evaluate_max_iterations_reached_true(self):
        """测试评估达到最大迭代次数（真）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="max_iterations",
            condition_type=ConditionType.MAX_ITERATIONS_REACHED,
            condition_parameters={}
        )
        
        # 创建达到最大迭代次数的状态
        state = Mock(spec=AgentState)
        state.iteration_count = 10
        state.max_iterations = 10
        
        result = edge.evaluate(state)
        assert result is True

    def test_evaluate_max_iterations_reached_false(self):
        """测试评估达到最大迭代次数（假）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="max_iterations",
            condition_type=ConditionType.MAX_ITERATIONS_REACHED,
            condition_parameters={}
        )
        
        # 创建未达到最大迭代次数的状态
        state = Mock(spec=AgentState)
        state.iteration_count = 5
        state.max_iterations = 10
        
        result = edge.evaluate(state)
        assert result is False

    def test_evaluate_has_errors_true(self):
        """测试评估有错误（真）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="has_errors",
            condition_type=ConditionType.HAS_ERRORS,
            condition_parameters={}
        )
        
        # 创建包含错误的状态
        state = Mock(spec=AgentState)
        state.tool_results = [Mock()]
        state.tool_results[0].success = False
        
        result = edge.evaluate(state)
        assert result is True

    def test_evaluate_has_errors_false(self):
        """测试评估有错误（假）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="has_errors",
            condition_type=ConditionType.HAS_ERRORS,
            condition_parameters={}
        )
        
        # 创建不包含错误的状态
        state = Mock(spec=AgentState)
        state.tool_results = [Mock()]
        state.tool_results[0].success = True
        
        result = edge.evaluate(state)
        assert result is False

    def test_evaluate_no_errors_true(self):
        """测试评估无错误（真）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="no_errors",
            condition_type=ConditionType.NO_ERRORS,
            condition_parameters={}
        )
        
        # 创建不包含错误的状态
        state = Mock(spec=AgentState)
        state.tool_results = [Mock()]
        state.tool_results[0].success = True
        
        result = edge.evaluate(state)
        assert result is True

    def test_evaluate_no_errors_false(self):
        """测试评估无错误（假）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="no_errors",
            condition_type=ConditionType.NO_ERRORS,
            condition_parameters={}
        )
        
        # 创建包含错误的状态
        state = Mock(spec=AgentState)
        state.tool_results = [Mock()]
        state.tool_results[0].success = False
        
        result = edge.evaluate(state)
        assert result is False

    def test_evaluate_message_contains_true(self):
        """测试评估消息包含（真）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="message_contains:test",
            condition_type=ConditionType.MESSAGE_CONTAINS,
            condition_parameters={"text": "test"}
        )
        
        # 创建包含指定文本的消息状态
        message = Mock()
        message.content = "这是一个测试消息"
        state = Mock(spec=AgentState)
        state.messages = [message]
        
        result = edge.evaluate(state)
        assert result is True

    def test_evaluate_message_contains_false(self):
        """测试评估消息包含（假）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="message_contains:test",
            condition_type=ConditionType.MESSAGE_CONTAINS,
            condition_parameters={"text": "test"}
        )
        
        # 创建不包含指定文本的消息状态
        message = Mock()
        message.content = "这是一个消息"
        state = Mock(spec=AgentState)
        state.messages = [message]
        
        result = edge.evaluate(state)
        assert result is False

    def test_evaluate_iteration_count_equals_true(self):
        """测试评估迭代次数等于（真）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="iteration_count_equals:5",
            condition_type=ConditionType.ITERATION_COUNT_EQUALS,
            condition_parameters={"count": 5}
        )
        
        # 创建迭代次数等于指定值的状态
        state = Mock(spec=AgentState)
        state.iteration_count = 5
        
        result = edge.evaluate(state)
        assert result is True

    def test_evaluate_iteration_count_equals_false(self):
        """测试评估迭代次数等于（假）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="iteration_count_equals:5",
            condition_type=ConditionType.ITERATION_COUNT_EQUALS,
            condition_parameters={"count": 5}
        )
        
        # 创建迭代次数不等于指定值的状态
        state = Mock(spec=AgentState)
        state.iteration_count = 3
        
        result = edge.evaluate(state)
        assert result is False

    def test_evaluate_iteration_count_greater_than_true(self):
        """测试评估迭代次数大于（真）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="iteration_count_greater_than:5",
            condition_type=ConditionType.ITERATION_COUNT_GREATER_THAN,
            condition_parameters={"count": 5}
        )
        
        # 创建迭代次数大于指定值的状态
        state = Mock(spec=AgentState)
        state.iteration_count = 7
        
        result = edge.evaluate(state)
        assert result is True

    def test_evaluate_iteration_count_greater_than_false(self):
        """测试评估迭代次数大于（假）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="iteration_count_greater_than:5",
            condition_type=ConditionType.ITERATION_COUNT_GREATER_THAN,
            condition_parameters={"count": 5}
        )
        
        # 创建迭代次数不大于指定值的状态
        state = Mock(spec=AgentState)
        state.iteration_count = 3
        
        result = edge.evaluate(state)
        assert result is False

    def test_evaluate_custom_condition_true(self):
        """测试评估自定义条件（真）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="custom_condition",
            condition_type=ConditionType.CUSTOM,
            condition_parameters={"expression": "True"}
        )
        
        state = Mock(spec=AgentState)
        result = edge.evaluate(state)
        assert result is True

    def test_evaluate_custom_condition_false(self):
        """测试评估自定义条件（假）"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="custom_condition",
            condition_type=ConditionType.CUSTOM,
            condition_parameters={"expression": "False"}
        )
        
        state = Mock(spec=AgentState)
        result = edge.evaluate(state)
        assert result is False

    def test_evaluate_unknown_condition_type(self):
        """测试评估未知条件类型"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="unknown",
            condition_type=Mock(),  # 模拟未知类型
            condition_parameters={}
        )
        
        state = Mock(spec=AgentState)
        
        with pytest.raises(ValueError, match="未知的条件类型"):
            edge.evaluate(state)

    def test_validate_success(self):
        """测试验证成功"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="has_tool_calls",
            condition_type=ConditionType.HAS_TOOL_CALLS,
            condition_parameters={}
        )
        
        node_names = {"node1", "node2"}
        errors = edge.validate(node_names)
        assert errors == []

    def test_validate_from_node_not_exists(self):
        """测试验证起始节点不存在"""
        edge = ConditionalEdge(
            from_node="node3",
            to_node="node2",
            condition="has_tool_calls",
            condition_type=ConditionType.HAS_TOOL_CALLS,
            condition_parameters={}
        )
        
        node_names = {"node1", "node2"}
        errors = edge.validate(node_names)
        assert len(errors) == 1
        assert "起始节点 'node3' 不存在" in errors

    def test_validate_to_node_not_exists(self):
        """测试验证目标节点不存在"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node3",
            condition="has_tool_calls",
            condition_type=ConditionType.HAS_TOOL_CALLS,
            condition_parameters={}
        )
        
        node_names = {"node1", "node2"}
        errors = edge.validate(node_names)
        assert len(errors) == 1
        assert "目标节点 'node3' 不存在" in errors

    def test_validate_self_loop(self):
        """测试验证自循环"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node1",
            condition="has_tool_calls",
            condition_type=ConditionType.HAS_TOOL_CALLS,
            condition_parameters={}
        )
        
        node_names = {"node1", "node2"}
        errors = edge.validate(node_names)
        assert len(errors) == 1
        assert "不允许节点自循环" in errors

    def test_validate_message_contains_missing_text(self):
        """测试验证消息包含条件缺少文本参数"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="message_contains",
            condition_type=ConditionType.MESSAGE_CONTAINS,
            condition_parameters={}
        )
        
        node_names = {"node1", "node2"}
        errors = edge.validate(node_names)
        assert len(errors) == 1
        assert "message_contains 条件需要指定 text 参数" in errors

    def test_validate_iteration_count_equals_missing_count(self):
        """测试验证迭代次数等于条件缺少计数参数"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="iteration_count_equals",
            condition_type=ConditionType.ITERATION_COUNT_EQUALS,
            condition_parameters={}
        )
        
        node_names = {"node1", "node2"}
        errors = edge.validate(node_names)
        assert len(errors) == 1
        assert "iteration_count_equals 条件需要指定 count 参数" in errors

    def test_parse_condition_builtin(self):
        """测试解析内置条件"""
        # 测试各种内置条件
        test_cases = [
            ("has_tool_call", ConditionType.HAS_TOOL_CALLS, {}),
            ("no_tool_call", ConditionType.NO_TOOL_CALLS, {}),
            ("has_tool_calls", ConditionType.HAS_TOOL_CALLS, {}),
            ("no_tool_calls", ConditionType.NO_TOOL_CALLS, {}),
            ("has_tool_result", ConditionType.HAS_TOOL_RESULTS, {}),
            ("has_tool_results", ConditionType.HAS_TOOL_RESULTS, {}),
            ("max_iterations", ConditionType.MAX_ITERATIONS_REACHED, {}),
            ("max_iterations_reached", ConditionType.MAX_ITERATIONS_REACHED, {}),
            ("has_error", ConditionType.HAS_ERRORS, {}),
            ("has_errors", ConditionType.HAS_ERRORS, {}),
            ("no_error", ConditionType.NO_ERRORS, {}),
            ("no_errors", ConditionType.NO_ERRORS, {}),
        ]
        
        for condition_str, expected_type, expected_params in test_cases:
            condition_type, condition_parameters = ConditionalEdge._parse_condition(condition_str)
            assert condition_type == expected_type
            assert condition_parameters == expected_params

    def test_parse_condition_with_parameters(self):
        """测试解析带参数的条件"""
        # 测试消息包含条件
        condition_type, condition_parameters = ConditionalEdge._parse_condition("message_contains:test")
        assert condition_type == ConditionType.MESSAGE_CONTAINS
        assert condition_parameters == {"text": "test"}
        
        # 测试迭代次数等于条件
        condition_type, condition_parameters = ConditionalEdge._parse_condition("iteration_count_equals:5")
        assert condition_type == ConditionType.ITERATION_COUNT_EQUALS
        assert condition_parameters == {"count": 5}
        
        # 测试迭代次数大于条件
        condition_type, condition_parameters = ConditionalEdge._parse_condition("iteration_count_greater_than:3")
        assert condition_type == ConditionType.ITERATION_COUNT_GREATER_THAN
        assert condition_parameters == {"count": 3}

    def test_parse_condition_custom(self):
        """测试解析自定义条件"""
        condition_type, condition_parameters = ConditionalEdge._parse_condition("custom_expression")
        assert condition_type == ConditionType.CUSTOM
        assert condition_parameters == {"expression": "custom_expression"}

    def test_str_representation(self):
        """测试字符串表示"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="has_tool_calls",
            condition_type=ConditionType.HAS_TOOL_CALLS,
            condition_parameters={}
        )
        
        result = str(edge)
        assert result == "ConditionalEdge(node1 -> node2 [has_tool_calls])"

    def test_repr_representation(self):
        """测试详细字符串表示"""
        edge = ConditionalEdge(
            from_node="node1",
            to_node="node2",
            condition="has_tool_calls",
            condition_type=ConditionType.HAS_TOOL_CALLS,
            condition_parameters={},
            description="测试条件边"
        )
        
        result = repr(edge)
        assert "ConditionalEdge" in result
        assert "from_node='node1'" in result
        assert "to_node='node2'" in result
        assert "condition='has_tool_calls'" in result
        assert "(测试条件边)" in result