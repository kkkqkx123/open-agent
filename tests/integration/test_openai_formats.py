"""OpenAI格式集成测试"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.llm.factory import create_client
from src.llm.clients.openai.config import OpenAIConfig
from src.llm.clients.openai.unified_client import OpenAIUnifiedClient
from langchain_core.messages import HumanMessage


class TestOpenAIFormatsIntegration:
    """OpenAI格式集成测试"""
    
    @pytest.fixture
    def chat_completion_config_dict(self):
        """Chat Completion配置字典"""
        return {
            "model_type": "openai",
            "model_name": "gpt-4",
            "api_key": "test-key",
            "api_format": "chat_completion",
            "temperature": 0.7,
            "max_tokens": 100
        }
    
    @pytest.fixture
    def responses_config_dict(self):
        """Responses API配置字典"""
        return {
            "model_type": "openai",
            "model_name": "gpt-4",
            "api_key": "test-key",
            "api_format": "responses",
            "temperature": 0.7,
            "max_tokens": 100
        }
    
    def test_factory_creates_unified_client(self, chat_completion_config_dict):
        """测试工厂创建统一客户端"""
        client = create_client(chat_completion_config_dict)
        
        assert isinstance(client, OpenAIUnifiedClient)
        assert client.get_current_api_format() == "chat_completion"
    
    def test_factory_with_responses_format(self, responses_config_dict):
        """测试工厂创建Responses API客户端"""
        client = create_client(responses_config_dict)
        
        assert isinstance(client, OpenAIUnifiedClient)
        assert client.get_current_api_format() == "responses"
    
    def test_config_from_dict_with_api_format(self):
        """测试从字典创建配置时包含API格式"""
        config_dict = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "api_key": "test-key",
            "api_format": "responses",
            "api_format_configs": {
                "chat_completion": {
                    "endpoint": "/chat/completions",
                    "supports_multiple_choices": True
                },
                "responses": {
                    "endpoint": "/responses",
                    "supports_reasoning": True
                }
            },
            "fallback_formats": ["chat_completion", "responses"]
        }
        
        config = OpenAIConfig.from_dict(config_dict)
        
        assert isinstance(config, OpenAIConfig)
        assert config.api_format == "responses"
        assert "chat_completion" in config.api_format_configs
        assert "responses" in config.api_format_configs
        assert "chat_completion" in config.fallback_formats
        assert "responses" in config.fallback_formats
    
    def test_backward_compatibility(self):
        """测试向后兼容性"""
        # 旧配置格式（不包含api_format）
        old_config_dict = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "api_key": "test-key",
            "temperature": 0.7
        }
        
        client = create_client(old_config_dict)
        
        assert isinstance(client, OpenAIUnifiedClient)
        # 默认应该使用chat_completion格式
        assert client.get_current_api_format() == "chat_completion"
    
    @patch('src.llm.clients.openai.adapters.chat_completion.ChatOpenAI')
    def test_chat_completion_generation(self, mock_chat_openai, chat_completion_config_dict):
        """测试Chat Completion生成"""
        # 模拟ChatOpenAI响应
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_response.model = "gpt-4"
        mock_response.usage_metadata = {
            'input_tokens': 10,
            'output_tokens': 5,
            'total_tokens': 15
        }
        mock_response.response_metadata = {}
        
        mock_instance = Mock()
        mock_instance.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_instance
        
        client = create_client(chat_completion_config_dict)
        
        messages = [HumanMessage(content="Hello, world!")]
        response = client.generate(messages)
        
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.token_usage.prompt_tokens == 10
        assert response.token_usage.completion_tokens == 5
        assert response.token_usage.total_tokens == 15
        
        # 验证调用了invoke方法
        mock_instance.invoke.assert_called_once()
    
    @patch('src.llm.clients.openai.native_client.OpenAIResponsesClient.create_response_sync')
    def test_responses_api_generation(self, mock_create_response, responses_config_dict):
        """测试Responses API生成"""
        # 模拟Responses API响应
        mock_response = {
            "id": "resp_123",
            "object": "response",
            "model": "gpt-4",
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "Test response from Responses API"
                        }
                    ]
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        mock_create_response.return_value = mock_response
        
        client = create_client(responses_config_dict)
        
        messages = [HumanMessage(content="Hello, world!")]
        response = client.generate(messages)
        
        assert response.content == "Test response from Responses API"
        assert response.model == "gpt-4"
        assert response.token_usage.prompt_tokens == 10
        assert response.token_usage.completion_tokens == 5
        assert response.token_usage.total_tokens == 15
        
        # 验证调用了create_response_sync方法
        mock_create_response.assert_called_once()
    
    def test_api_format_switching_integration(self, chat_completion_config_dict):
        """测试API格式切换集成"""
        client = create_client(chat_completion_config_dict)
        
        # 初始状态
        assert client.get_current_api_format() == "chat_completion"
        
        # 切换到Responses API
        client.switch_api_format("responses")
        assert client.get_current_api_format() == "responses"
        
        # 切换回Chat Completion
        client.switch_api_format("chat_completion")
        assert client.get_current_api_format() == "chat_completion"
    
    def test_fallback_configuration(self):
        """测试降级配置"""
        config_dict = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "api_key": "test-key",
            "api_format": "responses",
            "fallback_enabled": True,
            "fallback_formats": ["chat_completion", "responses"]
        }
        
        client = create_client(config_dict)
        
        # 当前使用responses格式
        assert client.get_current_api_format() == "responses"
        
        # 获取降级格式（应该排除当前格式）
        # 注意：降级功能在客户端内部实现，这里主要测试配置
        config = client.config
        fallback_formats = config.get_fallback_formats()
        assert "chat_completion" in fallback_formats
        assert "responses" not in fallback_formats
    
    def test_token_usage_integration(self, chat_completion_config_dict):
        """测试Token使用集成"""
        client = create_client(chat_completion_config_dict)
        
        # 测试文本Token计数
        text = "Hello, world! This is a test message."
        token_count = client.get_token_count(text)
        assert isinstance(token_count, int)
        assert token_count > 0
        
        # 测试消息Token计数
        messages = [
            HumanMessage(content="Hello, how are you?"),
            HumanMessage(content="What's the weather like today?")
        ]
        messages_token_count = client.get_messages_token_count(messages)
        assert isinstance(messages_token_count, int)
        assert messages_token_count > 0


if __name__ == "__main__":
    pytest.main([__file__])