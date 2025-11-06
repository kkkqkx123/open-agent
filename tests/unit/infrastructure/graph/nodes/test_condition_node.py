"""条件节点单元测试"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict, Optional, List, Callable

from src.infrastructure.graph.nodes.condition_node import ConditionNode
from src.infrastructure.graph.registry import NodeExecutionResult
from src.infrastructure.graph.states.workflow import WorkflowState


class AttrDict(dict):
    """支持属性访问的字典"""
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class TestConditionNode:
    """条件节点测试"""

    @pytest.fixture
    def node(self) -> ConditionNode:
        """创建条件节点实例"""
        return ConditionNode()

    @pytest.fixture
    def sample_state(self) -> AttrDict:
        """示例状态"""
        state = AttrDict()
        state.messages = []
        state.current_task = "测试输入"
        state.max_iterations = 10
        state.iteration_count = 0
        state.tool_results = []
        state.errors = []
        return state

    @pytest.fixture
    def sample_config(self) -> Dict[str, Any]:
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

    def test_init(self, node: ConditionNode) -> None:
        """测试初始化"""
        assert node.node_type == "condition_node"
        assert hasattr(node, '_evaluator')

    def test_node_type_property(self, node: ConditionNode) -> None:
        """测试节点类型属性"""
        assert node.node_type == "condition_node"

    def test_execute_with_matching_condition(self, node: ConditionNode, sample_state: AttrDict, sample_config: Dict[str, Any]) -> None:
        """测试执行匹配条件"""
        # 修改状态以匹配条件 - 使用属性访问
        from src.infrastructure.llm.models import LLMMessage, MessageRole
        message = LLMMessage(role=MessageRole.ASSISTANT, content="测试消息")
        message.metadata = {"tool_calls": [{"name": "test_tool"}]}
        sample_state.messages = [message]

        # 执行
        result = node.execute(sample_state, sample_config)

        # 验证
        assert isinstance(result, NodeExecutionResult)
        assert result.state == sample_state
        assert result.next_node == "execute_tool"
        assert result.metadata["condition_met"] == "has_tool_calls"

    def test_execute_with_default_condition(self, node: ConditionNode, sample_state: AttrDict, sample_config: Dict[str, Any]) -> None:
        """测试执行默认条件"""
        # 状态不匹配任何条件
        result = node.execute(sample_state, sample_config)

        # 验证
        assert isinstance(result, NodeExecutionResult)
        assert result.state == sample_state
        assert result.next_node == "default_node"
        assert result.metadata["condition_met"] is None

    def test_execute_without_conditions(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试执行没有条件"""
        config = {"default_next_node": "default_node"}
        
        # 执行
        result = node.execute(sample_state, config)

        # 验证
        assert isinstance(result, NodeExecutionResult)
        assert result.next_node == "default_node"

    def test_get_config_schema(self, node: ConditionNode) -> None:
        """测试获取配置模式"""
        schema = node.get_config_schema()
        
        # 验证
        assert isinstance(schema, dict)
        assert "type" in schema
        assert "properties" in schema
        assert "required" in schema
        assert "conditions" in schema["properties"]
        assert "default_next_node" in schema["properties"]
        assert "custom_condition_code" in schema["properties"]

    def test_evaluate_condition_success(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试评估条件成功"""
        condition_config = {
            "type": "has_tool_calls",
            "next_node": "execute_tool"
        }
        
        # 修改状态以匹配条件 - 使用属性访问
        from src.infrastructure.llm.models import LLMMessage, MessageRole
        message = LLMMessage(role=MessageRole.ASSISTANT, content="测试消息")
        message.metadata = {"tool_calls": [{"name": "test_tool"}]}
        sample_state.messages = [message]
        
        # 评估条件
        result = node._evaluate_condition(condition_config, sample_state, {})
        
        # 验证
        assert result is True

    def test_evaluate_condition_unknown_type(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试评估未知条件类型"""
        condition_config = {
            "type": "unknown_condition",
            "next_node": "next_node"
        }

        with pytest.raises(ValueError, match="未知的条件类型: unknown_condition"):
            node._evaluate_condition(condition_config, sample_state, {})

    def test_has_tool_calls_true(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试有工具调用条件（真）"""
        # 修改状态以包含工具调用 - 使用属性访问
        from src.infrastructure.llm.models import LLMMessage, MessageRole
        message = LLMMessage(role=MessageRole.ASSISTANT, content="测试消息")
        message.metadata = {"tool_calls": [{"name": "test_tool"}]}
        sample_state.messages = [message]

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {"type": "has_tool_calls", "next_node": "execute_tool"}
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "execute_tool"

    def test_has_tool_calls_false(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试有工具调用条件（假）"""
        # 修改状态以不包含工具调用 - 使用属性访问
        from src.infrastructure.llm.models import LLMMessage, MessageRole
        message = LLMMessage(role=MessageRole.ASSISTANT, content="测试消息")
        message.metadata = {}
        sample_state.messages = [message]

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {"type": "has_tool_calls", "next_node": "execute_tool"}
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "default_node"

    def test_no_tool_calls_true(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试无工具调用条件（真）"""
        # 修改状态以不包含工具调用 - 使用属性访问
        from src.infrastructure.llm.models import LLMMessage, MessageRole
        message = LLMMessage(role=MessageRole.ASSISTANT, content="测试消息")
        message.metadata = {}
        sample_state.messages = [message]

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {"type": "no_tool_calls", "next_node": "no_tool_node"}
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "no_tool_node"

    def test_no_tool_calls_false(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试无工具调用条件（假）"""
        # 修改状态以包含工具调用 - 使用属性访问
        from src.infrastructure.llm.models import LLMMessage, MessageRole
        message = LLMMessage(role=MessageRole.ASSISTANT, content="测试消息")
        message.metadata = {"tool_calls": [{"name": "test_tool"}]}
        sample_state.messages = [message]

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {"type": "no_tool_calls", "next_node": "no_tool_node"}
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "default_node"

    def test_has_tool_results_true(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试有工具结果条件（真）"""
        # 修改状态以包含工具结果 - 使用属性访问
        from src.domain.tools.interfaces import ToolResult
        tool_result = ToolResult(tool_name="test_tool", success=True, output="test_result")
        sample_state.tool_results = [tool_result]

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {"type": "has_tool_results", "next_node": "process_results"}
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "process_results"

    def test_has_tool_results_false(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试有工具结果条件（假）"""
        # 修改状态以不包含工具结果 - 使用属性访问
        sample_state.tool_results = []

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {"type": "has_tool_results", "next_node": "process_results"}
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "default_node"

    def test_max_iterations_reached_true(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试达到最大迭代次数条件（真）"""
        # 修改状态以达到最大迭代次数 - 使用属性访问
        sample_state.iteration_count = 10
        sample_state.max_iterations = 10

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {"type": "max_iterations_reached", "next_node": "end_node"}
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "end_node"

    def test_max_iterations_reached_false(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试达到最大迭代次数条件（假）"""
        # 修改状态以未达到最大迭代次数 - 使用属性访问
        sample_state.iteration_count = 5
        sample_state.max_iterations = 10

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {"type": "max_iterations_reached", "next_node": "end_node"}
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "default_node"

    def test_has_errors_true(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试有错误条件（真）"""
        # 修改状态以包含错误 - 使用属性访问
        from src.domain.tools.interfaces import ToolResult
        tool_result = ToolResult(tool_name="test_tool", success=False, error="测试错误")
        sample_state.tool_results = [tool_result]

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {"type": "has_errors", "next_node": "error_handler"}
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "error_handler"

    def test_has_errors_false(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试有错误条件（假）"""
        # 修改状态以不包含错误 - 使用属性访问
        from src.domain.tools.interfaces import ToolResult
        tool_result = ToolResult(tool_name="test_tool", success=True, output="测试结果")
        sample_state.tool_results = [tool_result]

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {"type": "has_errors", "next_node": "error_handler"}
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "default_node"

    def test_no_errors_true(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试无错误条件（真）"""
        # 修改状态以不包含错误 - 使用属性访问
        from src.domain.tools.interfaces import ToolResult
        tool_result = ToolResult(tool_name="test_tool", success=True, output="测试结果")
        sample_state.tool_results = [tool_result]

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {"type": "no_errors", "next_node": "continue_node"}
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "continue_node"

    def test_no_errors_false(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试无错误条件（假）"""
        # 修改状态以包含错误 - 使用属性访问
        from src.domain.tools.interfaces import ToolResult
        tool_result = ToolResult(tool_name="test_tool", success=False, error="测试错误")
        sample_state.tool_results = [tool_result]

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {"type": "no_errors", "next_node": "continue_node"}
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "default_node"

    def test_message_contains_true(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试消息包含条件（真）"""
        # 修改状态以包含指定文本 - 使用属性访问
        from src.infrastructure.llm.models import LLMMessage, MessageRole
        message = LLMMessage(role=MessageRole.ASSISTANT, content="这是一个测试消息")
        sample_state.messages = [message]

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {
                    "type": "message_contains",
                    "next_node": "test_node",
                    "parameters": {"text": "测试"}
                }
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "test_node"

    def test_message_contains_false(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试消息包含条件（假）"""
        # 修改状态以不包含指定文本 - 使用属性访问
        from src.infrastructure.llm.models import LLMMessage, MessageRole
        message = LLMMessage(role=MessageRole.ASSISTANT, content="这是一个消息")
        sample_state.messages = [message]

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {
                    "type": "message_contains",
                    "next_node": "test_node",
                    "parameters": {"text": "test"}
                }
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "default_node"

    def test_iteration_count_equals_true(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试迭代次数等于条件（真）"""
        # 修改状态以匹配迭代次数 - 使用属性访问
        sample_state.iteration_count = 5

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {
                    "type": "iteration_count_equals",
                    "next_node": "special_node",
                    "parameters": {"count": 5}
                }
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "special_node"

    def test_iteration_count_equals_false(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试迭代次数等于条件（假）"""
        # 修改状态以不匹配迭代次数 - 使用属性访问
        sample_state.iteration_count = 3

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {
                    "type": "iteration_count_equals",
                    "next_node": "special_node",
                    "parameters": {"count": 5}
                }
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "default_node"

    def test_iteration_count_greater_than_true(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试迭代次数大于条件（真）"""
        # 修改状态以满足条件 - 使用属性访问
        sample_state.iteration_count = 7

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {
                    "type": "iteration_count_greater_than",
                    "next_node": "advanced_node",
                    "parameters": {"count": 5}
                }
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "advanced_node"

    def test_iteration_count_greater_than_false(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试迭代次数大于条件（假）"""
        # 修改状态以不满足条件 - 使用属性访问
        sample_state.iteration_count = 3

        # 通过execute方法测试条件
        config = {
            "conditions": [
                {
                    "type": "iteration_count_greater_than",
                    "next_node": "advanced_node",
                    "parameters": {"count": 5}
                }
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "default_node"

    def test_custom_condition_success(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试自定义条件成功"""
        # 通过execute方法测试条件
        config = {
            "conditions": [
                {
                    "type": "custom",
                    "next_node": "custom_node",
                    "parameters": {"custom_condition_code": "True"}
                }
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "custom_node"

    def test_custom_condition_failure(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试自定义条件失败"""
        # 通过execute方法测试条件
        config = {
            "conditions": [
                {
                    "type": "custom",
                    "next_node": "custom_node",
                    "parameters": {"custom_condition_code": "False"}
                }
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证
        assert result.next_node == "default_node"

    def test_custom_condition_missing_code(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试自定义条件缺少代码"""
        # 通过execute方法测试条件
        config = {
            "conditions": [
                {
                    "type": "custom",
                    "next_node": "custom_node",
                    "parameters": {}
                }
            ],
            "default_next_node": "default_node"
        }
        
        # 应该抛出异常
        with pytest.raises(ValueError, match="自定义条件需要提供 custom_condition_code"):
            node.execute(sample_state, config)

    def test_custom_condition_exception(self, node: ConditionNode, sample_state: AttrDict) -> None:
        """测试自定义条件异常"""
        # 通过execute方法测试条件
        config = {
            "conditions": [
                {
                    "type": "custom",
                    "next_node": "custom_node",
                    "parameters": {"custom_condition_code": "invalid_code"}
                }
            ],
            "default_next_node": "default_node"
        }
        result = node.execute(sample_state, config)

        # 验证异常情况下返回默认节点
        assert result.next_node == "default_node"

    def test_register_condition_function(self, node: ConditionNode) -> None:
        """测试注册条件函数"""
        def custom_condition(state: WorkflowState, parameters: Dict[str, Any], config: Dict[str, Any]) -> bool:
            return True

        from src.infrastructure.graph.edges.conditions import ConditionType
        node.register_condition_function(ConditionType.CUSTOM, custom_condition)
        # 验证函数已注册（通过检查条件类型列表）
        assert ConditionType.CUSTOM in node._evaluator.list_condition_types()

    def test_list_condition_types(self, node: ConditionNode) -> None:
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