"""测试降级策略功能"""

import unittest
from unittest.mock import Mock, patch
from typing import Dict, Any, cast

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.llm.token_calculators.hybrid_calculator import HybridTokenCalculator
from src.llm.token_parsers.base import TokenUsage


class TestDegradationStrategy(unittest.TestCase):
    """测试降级策略功能"""
    
    def setUp(self) -> None:
        """测试前设置"""
        self.model_name = "gpt-3.5-turbo"
        self.provider = "openai"
    
    def test_degradation_when_api_tokens_less_than_quarter_local(self) -> None:
        """测试当API token数少于本地估算的1/4时，使用本地计算"""
        # 创建混合计算器，启用降级策略
        calculator = HybridTokenCalculator(
            model_name=self.model_name,
            provider=self.provider,
            prefer_api=True,
            enable_degradation=True,
            supports_token_caching=True
        )
        
        # 模拟API响应，token数很少
        api_response = {
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2
            }
        }
        
        # 更新API响应
        calculator.update_from_api_response(api_response, "test text")
        
        # 测试文本token计数
        text = "This is a test text that should be longer than 8 characters"
        token_count = calculator.count_tokens(text, api_response)
        
        # 由于API token数(2)应该少于本地估算的1/4，应该使用本地计算
        # 本地计算对于这段文本应该返回大约10个token
        self.assertGreater(token_count, 5)  # 本地计算应该返回更多的token
        
        # 检查统计信息
        stats = calculator.get_stats()
        self.assertEqual(stats["degradation_count"], 1)
        self.assertEqual(stats["local_count"], 1)
        self.assertEqual(stats["api_count"], 0)
    
    def test_no_degradation_when_api_tokens_reasonable(self) -> None:
        """测试当API token数合理时，使用API计算"""
        # 创建混合计算器，启用降级策略
        calculator = HybridTokenCalculator(
            model_name=self.model_name,
            provider=self.provider,
            prefer_api=True,
            enable_degradation=True,
            supports_token_caching=True
        )
        
        # 模拟API响应，token数合理
        api_response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        # 更新API响应
        calculator.update_from_api_response(api_response, "test text")
        
        # 测试文本token计数
        text = "short"
        token_count = calculator.count_tokens(text, api_response)
        
        # 由于API token数(15)应该不少于本地估算的1/4，应该使用API计算
        self.assertEqual(token_count, 15)
        
        # 检查统计信息
        stats = calculator.get_stats()
        self.assertEqual(stats["degradation_count"], 0)
        self.assertEqual(stats["local_count"], 0)
        self.assertEqual(stats["api_count"], 1)
    
    def test_degradation_disabled(self) -> None:
        """测试当降级策略禁用时，总是使用API计算"""
        # 创建混合计算器，禁用降级策略
        calculator = HybridTokenCalculator(
            model_name=self.model_name,
            provider=self.provider,
            prefer_api=True,
            enable_degradation=False,
            supports_token_caching=True
        )
        
        # 模拟API响应，token数很少
        api_response = {
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2
            }
        }
        
        # 更新API响应
        calculator.update_from_api_response(api_response, "test text")
        
        # 测试文本token计数
        text = "This is a test text that should be longer than 8 characters"
        token_count = calculator.count_tokens(text, api_response)
        
        # 即使API token数很少，由于降级策略禁用，应该使用API计算
        self.assertEqual(token_count, 2)
        
        # 检查统计信息
        stats = calculator.get_stats()
        self.assertEqual(stats["degradation_count"], 0)
        self.assertEqual(stats["local_count"], 0)
        self.assertEqual(stats["api_count"], 1)
    
    def test_degradation_with_messages(self) -> None:
        """测试消息列表的降级策略"""
        # 创建混合计算器，启用降级策略
        calculator = HybridTokenCalculator(
            model_name=self.model_name,
            provider=self.provider,
            prefer_api=True,
            enable_degradation=True,
            supports_token_caching=True
        )
        
        # 模拟API响应，token数很少
        api_response = {
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2
            }
        }
        
        # 创建消息列表
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Hello, how are you?"),
            AIMessage(content="I'm doing well, thank you!")
        ]
        
        # 更新API响应
        calculator.update_from_api_response(api_response)
        
        # 测试消息列表token计数
        token_count = calculator.count_messages_tokens(messages, api_response)
        
        # 由于API token数(2)应该少于本地估算的1/4，应该使用本地计算
        # 本地计算对于这些消息应该返回更多的token
        self.assertGreater(token_count, 10)
        
        # 检查统计信息
        stats = calculator.get_stats()
        self.assertEqual(stats["degradation_count"], 1)
        self.assertEqual(stats["local_count"], 1)
        self.assertEqual(stats["api_count"], 0)
    
    def test_caching_disabled_degradation(self) -> None:
        """测试当缓存禁用时的降级策略"""
        # 创建混合计算器，禁用缓存
        calculator = HybridTokenCalculator(
            model_name=self.model_name,
            provider=self.provider,
            prefer_api=True,
            enable_degradation=True,
            supports_token_caching=False
        )
        
        # 模拟API响应，token数很少
        api_response = {
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2
            }
        }
        
        # 测试文本token计数
        text = "This is a test text that should be longer than 8 characters"
        token_count = calculator.count_tokens(text, api_response)
        
        # 由于缓存禁用，应该直接使用本地计算
        # 本地计算对于这段文本应该返回大约10个token
        self.assertGreater(token_count, 5)
        
        # 检查统计信息
        stats = calculator.get_stats()
        self.assertEqual(stats["degradation_count"], 0)  # 降级策略不适用于禁用缓存的情况
        self.assertEqual(stats["local_count"], 1)
        self.assertEqual(stats["api_count"], 0)
        self.assertEqual(stats["fallback_count"], 1)
    
    def test_conversation_tracking_with_degradation(self) -> None:
        """测试对话跟踪功能与降级策略的集成"""
        # 创建混合计算器，启用降级策略和对话跟踪
        calculator = HybridTokenCalculator(
            model_name=self.model_name,
            provider=self.provider,
            prefer_api=True,
            enable_degradation=True,
            supports_token_caching=True,
            track_conversation=True
        )
        
        # 模拟API响应，token数很少
        api_response = {
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2
            }
        }
        
        # 更新API响应
        calculator.update_from_api_response(api_response, "test text")
        
        # 测试文本token计数
        text = "This is a test text that should be longer than 8 characters"
        token_count = calculator.count_tokens(text, api_response)
        
        # 检查对话统计信息
        conv_stats = calculator.get_conversation_stats()
        self.assertIsNotNone(conv_stats)
        conv_stats = cast(Dict[str, Any], conv_stats)
        self.assertEqual(conv_stats["total_messages"], 1)
        self.assertEqual(conv_stats["total_tokens_used"], token_count)
        
        # 检查来源分布 - 由于使用了降级策略，应该标记为precomputed
        source_dist = conv_stats["source_distribution"]
        self.assertEqual(source_dist["precomputed"], token_count)
        self.assertEqual(source_dist["api"], 0)
        self.assertEqual(source_dist["local"], 0)
    
    def test_prefer_local_with_degradation(self) -> None:
        """测试当优先使用本地计算器时的降级策略"""
        # 创建混合计算器，优先使用本地计算器
        calculator = HybridTokenCalculator(
            model_name=self.model_name,
            provider=self.provider,
            prefer_api=False,
            enable_degradation=True,
            supports_token_caching=True
        )
        
        # 模拟API响应，token数很少
        api_response = {
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2
            }
        }
        
        # 更新API响应
        calculator.update_from_api_response(api_response, "test text")
        
        # 测试文本token计数
        text = "This is a test text"
        token_count = calculator.count_tokens(text, api_response)
        
        # 由于优先使用本地计算器，应该直接使用本地计算
        self.assertGreater(token_count, 2)
        
        # 检查统计信息
        stats = calculator.get_stats()
        self.assertEqual(stats["degradation_count"], 0)  # 降级策略不适用于优先本地的情况
        self.assertEqual(stats["local_count"], 1)
        self.assertEqual(stats["api_count"], 0)


if __name__ == "__main__":
    unittest.main()