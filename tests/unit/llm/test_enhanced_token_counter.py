"""测试增强版Token计数器"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from src.llm.token_counter import (
    TokenUsage,
    ApiResponseParser,
    TokenUsageCache,
    TokenCalibrator,
    EnhancedTokenCounter,
    EnhancedOpenAITokenCounter,
    EnhancedGeminiTokenCounter,
    EnhancedAnthropicTokenCounter,
    TokenCounterFactory
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


class TestApiResponseParser(unittest.TestCase):
    """测试API响应解析器"""
    
    def test_parse_openai_response(self):
        """测试解析OpenAI响应"""
        response = {
            "id": "chatcmpl-123",
            "model": "gpt-4",
            "usage": {
                "prompt_tokens": 25,
                "completion_tokens": 15,
                "total_tokens": 40
            }
        }
        
        usage = ApiResponseParser.parse_openai_response(response)
        
        self.assertEqual(usage.prompt_tokens, 25)
        self.assertEqual(usage.completion_tokens, 15)
        self.assertEqual(usage.total_tokens, 40)
        self.assertEqual(usage.source, "api")
        self.assertEqual(usage.additional_info["model"], "gpt-4")  # type: ignore
        self.assertEqual(usage.additional_info["response_id"], "chatcmpl-123")  # type: ignore
    
    def test_parse_gemini_response(self):
        """测试解析Gemini响应"""
        response = {
            "model": "gemini-pro",
            "usageMetadata": {
                "promptTokenCount": 30,
                "candidatesTokenCount": 20,
                "totalTokenCount": 50,
                "thoughtsTokenCount": 5,
                "cachedContentTokenCount": 2
            }
        }
        
        usage = ApiResponseParser.parse_gemini_response(response)
        
        self.assertEqual(usage.prompt_tokens, 30)
        self.assertEqual(usage.completion_tokens, 20)
        self.assertEqual(usage.total_tokens, 50)
        self.assertEqual(usage.source, "api")
        self.assertEqual(usage.additional_info["thoughts_tokens"], 5)  # type: ignore
        self.assertEqual(usage.additional_info["cached_tokens"], 2)  # type: ignore
    
    def test_parse_anthropic_response(self):
        """测试解析Anthropic响应"""
        response = {
            "model": "claude-3-sonnet-20240229",
            "usage": {
                "input_tokens": 35,
                "output_tokens": 25,
                "cache_creation_input_tokens": 3,
                "cache_read_input_tokens": 2
            }
        }
        
        usage = ApiResponseParser.parse_anthropic_response(response)
        
        self.assertEqual(usage.prompt_tokens, 35)
        self.assertEqual(usage.completion_tokens, 25)
        self.assertEqual(usage.total_tokens, 60)  # 35 + 25
        self.assertEqual(usage.source, "api")
        self.assertEqual(usage.additional_info["cache_creation_tokens"], 3)  # type: ignore
        self.assertEqual(usage.additional_info["cache_read_tokens"], 2)  # type: ignore
    
    def test_parse_response_unknown_provider(self):
        """测试解析未知提供商响应"""
        response = {"some": "data"}
        
        usage = ApiResponseParser.parse_response("unknown", response)
        
        self.assertIsNone(usage)


class TestTokenUsageCache(unittest.TestCase):
    """测试Token使用缓存"""
    
    def setUp(self):
        """设置测试环境"""
        self.cache = TokenUsageCache(ttl_seconds=1, max_size=3)
    
    def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        usage = TokenUsage(total_tokens=10)
        
        self.cache.set("key1", usage)
        retrieved_usage = self.cache.get("key1")
        
        self.assertIsNotNone(retrieved_usage)
        self.assertEqual(retrieved_usage.total_tokens, 10)  # type: ignore
    
    def test_cache_miss(self):
        """测试缓存未命中"""
        result = self.cache.get("nonexistent_key")
        self.assertIsNone(result)
    
    def test_cache_ttl_expiration(self):
        """测试缓存TTL过期"""
        import time
        
        usage = TokenUsage(total_tokens=10)
        self.cache.set("key1", usage)
        
        # 等待缓存过期
        time.sleep(1.1)
        
        result = self.cache.get("key1")
        self.assertIsNone(result)
    
    def test_cache_lru_eviction(self):
        """测试LRU淘汰策略"""
        # 填满缓存
        for i in range(3):
            usage = TokenUsage(total_tokens=i)
            self.cache.set(f"key{i}", usage)
        
        # 添加第四个元素，应该淘汰最旧的
        usage = TokenUsage(total_tokens=3)
        self.cache.set("key3", usage)
        
        # 第一个元素应该被淘汰
        self.assertIsNone(self.cache.get("key0"))
        # 其他元素应该还在
        self.assertIsNotNone(self.cache.get("key1"))
        self.assertIsNotNone(self.cache.get("key2"))
        self.assertIsNotNone(self.cache.get("key3"))
    
    def test_cache_stats(self):
        """测试缓存统计"""
        usage = TokenUsage(total_tokens=10)
        
        # 未命中
        self.cache.get("nonexistent")
        
        # 命中
        self.cache.set("key1", usage)
        self.cache.get("key1")
        
        stats = self.cache.get_stats()
        
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["cache_size"], 1)
        self.assertGreater(stats["hit_rate"], 0)


class TestTokenCalibrator(unittest.TestCase):
    """测试Token校准器"""
    
    def setUp(self):
        """设置测试环境"""
        self.calibrator = TokenCalibrator(min_data_points=2, max_data_points=5)
    
    def test_add_calibration_point(self):
        """测试添加校准数据点"""
        self.calibrator.add_calibration_point(10, 12)
        self.calibrator.add_calibration_point(20, 24)
        
        stats = self.calibrator.get_stats()
        self.assertEqual(stats["data_points"], 2)
        self.assertGreater(stats["confidence"], 0)
    
    def test_calibration_factor_calculation(self):
        """测试校准因子计算"""
        # 添加数据点，API比本地多20%
        self.calibrator.add_calibration_point(10, 12)
        self.calibrator.add_calibration_point(20, 24)
        self.calibrator.add_calibration_point(30, 36)
        
        # 校准因子应该接近1.2
        self.assertAlmostEqual(self.calibrator.calibration_factor, 1.2, places=1)
    
    def test_calibrate_tokens(self):
        """测试token校准"""
        # 添加数据点，API比本地多20%
        self.calibrator.add_calibration_point(10, 12)
        self.calibrator.add_calibration_point(20, 24)
        self.calibrator.add_calibration_point(30, 36)
        
        # 校准后的计数应该增加约20%
        calibrated = self.calibrator.calibrate(100)
        self.assertEqual(calibrated, 120)
    
    def test_insufficient_data_points(self):
        """测试数据点不足时的行为"""
        # 只添加一个数据点
        self.calibrator.add_calibration_point(10, 12)
        
        # 校准应该返回原始值
        calibrated = self.calibrator.calibrate(100)
        self.assertEqual(calibrated, 100)
        
        # 置信度应该为0
        self.assertEqual(self.calibrator.get_confidence(), 0.0)
    
    def test_max_data_points_limit(self):
        """测试最大数据点限制"""
        # 添加超过最大限制的数据点
        for i in range(10):
            self.calibrator.add_calibration_point(i, int(i * 1.2))
        
        # 数据点数量应该不超过最大限制
        stats = self.calibrator.get_stats()
        self.assertLessEqual(stats["data_points"], 5)


class TestEnhancedTokenCounter(unittest.TestCase):
    """测试增强版Token计数器"""
    
    def setUp(self):
        """设置测试环境"""
        self.counter = EnhancedOpenAITokenCounter("gpt-4")
    
    def test_local_counting(self):
        """测试本地计数功能"""
        count = self.counter._local_count_tokens("Hello, world!")
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
    
    def test_calibration(self):
        """测试校准功能"""
        # 添加多个校准点
        for i in range(5):
            local = (i + 1) * 10
            api = int(local * 1.2)  # 模拟API比本地多20%
            self.counter.calibrator.add_calibration_point(local, api)  # type: ignore
        
        # 验证校准置信度
        confidence = self.counter.calibrator.get_confidence()  # type: ignore
        self.assertGreater(confidence, 0.5)

        # 验证校准效果
        calibrated = self.counter.calibrator.calibrate(100)  # type: ignore
        self.assertEqual(calibrated, 120)  # 应该增加20%
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        # 第一次计数（缓存未命中）
        count1 = self.counter.count_tokens("Test text")
        
        # 第二次计数（应该命中缓存）
        count2 = self.counter.count_tokens("Test text")
        
        self.assertEqual(count1, count2)
        
        # 验证缓存统计
        stats = self.counter.cache.get_stats()  # type: ignore
        self.assertGreater(stats["hit_rate"], 0)
    
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
        self.assertIn("calibration_confidence", info)
        self.assertIn("cache_stats", info)
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
                "ttl_seconds": 1800,
                "max_size": 500
            }
        }
        
        counter = TokenCounterFactory.create_with_config(config)
        
        self.assertIsInstance(counter, EnhancedOpenAITokenCounter)
        self.assertEqual(counter.model_name, "gpt-4")
        self.assertEqual(counter.provider, "openai")
        self.assertEqual(counter.cache.ttl, 1800)  # type: ignore
        self.assertEqual(counter.cache.max_size, 500)  # type: ignore
    
    def test_create_traditional_counter(self):
        """测试创建传统计数器"""
        config = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "enhanced": False
        }
        
        counter = TokenCounterFactory.create_with_config(config)
        
        # 应该是传统的OpenAITokenCounter
        from src.llm.token_counter import OpenAITokenCounter
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


if __name__ == '__main__':
    unittest.main()