"""增强缓存配置测试"""

import pytest
from typing import Any, Dict, Optional

from src.infrastructure.llm.cache.enhanced_cache_config import EnhancedCacheConfig, GeminiCacheConfig
from src.infrastructure.llm.cache.cache_config import CacheConfig


class TestEnhancedCacheConfig:
    """测试增强缓存配置"""
    
    def test_inheritance(self):
        """测试继承自CacheConfig"""
        config = EnhancedCacheConfig()
        
        # 应该继承所有CacheConfig的属性
        assert hasattr(config, 'enabled')
        assert hasattr(config, 'ttl_seconds')
        assert hasattr(config, 'max_size')
        assert hasattr(config, 'cache_type')
        assert hasattr(config, 'cache_control_type')
        assert hasattr(config, 'max_tokens')
        assert hasattr(config, 'content_cache_enabled')
        assert hasattr(config, 'content_cache_ttl')
        assert hasattr(config, 'content_cache_display_name')
        assert hasattr(config, 'provider_config')
        
        # 应该继承所有CacheConfig的方法
        assert hasattr(config, 'is_enabled')
        assert hasattr(config, 'get_ttl_seconds')
        assert hasattr(config, 'get_max_size')
        assert hasattr(config, 'get_provider_config')
        assert hasattr(config, 'from_dict')
        assert hasattr(config, 'to_dict')
    
    def test_default_values(self):
        """测试默认值"""
        config = EnhancedCacheConfig()
        
        # 继承的默认值
        assert config.enabled is True
        assert config.ttl_seconds == 3600
        assert config.max_size == 1000
        assert config.cache_type == "memory"
        assert config.cache_control_type is None
        assert config.max_tokens is None
        assert config.content_cache_enabled is False
        assert config.content_cache_ttl == "3600s"
        assert config.content_cache_display_name is None
        assert config.provider_config == {}
        
        # 新增的默认值
        assert config.server_cache_enabled is False
        assert config.auto_server_cache is False
        assert config.server_cache_ttl == "3600s"
        assert config.server_cache_display_name is None
        assert config.large_content_threshold == 1048576  # 1MB
        assert config.cache_strategy == "client_first"
        assert config.server_cache_for_large_content is True
    
    def test_custom_values(self):
        """测试自定义值"""
        config = EnhancedCacheConfig(
            # 继承的参数
            enabled=False,
            ttl_seconds=7200,
            max_size=500,
            cache_type="redis",
            cache_control_type="persistent",
            max_tokens=1000,
            content_cache_enabled=True,
            content_cache_ttl="7200s",
            content_cache_display_name="test_cache",
            provider_config={"host": "localhost"},
            
            # 新增的参数
            server_cache_enabled=True,
            auto_server_cache=True,
            server_cache_ttl="1800s",
            server_cache_display_name="server_cache",
            large_content_threshold=512 * 1024,  # 512KB
            cache_strategy="server_first",
            server_cache_for_large_content=False
        )
        
        # 验证继承的参数
        assert config.enabled is False
        assert config.ttl_seconds == 7200
        assert config.max_size == 500
        assert config.cache_type == "redis"
        assert config.cache_control_type == "persistent"
        assert config.max_tokens == 1000
        assert config.content_cache_enabled is True
        assert config.content_cache_ttl == "7200s"
        assert config.content_cache_display_name == "test_cache"
        assert config.provider_config == {"host": "localhost"}
        
        # 验证新增的参数
        assert config.server_cache_enabled is True
        assert config.auto_server_cache is True
        assert config.server_cache_ttl == "1800s"
        assert config.server_cache_display_name == "server_cache"
        assert config.large_content_threshold == 512 * 1024
        assert config.cache_strategy == "server_first"
        assert config.server_cache_for_large_content is False
    
    def test_invalid_cache_strategy(self):
        """测试无效的缓存策略"""
        with pytest.raises(ValueError, match="无效的缓存策略"):
            EnhancedCacheConfig(cache_strategy="invalid_strategy")
    
    def test_invalid_ttl_format(self):
        """测试无效的TTL格式"""
        with pytest.raises(ValueError, match="无效的服务器端缓存TTL格式"):
            EnhancedCacheConfig(server_cache_ttl="invalid_format")
    
    def test_valid_ttl_formats(self):
        """测试有效的TTL格式"""
        valid_ttls = ["300s", "1h", "1d", "1w", "60s", "24h", "7d"]
        
        for ttl in valid_ttls:
            config = EnhancedCacheConfig(server_cache_ttl=ttl)
            assert config.server_cache_ttl == ttl
    
    def test_invalid_ttl_formats(self):
        """测试无效的TTL格式"""
        invalid_ttls = ["300", "1hour", "h", "invalid", "300s_invalid", ""]
        
        for ttl in invalid_ttls:
            with pytest.raises(ValueError):
                EnhancedCacheConfig(server_cache_ttl=ttl)
    
    def test_to_dict(self):
        """测试转换为字典"""
        config = EnhancedCacheConfig(
            # 基础配置
            enabled=False,
            ttl_seconds=7200,
            max_size=500,
            cache_type="redis",
            cache_control_type="persistent",
            max_tokens=1000,
            content_cache_enabled=True,
            content_cache_ttl="7200s",
            content_cache_display_name="test_cache",
            provider_config={"host": "localhost"},
            
            # 服务器端缓存配置
            server_cache_enabled=True,
            auto_server_cache=True,
            server_cache_ttl="1800s",
            server_cache_display_name="server_cache",
            large_content_threshold=512 * 1024,
            cache_strategy="server_first",
            server_cache_for_large_content=False
        )
        
        config_dict = config.to_dict()
        
        expected_keys = [
            "enabled", "ttl_seconds", "max_size", "cache_type", "cache_control_type",
            "max_tokens", "content_cache_enabled", "content_cache_ttl", 
            "content_cache_display_name", "provider_config",
            "server_cache_enabled", "auto_server_cache", "server_cache_ttl",
            "server_cache_display_name", "large_content_threshold", 
            "cache_strategy", "server_cache_for_large_content"
        ]
        
        for key in expected_keys:
            assert key in config_dict
    
    def test_from_dict(self):
        """测试从字典创建配置"""
        config_dict = {
            # 基础配置
            "enabled": False,
            "ttl_seconds": 7200,
            "max_size": 500,
            "cache_type": "redis",
            "cache_control_type": "persistent",
            "max_tokens": 1000,
            "content_cache_enabled": True,
            "content_cache_ttl": "7200s",
            "content_cache_display_name": "test_cache",
            "provider_config": {"host": "localhost"},
            
            # 服务器端缓存配置
            "server_cache_enabled": True,
            "auto_server_cache": True,
            "server_cache_ttl": "1800s",
            "server_cache_display_name": "server_cache",
            "large_content_threshold": 512 * 1024,
            "cache_strategy": "server_first",
            "server_cache_for_large_content": False
        }
        
        config = EnhancedCacheConfig.from_dict(config_dict)
        
        # 验证所有属性
        assert config.enabled is False
        assert config.ttl_seconds == 7200
        assert config.max_size == 500
        assert config.cache_type == "redis"
        assert config.cache_control_type == "persistent"
        assert config.max_tokens == 1000
        assert config.content_cache_enabled is True
        assert config.content_cache_ttl == "7200s"
        assert config.content_cache_display_name == "test_cache"
        assert config.provider_config == {"host": "localhost"}
        
        assert config.server_cache_enabled is True
        assert config.auto_server_cache is True
        assert config.server_cache_ttl == "1800s"
        assert config.server_cache_display_name == "server_cache"
        assert config.large_content_threshold == 512 * 1024
        assert config.cache_strategy == "server_first"
        assert config.server_cache_for_large_content is False
    
    def test_should_use_server_cache_disabled(self):
        """测试服务器端缓存未启用"""
        config = EnhancedCacheConfig(server_cache_enabled=False)
        
        assert config.should_use_server_cache(1048576) is False  # 1MB
        assert config.should_use_server_cache(1048577) is False  # 1MB + 1
        assert config.should_use_server_cache(0) is False
    
    def test_should_use_server_cache_large_content(self):
        """测试大内容使用服务器端缓存"""
        config = EnhancedCacheConfig(
            server_cache_enabled=True,
            server_cache_for_large_content=True,
            large_content_threshold=1048576  # 1MB
        )
        
        # 小于阈值不应该使用服务器端缓存
        assert config.should_use_server_cache(1024) is False     # 1KB
        assert config.should_use_server_cache(1048575) is False  # 1MB - 1
        
        # 大于或等于阈值应该使用服务器端缓存
        assert config.should_use_server_cache(1048576) is True   # 1MB
        assert config.should_use_server_cache(2097152) is True   # 2MB
    
    def test_should_use_server_cache_auto(self):
        """测试自动服务器端缓存"""
        config = EnhancedCacheConfig(
            server_cache_enabled=True,
            auto_server_cache=True,
            server_cache_for_large_content=False
        )
        
        # 任何内容都应该使用服务器端缓存
        assert config.should_use_server_cache(1024) is True      # 小内容
        assert config.should_use_server_cache(1048576) is True   # 大内容
        assert config.should_use_server_cache(0) is True         # 空内容
    
    def test_get_cache_priority_client_first(self):
        """测试客户端优先策略"""
        config = EnhancedCacheConfig(cache_strategy="client_first")
        
        priority = config.get_cache_priority()
        assert priority == "client"
    
    def test_get_cache_priority_server_first(self):
        """测试服务器端优先策略"""
        config = EnhancedCacheConfig(cache_strategy="server_first")
        
        priority = config.get_cache_priority()
        assert priority == "server"
    
    def test_get_cache_priority_hybrid(self):
        """测试混合策略"""
        config = EnhancedCacheConfig(cache_strategy="hybrid")
        
        priority = config.get_cache_priority()
        assert priority == "hybrid"
    
    def test_merge_with_self(self):
        """测试与自身合并"""
        config = EnhancedCacheConfig(
            enabled=True,
            ttl_seconds=3600,
            server_cache_enabled=False
        )
        
        merged = config.merge_with(config)
        
        # 结果应该与原始配置相同
        assert merged.enabled == config.enabled
        assert merged.ttl_seconds == config.ttl_seconds
        assert merged.server_cache_enabled == config.server_cache_enabled
    
    def test_merge_with_different_config(self):
        """测试与不同配置合并"""
        config1 = EnhancedCacheConfig(
            enabled=True,
            ttl_seconds=3600,
            max_size=1000,
            server_cache_enabled=False,
            auto_server_cache=False
        )
        
        config2 = EnhancedCacheConfig(
            enabled=False,  # 不同的值
            ttl_seconds=7200,
            max_size=500,
            server_cache_enabled=True,  # 不同的值
            auto_server_cache=True,     # 不同的值
            server_cache_ttl="1800s"    # 新的值
        )
        
        merged = config1.merge_with(config2)
        
        # 应该使用config2的值（不同的值）
        assert merged.enabled is False
        assert merged.ttl_seconds == 7200
        assert merged.max_size == 500
        assert merged.server_cache_enabled is True
        assert merged.auto_server_cache is True
        assert merged.server_cache_ttl == "1800s"
    
    def test_merge_with_same_config(self):
        """测试与相同配置合并"""
        config1 = EnhancedCacheConfig(
            enabled=True,
            ttl_seconds=3600,
            server_cache_enabled=True,
            cache_strategy="client_first"
        )
        
        config2 = EnhancedCacheConfig(
            enabled=True,  # 相同
            ttl_seconds=3600,  # 相同
            server_cache_enabled=True,  # 相同
            cache_strategy="client_first"  # 相同
        )
        
        merged = config1.merge_with(config2)
        
        # 应该使用原始值（相同值）
        assert merged.enabled is True
        assert merged.ttl_seconds == 3600
        assert merged.server_cache_enabled is True
        assert merged.cache_strategy == "client_first"
    
    def test_merge_with_none_display_name(self):
        """测试与None显示名称合并"""
        config1 = EnhancedCacheConfig(
            content_cache_display_name="original",
            server_cache_display_name="original_server"
        )
        
        config2 = EnhancedCacheConfig(
            content_cache_display_name=None,  # None应该被忽略
            server_cache_display_name="new_server"
        )
        
        merged = config1.merge_with(config2)
        
        # 应该保留原始的content_cache_display_name
        assert merged.content_cache_display_name == "original"
        
        # 应该使用新的server_cache_display_name
        assert merged.server_cache_display_name == "new_server"


