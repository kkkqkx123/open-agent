"""Token计算器集成测试"""

import pytest
from typing import Any

# Import langchain messages
from langchain_core.messages import HumanMessage, AIMessage  # type: ignore

from src.llm.token_calculators.local_calculator import LocalTokenCalculator
from src.llm.token_calculators.api_calculator import ApiTokenCalculator
from src.llm.token_calculators.hybrid_calculator import HybridTokenCalculator
from src.llm.token_parsers.openai_parser import OpenAIParser
from src.llm.token_parsers.gemini_parser import GeminiParser
from src.llm.token_parsers.anthropic_parser import AnthropicParser


class TestTokenCalculatorIntegration:
    """Token计算器集成测试"""
    
    def test_local_calculator_integration(self) -> None:
        """测试本地计算器集成"""
        calculator = LocalTokenCalculator("gpt-3.5-turbo", "openai")
        
        # 测试文本token计数
        text = "Hello, world! This is a test message."
        token_count = calculator.count_tokens(text)
        assert isinstance(token_count, int)
        assert token_count > 0
        
        # 测试消息token计数
        messages = [
            HumanMessage(content="What is the weather today?"),
            AIMessage(content="It's sunny and warm.")
        ]
        message_token_count = calculator.count_messages_tokens(messages)
        assert isinstance(message_token_count, int)
        assert message_token_count > 0
        
        # 测试模型信息
        model_info = calculator.get_model_info()
        assert "model_name" in model_info
        assert "provider" in model_info
        assert "calculator_type" in model_info
    
    def test_api_calculator_integration(self) -> None:
        """测试API计算器集成"""
        calculator = ApiTokenCalculator("gpt-3.5-turbo", "openai")
        
        # 初始状态检查
        assert calculator.is_api_usage_available() is False
        assert calculator.get_last_api_usage() is None
        
        # 模拟API响应
        api_response = {
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 8,
                "total_tokens": 23
            },
            "model": "gpt-3.5-turbo"
        }
        
        # 更新API响应
        success = calculator.update_from_api_response(api_response, "test context")
        assert success is True
        assert calculator.is_api_usage_available() is True
        
        # 获取最后使用情况
        last_usage = calculator.get_last_api_usage()
        assert last_usage is not None
        assert last_usage.total_tokens == 23
        
        # 测试缓存功能
        cached_count = calculator.count_tokens("test context")
        assert cached_count == 23
    
    def test_hybrid_calculator_integration(self) -> None:
        """测试混合计算器集成"""
        calculator = HybridTokenCalculator("gpt-3.5-turbo", "openai", True)
        
        # 初始状态：API不可用，应该使用本地计算器
        text = "Hello, world! This is a test message."
        count1 = calculator.count_tokens(text)
        stats = calculator.get_stats()
        assert stats["local_count"] == 1
        assert stats["api_count"] == 0
        
        # 更新API响应后，API变为可用
        api_response = {
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 6,
                "total_tokens": 18
            }
        }
        calculator.update_from_api_response(api_response, text)
        
        # 现在应该使用API计算器
        count2 = calculator.count_tokens(text)
        stats = calculator.get_stats()
        assert stats["api_count"] == 1
        assert count2 == 18
        
        # 测试模型信息
        model_info = calculator.get_model_info()
        assert "model_name" in model_info
        assert "provider" in model_info
        assert "calculator_type" in model_info
        assert "stats" in model_info
    
    def test_parser_integration(self) -> None:
        """测试解析器集成"""
        # 测试OpenAI解析器
        openai_parser = OpenAIParser()
        openai_response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            },
            "model": "gpt-3.5-turbo"
        }
        openai_usage = openai_parser.parse_response(openai_response)
        assert openai_usage is not None
        assert openai_usage.total_tokens == 15
        
        # 测试Gemini解析器
        gemini_parser = GeminiParser()
        gemini_response = {
            "usageMetadata": {
                "promptTokenCount": 8,
                "candidatesTokenCount": 4,
                "totalTokenCount": 12
            },
            "model": "gemini-pro"
        }
        gemini_usage = gemini_parser.parse_response(gemini_response)
        assert gemini_usage is not None
        assert gemini_usage.total_tokens == 12
        
        # 测试Anthropic解析器
        anthropic_parser = AnthropicParser()
        anthropic_response = {
            "usage": {
                "input_tokens": 12,
                "output_tokens": 6
            },
            "model": "claude-3-sonnet-20240229"
        }
        anthropic_usage = anthropic_parser.parse_response(anthropic_response)
        assert anthropic_usage is not None
        assert anthropic_usage.total_tokens == 18


class TestCrossProviderIntegration:
    """跨提供商集成测试"""
    
    def test_different_providers_local_calculation(self) -> None:
        """测试不同提供商的本地计算"""
        providers = [
            ("gpt-3.5-turbo", "openai"),
            ("gemini-pro", "gemini"),
            ("claude-3-sonnet-20240229", "anthropic")
        ]
        
        text = "Hello, world! This is a test message for cross-provider integration."
        
        for model_name, provider in providers:
            calculator = LocalTokenCalculator(model_name, provider)
            token_count = calculator.count_tokens(text)
            
            # 验证返回值类型
            assert isinstance(token_count, int)
            assert token_count > 0
            
            # 验证模型信息
            model_info = calculator.get_model_info()
            assert model_info["model_name"] == model_name
            assert model_info["provider"] == provider
    
    def test_hybrid_calculator_with_different_providers(self) -> None:
        """测试混合计算器与不同提供商"""
        providers = [
            ("gpt-3.5-turbo", "openai"),
            ("gemini-pro", "gemini"),
            ("claude-3-sonnet-20240229", "anthropic")
        ]
        
        text = "Hello, world! This is a test message."
        
        for model_name, provider in providers:
            calculator = HybridTokenCalculator(model_name, provider, True)
            
            # 初始状态：使用本地计算器
            count = calculator.count_tokens(text)
            assert isinstance(count, int)
            assert count > 0
            
            # 更新API响应
            response = None
            if provider == "openai":
                response = {"usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}}
            elif provider == "gemini":
                response = {"usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 3, "totalTokenCount": 8}}
            elif provider == "anthropic":
                response = {"usage": {"input_tokens": 5, "output_tokens": 3}}
            
            assert response is not None
            success = calculator.update_from_api_response(response, text)
            assert success is True
            
            # 现在应该使用API计算器
            count = calculator.count_tokens(text)
            assert count == 8
