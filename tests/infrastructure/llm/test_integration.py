"""HTTP客户端集成测试

测试HTTP客户端系统的端到端功能。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from httpx import Response

from src.infrastructure.llm.http_client import create_http_client
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.infrastructure.messages import HumanMessage, AIMessage


class TestHttpClientIntegration:
    """HTTP客户端集成测试类"""
    
    @pytest.fixture
    def mock_openai_response(self):
        """模拟OpenAI响应数据"""
        return {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you today?"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 9,
                "total_tokens": 19
            }
        }
    
    @pytest.fixture
    def mock_gemini_response(self):
        """模拟Gemini响应数据"""
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "Hello! How can I help you today?"
                            }
                        ],
                        "role": "model"
                    },
                    "finishReason": "STOP"
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 9,
                "totalTokenCount": 19
            }
        }
    
    @pytest.fixture
    def mock_anthropic_response(self):
        """模拟Anthropic响应数据"""
        return {
            "id": "msg_test",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "Hello! How can I help you today?"
                }
            ],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 9
            }
        }
    
    @pytest.mark.asyncio
    async def test_openai_client_integration(self, mock_openai_response):
        """测试OpenAI客户端集成"""
        # 创建模拟响应
        mock_response = Mock(spec=Response)
        mock_response.json.return_value = mock_openai_response
        mock_response.raise_for_status = Mock()
        
        # 创建客户端
        with patch('src.infrastructure.llm.http_client.openai_http_client.OpenAIHttpClient.post') as mock_post:
            mock_post.return_value = mock_response
            
            client = create_http_client(
                provider="openai",
                model="gpt-4",
                api_key="test-api-key"
            )
            
            # 测试聊天完成
            messages = [HumanMessage(content="Hello")]
            response = await client.chat_completions(
                messages=messages,
                model="gpt-4"
            )
            
            # 验证响应
            assert isinstance(response, LLMResponse)
            assert response.content == "Hello! How can I help you today?"
            assert response.model == "gpt-4"
            assert response.finish_reason == "stop"
            assert isinstance(response.token_usage, TokenUsage)
            assert response.token_usage.total_tokens == 19
            
            # 验证API调用
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_gemini_client_integration(self, mock_gemini_response):
        """测试Gemini客户端集成"""
        # 创建模拟响应
        mock_response = Mock(spec=Response)
        mock_response.json.return_value = mock_gemini_response
        mock_response.raise_for_status = Mock()
        
        # 创建客户端
        with patch('src.infrastructure.llm.http_client.gemini_http_client.GeminiHttpClient.post') as mock_post:
            mock_post.return_value = mock_response
            
            client = create_http_client(
                provider="gemini",
                model="gemini-1.5-pro",
                api_key="test-gemini-key"
            )
            
            # 测试聊天完成
            messages = [HumanMessage(content="Hello")]
            response = await client.chat_completions(
                messages=messages,
                model="gemini-1.5-pro"
            )
            
            # 验证响应
            assert isinstance(response, LLMResponse)
            assert response.content == "Hello! How can I help you today?"
            assert response.model == "gemini-1.5-pro"
            assert response.finish_reason == "STOP"
            assert isinstance(response.token_usage, TokenUsage)
            assert response.token_usage.total_tokens == 19
            
            # 验证API调用
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_anthropic_client_integration(self, mock_anthropic_response):
        """测试Anthropic客户端集成"""
        # 创建模拟响应
        mock_response = Mock(spec=Response)
        mock_response.json.return_value = mock_anthropic_response
        mock_response.raise_for_status = Mock()
        
        # 创建客户端
        with patch('src.infrastructure.llm.http_client.anthropic_http_client.AnthropicHttpClient.post') as mock_post:
            mock_post.return_value = mock_response
            
            client = create_http_client(
                provider="anthropic",
                model="claude-3-sonnet-20240229",
                api_key="test-anthropic-key"
            )
            
            # 测试聊天完成
            messages = [HumanMessage(content="Hello")]
            response = await client.chat_completions(
                messages=messages,
                model="claude-3-sonnet-20240229"
            )
            
            # 验证响应
            assert isinstance(response, LLMResponse)
            assert response.content == "Hello! How can I help you today?"
            assert response.model == "claude-3-sonnet-20240229"
            assert response.finish_reason == "end_turn"
            assert isinstance(response.token_usage, TokenUsage)
            assert response.token_usage.total_tokens == 19
            
            # 验证API调用
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_openai_streaming_integration(self):
        """测试OpenAI流式响应集成"""
        # 模拟流式响应数据
        stream_chunks = [
            'data: {"choices": [{"delta": {"content": "Hello"}}]}\n',
            'data: {"choices": [{"delta": {"content": "!"}}]}\n',
            'data: {"choices": [{"delta": {"content": " How"}}]}\n',
            'data: {"choices": [{"delta": {"content": " can"}}]}\n',
            'data: {"choices": [{"delta": {"content": " I"}}]}\n',
            'data: {"choices": [{"delta": {"content": " help"}}]}\n',
            'data: {"choices": [{"delta": {"content": " you"}}]}\n',
            'data: {"choices": [{"delta": {"content": "?"}}]}\n',
            'data: [DONE]\n'
        ]
        
        # 创建客户端
        with patch('src.infrastructure.llm.http_client.openai_http_client.OpenAIHttpClient.stream_post') as mock_stream:
            mock_stream.return_value = stream_chunks.__aiter__()
            
            client = create_http_client(
                provider="openai",
                model="gpt-4",
                api_key="test-api-key"
            )
            
            # 测试流式聊天完成
            messages = [HumanMessage(content="Hello")]
            stream_response = client.chat_completions(
                messages=messages,
                model="gpt-4",
                stream=True
            )
            
            # 收集流式响应
            content_chunks = []
            async for chunk in stream_response:
                content_chunks.append(chunk)
            
            # 验证流式响应
            assert len(content_chunks) == 8
            assert "".join(content_chunks) == "Hello! How can I help you?"
            
            # 验证API调用
            mock_stream.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 创建客户端
        with patch('src.infrastructure.llm.http_client.openai_http_client.OpenAIHttpClient.post') as mock_post:
            # 模拟API错误
            mock_post.side_effect = Exception("API Error")
            
            client = create_http_client(
                provider="openai",
                model="gpt-4",
                api_key="test-api-key"
            )
            
            # 测试错误处理
            messages = [HumanMessage(content="Hello")]
            
            with pytest.raises(Exception, match="API Error"):
                await client.chat_completions(
                    messages=messages,
                    model="gpt-4"
                )
    
    def test_provider_support(self):
        """测试提供商支持"""
        # 测试所有支持的提供商
        providers = ["openai", "gemini", "anthropic"]
        
        for provider in providers:
            client = create_http_client(
                provider=provider,
                api_key="test-key"
            )
            
            assert client.get_provider_name() == provider
            
            # 验证支持的模型
            models = client.get_supported_models()
            assert isinstance(models, list)
            assert len(models) > 0
    
    def test_client_configuration(self):
        """测试客户端配置"""
        # 测试自定义配置
        client = create_http_client(
            provider="openai",
            api_key="test-key",
            timeout=60,
            max_retries=5,
            pool_connections=20
        )
        
        # 验证配置已应用
        assert client.timeout == 60
        assert client.max_retries == 5
    
    @pytest.mark.asyncio
    async def test_responses_api_compatibility(self):
        """测试Responses API兼容性"""
        # 创建模拟响应
        mock_response = Mock(spec=Response)
        mock_response.json.return_value = {
            "id": "resp_test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-5",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a responses API response"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 6,
                "total_tokens": 11,
                "reasoning_tokens": 3
            }
        }
        mock_response.raise_for_status = Mock()
        
        # 创建客户端
        with patch('src.infrastructure.llm.http_client.openai_http_client.OpenAIHttpClient.post') as mock_post:
            mock_post.return_value = mock_response
            
            client = create_http_client(
                provider="openai",
                model="gpt-5",
                api_key="test-api-key"
            )
            
            # 测试Responses API
            response = await client.responses_api(
                input_text="Test input",
                model="gpt-5"
            )
            
            # 验证响应
            assert isinstance(response, LLMResponse)
            assert response.content == "This is a responses API response"
            assert response.model == "gpt-5"
            assert response.token_usage.reasoning_tokens == 3


if __name__ == "__main__":
    pytest.main([__file__])