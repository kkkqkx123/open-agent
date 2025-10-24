"""测试增强版Token计数器"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

# 更新导入，使用新的模块结构
from src.infrastructure.llm.token_parsers.base import TokenUsage
from src.infrastructure.llm.token_counter import (
    EnhancedOpenAITokenCounter,
    EnhancedGeminiTokenCounter,
    EnhancedAnthropicTokenCounter,
    TokenCounterFactory,
    OpenAITokenCounter,
    GeminiTokenCounter,
    AnthropicTokenCounter,
    MockTokenCounter
)
from langchain_core.messages import HumanMessage, AIMessage


class TestTokenUsage(unittest.TestCase):
    """测试TokenUsage数据类"""
    
    def test_token_usage_creation(self):
        """测试TokenUsage创建"""
        usage = TokenUsage(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15
        )
        
        self.assertEqual(usage.prompt_tokens, 10)
        self.assertEqual(usage.completion_tokens, 5)
        self.assertEqual(usage.total_tokens, 15)
        self.assertEqual(usage.source, "local")
        self.assertIsInstance(usage.timestamp, datetime)
        self.assertEqual(usage.additional_info, {})
    
    def test_token_usage_with_custom_values(self):
        """测试自定义值的TokenUsage"""
        custom_time = datetime.now()
        custom_info = {"model": "gpt-4"}
        
        usage = TokenUsage(
            prompt_tokens=20,
            completion_tokens=10,
            total_tokens=30,
            source="api",
            timestamp=custom_time,
            additional_info=custom_info
        )
        
        self.assertEqual(usage.source, "api")
        self.assertEqual(usage.timestamp, custom_time)
        self.assertEqual(usage.additional_info, custom_info)


class TestEnhancedTokenCounter(unittest.TestCase):
    """测试增强版Token计数器"""
    
    def setUp(self):
        """设置测试环境"""
        self.counter = EnhancedOpenAITokenCounter("gpt-4")
    
    def test_local_counting(self):
        """测试本地计数功能"""
        count = self.counter.count_tokens("Hello, world!")
        self.assertGreater(count, 0)
    
    def test_api_response_update(self):
        """测试API响应更新"""
        response = {
            "id": "chatcmpl-123",
            "model": "gpt-4",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        success = self.counter.update_from_api_response(response, "Hello")
        self.assertTrue(success)
        
        # 验证缓存
        usage = self.counter.get_last_api_usage()
        self.assertIsNotNone(usage)
        self.assertEqual(usage.total_tokens, 15)  # type: ignore
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        # 第一次计数（缓存未命中）
        count1 = self.counter.count_tokens("Test text")
        
        # 第二次计数（应该命中缓存）
        count2 = self.counter.count_tokens("Test text")
        
        self.assertEqual(count1, count2)
        
        # 验证缓存存在
        self.assertIsNotNone(self.counter.cache)
    
    def test_messages_counting(self):
        """测试消息计数"""
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!")
        ]
        
        count = self.counter.count_messages_tokens(messages)
        self.assertGreater(count, 0)
    
    def test_model_info(self):
        """测试模型信息获取"""
        info = self.counter.get_model_info()
        
        self.assertIn("model_name", info)
        self.assertIn("provider", info)
        self.assertIn("supports_api_usage", info)
        self.assertIn("api_usage_stats", info)


class TestTokenCounterFactory(unittest.TestCase):
    """测试Token计数器工厂"""
    
    def test_create_enhanced_counter(self):
        """测试创建增强版计数器"""
        config = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "enhanced": True,
            "cache": {
                "clear_on_init": True
            }
        }
        
        counter = TokenCounterFactory.create_with_config(config)
        
        self.assertIsInstance(counter, EnhancedOpenAITokenCounter)
        self.assertEqual(counter.model_name, "gpt-4") # type: ignore
        self.assertEqual(counter.provider, "openai") # type: ignore
    
    def test_create_traditional_counter(self):
        """测试创建传统计数器"""
        config = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "enhanced": False
        }
        
        counter = TokenCounterFactory.create_with_config(config)
        
        # 应该是传统的OpenAITokenCounter
        self.assertIsInstance(counter, OpenAITokenCounter)
    
    def test_create_different_providers(self):
        """测试创建不同提供商的计数器"""
        # OpenAI
        openai_counter = TokenCounterFactory.create_counter("openai", "gpt-4", enhanced=True)
        self.assertIsInstance(openai_counter, EnhancedOpenAITokenCounter)
        
        # Gemini
        gemini_counter = TokenCounterFactory.create_counter("gemini", "gemini-pro", enhanced=True)
        self.assertIsInstance(gemini_counter, EnhancedGeminiTokenCounter)
        
        # Anthropic
        anthropic_counter = TokenCounterFactory.create_counter("anthropic", "claude-3", enhanced=True)
        self.assertIsInstance(anthropic_counter, EnhancedAnthropicTokenCounter)
    
    def test_create_mock_counter(self):
        """测试创建Mock计数器"""
        mock_counter = TokenCounterFactory.create_counter("mock", "mock-model", enhanced=False)
        self.assertIsInstance(mock_counter, MockTokenCounter)
        
        # 测试Mock计数器的特殊逻辑
        count = mock_counter.count_tokens("测试文本")  # 8个字符
        self.assertEqual(count, 2)  # 对于短文本，至少返回2个token
        
        count = mock_counter.count_tokens("消息1")  # 3个字符
        self.assertEqual(count, 2)  # 对于短文本，至少返回2个token
    
    def test_backward_compatibility(self):
        """测试向后兼容性"""
        # 测试所有传统计数器仍然可以正常工作
        openai_counter = OpenAITokenCounter("gpt-3.5-turbo")
        self.assertEqual(openai_counter.model_name, "gpt-3.5-turbo")
        self.assertEqual(openai_counter.provider, "openai")
        self.assertIsNone(openai_counter.cache)
        self.assertIsNone(openai_counter.calibrator)
        
        gemini_counter = GeminiTokenCounter("gemini-pro")
        self.assertEqual(gemini_counter.model_name, "gemini-pro")
        self.assertEqual(gemini_counter.provider, "gemini")
        
        anthropic_counter = AnthropicTokenCounter("claude-3-sonnet-20240229")
        self.assertEqual(anthropic_counter.model_name, "claude-3-sonnet-20240229")
        self.assertEqual(anthropic_counter.provider, "anthropic")
        
        mock_counter = MockTokenCounter("mock-model")
        self.assertEqual(mock_counter.model_name, "mock-model")
        self.assertEqual(mock_counter.provider, "mock")
    
    def test_enhanced_counters_use_hybrid_calculator(self):
        """测试增强版计数器使用混合计算器"""
        counter = EnhancedOpenAITokenCounter("gpt-4")
        
        # 验证内部使用了混合计算器
        self.assertTrue(hasattr(counter, '_calculator'))
        
        # 验证混合计算器的属性
        self.assertEqual(counter._calculator.model_name, "gpt-4")
        self.assertEqual(counter._calculator.provider, "openai")
        self.assertTrue(counter._calculator.prefer_api)
    
    def test_api_usage_methods(self):
        """测试API使用相关方法"""
        counter = EnhancedOpenAITokenCounter("gpt-4")
        
        # 初始状态应该没有API使用数据
        self.assertFalse(counter.is_api_usage_available())
        self.assertIsNone(counter.get_last_api_usage())
        
        # 更新API响应后应该有数据
        response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        success = counter.update_from_api_response(response, "test context")
        self.assertTrue(success)
        self.assertTrue(counter.is_api_usage_available())
        self.assertIsNotNone(counter.get_last_api_usage())


if __name__ == '__main__':
    unittest.main()
