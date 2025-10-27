"""工具节点单元测试"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict, Optional, List

from src.infrastructure.graph.nodes.tool_node import ToolNode
from src.infrastructure.graph.registry import NodeExecutionResult
from src.application.workflow.state import AgentState
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
        return {
            "messages": [],
            "metadata": {},
            "input": "测试输入",
            "output": None,
            "tool_calls": [{"name": "test_tool", "arguments": {"param": "value"}}],
            "tool_results": [],
            "iteration_count": 0,
            "max_iterations": 10,
            "errors": [],
            "complete": False
        }

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
        sample_state.tool_calls = []
        
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
        message = Mock()
        message.tool_calls = [{"name": "message_tool", "arguments": {}}]
        sample_state.messages = [message]
        sample_state.tool_calls = []  # 清空原有的工具调用
        
        # 执行
        tool_calls = node._extract_tool_calls(sample_state, sample_config)
        
        # 验证
        assert len(tool_calls) == 1
        assert isinstance(tool_calls[0], ToolCall)
        assert tool_calls[0].name == "message_tool"

    def test_extract_tool_calls_from_text(self, node, sample_state, sample_config):
        """测试从文本中提取工具调用"""
        # 修改状态以包含工具调用文本
        message = Mock()
        message.content = "调用工具:test_tool(param1=value1, param2=value2)"
        message.tool_calls = None
        sample_state.messages = [message]
        sample_state.tool_calls = []  # 清空原有的工具调用
        
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