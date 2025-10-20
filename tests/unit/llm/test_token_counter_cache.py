"""Token计数器缓存功能测试"""

import unittest
from unittest.mock import Mock, patch
from src.llm.token_counter import (
    TokenCounterFactory,
    EnhancedOpenAITokenCounter,
    EnhancedGeminiTokenCounter,
    EnhancedAnthropicTokenCounter,
    ApiTokenCalculator
)
from src.config.models.llm_config import LLMConfig
from src.llm.token_parsers.base import TokenUsage


class TestTokenCounterCache(unittest.TestCase):
    """Token计数器缓存功能测试类"""

    def test_api_token_calculator_initialization(self):
        """测试API Token计算器初始化"""
        calculator = ApiTokenCalculator("gpt-4", "openai", supports_caching=True)
        
        self.assertEqual(calculator.model_name, "gpt-4")
        self.assertEqual(calculator.provider, "openai")
        self.assertTrue(calculator.supports_caching)
        self.assertEqual(calculator._usage_cache, {})
        self.assertIsNone(calculator._last_usage)

    def test_api_token_calculator_initialization_without_caching(self):
        """测试API Token计算器初始化（不支持缓存）"""
        calculator = ApiTokenCalculator("gpt-4", "openai", supports_caching=False)
        
        self.assertFalse(calculator.supports_caching)
        self.assertEqual(calculator._usage_cache, {})

    def test_api_token_calculator_update_from_api_response(self):
        """测试从API响应更新token信息"""
        calculator = ApiTokenCalculator("gpt-4", "openai", supports_caching=True)
        
        # 模拟API响应
        api_response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        context = "Hello, how are you?"
        success = calculator.update_from_api_response(api_response, context)
        
        self.assertTrue(success)
        self.assertIsNotNone(calculator._last_usage)
        self.assertEqual(calculator._last_usage.prompt_tokens, 10)
        self.assertEqual(calculator._last_usage.completion_tokens, 5)
        self.assertEqual(calculator._last_usage.total_tokens, 15)
        
        # 验证缓存
        cache_key = calculator._generate_cache_key(context)
        self.assertIn(cache_key, calculator._usage_cache)
        cached_usage = calculator._usage_cache[cache_key]
        self.assertEqual(cached_usage.total_tokens, 15)

    def test_api_token_calculator_count_tokens_with_cache(self):
        """测试使用缓存计算token"""
        calculator = ApiTokenCalculator("gpt-4", "openai", supports_caching=True)
        
        # 先更新API响应到缓存
        api_response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        context = "Hello, how are you?"
        calculator.update_from_api_response(api_response, context)
        
        # 使用缓存计算token
        tokens = calculator.count_tokens(context)
        self.assertEqual(tokens, 15)

    def test_api_token_calculator_count_tokens_without_cache(self):
        """测试无缓存时的token计算"""
        calculator = ApiTokenCalculator("gpt-4", "openai", supports_caching=True)
        
        # 不在缓存中的文本
        text = "This is a test text"
        tokens = calculator.count_tokens(text)
        
        # 由于没有缓存，应该使用估算（长度/4）
        expected_tokens = len(text) // 4
        self.assertEqual(tokens, expected_tokens)

    def test_api_token_calculator_count_tokens_without_caching_support(self):
        """测试不支持缓存时的token计算"""
        calculator = ApiTokenCalculator("gpt-4", "openai", supports_caching=False)
        
        # 即使有缓存，由于不支持缓存，也会使用估算
        text = "Hello, how are you?"
        tokens = calculator.count_tokens(text)
        
        # 使用估算（长度/4）
        expected_tokens = len(text) // 4
        self.assertEqual(tokens, expected_tokens)

    def test_api_token_calculator_cache_clear(self):
        """测试缓存清空功能"""
        calculator = ApiTokenCalculator("gpt-4", "openai", supports_caching=True)
        
        # 添加一些缓存数据
        api_response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        context = "Hello, how are you?"
        calculator.update_from_api_response(api_response, context)
        
        # 验证缓存已添加
        self.assertEqual(len(calculator._usage_cache), 1)
        self.assertIsNotNone(calculator._last_usage)
        
        # 清空缓存
        calculator.clear_cache()
        
        # 验证缓存已清空
        self.assertEqual(len(calculator._usage_cache), 0)
        self.assertIsNone(calculator._last_usage)

    def test_api_token_calculator_stats(self):
        """测试统计信息"""
        calculator = ApiTokenCalculator("gpt-4", "openai", supports_caching=True)
        
        # 初始统计
        initial_stats = calculator.get_stats()
        self.assertEqual(initial_stats["total_requests"], 0)
        self.assertEqual(initial_stats["api_success"], 0)
        self.assertEqual(initial_stats["api_failed"], 0)
        self.assertEqual(initial_stats["fallback_to_local"], 0)
        self.assertEqual(initial_stats["cache_size"], 0)

        # 更新API响应
        api_response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        context = "Hello, how are you?"
        calculator.update_from_api_response(api_response, context)
        
        # 验证统计更新
        stats = calculator.get_stats()
        self.assertEqual(stats["total_requests"], 1)
        self.assertEqual(stats["api_success"], 1)
        self.assertEqual(stats["cache_size"], 1)

        # 使用缓存计算token
        calculator.count_tokens(context)
        
        # 验证统计再次更新
        stats = calculator.get_stats()
        self.assertEqual(stats["total_requests"], 2)
        self.assertEqual(stats["api_success"], 2)

    def test_enhanced_token_counter_with_caching_config(self):
        """测试增强版计数器的缓存配置"""
        # 测试OpenAI增强版计数器
        config = {
            "supports_token_caching": True,
            "prefer_api": True,
            "enable_degradation": True
        }
        
        counter = EnhancedOpenAITokenCounter("gpt-4", config)
        
        # 验证配置已应用
        self.assertTrue(counter.config["supports_token_caching"])
        self.assertTrue(counter.config["prefer_api"])
        
        # 验证内部计算器使用了正确的配置
        self.assertTrue(counter._calculator._api_calculator.supports_caching)

    def test_enhanced_token_counter_without_caching(self):
        """测试增强版计数器不支持缓存的情况"""
        config = {
            "supports_token_caching": False,
            "prefer_api": True,
            "enable_degradation": True
        }
        
        counter = EnhancedOpenAITokenCounter("gpt-4", config)
        
        # 验证配置已应用
        self.assertFalse(counter.config["supports_token_caching"])
        
        # 验证内部计算器不支持缓存
        self.assertFalse(counter._calculator._api_calculator.supports_caching)

    def test_token_counter_factory_create_with_model_config_caching(self):
        """测试Token计数器工厂使用模型配置创建（缓存支持）"""
        # 模拟LLM配置
        model_config = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "supports_caching": True,
            "cache_config": {
                "ttl_seconds": 3600,
                "max_size": 1000,
                "enabled": True
            }
        }
        
        counter = TokenCounterFactory.create_with_model_config(model_config)
        
        # 验证创建了增强版计数器
        self.assertIsInstance(counter, EnhancedOpenAITokenCounter)
        
        # 验证缓存配置已应用
        self.assertTrue(counter._calculator._api_calculator.supports_caching)

    def test_token_counter_factory_create_with_model_config_no_caching(self):
        """测试Token计数器工厂使用模型配置创建（不支持缓存）"""
        # 模拟LLM配置
        model_config = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "supports_caching": False,
            "cache_config": {
                "enabled": False,
                "ttl_seconds": 1800,
                "max_size": 500
            }
        }
        
        counter = TokenCounterFactory.create_with_model_config(model_config)
        
        # 验证创建了增强版计数器
        self.assertIsInstance(counter, EnhancedOpenAITokenCounter)
        
        # 验证缓存配置已应用
        self.assertFalse(counter._calculator._api_calculator.supports_caching)

    def test_different_provider_caching_support(self):
        """测试不同提供商的缓存支持"""
        # OpenAI配置 - 不支持缓存
        openai_config = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "supports_caching": False
        }
        
        openai_counter = TokenCounterFactory.create_with_model_config(openai_config)
        self.assertFalse(openai_counter._calculator._api_calculator.supports_caching)

        # Anthropic配置 - 支持缓存
        anthropic_config = {
            "model_type": "anthropic",
            "model_name": "claude-3",
            "supports_caching": True
        }
        
        anthropic_counter = TokenCounterFactory.create_with_model_config(anthropic_config)
        self.assertTrue(anthropic_counter._calculator._api_calculator.supports_caching)

        # Gemini配置 - 支持缓存
        gemini_config = {
            "model_type": "gemini",
            "model_name": "gemini-pro",
            "supports_caching": True
        }
        
        gemini_counter = TokenCounterFactory.create_with_model_config(gemini_config)
        self.assertTrue(gemini_counter._calculator._api_calculator.supports_caching)

    def test_token_usage_cache_functionality(self):
        """测试Token使用缓存功能"""
        calculator = ApiTokenCalculator("gpt-4", "openai", supports_caching=True)
        
        # 模拟多个API响应
        responses = [
            {
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15
                }
            },
            {
                "usage": {
                    "prompt_tokens": 20,
                    "completion_tokens": 10,
                    "total_tokens": 30
                }
            }
        ]
        
        contexts = ["Hello world", "How are you?"]
        
        # 更新多个API响应到缓存
        for i, response in enumerate(responses):
            calculator.update_from_api_response(response, contexts[i])
        
        # 验证缓存大小
        self.assertEqual(len(calculator._usage_cache), 2)
        
        # 验证可以从缓存获取token
        tokens1 = calculator.count_tokens(contexts[0])
        tokens2 = calculator.count_tokens(contexts[1])
        
        self.assertEqual(tokens1, 15)
        self.assertEqual(tokens2, 30)

    def test_cache_key_generation(self):
        """测试缓存key生成"""
        calculator1 = ApiTokenCalculator("gpt-4", "openai", supports_caching=True)
        calculator2 = ApiTokenCalculator("gpt-3.5", "openai", supports_caching=True)
        
        content = "Hello, world!"
        
        key1 = calculator1._generate_cache_key(content)
        key2 = calculator2._generate_cache_key(content)
        
        # 不同模型应该有不同的缓存key
        self.assertNotEqual(key1, key2)
        
        # 相同模型和内容应该有相同的缓存key
        key3 = calculator1._generate_cache_key(content)
        self.assertEqual(key1, key3)

    def test_api_token_calculator_is_api_usage_available(self):
        """测试API使用情况是否可用"""
        calculator = ApiTokenCalculator("gpt-4", "openai", supports_caching=True)
        
        # 初始状态应该不可用
        self.assertFalse(calculator.is_api_usage_available())
        
        # 更新API响应后应该可用
        api_response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        calculator.update_from_api_response(api_response, "test")
        self.assertTrue(calculator.is_api_usage_available())

    def test_api_token_calculator_get_last_api_usage(self):
        """测试获取最后的API使用情况"""
        calculator = ApiTokenCalculator("gpt-4", "openai", supports_caching=True)
        
        # 初始状态应该返回None
        self.assertIsNone(calculator.get_last_api_usage())
        
        # 更新API响应后应该返回使用情况
        api_response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        calculator.update_from_api_response(api_response, "test")
        last_usage = calculator.get_last_api_usage()
        
        self.assertIsNotNone(last_usage)
        self.assertEqual(last_usage.prompt_tokens, 10)
        self.assertEqual(last_usage.completion_tokens, 5)
        self.assertEqual(last_usage.total_tokens, 15)

    def test_enhanced_counter_cache_property(self):
        """测试增强版计数器的缓存属性"""
        config = {"supports_token_caching": True}
        counter = EnhancedOpenAITokenCounter("gpt-4", config)
        
        # 验证缓存属性
        cache = counter.cache
        self.assertIsNotNone(cache)  # 应该返回API计算器的缓存

    def test_cache_config_application_from_llm_config(self):
        """测试从LLM配置应用缓存配置"""
        # 创建LLM配置
        llm_config_dict = {
            "model_type": "anthropic",
            "model_name": "claude-3",
            "supports_caching": True,
            "cache_config": {
                "ttl_seconds": 7200,
                "max_size": 2000,
                "enabled": True
            }
        }
        
        llm_config = LLMConfig(**llm_config_dict)
        
        # 验证LLM配置的缓存方法
        self.assertTrue(llm_config.supports_api_caching())
        self.assertEqual(llm_config.get_cache_ttl(), 7200)
        self.assertEqual(llm_config.get_cache_max_size(), 2000)
        
        # 使用LLM配置创建计数器
        counter = TokenCounterFactory.create_with_model_config(llm_config_dict)
        
        # 验证计数器使用了正确的缓存配置
        self.assertTrue(counter._calculator._api_calculator.supports_caching)


if __name__ == '__main__':
    unittest.main()