class TestGeminiCacheConfig:
    """测试Gemini缓存配置"""
    
    def test_inheritance(self):
        """测试继承自EnhancedCacheConfig"""
        config = GeminiCacheConfig()
        
        # 应该继承所有EnhancedCacheConfig的属性
        assert hasattr(config, 'server_cache_enabled')
        assert hasattr(config, 'auto_server_cache')
        assert hasattr(config, 'server_cache_ttl')
        assert hasattr(config, 'server_cache_display_name')
        assert hasattr(config, 'large_content_threshold')
        assert hasattr(config, 'cache_strategy')
        assert hasattr(config, 'server_cache_for_large_content')
        
        # 应该有Gemini特定的属性
        assert hasattr(config, 'model_name')
    
    def test_default_values(self):
        """测试默认值"""
        config = GeminiCacheConfig()
        
        # 继承的默认值（可能被子类修改）
        assert config.enabled is True
        assert config.ttl_seconds == 3600
        assert config.max_size == 1000
        assert config.cache_type == "memory"
        
        # Gemini特定的默认值
        assert config.model_name == "gemini-2.0-flash-001"
        
        # 继承EnhancedCacheConfig的默认值
        assert config.server_cache_enabled is False
        assert config.auto_server_cache is False
        assert config.server_cache_ttl == "3600s"
        assert config.server_cache_display_name is None
        assert config.large_content_threshold == 512 * 1024  # 在__post_init__中被修改
        assert config.cache_strategy == "client_first"
        assert config.server_cache_for_large_content is True
    
    def test_custom_model_name(self):
        """测试自定义模型名称"""
        config = GeminiCacheConfig(model_name="custom-model")
        
        assert config.model_name == "custom-model"
    
    def test_large_content_threshold_adjustment(self):
        """测试大内容阈值调整"""
        # 测试默认值（应该被调整为512KB）
        config = GeminiCacheConfig()
        assert config.large_content_threshold == 512 * 1024
        
        # 测试自定义值（不应该被调整）
        config = GeminiCacheConfig(large_content_threshold=1024 * 1024)
        assert config.large_content_threshold == 1024 * 1024
    
    def test_server_cache_auto_enabled(self):
        """测试自动启用服务器端缓存"""
        config = GeminiCacheConfig(auto_server_cache=True)
        
        # 当auto_server_cache为True时，server_cache_enabled也应该为True
        assert config.server_cache_enabled is True
        assert config.auto_server_cache is True
    
    def test_create_default(self):
        """测试创建默认配置"""
        config = GeminiCacheConfig.create_default()
        
        assert config.enabled is True
        assert config.max_size == 1000
        assert config.ttl_seconds == 3600
        assert config.cache_type == "memory"
        assert config.server_cache_enabled is True
        assert config.auto_server_cache is True
        assert config.server_cache_ttl == "3600s"
        assert config.large_content_threshold == 512 * 1024
        assert config.cache_strategy == "hybrid"
        assert config.server_cache_for_large_content is True
        assert config.model_name == "gemini-2.0-flash-001"
    
    def test_create_client_only(self):
        """测试创建仅客户端缓存配置"""
        config = GeminiCacheConfig.create_client_only()
        
        assert config.enabled is True
        assert config.max_size == 1000
        assert config.ttl_seconds == 3600
        assert config.cache_type == "memory"
        assert config.server_cache_enabled is False
        assert config.auto_server_cache is False
        assert config.cache_strategy == "client_first"
        assert config.server_cache_for_large_content is False
        assert config.model_name == "gemini-2.0-flash-001"
    
    def test_create_server_focused(self):
        """测试创建以服务器端缓存为主的配置"""
        config = GeminiCacheConfig.create_server_focused()
        
        assert config.enabled is True
        assert config.max_size == 100  # 减少的客户端缓存
        assert config.ttl_seconds == 1800  # 减少的客户端缓存TTL
        assert config.cache_type == "memory"
        assert config.server_cache_enabled is True
        assert config.auto_server_cache is True
        assert config.server_cache_ttl == "7200s"  # 增加的服务器端缓存TTL
        assert config.large_content_threshold == 256 * 1024  # 降低的阈值
        assert config.cache_strategy == "server_first"
        assert config.server_cache_for_large_content is True
        assert config.model_name == "gemini-2.0-flash-001"


