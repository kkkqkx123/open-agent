"""Token计算器单元测试"""

import sys
import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage

from src.llm.token_calculators.base import ITokenCalculator
from src.llm.token_calculators.local_calculator import LocalTokenCalculator
from src.llm.token_calculators.api_calculator import ApiTokenCalculator
from src.llm.token_calculators.hybrid_calculator import HybridTokenCalculator
from src.llm.token_parsers.base import TokenUsage


class TestLocalTokenCalculator:
    """本地Token计算器测试"""
    
    def test_initialization(self):
        """测试初始化"""
        calculator = LocalTokenCalculator("gpt-3.5-turbo", "openai")
        assert calculator.model_name == "gpt-3.5-turbo"
        assert calculator.provider == "openai"
    
    def test_count_tokens_with_tiktoken(self):
        """测试使用tiktoken计数token"""
        with patch('tiktoken.encoding_for_model') as mock_encoding_for_model:
            mock_encoding = Mock()
            mock_encoding.encode.return_value = [1, 2, 3]
            mock_encoding_for_model.return_value = mock_encoding
            
            calculator = LocalTokenCalculator("gpt-3.5-turbo", "openai")
            count = calculator.count_tokens("Hello, world!")
            
            assert count == 3
            mock_encoding.encode.assert_called_once_with("Hello, world!")
    
    def test_count_tokens_without_tiktoken(self):
        """测试不使用tiktoken计数token"""
        calculator = LocalTokenCalculator("gemini-pro", "gemini")
        # 强制设置_encoding为None以模拟没有tiktoken的情况
        calculator._encoding = None
        
        text = "Hello, world!"  # 13 characters
        expected_count = len(text) // 4  # 13 // 4 = 3
        count = calculator.count_tokens(text)
        assert count == expected_count
    
    def test_count_tokens_with_simple_estimation(self):
        """测试使用简单估算计数token"""
        # 使用非OpenAI提供商来触发简单估算
        calculator = LocalTokenCalculator("test-model", "unknown")
        
        # 检查是否正确初始化为简单估算模式
        assert calculator._encoding is None
        
        test_cases = [
            ("Hello", 5 // 4),  # 1 token
            ("Hello, world!", 13 // 4),  # 3 tokens
            ("This is a longer text for testing token counting", 48 // 4),  # 12 tokens
            ("", 0),  # 0 tokens
            ("a", 1 // 4),  # 0 tokens
            ("ab", 2 // 4),  # 0 tokens
            ("abc", 3 // 4),  # 0 tokens
            ("abcd", 4 // 4),  # 1 token
        ]
        
        for text, expected_count in test_cases:
            count = calculator.count_tokens(text)
            assert count == expected_count, f"Text '{text}' should have {expected_count} tokens, got {count}"
    
    def test_tiktoken_import_error_fallback(self):
        """测试tiktoken导入错误时的降级"""
        # 模拟tiktoken导入失败
        with patch.dict('sys.modules', {'tiktoken': None}):
            # 创建计算器，应该降级到简单估算
            calculator = LocalTokenCalculator("gpt-3.5-turbo", "openai")
            
            # 验证降级到简单估算
            assert calculator._encoding is None
            
            # 测试简单估算功能
            text = "Hello, world!"  # 13 characters
            expected_count = len(text) // 4  # 13 // 4 = 3
            count = calculator.count_tokens(text)
            assert count == expected_count
    
    def test_count_messages_tokens_openai(self):
        """测试计算OpenAI消息token"""
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!")
        ]
        
        with patch('tiktoken.encoding_for_model') as mock_encoding_for_model:
            mock_encoding = Mock()
            mock_encoding.encode.return_value = [1, 2]
            mock_encoding_for_model.return_value = mock_encoding
            
            calculator = LocalTokenCalculator("gpt-3.5-turbo", "openai")
            count = calculator.count_messages_tokens(messages)
            
            # 应该调用多次encode方法
            assert mock_encoding.encode.call_count >= 2
            assert count > 0
    
    def test_count_messages_tokens_generic(self):
        """测试计算通用消息token"""
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!")
        ]
        
        calculator = LocalTokenCalculator("gemini-pro", "gemini")
        calculator._encoding = None  # 模拟没有tiktoken
        
        count = calculator.count_messages_tokens(messages)
        assert count > 0
    
    def test_get_model_info(self):
        """测试获取模型信息"""
        calculator = LocalTokenCalculator("gpt-3.5-turbo", "openai")
        info = calculator.get_model_info()
        
        assert info["model_name"] == "gpt-3.5-turbo"
        assert info["provider"] == "openai"
        assert info["calculator_type"] == "local"
    
    def test_api_methods_return_false_or_none(self):
        """测试API相关方法返回False或None"""
        calculator = LocalTokenCalculator("gpt-3.5-turbo", "openai")
        
        assert calculator.update_from_api_response({}, "context") is False
        assert calculator.get_last_api_usage() is None
        assert calculator.is_api_usage_available() is False


class TestApiTokenCalculator:
    """API Token计算器测试"""
    
    def test_initialization(self):
        """测试初始化"""
        calculator = ApiTokenCalculator("gpt-3.5-turbo", "openai")
        assert calculator.model_name == "gpt-3.5-turbo"
        assert calculator.provider == "openai"
        assert calculator._last_usage is None
        assert len(calculator._usage_cache) == 0
    
    def test_count_tokens_with_cache(self):
        """测试使用缓存计数token"""
        calculator = ApiTokenCalculator("gpt-3.5-turbo", "openai")
        text = "Hello, world!"
        
        # 先更新缓存
        response = {
            "usage": {
                "prompt_tokens": 3,
                "completion_tokens": 2,
                "total_tokens": 5
            }
        }
        calculator.update_from_api_response(response, text)
        
        # 现在应该从缓存中获取
        count = calculator.count_tokens(text)
        assert count == 5
    
    def test_count_tokens_without_cache(self):
        """测试不使用缓存计数token"""
        calculator = ApiTokenCalculator("gpt-3.5-turbo", "openai")
        text = "Hello, world!"
        
        # 没有缓存时应该使用简单估算
        count = calculator.count_tokens(text)  # 13 characters
        assert count == 3  # 13 // 4 = 3
    
    def test_update_from_api_response_success(self):
        """测试成功更新API响应"""
        calculator = ApiTokenCalculator("gpt-3.5-turbo", "openai")
        response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            },
            "model": "gpt-3.5-turbo"
        }
        
        success = calculator.update_from_api_response(response, "test context")
        assert success is True
        assert calculator._last_usage is not None
        assert calculator._last_usage.total_tokens == 15
        assert len(calculator._usage_cache) == 1
    
    def test_update_from_api_response_failure(self):
        """测试更新API响应失败"""
        calculator = ApiTokenCalculator("gpt-3.5-turbo", "openai")
        response = {"invalid": "response"}
        
        success = calculator.update_from_api_response(response, "test context")
        assert success is False
        assert calculator._last_usage is None
        assert len(calculator._usage_cache) == 0
    
    def test_get_last_api_usage(self):
        """测试获取最后API使用情况"""
        calculator = ApiTokenCalculator("gpt-3.5-turbo", "openai")
        response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        calculator.update_from_api_response(response)
        usage = calculator.get_last_api_usage()
        
        assert usage is not None
        assert usage.total_tokens == 15
    
    def test_is_api_usage_available(self):
        """测试API使用是否可用"""
        calculator = ApiTokenCalculator("gpt-3.5-turbo", "openai")
        assert calculator.is_api_usage_available() is False
        
        response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        calculator.update_from_api_response(response)
        assert calculator.is_api_usage_available() is True


class TestHybridTokenCalculator:
    """混合Token计算器测试"""
    
    def test_initialization(self):
        """测试初始化"""
        calculator = HybridTokenCalculator("gpt-3.5-turbo", "openai", True)
        assert calculator.model_name == "gpt-3.5-turbo"
        assert calculator.provider == "openai"
        assert calculator.prefer_api is True
    
    def test_count_tokens_prefer_api_with_api_available(self):
        """测试优先使用API且API可用时计数token"""
        calculator = HybridTokenCalculator("gpt-3.5-turbo", "openai", True)
        
        # 模拟API可用
        response = {
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 3,
                "total_tokens": 8
            }
        }
        calculator.update_from_api_response(response, "test")
        
        count = calculator.count_tokens("test")
        assert count == 8
        assert calculator._stats["api_count"] == 1
    
    def test_count_tokens_prefer_api_with_api_unavailable(self):
        """测试优先使用API但API不可用时计数token"""
        calculator = HybridTokenCalculator("gpt-3.5-turbo", "openai", True)
        
        # API不可用，应该降级到本地计算器
        text = "Hello, world!"  # 13 characters
        # 本地计算器使用tiktoken编码器，所以结果可能不是简单的len(text) // 4
        count = calculator.count_tokens(text)
        # 我们只验证降级逻辑是否正确执行，而不验证具体数值
        assert count > 0
        assert calculator._stats["fallback_count"] == 1
        assert calculator._stats["local_count"] == 1
    
    def test_count_tokens_prefer_local(self):
        """测试优先使用本地计算器计数token"""
        calculator = HybridTokenCalculator("gpt-3.5-turbo", "openai", False)
        
        text = "Hello, world!"  # 13 characters
        # 本地计算器使用tiktoken编码器，所以结果可能不是简单的len(text) // 4
        count = calculator.count_tokens(text)
        # 我们只验证逻辑是否正确执行，而不验证具体数值
        assert count > 0
        assert calculator._stats["local_count"] == 1
    
    def test_get_stats(self):
        """测试获取统计信息"""
        calculator = HybridTokenCalculator("gpt-3.5-turbo", "openai", True)
        
        # 执行一些操作
        calculator.count_tokens("test1")
        calculator.count_tokens("test2")
        
        stats = calculator.get_stats()
        # 当API不可用时，会降级到本地计算器，因此local_count和fallback_count都应该为2
        assert stats["local_count"] == 2
        assert stats["api_count"] == 0
        assert stats["fallback_count"] == 2
        assert stats["total_requests"] == 2
        # fallback_rate_percent = fallback_count / total_requests * 100 = 2 / 2 * 100 = 100.0
        assert stats["fallback_rate_percent"] == 100.0
    
    def test_force_local_calculation(self):
        """测试强制使用本地计算器"""
        calculator = HybridTokenCalculator("gpt-3.5-turbo", "openai", True)
        
        text = "Hello, world!"  # 13 characters
        # 本地计算器使用tiktoken编码器，所以结果可能不是简单的len(text) // 4
        count = calculator.force_local_calculation(text)
        # 我们只验证逻辑是否正确执行，而不验证具体数值
        assert count > 0
        assert calculator._stats["local_count"] == 1
    
    def test_set_prefer_api(self):
        """测试设置优先使用API"""
        calculator = HybridTokenCalculator("gpt-3.5-turbo", "openai", False)
        assert calculator.prefer_api is False
        
        calculator.set_prefer_api(True)
        assert calculator.prefer_api is True