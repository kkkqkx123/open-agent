"""工具节点单元测试"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict, Optional, List

from src.infrastructure.graph.nodes.tool_node import ToolNode
from src.infrastructure.graph.registry import NodeExecutionResult
from src.domain.agent.state import AgentState
from src.domain.tools.interfaces import IToolRegistry, ToolCall, ToolResult


class TestToolNode:
    """工具节点测试"""

    @pytest.fixture
    def mock_tool_manager(self):
        """模拟工具管理器"""
        return Mock(spec=IToolRegistry)

    @pytest.fixture
    def node(self, mock_tool_manager):
        """创建工具节点实例"""
        return ToolNode(mock_tool_manager)

    @pytest.fixture
    def sample_state(self):
        """示例状态"""
        from src.domain.agent.state import AgentState, AgentMessage
        from src.domain.tools.interfaces import ToolCall
        
        state = AgentState(
            agent_id="test-agent",
            agent_type="test",
            messages=[],
            tool_results=[],
            max_iterations=10,
            iteration_count=0,
            errors=[]
        )
        
        # 添加工具调用到消息的新属性中
        message = AgentMessage(
            content="测试输入",
            role="human",
            tool_calls=[{"name": "test_tool", "arguments": {"param": "value"}}]
        )
        # 同时保持 metadata 中的工具调用（向后兼容）
        message.metadata["tool_calls"] = [{"name": "test_tool", "arguments": {"param": "value"}}]
        state.messages.append(message)
        
        return state

    @pytest.fixture
    def sample_config(self):
        """示例配置"""
        return {
            "tool_manager": "test_manager",
            "timeout": 30,
            "continue_on_error": True
        }

    def test_init(self, mock_tool_manager):
        """测试初始化"""
        node = ToolNode(mock_tool_manager)
        assert node._tool_manager == mock_tool_manager

    def test_init_without_tool_manager(self):
        """测试不带工具管理器初始化"""
        node = ToolNode()
        assert node._tool_manager is None

    def test_node_type_property(self, node):
        """测试节点类型属性"""
        assert node.node_type == "tool_node"

    def test_execute_success(self, node, mock_tool_manager, sample_state, sample_config):
        """测试执行成功"""
        # 创建模拟工具和结果
        mock_tool = Mock()
        mock_tool.execute.return_value = "工具执行结果"
        mock_tool_manager.get_tool.return_value = mock_tool
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert isinstance(result, NodeExecutionResult)
        assert len(result.state.tool_results) == 1
        assert result.state.tool_results[0].success is True
        assert result.state.tool_results[0].output == "工具执行结果"
        assert result.next_node == "analyze"
        assert result.metadata is not None
        assert "tool_calls_count" in result.metadata
        assert result.metadata["tool_calls_count"] == 1

    def test_execute_no_tool_calls(self, node, sample_state, sample_config):
        """测试执行无工具调用"""
        # 清空工具调用
        sample_state.messages[-1].metadata["tool_calls"] = []
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert isinstance(result, NodeExecutionResult)
        assert result.state == sample_state
        assert result.next_node == "analyze"
        assert result.metadata is not None
        assert "message" in result.metadata
        assert result.metadata["message"] == "没有找到工具调用"

    def test_execute_tool_not_found(self, node, mock_tool_manager, sample_state, sample_config):
        """测试执行工具未找到"""
        # 配置模拟返回None
        mock_tool_manager.get_tool.return_value = None
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert isinstance(result, NodeExecutionResult)
        assert len(result.state.tool_results) == 1
        assert result.state.tool_results[0].success is False
        assert result.state.tool_results[0].error is not None
        assert "not found" in result.state.tool_results[0].error
        assert result.next_node == "analyze"

    def test_execute_tool_exception(self, node, mock_tool_manager, sample_state, sample_config):
        """测试执行工具异常"""
        # 配置模拟抛出异常
        mock_tool = Mock()
        mock_tool.execute.side_effect = Exception("工具执行错误")
        mock_tool_manager.get_tool.return_value = mock_tool
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert isinstance(result, NodeExecutionResult)
        assert len(result.state.tool_results) == 1
        assert result.state.tool_results[0].success is False
        assert result.state.tool_results[0].error is not None
        assert "工具执行错误" in result.state.tool_results[0].error
        assert result.next_node == "analyze"
        assert result.metadata is not None
        assert "errors" in result.metadata

    def test_execute_continue_on_error_false(self, node, mock_tool_manager, sample_state):
        """测试执行错误时不停止"""
        # 配置模拟抛出异常
        mock_tool = Mock()
        mock_tool.execute.side_effect = Exception("工具执行错误")
        mock_tool_manager.get_tool.return_value = mock_tool
        
        # 修改配置
        config = {
            "tool_manager": "test_manager",
            "timeout": 30,
            "continue_on_error": False
        }
        
        # 执行
        result = node.execute(sample_state, config)
        
        # 验证
        assert result.next_node == "analyze"  # 即使错误也返回analyze

    def test_get_config_schema(self, node):
        """测试获取配置模式"""
        schema = node.get_config_schema()
        
        assert isinstance(schema, dict)
        assert "type" in schema
        assert "properties" in schema
        assert "required" in schema
        assert "tool_manager" in schema["properties"]
        assert "timeout" in schema["properties"]
        assert "continue_on_error" in schema["properties"]
        assert "tool_manager" in schema["required"]

    def test_get_tool_manager_with_instance(self, mock_tool_manager):
        """测试获取工具管理器（使用实例）"""
        node = ToolNode(mock_tool_manager)
        result = node._get_tool_manager({})
        assert result == mock_tool_manager

    def test_get_tool_manager_without_instance(self):
        """测试获取工具管理器（不使用实例）"""
        node = ToolNode()
        result = node._get_tool_manager({})
        assert result is not None
        assert isinstance(result, IToolRegistry)

    def test_extract_tool_calls_from_messages(self, node, sample_state, sample_config):
        """测试从消息中提取工具调用"""
        # 修改状态以包含工具调用消息
        from src.domain.agent.state import AgentMessage
        message = AgentMessage(content="测试消息", role="human")
        message.metadata["tool_calls"] = [{"name": "message_tool", "arguments": {}}]
        sample_state.messages = [message]
        
        # 执行
        tool_calls = node._extract_tool_calls(sample_state, sample_config)
        
        # 验证
        assert len(tool_calls) == 1
        assert isinstance(tool_calls[0], ToolCall)
        assert tool_calls[0].name == "message_tool"

    def test_extract_tool_calls_from_text(self, node, sample_state, sample_config):
        """测试从文本中提取工具调用"""
        # 修改状态以包含工具调用文本
        from src.domain.agent.state import AgentMessage
        message = AgentMessage(
            content="调用工具:test_tool(param1=value1, param2=value2)", 
            role="human"
        )
        sample_state.messages = [message]
        
        # 执行
        tool_calls = node._extract_tool_calls(sample_state, sample_config)
        
        # 验证
        assert len(tool_calls) == 1
        assert isinstance(tool_calls[0], ToolCall)
        assert tool_calls[0].name == "test_tool"

    def test_parse_tool_calls_from_text_success(self, node):
        """测试从文本解析工具调用成功"""
        content = "调用工具:test_tool(param1=value1, param2=value2)"
        tool_calls = node._parse_tool_calls_from_text(content)
        
        assert len(tool_calls) == 1
        assert isinstance(tool_calls[0], ToolCall)
        assert tool_calls[0].name == "test_tool"

    def test_parse_tool_calls_from_text_invalid_json(self, node):
        """测试从文本解析工具调用（无效JSON）"""
        content = "调用工具:test_tool(invalid_json)"
        tool_calls = node._parse_tool_calls_from_text(content)
        
        assert len(tool_calls) == 1
        assert isinstance(tool_calls[0], ToolCall)
        assert tool_calls[0].name == "test_tool"

    def test_parse_tool_calls_from_text_no_match(self, node):
        """测试从文本解析工具调用（无匹配）"""
        content = "普通文本内容"
        tool_calls = node._parse_tool_calls_from_text(content)
        
        assert len(tool_calls) == 0

    def test_determine_next_node_all_success(self, node, sample_config):
        """测试确定下一个节点（全部成功）"""
        tool_results = [Mock(success=True), Mock(success=True)]
        execution_errors = []
        
        next_node = node._determine_next_node(tool_results, execution_errors, sample_config)
        assert next_node == "analyze"

    def test_determine_next_node_with_errors_continue(self, node, sample_config):
        """测试确定下一个节点（有错误但继续）"""
        tool_results = [Mock(success=True)]
        execution_errors = ["错误1"]
        
        next_node = node._determine_next_node(tool_results, execution_errors, sample_config)
        assert next_node == "analyze"

    def test_determine_next_node_with_errors_stop(self, node):
        """测试确定下一个节点（有错误且停止）"""
        tool_results = [Mock(success=True)]
        execution_errors = ["错误1"]
        config = {"continue_on_error": False}
        
        next_node = node._determine_next_node(tool_results, execution_errors, config)
        assert next_node == "analyze"  # 当前实现总是返回analyze

    def test_extract_tool_calls_from_new_property(self, node, sample_config):
        """测试从新的 tool_calls 属性中提取工具调用"""
        from src.domain.agent.state import AgentMessage
        
        # 创建带有新属性的消息
        message = AgentMessage(
            content="测试输入",
            role="human",
            tool_calls=[
                {"name": "new_tool", "arguments": {"param1": "value1"}},
                {"name": "another_tool", "arguments": {"param2": "value2"}}
            ]
        )
        
        state = AgentState(
            agent_id="test-agent",
            agent_type="test",
            messages=[message],
            tool_results=[],
            max_iterations=10,
            iteration_count=0,
            errors=[]
        )
        
        # 执行
        tool_calls = node._extract_tool_calls(state, sample_config)
        
        # 验证
        assert len(tool_calls) == 2
        assert tool_calls[0].name == "new_tool"
        assert tool_calls[0].arguments["param1"] == "value1"
        assert tool_calls[1].name == "another_tool"
        assert tool_calls[1].arguments["param2"] == "value2"

    def test_extract_tool_calls_prefer_new_property(self, node, sample_config):
        """测试优先使用新的 tool_calls 属性而不是 metadata"""
        from src.domain.agent.state import AgentMessage
        
        # 创建同时有新属性和 metadata 的消息
        message = AgentMessage(
            content="测试输入",
            role="human",
            tool_calls=[{"name": "new_tool", "arguments": {"param": "value"}}],
            metadata={"tool_calls": [{"name": "old_tool", "arguments": {"param": "old_value"}}]}
        )
        
        state = AgentState(
            agent_id="test-agent",
            agent_type="test",
            messages=[message],
            tool_results=[],
            max_iterations=10,
            iteration_count=0,
            errors=[]
        )
        
        # 执行
        tool_calls = node._extract_tool_calls(state, sample_config)
        
        # 验证应该使用新属性
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "new_tool"
        assert tool_calls[0].arguments["param"] == "value"

    def test_extract_tool_calls_with_additional_kwargs(self, node, sample_config):
        """测试从 additional_kwargs 中提取工具调用（OpenAI 格式）"""
        from src.domain.agent.state import AgentMessage
        
        # 创建带有 additional_kwargs 的消息
        message = AgentMessage(
            content="测试输入",
            role="human",
            additional_kwargs={
                "tool_calls": [
                    {
                        "id": "call_123",
                        "function": {
                            "name": "openai_tool",
                            "arguments": '{"param": "openai_value"}'
                        },
                        "type": "function"
                    }
                ]
            }
        )
        
        state = AgentState(
            agent_id="test-agent",
            agent_type="test",
            messages=[message],
            tool_results=[],
            max_iterations=10,
            iteration_count=0,
            errors=[]
        )
        
        # 执行
        tool_calls = node._extract_tool_calls(state, sample_config)
        
        # 验证
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "openai_tool"
        assert tool_calls[0].arguments["param"] == "openai_value"
        assert tool_calls[0].call_id == "call_123"

    def test_parse_tool_calls_from_text_multiple_patterns(self, node):
        """测试从文本解析多种模式的工具调用"""
        # 测试英文模式
        content = "call tool:english_tool(arg1=value1)"
        tool_calls = node._parse_tool_calls_from_text(content)
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "english_tool"
        
        # 测试简化模式
        content = "simple_tool(param=value)"
        tool_calls = node._parse_tool_calls_from_text(content)
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "simple_tool"
        
        # 测试 JSON 模式
        content = '{"tool": "json_tool", "args": {"key": "value"}}'
        tool_calls = node._parse_tool_calls_from_text(content)
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "json_tool"
        assert tool_calls[0].arguments["key"] == "value"

    def test_parse_key_value_pairs(self, node):
        """测试键值对解析"""
        # 测试冒号分隔
        args = node._parse_key_value_pairs("key1:value1 key2:value2")
        assert args["key1"] == "value1"
        assert args["key2"] == "value2"
        
        # 测试等号分隔
        args = node._parse_key_value_pairs("key1=value1 key2=value2")
        assert args["key1"] == "value1"
        assert args["key2"] == "value2"
        
        # 测试类型推断
        args = node._parse_key_value_pairs("bool:true int:42 float:3.14 str:text")
        assert args["bool"] is True
        assert args["int"] == 42
        assert args["float"] == 3.14
        assert args["str"] == "text"

    def test_is_float(self, node):
        """测试浮点数检测"""
        assert node._is_float("3.14") is True
        assert node._is_float("42") is False
        assert node._is_float("not_a_number") is False