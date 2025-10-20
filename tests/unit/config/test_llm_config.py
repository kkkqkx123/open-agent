"""LLM配置模型测试"""

import unittest
from typing import Any, Dict
from src.config.models.llm_config import LLMConfig


class TestLLMConfig(unittest.TestCase):
    """LLM配置模型测试类"""

    def test_llm_config_creation(self) -> None:
        """测试LLM配置创建"""
        config_data: Dict[str, Any] = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "api_key": "test_key",
            "parameters": {"temperature": 0.7},
            "supports_caching": True,
            "cache_config": {"ttl_seconds": 3600}
        }
        
        config = LLMConfig(**config_data)
        
        self.assertEqual(config.model_type, "openai")
        self.assertEqual(config.model_name, "gpt-4")
        self.assertEqual(config.api_key, "test_key")
        self.assertEqual(config.parameters["temperature"], 0.7)
        self.assertTrue(config.supports_caching)
        self.assertEqual(config.cache_config["ttl_seconds"], 3600)

    def test_llm_config_default_values(self) -> None:
        """测试LLM配置默认值"""
        config_data: Dict[str, Any] = {
            "model_type": "openai",
            "model_name": "gpt-4"
        }
        
        config = LLMConfig(**config_data)
        
        self.assertEqual(config.model_type, "openai")
        self.assertEqual(config.model_name, "gpt-4")
        self.assertFalse(config.supports_caching)  # 默认值
        self.assertEqual(config.cache_config, {})  # 默认值
        self.assertTrue(config.fallback_enabled)  # 默认值

    def test_llm_config_provider_inference(self) -> None:
        """测试提供商推断"""
        config_data: Dict[str, Any] = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "provider": "openai"
        }
        
        config = LLMConfig(**config_data)
        
        self.assertEqual(config.model_type, "openai")
        self.assertEqual(config.provider, "openai")
        self.assertEqual(config.get_provider_name(), "openai")

    def test_llm_config_provider_inference_without_explicit_provider(self) -> None:
        """测试没有显式提供商时的推断"""
        config_data: Dict[str, Any] = {
            "model_type": "gemini",
            "model_name": "gemini-pro"
        }
        
        config = LLMConfig(**config_data)
        
        self.assertEqual(config.model_type, "gemini")
        self.assertIsNone(config.provider)
        self.assertEqual(config.get_provider_name(), "gemini")

    def test_llm_config_supports_api_caching(self) -> None:
        """测试API缓存支持检查"""
        config_data: Dict[str, Any] = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "supports_caching": True
        }
        
        config = LLMConfig(**config_data)
        
        self.assertTrue(config.supports_api_caching())

        config_data["supports_caching"] = False
        config = LLMConfig(**config_data)
        
        self.assertFalse(config.supports_api_caching())

    def test_llm_config_cache_config_methods(self) -> None:
        """测试缓存配置方法"""
        config_data: Dict[str, Any] = {
            "model_type": "anthropic",
            "model_name": "claude-3",
            "cache_config": {
                "ttl_seconds": 7200,
                "max_size": 2000
            }
        }
        
        config = LLMConfig(**config_data)
        
        # 测试获取缓存配置
        self.assertEqual(config.get_cache_config("ttl_seconds"), 7200)
        self.assertEqual(config.get_cache_config("max_size"), 2000)
        self.assertEqual(config.get_cache_config("nonexistent", "default"), "default")
        
        # 测试设置缓存配置
        config.set_cache_config("new_param", "value")
        self.assertEqual(config.get_cache_config("new_param"), "value")

    def test_llm_config_cache_ttl_and_max_size(self) -> None:
        """测试缓存TTL和最大大小"""
        config_data: Dict[str, Any] = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "cache_config": {
                "ttl_seconds": 1800,
                "max_size": 500
            }
        }
        
        config = LLMConfig(**config_data)
        
        self.assertEqual(config.get_cache_ttl(), 1800)
        self.assertEqual(config.get_cache_max_size(), 500)

        # 测试默认值
        config_data["cache_config"] = {}
        config = LLMConfig(**config_data)
        
        self.assertEqual(config.get_cache_ttl(), 3600)  # 默认值
        self.assertEqual(config.get_cache_max_size(), 1000)  # 默认值

    def test_llm_config_is_openai_compatible(self) -> None:
        """测试OpenAI兼容性检查"""
        config_data: Dict[str, Any] = {
            "model_type": "openai",
            "model_name": "gpt-4"
        }
        
        config = LLMConfig(**config_data)
        self.assertTrue(config.is_openai_compatible())

        config_data["model_type"] = "local"
        config = LLMConfig(**config_data)
        self.assertTrue(config.is_openai_compatible())

        config_data["model_type"] = "gemini"
        config = LLMConfig(**config_data)
        self.assertFalse(config.is_openai_compatible())

    def test_llm_config_is_gemini(self) -> None:
        """测试Gemini检查"""
        config_data: Dict[str, Any] = {
            "model_type": "gemini",
            "model_name": "gemini-pro"
        }
        
        config = LLMConfig(**config_data)
        self.assertTrue(config.is_gemini())

        config_data["model_type"] = "openai"
        config = LLMConfig(**config_data)
        self.assertFalse(config.is_gemini())

    def test_llm_config_is_anthropic(self) -> None:
        """测试Anthropic检查"""
        config_data: Dict[str, Any] = {
            "model_type": "anthropic",
            "model_name": "claude-3"
        }
        
        config = LLMConfig(**config_data)
        self.assertTrue(config.is_anthropic())

        config_data["model_type"] = "claude"
        config = LLMConfig(**config_data)
        self.assertTrue(config.is_anthropic())

        config_data["model_type"] = "openai"
        config = LLMConfig(**config_data)
        self.assertFalse(config.is_anthropic())

    def test_llm_config_fallback_methods(self) -> None:
        """测试降级方法"""
        config_data: Dict[str, Any] = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "fallback_enabled": True,
            "fallback_models": ["gpt-3.5-turbo", "gpt-4-turbo"],
            "max_fallback_attempts": 5
        }
        
        config = LLMConfig(**config_data)
        
        self.assertTrue(config.is_fallback_enabled())
        self.assertEqual(config.get_fallback_models(), ["gpt-3.5-turbo", "gpt-4-turbo"])
        self.assertEqual(config.get_max_fallback_attempts(), 5)

    def test_llm_config_metadata_methods(self) -> None:
        """测试元数据方法"""
        config_data: Dict[str, Any] = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "metadata": {"version": "v1", "region": "us-east-1"}
        }
        
        config = LLMConfig(**config_data)
        
        # 测试获取元数据
        self.assertEqual(config.get_metadata("version"), "v1")
        self.assertEqual(config.get_metadata("region"), "us-east-1")
        self.assertEqual(config.get_metadata("nonexistent", "default"), "default")
        
        # 测试设置元数据
        config.set_metadata("new_key", "new_value")
        self.assertEqual(config.get_metadata("new_key"), "new_value")

    def test_llm_config_parameter_methods(self) -> None:
        """测试参数方法"""
        config_data: Dict[str, Any] = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "parameters": {"temperature": 0.7, "max_tokens": 100}
        }
        
        config = LLMConfig(**config_data)
        
        # 测试获取参数
        self.assertEqual(config.get_parameter("temperature"), 0.7)
        self.assertEqual(config.get_parameter("max_tokens"), 100)
        self.assertEqual(config.get_parameter("nonexistent", 1.0), 1.0)
        
        # 测试设置参数
        config.set_parameter("new_param", "value")
        self.assertEqual(config.get_parameter("new_param"), "value")

    def test_llm_config_merge_parameters(self) -> None:
        """测试参数合并"""
        config_data: Dict[str, Any] = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "parameters": {"temperature": 0.7, "max_tokens": 100}
        }
        
        config = LLMConfig(**config_data)
        
        other_params = {"temperature": 0.5, "top_p": 0.9}
        merged = config.merge_parameters(other_params)
        
        # 验证合并结果
        self.assertEqual(merged["temperature"], 0.5)  # 覆盖
        self.assertEqual(merged["max_tokens"], 100)  # 保留
        self.assertEqual(merged["top_p"], 0.9)  # 新增

    def test_llm_config_validation_model_type(self) -> None:
        """测试模型类型验证"""
        # 使用字典解包来避免Pylance类型检查问题
        invalid_config: Dict[str, Any] = {
            "model_type": "invalid_type",
            "model_name": "test-model"
        }
        with self.assertRaises(ValueError):
            LLMConfig(**invalid_config)

        # 测试有效类型
        valid_types = ["openai", "gemini", "anthropic", "claude", "local"]
        for model_type in valid_types:
            valid_config: Dict[str, Any] = {
                "model_type": model_type,
                "model_name": "test-model"
            }
            config = LLMConfig(**valid_config)
            self.assertEqual(config.model_type, model_type.lower())

    def test_llm_config_validation_base_url(self) -> None:
        """测试基础URL验证"""
        # 使用字典解包来避免Pylance类型检查问题
        invalid_config: Dict[str, Any] = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "base_url": "invalid_url"
        }
        with self.assertRaises(ValueError):
            LLMConfig(**invalid_config)

        # 测试有效URL
        valid_config: Dict[str, Any] = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "base_url": "https://api.openai.com/v1"
        }
        config = LLMConfig(**valid_config)
        self.assertEqual(config.base_url, "https://api.openai.com/v1")

    def test_llm_config_get_headers(self) -> None:
        """测试获取请求头"""
        # 使用字典解包来避免Pylance类型检查问题
        config_data: Dict[str, Any] = {
            "model_type": "openai",
            "model_name": "gpt-4",
            "api_key": "test_key",
            "headers": {"User-Agent": "test-agent"}
        }
        config = LLMConfig(**config_data)
        
        headers = config.get_headers()
        
        # 验证API密钥被正确设置，以及User-Agent头也被保留
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], "Bearer test_key")
        self.assertEqual(headers["User-Agent"], "test-agent")

        # 测试不同提供商的API密钥头
        gemini_config: Dict[str, Any] = {
            "model_type": "gemini",
            "model_name": "gemini-pro",
            "api_key": "gemini_key"
        }
        config_gemini = LLMConfig(**gemini_config)
        
        headers_gemini = config_gemini.get_headers()
        self.assertIn("x-goog-api-key", headers_gemini)
        self.assertEqual(headers_gemini["x-goog-api-key"], "gemini_key")

        anthropic_config: Dict[str, Any] = {
            "model_type": "anthropic",
            "model_name": "claude-3",
            "api_key": "anthropic_key"
        }
        config_anthropic = LLMConfig(**anthropic_config)
        
        headers_anthropic = config_anthropic.get_headers()
        self.assertIn("x-api-key", headers_anthropic)
        self.assertEqual(headers_anthropic["x-api-key"], "anthropic_key")


if __name__ == '__main__':
    unittest.main()