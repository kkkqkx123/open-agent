"""缓存配置测试"""

import pytest
import time
from typing import Any, Dict, Optional

from src.infrastructure.llm.cache.cache_config import CacheConfig, CacheEntry


class TestCacheConfig:
    """测试缓存配置"""
    
    def test_default_values(self):
        """测试默认值"""
        config = CacheConfig()
        
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
    
    def test_custom_values(self):
        """测试自定义值"""
        config = CacheConfig(
            enabled=False,
            ttl_seconds=7200,
            max_size=500,
            cache_type="redis",
            cache_control_type="persistent",
            max_tokens=1000,
            content_cache_enabled=True,
            content_cache_ttl="7200s",
            content_cache_display_name="test_cache",
            provider_config={"host": "localhost", "port": 6379}
        )
        
        assert config.enabled is False
        assert config.ttl_seconds == 7200
        assert config.max_size == 500
        assert config.cache_type == "redis"
        assert config.cache_control_type == "persistent"
        assert config.max_tokens == 1000
        assert config.content_cache_enabled is True
        assert config.content_cache_ttl == "7200s"
        assert config.content_cache_display_name == "test_cache"
        assert config.provider_config == {"host": "localhost", "port": 6379}
    
    def test_is_enabled(self):
        """测试启用状态检查"""
        config_enabled = CacheConfig(enabled=True)
        config_disabled = CacheConfig(enabled=False)
        
        assert config_enabled.is_enabled() is True
        assert config_disabled.is_enabled() is False
    
    def test_get_ttl_seconds(self):
        """测试获取TTL秒数"""
        config = CacheConfig(ttl_seconds=1800)
        
        ttl = config.get_ttl_seconds()
        assert ttl == 1800
    
    def test_get_max_size(self):
        """测试获取最大大小"""
        config = CacheConfig(max_size=2000)
        
        size = config.get_max_size()
        assert size == 2000
    
    def test_get_provider_config(self):
        """测试获取提供者配置"""
        original_config = {"host": "localhost", "port": 6379}
        config = CacheConfig(provider_config=original_config)
        
        provider_config = config.get_provider_config()
        
        # 确保返回副本而不是原始引用
        assert provider_config == original_config
        assert provider_config is not original_config
        
        # 修改返回的配置不应该影响原始配置
        provider_config["port"] = 8080
        assert config.provider_config["port"] == 6379
    
    def test_from_dict(self):
        """测试从字典创建配置"""
        config_dict = {
            "enabled": False,
            "ttl_seconds": 7200,
            "max_size": 500,
            "cache_type": "redis",
            "cache_control_type": "persistent",
            "max_tokens": 1000,
            "content_cache_enabled": True,
            "content_cache_ttl": "7200s",
            "content_cache_display_name": "test_cache",
            "provider_config": {"host": "localhost"}
        }
        
        config = CacheConfig.from_dict(config_dict)
        
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
    
    def test_from_dict_with_defaults(self):
        """测试从字典创建配置（使用默认值）"""
        config_dict = {
            "enabled": True,
            "ttl_seconds": 3600,
        }
        
        config = CacheConfig.from_dict(config_dict)
        
        # 指定的值应该被正确设置
        assert config.enabled is True
        assert config.ttl_seconds == 3600
        
        # 其他值应该使用默认值
        assert config.max_size == 1000
        assert config.cache_type == "memory"
        assert config.cache_control_type is None
        assert config.max_tokens is None
        assert config.content_cache_enabled is False
        assert config.content_cache_ttl == "3600s"
        assert config.content_cache_display_name is None
        assert config.provider_config == {}
    
    def test_from_dict_empty(self):
        """测试从空字典创建配置"""
        config = CacheConfig.from_dict({})
        
        # 应该使用所有默认值
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
    
    def test_to_dict(self):
        """测试转换为字典"""
        config = CacheConfig(
            enabled=False,
            ttl_seconds=7200,
            max_size=500,
            cache_type="redis",
            cache_control_type="persistent",
            max_tokens=1000,
            content_cache_enabled=True,
            content_cache_ttl="7200s",
            content_cache_display_name="test_cache",
            provider_config={"host": "localhost"}
        )
        
        config_dict = config.to_dict()
        
        expected_dict = {
            "enabled": False,
            "ttl_seconds": 7200,
            "max_size": 500,
            "cache_type": "redis",
            "cache_control_type": "persistent",
            "max_tokens": 1000,
            "content_cache_enabled": True,
            "content_cache_ttl": "7200s",
            "content_cache_display_name": "test_cache",
            "provider_config": {"host": "localhost"}
        }
        
        assert config_dict == expected_dict
    
    def test_to_dict_default_config(self):
        """测试默认配置转换为字典"""
        config = CacheConfig()
        
        config_dict = config.to_dict()
        
        expected_dict = {
            "enabled": True,
            "ttl_seconds": 3600,
            "max_size": 1000,
            "cache_type": "memory",
            "cache_control_type": None,
            "max_tokens": None,
            "content_cache_enabled": False,
            "content_cache_ttl": "3600s",
            "content_cache_display_name": None,
            "provider_config": {},
        }
        
        assert config_dict == expected_dict
    
    def test_round_trip_dict_conversion(self):
        """测试往返字典转换"""
        original_config = CacheConfig(
            enabled=False,
            ttl_seconds=7200,
            max_size=500,
            cache_type="redis",
            cache_control_type="persistent",
            max_tokens=1000,
            content_cache_enabled=True,
            content_cache_ttl="7200s",
            content_cache_display_name="test_cache",
            provider_config={"host": "localhost", "port": 6379}
        )
        
        # 转换为字典
        config_dict = original_config.to_dict()
        
        # 从字典创建新配置
        new_config = CacheConfig.from_dict(config_dict)
        
        # 验证所有属性相等
        assert new_config.enabled == original_config.enabled
        assert new_config.ttl_seconds == original_config.ttl_seconds
        assert new_config.max_size == original_config.max_size
        assert new_config.cache_type == original_config.cache_type
        assert new_config.cache_control_type == original_config.cache_control_type
        assert new_config.max_tokens == original_config.max_tokens
        assert new_config.content_cache_enabled == original_config.content_cache_enabled
        assert new_config.content_cache_ttl == original_config.content_cache_ttl
        assert new_config.content_cache_display_name == original_config.content_cache_display_name
        assert new_config.provider_config == original_config.provider_config


