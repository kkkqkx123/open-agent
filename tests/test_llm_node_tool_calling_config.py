"""测试LLM节点工具调用配置功能"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from src.core.workflow.graph.nodes.llm_node import LLMNode
from src.interfaces.llm import ILLMClient
from src.interfaces.state.base import IState


class TestLLMNodeToolCallingConfig:
    """测试LLM节点工具调用配置"""

    @pytest.fixture
    def mock_llm_client(self) -> ILLMClient:
        """模拟LLM客户端"""
        client = Mock(spec=ILLMClient)
        client.supports_function_calling.return_value = True
        client.supports_jsonl.return_value = False
        client.generate = AsyncMock()
        client.get_model_info.return_value = {"model": "test-model"}
        return client

    @pytest.fixture
    def mock_state(self) -> IState:
        """模拟状态"""
        state = Mock(spec=IState)
        state.get_data.return_value = []
        state.set_data = Mock()
        return state

    @pytest.fixture
    def llm_node(self, mock_llm_client: ILLMClient) -> LLMNode:
        """创建LLM节点实例"""
        return LLMNode(llm_client=mock_llm_client)

    def test_process_tools_config_default_values(self, llm_node: LLMNode):
        """测试工具配置的默认值处理"""
        config = {}
        processed = llm_node._process_tools_config(config)
        
        # 验证默认值
        assert processed["tools"]["enabled"] is False
        assert processed["tools"]["available_tools"] == []

    def test_process_tools_config_custom_values(self, llm_node: LLMNode):
        """测试工具配置的自定义值处理"""
        config = {
            "tools": {
                "enabled": True,
                "available_tools": ["tool1", "tool2"]
            }
        }
        processed = llm_node._process_tools_config(config)
        
        # 验证自定义值
        assert processed["tools"]["enabled"] is True
        assert processed["tools"]["available_tools"] == ["tool1", "tool2"]

    def test_determine_tools_strategy(self, llm_node: LLMNode, mock_llm_client: Mock):
        """测试工具策略选择"""
        # 测试function_calling优先
        mock_llm_client.supports_function_calling = Mock(return_value=True)
        strategy = llm_node._determine_tools_strategy(mock_llm_client)
        assert strategy == "function_calling"
        
        # 测试jsonl回退
        mock_llm_client.supports_function_calling = Mock(return_value=False)
        strategy = llm_node._determine_tools_strategy(mock_llm_client)
        assert strategy == "jsonl"

    def test_should_enable_tools(self, llm_node: LLMNode):
        """测试工具启用判断逻辑"""
        # 测试默认情况（工具禁用）
        config = {}
        assert llm_node._should_enable_tools(config) is False
        
        # 测试工具禁用
        config = {"tools": {"enabled": False}}
        assert llm_node._should_enable_tools(config) is False
        
        # 测试无可用工具
        config = {"tools": {"enabled": True, "available_tools": []}}
        assert llm_node._should_enable_tools(config) is False
        
        # 测试完整启用条件
        config = {"tools": {"enabled": True, "available_tools": ["tool1"]}}
        assert llm_node._should_enable_tools(config) is True

    @pytest.mark.asyncio
    async def test_preprocess_config_integration(self, llm_node: LLMNode, mock_state: IState):
        """测试配置预处理的集成"""
        config = {
            "tools": {
                "enabled": True,
                "available_tools": ["tool1"]
            }
        }
        
        processed = await llm_node._preprocess_config(mock_state, config)
        
        # 验证工具配置被正确处理
        assert "tools" in processed
        assert processed["tools"]["enabled"] is True

    def test_get_fallback_schema_includes_tool_config(self, llm_node: LLMNode):
        """测试fallback schema包含工具配置"""
        schema = llm_node._get_fallback_schema()
        
        # 验证工具配置schema
        assert "tools" in schema["properties"]
        tools_schema = schema["properties"]["tools"]
        assert tools_schema["type"] == "object"
        assert "enabled" in tools_schema["properties"]
        assert "available_tools" in tools_schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_async_with_tool_config(self, llm_node: LLMNode, mock_llm_client: Mock, mock_state: Mock):
        """测试执行异步方法包含工具配置"""
        # 模拟LLM响应
        mock_response = Mock()
        mock_response.content = "测试响应"
        mock_llm_client.generate = AsyncMock(return_value=mock_response)
        
        config = {
            "tools": {
                "enabled": True,
                "available_tools": ["tool1"]
            },
            "user_input": "测试输入"
        }
        
        result = await llm_node.execute_async(mock_state, config)
        
        # 验证结果包含工具配置信息
        assert "tools_config" in result.metadata
        assert result.metadata["tools_config"]["enabled"] is True


if __name__ == "__main__":
    pytest.main([__file__])