"""OpenAI统一客户端单元测试"""

import pytest
from unittest.mock import Mock, patch

from src.llm.clients.openai.config import OpenAIConfig
from src.llm.clients.openai.unified_client import OpenAIUnifiedClient
from src.llm.clients.openai.adapters.chat_completion import ChatCompletionAdapter
from src.llm.clients.openai.adapters.responses_api import ResponsesAPIAdapter
from langchain_core.messages import BaseMessage
from typing import List, cast


class TestOpenAIUnifiedClient:
    """OpenAI统一客户端测试"""
    
    @pytest.fixture
    def chat_completion_config(self):
        """Chat Completion配置"""
        return OpenAIConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key",
            api_format="chat_completion"
        )
    
    @pytest.fixture
    def responses_config(self):
        """Responses API配置"""
        return OpenAIConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key",
            api_format="responses"
        )
    
    def test_chat_completion_adapter_selection(self, chat_completion_config):
        """测试Chat Completion适配器选择"""
        client = OpenAIUnifiedClient(chat_completion_config)
        assert isinstance(client._adapter, ChatCompletionAdapter)
    
    def test_responses_adapter_selection(self, responses_config):
        """测试Responses API适配器选择"""
        client = OpenAIUnifiedClient(responses_config)
        assert isinstance(client._adapter, ResponsesAPIAdapter)
    
    def test_api_format_switching(self, chat_completion_config):
        """测试API格式切换"""
        client = OpenAIUnifiedClient(chat_completion_config)
        
        # 初始应该是Chat Completion适配器
        assert isinstance(client._adapter, ChatCompletionAdapter)
        assert client.get_current_api_format() == "chat_completion"
        
        # 切换到Responses API
        client.switch_api_format("responses")
        assert isinstance(client._adapter, ResponsesAPIAdapter)
        assert client.get_current_api_format() == "responses"
        
        # 切换回Chat Completion
        client.switch_api_format("chat_completion")
        assert isinstance(client._adapter, ChatCompletionAdapter)
        assert client.get_current_api_format() == "chat_completion"
    
    def test_unsupported_api_format(self, chat_completion_config):
        """测试不支持的API格式"""
        client = OpenAIUnifiedClient(chat_completion_config)
        
        with pytest.raises(ValueError, match="不支持的API格式: unsupported"):
            client.switch_api_format("unsupported")
    
    def test_get_supported_api_formats(self, chat_completion_config):
        """测试获取支持的API格式"""
        client = OpenAIUnifiedClient(chat_completion_config)
        supported_formats = client.get_supported_api_formats()
        
        assert "chat_completion" in supported_formats
        assert "responses" in supported_formats
        assert len(supported_formats) == 2
    
    def test_supports_function_calling(self, chat_completion_config):
        """测试函数调用支持"""
        client = OpenAIUnifiedClient(chat_completion_config)
        assert client.supports_function_calling() is True
    
    def test_get_model_info(self, chat_completion_config):
        """测试获取模型信息"""
        client = OpenAIUnifiedClient(chat_completion_config)
        model_info = client.get_model_info()
        
        assert model_info["name"] == "gpt-4"
        assert model_info["type"] == "openai"
        assert model_info["supports_function_calling"] is True
        assert model_info["supports_streaming"] is True
    
    def test_config_api_format_switching(self):
        """测试配置的API格式切换"""
        config = OpenAIConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key",
            api_format="chat_completion"
        )
        
        assert config.api_format == "chat_completion"
        
        # 切换到Responses API
        config.switch_api_format("responses")
        assert config.api_format == "responses"
        
        # 切换回Chat Completion
        config.switch_api_format("chat_completion")
        assert config.api_format == "chat_completion"
    
    def test_config_unsupported_api_format(self):
        """测试配置的不支持的API格式"""
        config = OpenAIConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key",
            api_format="chat_completion"
        )
        
        with pytest.raises(ValueError, match="不支持的API格式: unsupported"):
            config.switch_api_format("unsupported")
    
    def test_config_get_api_format_config(self):
        """测试获取API格式配置"""
        config = OpenAIConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key"
        )
        
        chat_config = config.get_api_format_config("chat_completion")
        assert chat_config["endpoint"] == "/chat/completions"
        assert chat_config["supports_multiple_choices"] is True
        
        responses_config = config.get_api_format_config("responses")
        assert responses_config["endpoint"] == "/responses"
        assert responses_config["supports_reasoning"] is True
    
    def test_config_is_api_format_supported(self):
        """测试检查API格式支持"""
        config = OpenAIConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key"
        )
        
        assert config.is_api_format_supported("chat_completion") is True
        assert config.is_api_format_supported("responses") is True
        assert config.is_api_format_supported("unsupported") is False
    
    def test_config_get_fallback_formats(self):
        """测试获取降级格式"""
        config = OpenAIConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key",
            api_format="chat_completion",
            fallback_enabled=True,
            fallback_formats=["chat_completion", "responses"]
        )
        
        # 当前使用chat_completion，降级格式应该只有responses
        fallback_formats = config.get_fallback_formats()
        assert "responses" in fallback_formats
        assert "chat_completion" not in fallback_formats
        
        # 切换到responses，降级格式应该只有chat_completion
        config.switch_api_format("responses")
        fallback_formats = config.get_fallback_formats()
        assert "chat_completion" in fallback_formats
        assert "responses" not in fallback_formats
    
    def test_config_fallback_disabled(self):
        """测试降级功能禁用"""
        config = OpenAIConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key",
            fallback_enabled=False
        )
        
        fallback_formats = config.get_fallback_formats()
        assert fallback_formats == []
    
    def test_token_counting(self, chat_completion_config):
        """测试Token计数"""
        client = OpenAIUnifiedClient(chat_completion_config)
        
        # 测试文本Token计数
        text = "Hello, world!"
        token_count = client.get_token_count(text)
        assert isinstance(token_count, int)
        assert token_count > 0
        
        # 测试消息Token计数
        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content="Hello, world!")]
        # 显式转换类型以解决不变性问题
        base_messages: List[BaseMessage] = cast(List[BaseMessage], messages)
        messages_token_count = client.get_messages_token_count(base_messages)
        assert isinstance(messages_token_count, int)
        assert messages_token_count > 0


if __name__ == "__main__":
    pytest.main([__file__])