class TestEnhancedCacheConfigEdgeCases:
    """测试增强缓存配置的边界情况"""
    
    def test_large_threshold_values(self):
        """测试大的阈值"""
        config = EnhancedCacheConfig(large_content_threshold=1073741824)  # 1GB
        
        assert config.large_content_threshold == 1073741824
        assert config.should_use_server_cache(1073741823) is False
        assert config.should_use_server_cache(1073741824) is True
    
    def test_small_threshold_values(self):
        """测试小的阈值"""
        config = EnhancedCacheConfig(large_content_threshold=1024)  # 1KB
        
        assert config.large_content_threshold == 1024
        assert config.should_use_server_cache(1023) is False
        assert config.should_use_server_cache(1024) is True
    
    def test_zero_threshold(self):
        """测试零阈值"""
        config = EnhancedCacheConfig(large_content_threshold=0)
        
        assert config.large_content_threshold == 0
        # 任何内容都应该被视为大内容
        assert config.should_use_server_cache(1) is True
        assert config.should_use_server_cache(0) is True
    
    def test_all_cache_strategies(self):
        """测试所有缓存策略"""
        strategies = ["client_first", "server_first", "hybrid"]
        
        for strategy in strategies:
            config = EnhancedCacheConfig(cache_strategy=strategy)
            assert config.cache_strategy == strategy
            
            priority = config.get_cache_priority()
            if strategy == "client_first":
                assert priority == "client"
            elif strategy == "server_first":
                assert priority == "server"
            elif strategy == "hybrid":
                assert priority == "hybrid"


class TestGeminiCacheConfigEdgeCases:
    """测试Gemini缓存配置的边界情况"""
    
    def test_empty_model_name(self):
        """测试空模型名称"""
        config = GeminiCacheConfig(model_name="")
        assert config.model_name == ""
    
    def test_very_long_model_name(self):
        """测试很长的模型名称"""
        long_name = "very_long_model_name_" * 10
        config = GeminiCacheConfig(model_name=long_name)
        assert config.model_name == long_name
    
    def test_special_characters_in_model_name(self):
        """测试模型名称中的特殊字符"""
        special_name = "model-v2.0-flash@001"
        config = GeminiCacheConfig(model_name=special_name)
        assert config.model_name == special_name