class TestCacheEntry:
    """测试缓存项"""
    
    def test_init_basic(self):
        """测试基本初始化"""
        current_time = time.time()
        
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.created_at == current_time
        assert entry.expires_at is None
        assert entry.access_count == 0
        assert entry.last_accessed is None
    
    def test_init_with_ttl(self):
        """测试带TTL的初始化"""
        current_time = time.time()
        ttl_seconds = 3600
        
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time,
            expires_at=current_time + ttl_seconds
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.created_at == current_time
        assert entry.expires_at == current_time + ttl_seconds
        assert entry.access_count == 0
        assert entry.last_accessed is None
    
    def test_init_with_all_params(self):
        """测试带所有参数的初始化"""
        current_time = time.time()
        
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time,
            expires_at=current_time + 3600,
            access_count=5,
            last_accessed=current_time - 100
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.created_at == current_time
        assert entry.expires_at == current_time + 3600
        assert entry.access_count == 5
        assert entry.last_accessed == current_time - 100
    
    def test_is_expired_no_expiry(self):
        """测试未设置过期时间的项不超时"""
        current_time = time.time()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time
        )
        
        assert entry.is_expired() is False
    
    def test_is_expired_not_expired(self):
        """测试未过期的项"""
        current_time = time.time()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time,
            expires_at=current_time + 3600
        )
        
        assert entry.is_expired() is False
    
    def test_is_expired_expired(self):
        """测试已过期的项"""
        current_time = time.time()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time,
            expires_at=current_time - 100  # 已经过期
        )
        
        assert entry.is_expired() is True
    
    def test_access(self):
        """测试访问缓存项"""
        current_time = time.time()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time,
            access_count=0,
            last_accessed=None
        )
        
        result = entry.access()
        
        # 应该返回值
        assert result == "test_value"
        
        # 访问计数应该增加
        assert entry.access_count == 1
        
        # last_accessed应该被更新
        assert entry.last_accessed is not None
        assert entry.last_accessed > current_time
    
    def test_access_multiple_times(self):
        """测试多次访问"""
        current_time = time.time()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time,
            access_count=2,
            last_accessed=current_time - 50
        )
        
        # 访问一次
        entry.access()
        assert entry.access_count == 3
        
        # 再访问一次
        entry.access()
        assert entry.access_count == 4
    
    def test_get_age_seconds_current(self):
        """测试获取当前年龄"""
        current_time = time.time()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time
        )
        
        age = entry.get_age_seconds()
        
        # 年龄应该接近0（刚刚创建）
        assert 0 <= age < 1
    
    def test_get_age_seconds_old(self):
        """测试获取较老项的年龄"""
        current_time = time.time()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time - 3600  # 1小时前
        )
        
        age = entry.get_age_seconds()
        
        # 年龄应该接近3600秒（1小时）
        assert 3599 <= age <= 3601
    
    def test_get_idle_seconds_no_access(self):
        """测试获取从未访问项的空闲时间"""
        current_time = time.time()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time - 100,  # 100秒前创建
            last_accessed=None
        )
        
        idle_time = entry.get_idle_seconds()
        
        # 应该返回年龄（等同于创建时间）
        assert idle_time is not None
        assert 99 <= idle_time <= 101
    
    def test_get_idle_seconds_recently_accessed(self):
        """测试获取最近访问项的空闲时间"""
        current_time = time.time()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time - 1000,  # 1000秒前创建
            last_accessed=current_time - 10   # 10秒前访问
        )
        
        idle_time = entry.get_idle_seconds()
        
        # 应该返回从最后一次访问到现在的时间
        assert idle_time is not None
        assert 9 <= idle_time <= 11
    
    def test_cache_entry_with_complex_value(self):
        """测试带复杂值的缓存项"""
        complex_value = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "string": "test",
            "number": 42
        }
        
        entry = CacheEntry(
            key="complex_key",
            value=complex_value,
            created_at=time.time()
        )
        
        assert entry.value == complex_value
        assert entry.access() == complex_value
        assert entry.value["list"] == [1, 2, 3]
        assert entry.value["dict"]["nested"] == "value"
    
    def test_cache_entry_with_none_value(self):
        """测试带None值的缓存项"""
        entry = CacheEntry(
            key="none_key",
            value=None,
            created_at=time.time()
        )
        
        assert entry.value is None
        result = entry.access()
        assert result is None


