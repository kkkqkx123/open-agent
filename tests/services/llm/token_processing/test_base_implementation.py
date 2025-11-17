"""测试基础实现类"""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage

from src.services.llm.token_processing.base_implementation import (
    BaseTokenProcessor, 
    CachedTokenProcessor, 
    DegradationTokenProcessor
)
from src.services.llm.token_processing.token_types import TokenUsage


class TestBaseTokenProcessor:
    """测试BaseTokenProcessor类"""
    
    def test_initialization(self):
        """测试初始化"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        
        assert processor.model_name == "gpt-3.5-turbo"
        assert processor.provider == "openai"
        assert processor._last_usage is None
        assert processor._stats["total_requests"] == 0
        assert processor._stats["successful_calculations"] == 0
        assert processor._stats["failed_calculations"] == 0
    
    def test_supports_caching_default(self):
        """测试默认不支持缓存"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        assert processor.supports_caching() is False
    
    def test_supports_degradation_default(self):
        """测试默认不支持降级策略"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        assert processor.supports_degradation() is False
    
    def test_supports_conversation_tracking_default(self):
        """测试默认不支持对话跟踪"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        assert processor.supports_conversation_tracking() is False
    
    def test_clear_cache_default(self):
        """测试默认清空缓存"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        # 应该不会抛出异常
        processor.clear_cache()
    
    def test_get_cache_stats_default(self):
        """测试默认缓存统计"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        stats = processor.get_cache_stats()
        
        assert stats["supports_caching"] is False
        assert stats["cache_size"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
    
    def test_set_degradation_enabled_default(self):
        """测试默认设置降级策略"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        # 应该不会抛出异常
        processor.set_degradation_enabled(True)
        assert processor.is_degradation_enabled() is False
    
    def test_set_conversation_tracking_enabled_default(self):
        """测试默认设置对话跟踪"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        # 应该不会抛出异常
        processor.set_conversation_tracking_enabled(True)
        assert processor.supports_conversation_tracking() is False
    
    def test_get_conversation_stats_default(self):
        """测试默认对话统计"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        stats = processor.get_conversation_stats()
        assert stats is None
    
    def test_clear_conversation_history_default(self):
        """测试默认清空对话历史"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        # 应该不会抛出异常
        processor.clear_conversation_history()
    
    def test_update_stats_on_success(self):
        """测试更新成功统计"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        
        processor._update_stats_on_success()
        
        assert processor._stats["total_requests"] == 1
        assert processor._stats["successful_calculations"] == 1
        assert processor._stats["failed_calculations"] == 0
    
    def test_update_stats_on_failure(self):
        """测试更新失败统计"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        
        processor._update_stats_on_failure()
        
        assert processor._stats["total_requests"] == 1
        assert processor._stats["successful_calculations"] == 0
        assert processor._stats["failed_calculations"] == 1
    
    def test_get_stats(self):
        """测试获取统计信息"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        
        # 添加一些统计数据
        processor._stats["total_requests"] = 10
        processor._stats["successful_calculations"] = 8
        processor._stats["failed_calculations"] = 2
        
        stats = processor.get_stats()
        
        assert stats["total_requests"] == 10
        assert stats["successful_calculations"] == 8
        assert stats["failed_calculations"] == 2
        assert stats["success_rate_percent"] == 80.0
        assert stats["model_name"] == "gpt-3.5-turbo"
        assert stats["provider"] == "openai"
        assert stats["supports_caching"] is False
        assert stats["supports_degradation"] is False
        assert stats["supports_conversation_tracking"] is False
    
    def test_reset_stats(self):
        """测试重置统计信息"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        
        # 添加一些统计数据
        processor._stats["total_requests"] = 10
        processor._stats["successful_calculations"] = 8
        
        processor.reset_stats()
        
        assert processor._stats["total_requests"] == 0
        assert processor._stats["successful_calculations"] == 0
        assert processor._stats["failed_calculations"] == 0
    
    def test_get_provider_name(self):
        """测试获取提供商名称"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        assert processor.get_provider_name() == "openai"
    
    def test_get_last_api_usage(self):
        """测试获取最近API使用情况"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        
        # 初始状态应该是None
        assert processor.get_last_api_usage() is None
        
        # 设置一个usage
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        processor._last_usage = usage
        
        assert processor.get_last_api_usage() == usage
    
    def test_is_api_usage_available(self):
        """测试检查API使用数据是否可用"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        
        # 初始状态应该是False
        assert processor.is_api_usage_available() is False
        
        # 设置一个usage
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        processor._last_usage = usage
        
        assert processor.is_api_usage_available() is True
    
    def test_get_model_info(self):
        """测试获取模型信息"""
        processor = BaseTokenProcessor("gpt-3.5-turbo", "openai")
        
        info = processor.get_model_info()
        
        assert info["model_name"] == "gpt-3.5-turbo"
        assert info["provider"] == "openai"
        assert info["processor_type"] == "BaseTokenProcessor"
        assert info["supports_caching"] is False
        assert info["supports_degradation"] is False
        assert info["supports_conversation_tracking"] is False
        assert "stats" in info


class TestCachedTokenProcessor:
    """测试CachedTokenProcessor类"""
    
    def test_initialization(self):
        """测试初始化"""
        processor = CachedTokenProcessor("gpt-3.5-turbo", "openai", cache_size=500)
        
        assert processor.model_name == "gpt-3.5-turbo"
        assert processor.provider == "openai"
        assert processor.cache_size == 500
        assert len(processor._usage_cache) == 0
    
    def test_supports_caching(self):
        """测试支持缓存"""
        processor = CachedTokenProcessor("gpt-3.5-turbo", "openai")
        assert processor.supports_caching() is True
    
    def test_get_cache_stats(self):
        """测试获取缓存统计"""
        processor = CachedTokenProcessor("gpt-3.5-turbo", "openai", cache_size=100)
        
        stats = processor.get_cache_stats()
        
        assert stats["supports_caching"] is True
        assert stats["cache_size"] == 0
        assert stats["max_cache_size"] == 100
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
    
    def test_cache_operations(self):
        """测试缓存操作"""
        processor = CachedTokenProcessor("gpt-3.5-turbo", "openai", cache_size=2)
        
        # 添加到缓存
        usage1 = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        usage2 = TokenUsage(prompt_tokens=20, completion_tokens=10, total_tokens=30)
        
        cache_key1 = processor._generate_cache_key("test1")
        cache_key2 = processor._generate_cache_key("test2")
        
        processor._add_to_cache(cache_key1, usage1)
        processor._add_to_cache(cache_key2, usage2)
        
        # 验证缓存命中
        assert processor._get_from_cache(cache_key1) == usage1
        assert processor._get_from_cache(cache_key2) == usage2
        
        # 验证缓存未命中
        assert processor._get_from_cache("nonexistent") is None
        
        # 验证统计
        stats = processor.get_cache_stats()
        assert stats["cache_hits"] == 2
        assert stats["cache_misses"] == 1
    
    def test_cache_size_limit(self):
        """测试缓存大小限制"""
        processor = CachedTokenProcessor("gpt-3.5-turbo", "openai", cache_size=2)
        
        # 添加超过缓存大小的项目
        usage1 = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        usage2 = TokenUsage(prompt_tokens=20, completion_tokens=10, total_tokens=30)
        usage3 = TokenUsage(prompt_tokens=30, completion_tokens=15, total_tokens=45)
        
        processor._add_to_cache("key1", usage1)
        processor._add_to_cache("key2", usage2)
        processor._add_to_cache("key3", usage3)  # 应该移除key1
        
        # 验证缓存大小
        assert len(processor._usage_cache) == 2
        assert "key1" not in processor._usage_cache
        assert "key2" in processor._usage_cache
        assert "key3" in processor._usage_cache
    
    def test_clear_cache(self):
        """测试清空缓存"""
        processor = CachedTokenProcessor("gpt-3.5-turbo", "openai")
        
        # 添加一些缓存
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        processor._add_to_cache("test", usage)
        
        assert len(processor._usage_cache) == 1
        
        # 清空缓存
        processor.clear_cache()
        
        assert len(processor._usage_cache) == 0
    
    def test_generate_cache_key(self):
        """测试生成缓存key"""
        processor = CachedTokenProcessor("gpt-3.5-turbo", "openai")
        
        key1 = processor._generate_cache_key("test content")
        key2 = processor._generate_cache_key("test content")
        key3 = processor._generate_cache_key("different content")
        
        # 相同内容应该生成相同的key
        assert key1 == key2
        # 不同内容应该生成不同的key
        assert key1 != key3
        
        # key应该是MD5哈希（32个字符）
        assert len(key1) == 32


class TestDegradationTokenProcessor:
    """测试DegradationTokenProcessor类"""
    
    def test_initialization(self):
        """测试初始化"""
        processor = DegradationTokenProcessor("gpt-3.5-turbo", "openai", degradation_enabled=True)
        
        assert processor.model_name == "gpt-3.5-turbo"
        assert processor.provider == "openai"
        assert processor._degradation_enabled is True
    
    def test_supports_degradation(self):
        """测试支持降级策略"""
        processor = DegradationTokenProcessor("gpt-3.5-turbo", "openai")
        assert processor.supports_degradation() is True
    
    def test_set_degradation_enabled(self):
        """测试设置降级策略"""
        processor = DegradationTokenProcessor("gpt-3.5-turbo", "openai")
        
        processor.set_degradation_enabled(True)
        assert processor.is_degradation_enabled() is True
        
        processor.set_degradation_enabled(False)
        assert processor.is_degradation_enabled() is False
    
    def test_should_degrade(self):
        """测试降级判断"""
        processor = DegradationTokenProcessor("gpt-3.5-turbo", "openai", degradation_enabled=True)
        
        # 测试需要降级的情况（API token数少于本地的25%）
        assert processor._should_degrade(api_count=5, local_count=25) is True
        assert processor._should_degrade(api_count=10, local_count=50) is True
        
        # 测试不需要降级的情况
        assert processor._should_degrade(api_count=15, local_count=25) is False
        assert processor._should_degrade(api_count=30, local_count=50) is False
        
        # 测试禁用降级的情况
        processor.set_degradation_enabled(False)
        assert processor._should_degrade(api_count=5, local_count=25) is False
    
    def test_should_degrade_with_custom_threshold(self):
        """测试自定义阈值的降级判断"""
        processor = DegradationTokenProcessor("gpt-3.5-turbo", "openai", degradation_enabled=True)
        
        # 使用50%的阈值
        assert processor._should_degrade(api_count=10, local_count=25, threshold=0.5) is True
        assert processor._should_degrade(api_count=15, local_count=25, threshold=0.5) is False