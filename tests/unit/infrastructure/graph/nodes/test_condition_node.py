"""条件节点单元测试"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict, Optional, List, Callable

from src.infrastructure.graph.nodes.condition_node import ConditionNode
from src.infrastructure.graph.registry import NodeExecutionResult
from src.domain.agent.state import AgentState


class TestConditionNode:
    """条件节点测试"""

    @pytest.fixture
    def node(self):
        """创建条件节点实例"""
        return ConditionNode()

    @pytest.fixture
    def sample_state(self):
        """示例状态"""
        state = AgentState()
        state.messages = []
        state.current_task = "测试输入"
        state.max_iterations = 10
        state.iteration_count = 0
        state.tool_results = []
        state.errors = []
        return state

    @pytest.fixture
    def sample_config(self):
        """示例配置"""
        return {
            "conditions": [
                {
                    "type": "has_tool_calls",
                    "next_node": "execute_tool"
                }
            ],
            "default_next_node": "default_node"
        }

    def test_init(self, node):
        """测试初始化"""
        assert isinstance(node, ConditionNode)
        assert hasattr(node, '_condition_functions')
        assert isinstance(node._condition_functions, dict)
        # 检查内置条件函数是否存在
        assert "has_tool_calls" in node._condition_functions
        assert "no_tool_calls" in node._condition_functions
        assert "has_tool_results" in node._condition_functions
        assert "max_iterations_reached" in node._condition_functions
        assert "has_errors" in node._condition_functions
        assert "no_errors" in node._condition_functions
        assert "message_contains" in node._condition_functions
        assert "iteration_count_equals" in node._condition_functions
        assert "iteration_count_greater_than" in node._condition_functions
        assert "custom" in node._condition_functions

    def test_node_type_property(self, node):
        """测试节点类型属性"""
        assert node.node_type == "condition_node"

    def test_execute_with_matching_condition(self, node, sample_state, sample_config):
        """测试执行匹配条件"""
        # 修改状态以匹配条件 - 使用属性访问
        from src.domain.agent.state import AgentMessage
        message = AgentMessage(content="测试消息", role="ai")
        message.metadata = {"tool_calls": [{"name": "test_tool"}]}
        sample_state.messages = [message]
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert isinstance(result, NodeExecutionResult)
        assert result.state == sample_state
        assert result.next_node == "execute_tool"
        assert result.metadata is not None
        assert "condition_met" in result.metadata
        assert result.metadata["condition_met"] == "has_tool_calls"

    def test_execute_with_default_condition(self, node, sample_state, sample_config):
        """测试执行默认条件"""
        # 确保没有条件匹配 - 使用属性访问
        from src.domain.agent.state import AgentMessage
        message = AgentMessage(content="测试消息", role="ai")
        message.metadata = {}
        sample_state.messages = [message]
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert isinstance(result, NodeExecutionResult)
        assert result.state == sample_state
        assert result.next_node == "default_node"
        assert result.metadata is not None
        assert "condition_met" in result.metadata
        assert result.metadata["condition_met"] is None

    def test_execute_without_conditions(self, node, sample_state):
        """测试执行无条件配置"""
        config = {}
        
        # 执行
        result = node.execute(sample_state, config)
        
        # 验证使用默认条件
        assert isinstance(result, NodeExecutionResult)
        assert result.state == sample_state

    def test_get_config_schema(self, node):
        """测试获取配置模式"""
        schema = node.get_config_schema()
        
        assert isinstance(schema, dict)
        assert "type" in schema
        assert "properties" in schema
        assert "required" in schema
        assert "conditions" in schema["properties"]
        assert "default_next_node" in schema["properties"]
        assert "custom_condition_code" in schema["properties"]

    def test_evaluate_condition_success(self, node, sample_state):
        """测试评估条件成功"""
        condition_config = {
            "type": "has_tool_calls",
            "next_node": "execute_tool"
        }
        
        # 修改状态以匹配条件 - 使用属性访问
        from src.domain.agent.state import AgentMessage
        message = AgentMessage(content="测试消息", role="ai")
        message.metadata = {"tool_calls": [{"name": "test_tool"}]}
        sample_state.messages = [message]
        
        # 评估条件
        result = node._evaluate_condition(condition_config, sample_state)
        assert result is True

    def test_evaluate_condition_unknown_type(self, node, sample_state):
        """测试评估未知条件类型"""
        condition_config = {
            "type": "unknown_condition",
            "next_node": "next_node"
        }
        
        with pytest.raises(ValueError, match="未知的条件类型: unknown_condition"):
            node._evaluate_condition(condition_config, sample_state)

    def test_has_tool_calls_true(self, node, sample_state):
        """测试有工具调用条件（真）"""
        parameters = {}
        config = {}
        
        # 修改状态以包含工具调用 - 使用属性访问
        from src.domain.agent.state import AgentMessage
        message = AgentMessage(content="测试消息", role="ai")
        message.metadata = {"tool_calls": [{"name": "test_tool"}]}
        sample_state.messages = [message]
        
        result = node._has_tool_calls(sample_state, parameters, config)
        assert result is True

    def test_has_tool_calls_false(self, node, sample_state):
        """测试有工具调用条件（假）"""
        parameters = {}
        config = {}
        
        # 修改状态以不包含工具调用 - 使用属性访问
        from src.domain.agent.state import AgentMessage
        message = AgentMessage(content="测试消息", role="ai")
        message.metadata = {}
        sample_state.messages = [message]
        
        result = node._has_tool_calls(sample_state, parameters, config)
        assert result is False

    def test_no_tool_calls_true(self, node, sample_state):
        """测试无工具调用条件（真）"""
        parameters = {}
        config = {}
        
        # 修改状态以不包含工具调用 - 使用属性访问
        from src.domain.agent.state import AgentMessage
        message = AgentMessage(content="测试消息", role="ai")
        message.metadata = {}
        sample_state.messages = [message]
        
        result = node._no_tool_calls(sample_state, parameters, config)
        assert result is True

    def test_no_tool_calls_false(self, node, sample_state):
        """测试无工具调用条件（假）"""
        parameters = {}
        config = {}
        
        # 修改状态以包含工具调用 - 使用属性访问
        from src.domain.agent.state import AgentMessage
        message = AgentMessage(content="测试消息", role="ai")
        message.metadata = {"tool_calls": [{"name": "test_tool"}]}
        sample_state.messages = [message]
        
        result = node._no_tool_calls(sample_state, parameters, config)
        assert result is False

    def test_has_tool_results_true(self, node, sample_state):
        """测试有工具结果条件（真）"""
        parameters = {}
        config = {}
        
        # 修改状态以包含工具结果 - 使用属性访问
        from src.domain.tools.interfaces import ToolResult
        tool_result = ToolResult(tool_name="test_tool", success=True, output="test_result")
        sample_state.tool_results = [tool_result]
        
        result = node._has_tool_results(sample_state, parameters, config)
        assert result is True

    def test_has_tool_results_false(self, node, sample_state):
        """测试有工具结果条件（假）"""
        parameters = {}
        config = {}
        
        # 修改状态以不包含工具结果 - 使用属性访问
        sample_state.tool_results = []
        
        result = node._has_tool_results(sample_state, parameters, config)
        assert result is False

    def test_max_iterations_reached_true(self, node, sample_state):
        """测试达到最大迭代次数条件（真）"""
        parameters = {}
        config = {}
        
        # 修改状态以达到最大迭代次数 - 使用属性访问
        sample_state.iteration_count = 10
        sample_state.max_iterations = 10
        
        result = node._max_iterations_reached(sample_state, parameters, config)
        assert result is True

    def test_max_iterations_reached_false(self, node, sample_state):
        """测试达到最大迭代次数条件（假）"""
        parameters = {}
        config = {}
        
        # 修改状态以未达到最大迭代次数 - 使用属性访问
        sample_state.iteration_count = 5
        sample_state.max_iterations = 10
        
        result = node._max_iterations_reached(sample_state, parameters, config)
        assert result is False

    def test_has_errors_true(self, node, sample_state):
        """测试有错误条件（真）"""
        parameters = {}
        config = {}
        
        # 修改状态以包含错误 - 使用属性访问
        from src.domain.tools.interfaces import ToolResult
        tool_result = ToolResult(tool_name="test_tool", success=False, error="测试错误")
        sample_state.tool_results = [tool_result]
        
        result = node._has_errors(sample_state, parameters, config)
        assert result is True

    def test_has_errors_false(self, node, sample_state):
        """测试有错误条件（假）"""
        parameters = {}
        config = {}
        
        # 修改状态以不包含错误 - 使用属性访问
        from src.domain.tools.interfaces import ToolResult
        tool_result = ToolResult(tool_name="test_tool", success=True, output="测试结果")
        sample_state.tool_results = [tool_result]
        
        result = node._has_errors(sample_state, parameters, config)
        assert result is False

    def test_no_errors_true(self, node, sample_state):
        """测试无错误条件（真）"""
        parameters = {}
        config = {}
        
        # 修改状态以不包含错误 - 使用属性访问
        from src.domain.tools.interfaces import ToolResult
        tool_result = ToolResult(tool_name="test_tool", success=True, output="测试结果")
        sample_state.tool_results = [tool_result]
        
        result = node._no_errors(sample_state, parameters, config)
        assert result is True

    def test_no_errors_false(self, node, sample_state):
        """测试无错误条件（假）"""
        parameters = {}
        config = {}
        
        # 修改状态以包含错误 - 使用属性访问
        from src.domain.tools.interfaces import ToolResult
        tool_result = ToolResult(tool_name="test_tool", success=False, error="测试错误")
        sample_state.tool_results = [tool_result]
        
        result = node._no_errors(sample_state, parameters, config)
        assert result is False

    def test_message_contains_true(self, node, sample_state):
        """测试消息包含条件（真）"""
        parameters = {"text": "测试"}
        config = {}
        
        # 修改状态以包含指定文本 - 使用属性访问
        from src.domain.agent.state import AgentMessage
        message = AgentMessage(content="这是一个测试消息", role="ai")
        sample_state.messages = [message]
        
        result = node._message_contains(sample_state, parameters, config)
        assert result is True

    def test_message_contains_false(self, node, sample_state):
        """测试消息包含条件（假）"""
        parameters = {"text": "test"}
        config = {}
        
        # 修改状态以不包含指定文本 - 使用属性访问
        from src.domain.agent.state import AgentMessage
        message = AgentMessage(content="这是一个消息", role="ai")
        sample_state.messages = [message]
        
        result = node._message_contains(sample_state, parameters, config)
        assert result is False

    def test_iteration_count_equals_true(self, node, sample_state):
        """测试迭代次数等于条件（真）"""
        parameters = {"count": 5}
        config = {}
        
        # 修改状态以匹配迭代次数 - 使用属性访问
        sample_state.iteration_count = 5
        
        result = node._iteration_count_equals(sample_state, parameters, config)
        assert result is True

    def test_iteration_count_equals_false(self, node, sample_state):
        """测试迭代次数等于条件（假）"""
        parameters = {"count": 5}
        config = {}
        
        # 修改状态以不匹配迭代次数 - 使用属性访问
        sample_state.iteration_count = 3
        
        result = node._iteration_count_equals(sample_state, parameters, config)
        assert result is False

    def test_iteration_count_greater_than_true(self, node, sample_state):
        """测试迭代次数大于条件（真）"""
        parameters = {"count": 5}
        config = {}
        
        # 修改状态以满足条件 - 使用属性访问
        sample_state.iteration_count = 7
        
        result = node._iteration_count_greater_than(sample_state, parameters, config)
        assert result is True

    def test_iteration_count_greater_than_false(self, node, sample_state):
        """测试迭代次数大于条件（假）"""
        parameters = {"count": 5}
        config = {}
        
        # 修改状态以不满足条件 - 使用属性访问
        sample_state.iteration_count = 3
        
        result = node._iteration_count_greater_than(sample_state, parameters, config)
        assert result is False

    def test_custom_condition_success(self, node, sample_state):
        """测试自定义条件成功"""
        parameters = {"custom_condition_code": "True"}
        config = {}
        
        result = node._custom_condition(sample_state, parameters, config)
        assert result is True

    def test_custom_condition_failure(self, node, sample_state):
        """测试自定义条件失败"""
        parameters = {"custom_condition_code": "False"}
        config = {}
        
        result = node._custom_condition(sample_state, parameters, config)
        assert result is False

    def test_custom_condition_missing_code(self, node, sample_state):
        """测试自定义条件缺少代码"""
        parameters = {}
        config = {}
        
        with pytest.raises(ValueError, match="自定义条件需要提供 custom_condition_code"):
            node._custom_condition(sample_state, parameters, config)

    def test_custom_condition_exception(self, node, sample_state):
        """测试自定义条件异常"""
        parameters = {"custom_condition_code": "invalid_code"}
        config = {}
        
        result = node._custom_condition(sample_state, parameters, config)
        assert result is False

    def test_register_condition_function(self, node):
        """测试注册条件函数"""
        def custom_condition(state, parameters, config):
            return True
        
        node.register_condition_function("custom_test", custom_condition)
        assert "custom_test" in node._condition_functions
        assert node._condition_functions["custom_test"] == custom_condition

    def test_list_condition_types(self, node):
        """测试列出条件类型"""
        condition_types = node.list_condition_types()
        assert isinstance(condition_types, list)
        assert "has_tool_calls" in condition_types
        assert "no_tool_calls" in condition_types
        assert "has_tool_results" in condition_types
        assert "max_iterations_reached" in condition_types
        assert "has_errors" in condition_types
        assert "no_errors" in condition_types
        assert "message_contains" in condition_types
        assert "iteration_count_equals" in condition_types
        assert "iteration_count_greater_than" in condition_types
        assert "custom" in condition_types