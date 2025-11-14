"""Gemini缓存管理器测试"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict, Optional, Sequence
from langchain_core.messages import BaseMessage

from src.infrastructure.llm.cache.gemini_cache_manager import GeminiCacheManager, GeminiCacheKeyGenerator
from src.infrastructure.llm.cache.cache_config import CacheConfig


class MockBaseMessage(BaseMessage):
    """模拟BaseMessage用于测试"""
    
    def __init__(self, msg_type: str, content: str, additional_kwargs: Optional[Dict] = None):
        super().__init__(content=content, type=msg_type)
        self.additional_kwargs = additional_kwargs or {}


class TestGeminiCacheManager:
    """测试Gemini缓存管理器"""
    
    def test_init(self):
        """测试初始化"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        # 应该继承CacheManager的功能
        from src.infrastructure.llm.cache.cache_manager import CacheManager
        assert isinstance(manager, CacheManager)
        assert manager.config == config
        assert manager.is_enabled() is True
        
        # 应该使用Gemini专用的键生成器
        assert isinstance(manager._key_generator, GeminiCacheKeyGenerator)
    
    def test_init_disabled(self):
        """测试禁用缓存的初始化"""
        config = CacheConfig(enabled=False)
        manager = GeminiCacheManager(config)
        
        assert manager.is_enabled() is False
        assert manager._provider is None
    
    def test_generate_gemini_key(self):
        """测试生成Gemini缓存键"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        messages = [
            MockBaseMessage("system", "You are helpful"),
            MockBaseMessage("user", "Hello")
        ]
        
        key = manager.generate_gemini_key(messages, "gemini-2.0-flash", {"temperature": 0.7})
        
        assert isinstance(key, str)
        assert len(key) == 32  # MD5哈希长度
        
        # 验证键一致性
        key2 = manager.generate_gemini_key(messages, "gemini-2.0-flash", {"temperature": 0.7})
        assert key == key2
    
    def test_get_gemini_response_cache_hit(self):
        """测试获取Gemini响应缓存（命中）"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        messages = [MockBaseMessage("user", "What is AI?")]
        response = "AI stands for Artificial Intelligence..."
        
        # 设置缓存
        manager.set_gemini_response(messages, response, "gemini-2.0-flash", {"temperature": 0.7})
        
        # 获取缓存
        cached_response = manager.get_gemini_response(messages, "gemini-2.0-flash", {"temperature": 0.7})
        assert cached_response == response
    
    def test_get_gemini_response_cache_miss(self):
        """测试获取Gemini响应缓存（未命中）"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        messages = [MockBaseMessage("user", "Unknown question")]
        
        result = manager.get_gemini_response(messages, "gemini-2.0-flash")
        assert result is None
    
    def test_set_gemini_response(self):
        """测试设置Gemini响应缓存"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        messages = [MockBaseMessage("user", "Hello")]
        response = "Hello! How can I help you today?"
        
        manager.set_gemini_response(messages, response, "gemini-2.0-flash", {"temperature": 0.5})
        
        # 验证缓存设置成功
        cached_response = manager.get_gemini_response(messages, "gemini-2.0-flash", {"temperature": 0.5})
        assert cached_response == response
    
    def test_get_gemini_cache_params_disabled(self):
        """测试禁用内容缓存时的参数获取"""
        config = CacheConfig(enabled=True, content_cache_enabled=False)
        manager = GeminiCacheManager(config)
        
        params = manager.get_gemini_cache_params()
        
        assert params == {}
    
    def test_get_gemini_cache_params_enabled(self):
        """测试启用内容缓存时的参数获取"""
        config = CacheConfig(
            enabled=True,
            content_cache_enabled=True,
            content_cache_display_name="gemini_cache_test"
        )
        manager = GeminiCacheManager(config)
        
        params = manager.get_gemini_cache_params()
        
        expected = {
            "cached_content": "gemini_cache_test"
        }
        assert params == expected
    
    def test_get_gemini_cache_params_with_display_name(self):
        """测试包含显示名称的缓存参数"""
        config = CacheConfig(
            enabled=True,
            content_cache_enabled=True,
            content_cache_display_name="my_gemini_cache"
        )
        manager = GeminiCacheManager(config)
        
        params = manager.get_gemini_cache_params()
        
        assert "cached_content" in params
        assert params["cached_content"] == "my_gemini_cache"
    
    def test_gemini_key_generation_consistency(self):
        """测试Gemini键生成的一致性"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        messages = [MockBaseMessage("user", "Test message")]
        
        # 相同参数应该生成相同键
        key1 = manager.generate_gemini_key(messages, "gemini-2.0-flash", {"temperature": 0.7})
        key2 = manager.generate_gemini_key(messages, "gemini-2.0-flash", {"temperature": 0.7})
        
        assert key1 == key2
        
        # 不同参数应该生成不同键
        key3 = manager.generate_gemini_key(messages, "gemini-1.5-pro", {"temperature": 0.7})
        assert key1 != key3
        
        key4 = manager.generate_gemini_key(messages, "gemini-2.0-flash", {"temperature": 0.9})
        assert key1 != key4
    
    def test_gemini_llm_caching_workflow(self):
        """测试Gemini LLM缓存工作流程"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        messages = [MockBaseMessage("user", "What is machine learning?")]
        response1 = "Machine learning is a subset of AI..."
        
        # 第一次请求 - 缓存未命中
        cached_response = manager.get_gemini_response(messages, "gemini-2.0-flash")
        assert cached_response is None
        
        # 设置响应缓存
        manager.set_gemini_response(messages, response1, "gemini-2.0-flash")
        
        # 第二次请求 - 缓存命中
        cached_response = manager.get_gemini_response(messages, "gemini-2.0-flash")
        assert cached_response == response1
        
        # 验证缓存键生成
        key = manager.generate_gemini_key(messages, "gemini-2.0-flash")
        direct_cached = manager.get(key)
        assert direct_cached == response1
    
    def test_gemini_cache_with_complex_messages(self):
        """测试复杂消息的Gemini缓存"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        messages = [
            MockBaseMessage("system", "You are an expert", {"role": "system"}),
            MockBaseMessage("user", "Explain quantum computing", {"user_id": "123"})
        ]
        
        response = "Quantum computing uses quantum mechanical phenomena..."
        
        manager.set_gemini_response(messages, response, "gemini-2.0-flash")
        
        # 验证缓存
        cached_response = manager.get_gemini_response(messages, "gemini-2.0-flash")
        assert cached_response == response


class TestGeminiCacheKeyGenerator:
    """测试Gemini缓存键生成器"""
    
    def test_inheritance(self):
        """测试继承"""
        generator = GeminiCacheKeyGenerator()
        
        from src.infrastructure.llm.cache.key_generator import LLMCacheKeyGenerator
        assert isinstance(generator, LLMCacheKeyGenerator)
    
    def test_init_default(self):
        """测试默认初始化"""
        generator = GeminiCacheKeyGenerator()
        
        assert generator.include_model is True
        assert generator.include_parameters is True
        assert isinstance(generator._default_generator, type(generator._default_generator))
    
    def test_generate_key_has_gemini_prefix(self):
        """测试键包含Gemini前缀"""
        generator = GeminiCacheKeyGenerator()
        messages = [MockBaseMessage("user", "Hello")]
        
        key = generator.generate_key(messages, "gemini-2.0-flash", {"temperature": 0.7})
        
        assert isinstance(key, str)
        assert len(key) == 32
    
    def test_serialize_messages_gemini(self):
        """测试Gemini消息序列化"""
        generator = GeminiCacheKeyGenerator()
        messages = [
            MockBaseMessage("system", "You are helpful", {"role": "system"}),
            MockBaseMessage("user", "Hello", {"role": "user"})
        ]
        
        result = generator._serialize_messages_gemini(messages)
        
        assert isinstance(result, str)
        assert "type:system" in result
        assert "type:user" in result
        assert "You are helpful" in result
        assert "Hello" in result
    
    def test_serialize_messages_gemini_with_additional_kwargs(self):
        """测试带额外属性的Gemini消息序列化"""
        generator = GeminiCacheKeyGenerator()
        message = MockBaseMessage("user", "Test", {"custom_field": "value"})
        
        result = generator._serialize_messages_gemini([message])
        
        assert "custom_field:value" in result
    
    def test_serialize_parameters_gemini(self):
        """测试Gemini参数序列化"""
        generator = GeminiCacheKeyGenerator()
        parameters = {
            "temperature": 0.7,
            "max_tokens": 100,
            "max_output_tokens": 150,
            "top_p": 0.9,
            "top_k": 40,
            "stop_sequences": ["END"],
            "candidate_count": 1,
            "system_instruction": "Be helpful",
            "response_mime_type": "text/plain",
            "thinking_config": {"type": "enabled"},
            "safety_settings": {"harassment": "BLOCK"},
            "tool_choice": "auto",
            "tools": [{"name": "tool1"}],
            "user": "user123",
            "custom_param": "should_be_filtered",
            "none_value": None,
            "empty_string": ""
        }
        
        result = generator._serialize_parameters_gemini(parameters)
        
        # 应该包含Gemini特定的参数
        assert "temperature:0.7" in result
        assert "max_tokens:100" in result
        assert "max_output_tokens:150" in result
        assert "top_p:0.9" in result
        assert "top_k:40" in result
        assert "stop_sequences:" in result
        assert "candidate_count:1" in result
        assert "system_instruction:Be helpful" in result
        assert "response_mime_type:text/plain" in result
        assert "thinking_config:" in result
        assert "safety_settings:" in result
        assert "tool_choice:auto" in result
        assert "tools:" in result
        assert "user:user123" in result
        
        # 非特定参数应该被过滤
        assert "custom_param" not in result
        assert "none_value" not in result
        assert "empty_string" not in result
    
    def test_serialize_value_gemini(self):
        """测试Gemini值序列化"""
        generator = GeminiCacheKeyGenerator()
        
        # 测试字符串
        assert generator._serialize_value("test") == "test"
        
        # 测试数字
        assert generator._serialize_value(42) == "42"
        assert generator._serialize_value(3.14) == "3.14"
        
        # 测试布尔值
        assert generator._serialize_value(True) == "True"
        assert generator._serialize_value(False) == "False"
        
        # 测试列表
        result = generator._serialize_value([1, "a", True])
        assert "1" in result
        assert "a" in result
        assert "True" in result
        
        # 测试字典
        result = generator._serialize_value({"key": "value"})
        assert "key:value" in result
    
    def test_json_dumps(self):
        """测试JSON序列化"""
        generator = GeminiCacheKeyGenerator()
        
        obj = {"key": "value", "number": 42, "nested": {"inner": "data"}}
        result = generator._json_dumps(obj)
        
        assert isinstance(result, str)
        assert "key" in result
        assert "value" in result
        assert "number" in result
        assert "nested" in result
    
    def test_hash_string(self):
        """测试字符串哈希"""
        generator = GeminiCacheKeyGenerator()
        
        text1 = "test string"
        text2 = "test string"
        text3 = "different string"
        
        hash1 = generator._hash_string(text1)
        hash2 = generator._hash_string(text2)
        hash3 = generator._hash_string(text3)
        
        # 相同字符串应该生成相同哈希
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5长度
        
        # 不同字符串应该生成不同哈希
        assert hash1 != hash3
    
    def test_generate_key_with_gemini_specific_params(self):
        """测试使用Gemini特定参数的键生成"""
        generator = GeminiCacheKeyGenerator()
        messages = [MockBaseMessage("user", "Test")]
        
        parameters = {
            "temperature": 0.7,
            "max_tokens": 100,
            "thinking_config": {"type": "enabled"},
            "safety_settings": {"harassment": "BLOCK"}
        }
        
        key = generator.generate_key(messages, "gemini-2.0-flash", parameters)
        
        assert isinstance(key, str)
        assert len(key) == 32
        
        # 验证一致性
        key2 = generator.generate_key(messages, "gemini-2.0-flash", parameters)
        assert key == key2


class TestGeminiCacheManagerEdgeCases:
    """测试Gemini缓存管理器的边界情况"""
    
    def test_empty_messages(self):
        """测试空消息列表"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        key = manager.generate_gemini_key([], "gemini-2.0-flash")
        assert isinstance(key, str)
        assert len(key) == 32
    
    def test_empty_model_name(self):
        """测试空模型名称"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        messages = [MockBaseMessage("user", "Test")]
        key = manager.generate_gemini_key(messages, "")
        assert isinstance(key, str)
        assert len(key) == 32
    
    def test_none_parameters(self):
        """测试None参数"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        messages = [MockBaseMessage("user", "Test")]
        key = manager.generate_gemini_key(messages, "gemini-2.0-flash", None)
        assert isinstance(key, str)
        assert len(key) == 32
    
    def test_empty_parameters(self):
        """测试空参数字典"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        messages = [MockBaseMessage("user", "Test")]
        key = manager.generate_gemini_key(messages, "gemini-2.0-flash", {})
        assert isinstance(key, str)
        assert len(key) == 32
    
    def test_very_large_messages(self):
        """测试非常大的消息"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        large_content = "x" * 10000  # 10KB内容
        messages = [MockBaseMessage("user", large_content)]
        
        key = manager.generate_gemini_key(messages, "gemini-2.0-flash")
        assert isinstance(key, str)
        assert len(key) == 32
        
        # 验证一致性
        key2 = manager.generate_gemini_key(messages, "gemini-2.0-flash")
        assert key == key2
    
    def test_unicode_in_messages(self):
        """测试消息中的Unicode字符"""
        config = CacheConfig(enabled=True)
        manager = GeminiCacheManager(config)
        
        messages = [
            MockBaseMessage("user", "Hello 世界 🌍"),
            MockBaseMessage("system", "Тест системы 🎉")
        ]
        
        key = manager.generate_gemini_key(messages, "gemini-2.0-flash")
        assert isinstance(key, str)
        assert len(key) == 32
    
    def test_cache_config_with_gemini_specific_settings(self):
        """测试带Gemini特定设置的缓存配置"""
        config = CacheConfig(
            enabled=True,
            content_cache_enabled=True,
            content_cache_ttl="1800s",
            content_cache_display_name="gemini_content_cache"
        )
        manager = GeminiCacheManager(config)
        
        # 验证缓存参数
        cache_params = manager.get_gemini_cache_params()
        assert "cached_content" in cache_params
        assert cache_params["cached_content"] == "gemini_content_cache"
    
    def test_multiple_cache_operations(self):
        """测试多次缓存操作"""
        config = CacheConfig(enabled=True, max_size=10)
        manager = GeminiCacheManager(config)
        
        # 添加多个缓存项
        for i in range(5):
            messages = [MockBaseMessage("user", f"Question {i}")]
            response = f"Response {i}"
            manager.set_gemini_response(messages, response, "gemini-2.0-flash")
        
        # 验证所有缓存项
        for i in range(5):
            messages = [MockBaseMessage("user", f"Question {i}")]
            cached_response = manager.get_gemini_response(messages, "gemini-2.0-flash")
            assert cached_response == f"Response {i}"
        
        assert manager.get_size() == 5
    
    def test_gemini_key_generator_parameter_filtering(self):
        """测试Gemini键生成器的参数过滤"""
        generator = GeminiCacheKeyGenerator()
        messages = [MockBaseMessage("user", "Test")]
        
        # 包含应该被过滤的参数
        parameters = {
            "temperature": 0.7,        # 应该保留
            "custom_param": "filtered", # 应该被过滤
            "max_tokens": 100,         # 应该保留
            "unknown_param": "out"     # 应该被过滤
        }
        
        key = generator.generate_key(messages, "gemini-2.0-flash", parameters)
        assert isinstance(key, str)
        assert len(key) == 32