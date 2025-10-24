"""Token解析器单元测试"""

import pytest
from datetime import datetime
from src.llm.token_parsers.base import TokenUsage, ITokenParser
from src.llm.token_parsers.openai_parser import OpenAIParser
from src.llm.token_parsers.gemini_parser import GeminiParser
from src.llm.token_parsers.anthropic_parser import AnthropicParser


class TestTokenUsage:
    """TokenUsage数据类测试"""
    
    def test_token_usage_initialization(self) -> None:
        """测试TokenUsage初始化"""
        usage = TokenUsage(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15
        )
        
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 15
        assert usage.source == "local"
        assert isinstance(usage.timestamp, datetime)
        assert usage.additional_info == {}
    
    def test_token_usage_with_custom_values(self) -> None:
        """测试TokenUsage自定义值"""
        custom_info = {"model": "gpt-3.5-turbo"}
        usage = TokenUsage(
            prompt_tokens=20,
            completion_tokens=10,
            total_tokens=30,
            source="api",
            additional_info=custom_info
        )
        
        assert usage.prompt_tokens == 20
        assert usage.completion_tokens == 10
        assert usage.total_tokens == 30
        assert usage.source == "api"
        assert usage.additional_info == custom_info


class TestOpenAIParser:
    """OpenAI解析器测试"""
    
    def test_parse_valid_response(self) -> None:
        """测试解析有效的OpenAI响应"""
        parser = OpenAIParser()
        response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            },
            "model": "gpt-3.5-turbo",
            "id": "chatcmpl-123"
        }
        
        usage = parser.parse_response(response)
        assert usage is not None
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 15
        assert usage.source == "api"
        assert usage.additional_info is not None
        assert usage.additional_info["model"] == "gpt-3.5-turbo"
        assert usage.additional_info["response_id"] == "chatcmpl-123"
    
    def test_parse_invalid_response(self) -> None:
        """测试解析无效的OpenAI响应"""
        parser = OpenAIParser()
        response = {"invalid": "response"}
        
        usage = parser.parse_response(response)
        assert usage is None
    
    def test_get_provider_name(self) -> None:
        """测试获取提供商名称"""
        parser = OpenAIParser()
        assert parser.get_provider_name() == "openai"
    
    def test_is_supported_response(self) -> None:
        """测试是否支持响应"""
        parser = OpenAIParser()
        response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        assert parser.is_supported_response(response) is True
        
        invalid_response = {"invalid": "response"}
        assert parser.is_supported_response(invalid_response) is False


class TestGeminiParser:
    """Gemini解析器测试"""
    
    def test_parse_valid_response(self) -> None:
        """测试解析有效的Gemini响应"""
        parser = GeminiParser()
        response = {
            "usageMetadata": {
                "promptTokenCount": 8,
                "candidatesTokenCount": 4,
                "totalTokenCount": 12
            },
            "model": "gemini-pro"
        }
        
        usage = parser.parse_response(response)
        assert usage is not None
        assert usage.prompt_tokens == 8
        assert usage.completion_tokens == 4
        assert usage.total_tokens == 12
        assert usage.source == "api"
        assert usage.additional_info is not None
        assert usage.additional_info["model"] == "gemini-pro"
    
    def test_parse_invalid_response(self) -> None:
        """测试解析无效的Gemini响应"""
        parser = GeminiParser()
        response = {"invalid": "response"}
        
        usage = parser.parse_response(response)
        assert usage is None
    
    def test_get_provider_name(self) -> None:
        """测试获取提供商名称"""
        parser = GeminiParser()
        assert parser.get_provider_name() == "gemini"
    
    def test_is_supported_response(self) -> None:
        """测试是否支持响应"""
        parser = GeminiParser()
        response = {
            "usageMetadata": {
                "promptTokenCount": 8,
                "candidatesTokenCount": 4,
                "totalTokenCount": 12
            }
        }
        
        assert parser.is_supported_response(response) is True
        
        invalid_response = {"invalid": "response"}
        assert parser.is_supported_response(invalid_response) is False


class TestAnthropicParser:
    """Anthropic解析器测试"""
    
    def test_parse_valid_response(self) -> None:
        """测试解析有效的Anthropic响应"""
        parser = AnthropicParser()
        response = {
            "usage": {
                "input_tokens": 12,
                "output_tokens": 6
            },
            "model": "claude-3-sonnet-20240229",
            "type": "message"
        }
        
        usage = parser.parse_response(response)
        assert usage is not None
        assert usage.prompt_tokens == 12
        assert usage.completion_tokens == 6
        assert usage.total_tokens == 18
        assert usage.source == "api"
        assert usage.additional_info is not None
        assert usage.additional_info["model"] == "claude-3-sonnet-20240229"
    
    def test_parse_invalid_response(self) -> None:
        """测试解析无效的Anthropic响应"""
        parser = AnthropicParser()
        response = {"invalid": "response"}
        
        usage = parser.parse_response(response)
        assert usage is None
    
    def test_get_provider_name(self) -> None:
        """测试获取提供商名称"""
        parser = AnthropicParser()
        assert parser.get_provider_name() == "anthropic"
    
    def test_is_supported_response(self) -> None:
        """测试是否支持响应"""
        parser = AnthropicParser()
        response = {
            "usage": {
                "input_tokens": 12,
                "output_tokens": 6
            }
        }
        
        assert parser.is_supported_response(response) is True
        
        response2 = {"type": "message"}
        assert parser.is_supported_response(response2) is True
        
        invalid_response = {"invalid": "response"}
        assert parser.is_supported_response(invalid_response) is False