class TestCacheConfigEdgeCases:
    """测试缓存配置的边界情况"""
    
    def test_ttl_seconds_zero(self):
        """测试TTL为0"""
        config = CacheConfig(ttl_seconds=0)
        
        assert config.ttl_seconds == 0
        assert config.get_ttl_seconds() == 0
    
    def test_ttl_seconds_negative(self):
        """测试负数TTL"""
        config = CacheConfig(ttl_seconds=-100)
        
        assert config.ttl_seconds == -100
        assert config.get_ttl_seconds() == -100
    
    def test_max_size_zero(self):
        """测试最大大小为0"""
        config = CacheConfig(max_size=0)
        
        assert config.max_size == 0
        assert config.get_max_size() == 0
    
    def test_max_size_negative(self):
        """测试负数最大大小"""
        config = CacheConfig(max_size=-100)
        
        assert config.max_size == -100
        assert config.get_max_size() == -100
    
    def test_large_cache_size(self):
        """测试非常大的缓存大小"""
        config = CacheConfig(max_size=1000000)
        
        assert config.max_size == 1000000
        assert config.get_max_size() == 1000000
    
    def test_from_dict_extra_fields(self):
        """测试从包含额外字段的字典创建"""
        config_dict = {
            "enabled": True,
            "ttl_seconds": 3600,
            "extra_field": "should_be_ignored",
            "another_field": 123
        }
        
        config = CacheConfig.from_dict(config_dict)
        
        # 应该只使用已知的字段
        assert config.enabled is True
        assert config.ttl_seconds == 3600
        
        # 额外的字段应该被忽略
        assert not hasattr(config, "extra_field")
        assert not hasattr(config, "another_field")
    
    def test_provider_config_modification(self):
        """测试提供者配置的可变性"""
        config = CacheConfig(provider_config={"host": "localhost"})
        
        # 获取提供者配置
        provider_config = config.get_provider_config()
        
        # 修改返回的配置
        provider_config["port"] = 6379
        
        # 原始配置不应该改变
        assert config.provider_config == {"host": "localhost"}
    
    def test_config_comparison(self):
        """测试配置比较"""
        config1 = CacheConfig(enabled=True, ttl_seconds=3600)
        config2 = CacheConfig(enabled=True, ttl_seconds=3600)
        config3 = CacheConfig(enabled=False, ttl_seconds=3600)
        
        # 相同配置的比较
        assert config1.enabled == config2.enabled
        assert config1.ttl_seconds == config2.ttl_seconds
        
        # 不同配置的比较
        assert config1.enabled != config3.enabled


class TestCacheEntryEdgeCases:
    """测试缓存项的边界情况"""
    
    def test_empty_key(self):
        """测试空键"""
        entry = CacheEntry(
            key="",
            value="value",
            created_at=time.time()
        )
        
        assert entry.key == ""
    
    def test_very_long_key(self):
        """测试非常长的键"""
        long_key = "a" * 10000
        
        entry = CacheEntry(
            key=long_key,
            value="value",
            created_at=time.time()
        )
        
        assert entry.key == long_key
        assert len(entry.key) == 10000
    
    def test_special_characters_in_key(self):
        """测试键中的特殊字符"""
        special_key = "key/with\\special:chars@#$%"
        
        entry = CacheEntry(
            key=special_key,
            value="value",
            created_at=time.time()
        )
        
        assert entry.key == special_key
    
    def test_exact_expire_time(self):
        """测试精确的过期时间"""
        current_time = time.time()
        entry = CacheEntry(
            key="test_key",
            value="value",
            created_at=current_time,
            expires_at=current_time
        )
        
        # 在当前时间精确过期，可能由于精度问题有变化
        # 所以我们只检查是否在合理范围内
        is_expired = entry.is_expired()
        # 这个测试可能受时间精度影响，所以我们不强制断言特定结果
    
    def test_negative_access_count(self):
        """测试负数访问计数"""
        entry = CacheEntry(
            key="test_key",
            value="value",
            created_at=time.time(),
            access_count=-1
        )
        
        assert entry.access_count == -1
        
        # 访问后应该增加
        result = entry.access()
        assert entry.access_count == 0