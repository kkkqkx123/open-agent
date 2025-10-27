"""LLM节点单元测试"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict, Optional, List

from src.infrastructure.graph.nodes.llm_node import LLMNode
from src.infrastructure.graph.registry import NodeExecutionResult
from src.domain.agent.state import AgentState, AgentMessage
from src.infrastructure.llm.interfaces import ILLMClient
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.infrastructure.llm.config import LLMConfig


class TestLLMNode:
    """LLM节点测试"""

    @pytest.fixture
    def mock_llm_client(self):
        """模拟LLM客户端"""
        return Mock(spec=ILLMClient)

    @pytest.fixture
    def node(self, mock_llm_client):
        """创建LLM节点实例"""
        return LLMNode(mock_llm_client)

    @pytest.fixture
    def sample_state(self):
        """示例状态"""
        return AgentState(
            messages=[
                AgentMessage(content="用户输入", role="user"),
                AgentMessage(content="分析结果", role="assistant")
            ],
            input="用户输入",
            output=None,
            tool_calls=[],
            tool_results=[{"result": "工具执行结果"}],
            iteration_count=0,
            max_iterations=10,
            errors=[],
            complete=False,
            context={},
            current_step="llm_generation"
        )

    @pytest.fixture
    def sample_config(self):
        """示例配置"""
        return {
            "llm_client": "test_client",
            "max_tokens": 1000,
            "temperature": 0.7,
            "system_prompt": "你是一个智能助手",
            "include_tool_results": True
        }

    @pytest.fixture
    def sample_llm_response(self):
        """示例LLM响应"""
        return LLMResponse(
            content="LLM生成的响应",
            message=AgentMessage(content="LLM生成的响应", role="assistant"),
            model="test-model",
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        )

    def test_init(self, mock_llm_client):
        """测试初始化"""
        node = LLMNode(mock_llm_client)
        assert node._llm_client == mock_llm_client

    def test_init_without_llm_client(self):
        """测试不带LLM客户端初始化"""
        node = LLMNode()
        assert node._llm_client is None

    def test_node_type_property(self, node):
        """测试节点类型属性"""
        assert node.node_type == "llm_node"

    def test_execute_success(self, node, mock_llm_client, sample_state, sample_config, sample_llm_response):
        """测试执行成功"""
        # 配置模拟
        mock_llm_client.generate.return_value = sample_llm_response
        mock_llm_client.get_model_info.return_value = {"model": "test-model"}
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert isinstance(result, NodeExecutionResult)
        assert len(result.state.messages) == 3  # 原有2条消息 + 新增1条
        assert result.state.messages[-1].content == "LLM生成的响应"
        assert result.state.messages[-1].role == "assistant"
        assert result.next_node is None
        assert "llm_response" in result.metadata
        assert result.metadata["llm_response"] == "LLM生成的响应"
        assert "model_info" in result.metadata

    def test_execute_with_next_node(self, node, mock_llm_client, sample_state, sample_config, sample_llm_response):
        """测试执行并指定下一个节点"""
        # 配置模拟
        mock_llm_client.generate.return_value = sample_llm_response
        mock_llm_client.get_model_info.return_value = {"model": "test-model"}
        
        # 修改配置以指定下一个节点
        sample_config["next_node"] = "next_node"
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert result.next_node == "next_node"

    def test_execute_with_follow_up(self, node, mock_llm_client, sample_state, sample_config):
        """测试执行并需要进一步处理"""
        # 创建需要进一步处理的响应
        llm_response = LLMResponse(
            content="需要更多信息来回答这个问题",
            message=AgentMessage(content="需要更多信息来回答这个问题", role="assistant"),
            model="test-model",
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        )
        
        # 配置模拟
        mock_llm_client.generate.return_value = llm_response
        mock_llm_client.get_model_info.return_value = {"model": "test-model"}
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert result.next_node == "analyze"

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
        node = LLMNode(mock_llm_client)
        result = node._get_llm_client({})
        assert result == mock_llm_client

    def test_get_llm_client_without_instance(self):
        """测试获取LLM客户端（不使用实例）"""
        node = LLMNode()
        result = node._get_llm_client({})
        assert result is not None
        assert isinstance(result, ILLMClient)

    def test_build_system_prompt_with_template(self, node):
        """测试构建系统提示词（使用模板）"""
        state = Mock()
        state.tool_results = []
        config = {
            "system_prompt_template": "最大迭代次数: {max_iterations}, 当前步骤: {current_step}",
            "max_iterations": 10
        }
        state.max_iterations = 10
        state.current_step = "test_step"
        
        prompt = node._build_system_prompt(state, config)
        assert "最大迭代次数: 10" in prompt
        assert "当前步骤: test_step" in prompt

    def test_build_system_prompt_with_tool_results(self, node, sample_state):
        """测试构建系统提示词（包含工具结果）"""
        config = {
            "system_prompt": "基础提示词",
            "include_tool_results": True
        }
        
        prompt = node._build_system_prompt(sample_state, config)
        assert "基础提示词" in prompt
        assert "工具执行结果" in prompt

    def test_process_prompt_template(self, node):
        """测试处理提示词模板"""
        template = "最大迭代次数: {max_iterations}, 消息数量: {messages_count}"
        state = Mock()
        state.max_iterations = 10
        state.messages = ["msg1", "msg2"]
        config = {}
        
        result = node._process_prompt_template(template, state, config)
        assert result == "最大迭代次数: 10, 消息数量: 2"

    def test_get_default_system_prompt(self, node):
        """测试获取默认系统提示词"""
        prompt = node._get_default_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "智能助手" in prompt

    def test_format_tool_results(self, node):
        """测试格式化工具结果"""
        tool_results = [
            Mock(success=True, tool_name="tool1", result="结果1", error=None),
            Mock(success=False, tool_name="tool2", result=None, error="错误信息")
        ]
        
        formatted = node._format_tool_results(tool_results)
        assert isinstance(formatted, str)
        assert "工具 1: tool1 - 成功" in formatted
        assert "工具 2: tool2 - 失败" in formatted
        assert "结果: 结果1" in formatted
        assert "错误: 错误信息" in formatted

    def test_format_tool_results_empty(self, node):
        """测试格式化空工具结果"""
        tool_results = []
        formatted = node._format_tool_results(tool_results)
        assert formatted == "没有工具执行结果"

    def test_prepare_messages(self, node, sample_state):
        """测试准备消息"""
        system_prompt = "系统提示词"
        messages = node._prepare_messages(sample_state, system_prompt)
        
        assert isinstance(messages, list)
        assert len(messages) == 3  # 系统消息 + 2条原有消息
        # 检查系统消息类型（可能因LangChain可用性而不同）
        assert hasattr(messages[0], 'content') or isinstance(messages[0], dict)

    def test_truncate_messages_for_context(self, node):
        """测试截断消息以适应上下文"""
        messages = [Mock() for _ in range(15)]  # 创建15条消息
        system_prompt = "系统提示词"
        
        truncated = node._truncate_messages_for_context(messages, system_prompt)
        assert len(truncated) <= 10  # 应该被截断到最多10条

    def test_prepare_parameters(self, node):
        """测试准备参数"""
        config = {
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1,
            "stop_sequences": ["\n", "."]
        }
        
        parameters = node._prepare_parameters(config)
        assert parameters["max_tokens"] == 1000
        assert parameters["temperature"] == 0.7
        assert parameters["top_p"] == 0.9
        assert parameters["frequency_penalty"] == 0.1
        assert parameters["presence_penalty"] == 0.1
        assert parameters["stop"] == ["\n", "."]

    def test_determine_next_node_with_config(self, node, sample_config):
        """测试确定下一个节点（配置指定）"""
        sample_config["next_node"] = "next_node"
        response = Mock()
        response.content = "普通响应"
        
        next_node = node._determine_next_node(response, sample_config)
        assert next_node == "next_node"

    def test_determine_next_node_with_follow_up(self, node, sample_config):
        """测试确定下一个节点（需要进一步处理）"""
        sample_config.pop("next_node", None)  # 确保没有配置下一个节点
        response = Mock()
        response.content = "需要更多信息来完成这个任务"
        
        next_node = node._determine_next_node(response, sample_config)
        assert next_node == "analyze"

    def test_determine_next_node_default(self, node, sample_config):
        """测试确定下一个节点（默认情况）"""
        sample_config.pop("next_node", None)  # 确保没有配置下一个节点
        response = Mock()
        response.content = "普通响应"
        
        next_node = node._determine_next_node(response, sample_config)
        assert next_node is None

    def test_needs_follow_up_true(self, node):
        """测试需要进一步处理（真）"""
        content = "我需要更多信息来回答这个问题"
        result = node._needs_follow_up(content)
        assert result is True

    def test_needs_follow_up_false(self, node):
        """测试需要进一步处理（假）"""
        content = "这是完整的答案"
        result = node._needs_follow_up(content)
        assert result is False