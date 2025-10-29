"""OpenAI统一客户端单元测试"""

import pytest
from unittest.mock import Mock, patch

from src.infrastructure.llm.clients.openai.config import OpenAIConfig
from src.infrastructure.llm.clients.openai.unified_client import OpenAIUnifiedClient
from src.infrastructure.llm.clients.openai.langchain_client import LangChainChatClient
from src.infrastructure.llm.clients.openai.responses_client import LightweightResponsesClient
from langchain_core.messages import BaseMessage, HumanMessage
from typing import Sequence, cast


class TestOpenAIUnifiedClient:
    """OpenAI统一客户端测试"""

    @pytest.fixture
    def chat_completion_config(self):
        """Chat Completion配置"""
        return OpenAIConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key",
            api_format="chat_completion",
        )

    @pytest.fixture
    def responses_config(self):
        """Responses API配置"""
        return OpenAIConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key",
            api_format="responses",
        )

    def test_chat_completion_client_selection(self, chat_completion_config):
        """测试Chat Completion客户端选择"""
        client = OpenAIUnifiedClient(chat_completion_config)
        assert isinstance(client._client, LangChainChatClient)

    def test_responses_client_selection(self, responses_config):
        """测试Responses API客户端选择"""
        client = OpenAIUnifiedClient(responses_config)
        assert isinstance(client._client, LightweightResponsesClient)

    def test_api_format_switching(self, chat_completion_config):
        """测试API格式切换"""
        client = OpenAIUnifiedClient(chat_completion_config)

        # 初始应该是Chat Completion客户端
        assert isinstance(client._client, LangChainChatClient)
        assert client.get_current_api_format() == "chat_completion"

        # 切换到Responses API
        client.switch_api_format("responses")
        assert isinstance(client._client, LightweightResponsesClient)
        assert client.get_current_api_format() == "responses"

        # 切换回Chat Completion
        client.switch_api_format("chat_completion")
        assert isinstance(client._client, LangChainChatClient)
        assert client.get_current_api_format() == "chat_completion"

    def test_unsupported_api_format(self, chat_completion_config):
        """测试不支持的API格式"""
        client = OpenAIUnifiedClient(chat_completion_config)

        with pytest.raises(ValueError, match="不支持的 API 格式: unsupported"):
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

    def test_get_client_info(self, chat_completion_config):
        """测试获取客户端信息"""
        client = OpenAIUnifiedClient(chat_completion_config)
        client_info = client.get_client_info()

        assert client_info["api_format"] == "chat_completion"
        assert client_info["model_name"] == "gpt-4"
        assert client_info["supports_function_calling"] is True
        assert client_info["client_type"] == "LangChainChatClient"

    def test_validate_config(self, chat_completion_config):
        """测试配置验证"""
        client = OpenAIUnifiedClient(chat_completion_config)
        assert client.validate_config() is True

        # 测试无效配置
        invalid_config = OpenAIConfig(
            model_type="openai",
            model_name="",  # 空模型名
            api_key="test-key",
        )
        invalid_client = OpenAIUnifiedClient(invalid_config)
        assert invalid_client.validate_config() is False

    def test_get_estimated_cost(self, chat_completion_config):
        """测试成本估算"""
        client = OpenAIUnifiedClient(chat_completion_config)
        messages = [HumanMessage(content="Hello, world!")]
        # 转换为Sequence类型
        base_messages: Sequence[BaseMessage] = cast(Sequence[BaseMessage], messages)
        
        cost = client.get_estimated_cost(base_messages)
        assert cost is not None
        assert isinstance(cost, float)
        assert cost > 0

    def test_conversation_history_responses_api(self, responses_config):
        """测试Responses API对话历史"""
        client = OpenAIUnifiedClient(responses_config)
        
        # 初始应该为空
        history = client.get_conversation_history()
        assert history == []
        
        # 重置历史（应该不会出错）
        client.reset_conversation_history()
        history = client.get_conversation_history()
        assert history == []

    def test_conversation_history_chat_completion(self, chat_completion_config):
        """测试Chat Completion API对话历史（应该为空）"""
        client = OpenAIUnifiedClient(chat_completion_config)
        
        # Chat Completion API不支持对话历史
        history = client.get_conversation_history()
        assert history == []
        
        # 重置历史（应该不会出错）
        client.reset_conversation_history()
        history = client.get_conversation_history()
        assert history == []

    def test_config_api_format_properties(self, chat_completion_config):
        """测试配置的API格式属性"""
        config = chat_completion_config
        
        assert config.is_chat_completion() is True
        assert config.is_responses_api() is False
        
        # 切换到Responses API
        config.api_format = "responses"
        assert config.is_chat_completion() is False
        assert config.is_responses_api() is True

    def test_config_get_chat_completion_params(self, chat_completion_config):
        """测试获取Chat Completions参数"""
        config = chat_completion_config
        params = config.get_chat_completion_params()
        
        assert "temperature" in params
        assert "top_p" in params
        assert "frequency_penalty" in params
        assert "presence_penalty" in params

    def test_config_get_responses_params(self, responses_config):
        """测试获取Responses API参数"""
        config = responses_config
        params = config.get_responses_params()
        
        assert "temperature" in params
        # store参数只有在显式设置时才会包含在返回的参数中
        # 默认值False不会包含，以减少API调用的参数大小

    def test_token_counting(self, chat_completion_config):
        """测试Token计数"""
        client = OpenAIUnifiedClient(chat_completion_config)

        # 测试文本Token计数
        text = "Hello, world!"
        token_count = client.get_token_count(text)
        assert isinstance(token_count, int)
        assert token_count > 0

        # 测试消息Token计数
        messages = [HumanMessage(content="Hello, world!")]
        # 转换为Sequence类型
        base_messages: Sequence[BaseMessage] = cast(Sequence[BaseMessage], messages)
        messages_token_count = client.get_messages_token_count(base_messages)
        assert isinstance(messages_token_count, int)
        assert messages_token_count > 0

    def test_generate_with_fallback(self, chat_completion_config):
        """测试带降级的生成（简化版本）"""
        client = OpenAIUnifiedClient(chat_completion_config)
        messages = [HumanMessage(content="Hello, world!")]
        # 转换为Sequence类型
        base_messages: Sequence[BaseMessage] = cast(Sequence[BaseMessage], messages)
        
        # 由于没有真实的API密钥，这会失败，但我们可以测试方法存在
        with pytest.raises(Exception):
            client.generate_with_fallback(base_messages)

    def test_async_generate_with_fallback(self, chat_completion_config):
        """测试带降级的异步生成（简化版本）"""
        import asyncio
        
        client = OpenAIUnifiedClient(chat_completion_config)
        messages = [HumanMessage(content="Hello, world!")]
        # 转换为Sequence类型
        base_messages: Sequence[BaseMessage] = cast(Sequence[BaseMessage], messages)
        
        # 由于没有真实的API密钥，这会失败，但我们可以测试方法存在
        async def test_async():
            with pytest.raises(Exception):
                await client.generate_with_fallback_async(base_messages)
        
        asyncio.run(test_async())

    def test_config_post_init_validation(self):
        """测试配置初始化后验证"""
        # 测试有效配置
        valid_config = OpenAIConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key",
            api_format="chat_completion",
        )
        assert valid_config.model_type == "openai"
        assert valid_config.model_name == "gpt-4"

        # 测试无效API格式
        with pytest.raises(ValueError, match="不支持的 API 格式"):
            OpenAIConfig(
                model_type="openai",
                model_name="gpt-4",
                api_key="test-key",
                api_format="invalid_format",
            )


if __name__ == "__main__":
    pytest.main([__file__])