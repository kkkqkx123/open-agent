"""分析节点单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, Optional, List

from src.infrastructure.graph.nodes.analysis_node import AnalysisNode
from src.infrastructure.graph.registry import NodeExecutionResult
from src.domain.agent.state import AgentState, AgentMessage
from src.infrastructure.llm.interfaces import ILLMClient
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.infrastructure.llm.config import LLMConfig


class TestAnalysisNode:
    """分析节点测试"""

    @pytest.fixture
    def mock_llm_client(self):
        """模拟LLM客户端"""
        return Mock(spec=ILLMClient)

    @pytest.fixture
    def node(self, mock_llm_client):
        """创建分析节点实例"""
        return AnalysisNode(mock_llm_client)

    @pytest.fixture
    def sample_state(self):
        """示例状态"""
        # 使用域层的状态类型
        from src.domain.agent.state import AgentState, AgentMessage
        state = AgentState(
            messages=[
                AgentMessage(content="用户输入", role="user"),
                AgentMessage(content="AI响应", role="assistant")
            ]
        )
        return state
        return state

    @pytest.fixture
    def sample_config(self):
        """示例配置"""
        return {
            "llm_client": "test_client",
            "max_tokens": 1000,
            "temperature": 0.7,
            "system_prompt": "你是一个智能助手"
        }

    @pytest.fixture
    def sample_llm_response(self):
        """示例LLM响应"""
        return LLMResponse(
            content="分析结果",
            message=AgentMessage(content="分析结果", role="assistant"),
            model="test-model",
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        )

    def test_init(self, mock_llm_client):
        """测试初始化"""
        node = AnalysisNode(mock_llm_client)
        assert node._llm_client == mock_llm_client

    def test_init_without_llm_client(self):
        """测试不带LLM客户端初始化"""
        node = AnalysisNode()
        assert node._llm_client is None

    def test_node_type_property(self, node):
        """测试节点类型属性"""
        assert node.node_type == "analysis_node"

    def test_execute_success(self, node, mock_llm_client, sample_state, sample_config, sample_llm_response):
        """测试执行成功"""
        # 配置模拟
        mock_llm_client.generate.return_value = sample_llm_response
        mock_llm_client.supports_function_calling.return_value = False
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert isinstance(result, NodeExecutionResult)
        # 处理不同类型的state.messages
        if hasattr(result.state, 'messages'):
            # 如果state是对象且有messages属性
            messages = result.state.messages
        elif isinstance(result.state, dict) and 'messages' in result.state:
            # 如果state是字典且包含messages键
            messages = result.state['messages']
        else:
            # 如果无法识别state的类型，默认为空列表
            messages = []
        
        # 系统消息不会被添加到状态中，只用于LLM调用
        # 所以状态中应该只有原有2条消息 + 新增1条 = 3条消息
        # 系统消息只用于LLM调用，不会添加到状态中
        assert len(messages) == 3  # 原有2条消息 + 新增1条
        # 检查最后一条消息的内容
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            assert last_message.content == "分析结果"
        elif isinstance(last_message, dict):
            assert last_message.get('content') == "分析结果"
        assert result.next_node is None
        assert result.metadata is not None
        assert "llm_response" in result.metadata
        assert result.metadata["llm_response"] == "分析结果"

    def test_execute_with_tool_calls(self, node, mock_llm_client, sample_state, sample_config):
        """测试执行并检测到工具调用"""
        # 创建包含工具调用的响应
        llm_response = LLMResponse(
            content="需要调用工具",
            message=AgentMessage(content="需要调用工具", role="assistant"),
            model="test-model",
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        )
        
        # 配置模拟
        mock_llm_client.generate.return_value = llm_response
        mock_llm_client.supports_function_calling.return_value = True
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert result.next_node == "execute_tool"
        assert "tool_calls" in result.metadata

    def test_execute_with_tool_indication(self, node, mock_llm_client, sample_state, sample_config):
        """测试执行并检测到工具调用指示"""
        # 创建包含工具调用指示的响应
        llm_response = LLMResponse(
            content="我需要调用一个工具来获取信息",
            message=AgentMessage(content="我需要调用一个工具来获取信息", role="assistant"),
            model="test-model",
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        )
        
        # 配置模拟
        mock_llm_client.generate.return_value = llm_response
        mock_llm_client.supports_function_calling.return_value = False
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert result.next_node == "execute_tool"

    def test_get_config_schema(self, node):
        """测试获取配置模式"""
        schema = node.get_config_schema()
        
        assert isinstance(schema, dict)
        assert "type" in schema
        assert "properties" in schema
        assert "required" in schema
        assert "llm_client" in schema["properties"]
        assert "system_prompt" in schema["properties"]
        assert "max_tokens" in schema["properties"]
        assert "temperature" in schema["properties"]
        assert "llm_client" in schema["required"]

    def test_get_llm_client_with_instance(self, mock_llm_client):
        """测试获取LLM客户端（使用实例）"""
        node = AnalysisNode(mock_llm_client)
        result = node._get_llm_client({})
        assert result == mock_llm_client

    def test_get_llm_client_without_instance(self):
        """测试获取LLM客户端（不使用实例）"""
        node = AnalysisNode()
        result = node._get_llm_client({})
        assert result is not None
        assert isinstance(result, ILLMClient)

    def test_get_default_system_prompt(self, node):
        """测试获取默认系统提示词"""
        prompt = node._get_default_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "智能助手" in prompt

    def test_prepare_messages(self, node, sample_state):
        """测试准备消息"""
        system_prompt = "系统提示词"
        messages = node._prepare_messages(sample_state, system_prompt)
        
        assert isinstance(messages, list)
        # 系统消息 + 2条原有消息 = 3条消息
        assert len(messages) == 3
        # 检查系统消息类型（应该是一个字典）
        assert isinstance(messages[0], dict)
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "系统提示词"
        # 检查历史消息是否被正确转换
        assert messages[1]["role"] == "user"  # HumanMessage转换为user
        assert messages[1]["content"] == "用户输入"
        assert messages[2]["role"] == "assistant"  # AIMessage转换为assistant
        assert messages[2]["content"] == "AI响应"

    def test_get_tool_functions(self, node):
        """测试获取工具函数"""
        config_with_tools = {"available_tools": ["tool1", "tool2"]}
        config_without_tools = {"available_tools": []}
        
        # 测试有可用工具的情况
        result = node._get_tool_functions(config_with_tools)
        assert result is not None  # 当前实现返回空列表
        
        # 测试无可用工具的情况
        result = node._get_tool_functions(config_without_tools)
        assert result is None

    def test_determine_next_node_with_tool_calls(self, node, sample_config):
        """测试确定下一个节点（有工具调用）"""
        response = Mock()
        response.tool_calls = [{"name": "test_tool"}]
        
        next_node = node._determine_next_node(response, sample_config)
        assert next_node == "execute_tool"

    def test_determine_next_node_with_tool_indication(self, node, sample_config):
        """测试确定下一个节点（有工具调用指示）"""
        response = Mock()
        response.tool_calls = None
        response.content = "我需要调用工具"
        
        next_node = node._determine_next_node(response, sample_config)
        assert next_node == "execute_tool"

    def test_determine_next_node_default(self, node, sample_config):
        """测试确定下一个节点（默认情况）"""
        response = Mock()
        response.tool_calls = None
        response.content = "普通响应"
        
        next_node = node._determine_next_node(response, sample_config)
        assert next_node is None

    def test_contains_tool_indication_true(self, node):
        """测试包含工具调用指示（真）"""
        content = "我需要查询数据库来获取信息"
        result = node._contains_tool_indication(content)
        assert result is True

    def test_contains_tool_indication_false(self, node):
        """测试包含工具调用指示（假）"""
        content = "这是一个普通响应"
        result = node._contains_tool_indication(content)
        assert result is False