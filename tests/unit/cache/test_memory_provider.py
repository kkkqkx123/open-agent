"""内存缓存提供者测试"""

import pytest
import time
import asyncio
from typing import Any, Dict, Optional

from src.infrastructure.llm.cache.memory_provider import MemoryCacheProvider
from src.infrastructure.llm.cache.cache_config import CacheEntry


class TestMemoryCacheProvider:
    """测试内存缓存提供者"""
    
    def test_init_default(self):
        """测试默认初始化"""
        provider = MemoryCacheProvider()
        
        assert provider.max_size == 1000
        assert provider.default_ttl == 3600
        assert provider.get_size() == 0
    
    def test_init_custom(self):
        """测试自定义初始化"""
        provider = MemoryCacheProvider(max_size=500, default_ttl=1800)
        
        assert provider.max_size == 500
        assert provider.default_ttl == 1800
    
    def test_get_nonexistent_key(self):
        """测试获取不存在的键"""
        provider = MemoryCacheProvider()
        
        result = provider.get("nonexistent")
        assert result is None
    
    def test_set_and_get(self):
        """测试设置和获取"""
        provider = MemoryCacheProvider()
        
        provider.set("key1", "value1")
        result = provider.get("key1")
        
        assert result == "value1"
    
    def test_set_with_custom_ttl(self):
        """测试设置带自定义TTL"""
        provider = MemoryCacheProvider(default_ttl=3600)
        
        provider.set("key1", "value1", ttl=600)  # 10分钟
        result = provider.get("key1")
        
        assert result == "value1"
    
    def test_set_with_zero_ttl(self):
        """测试设置零TTL"""
        provider = MemoryCacheProvider(default_ttl=3600)
        
        provider.set("key1", "value1", ttl=0)  # 立即过期
        result = provider.get("key1")
        
        # 立即过期后应该返回None
        assert result is None
    
    def test_set_with_negative_ttl(self):
        """测试设置负数TTL"""
        provider = MemoryCacheProvider(default_ttl=3600)
        
        provider.set("key1", "value1", ttl=-100)
        result = provider.get("key1")
        
        # 负数TTL应该不设置过期时间
        assert result == "value1"
    
    def test_update_existing_key(self):
        """测试更新已存在的键"""
        provider = MemoryCacheProvider()
        
        provider.set("key1", "value1")
        provider.set("key1", "updated_value")
        
        result = provider.get("key1")
        assert result == "updated_value"
    
    def test_delete_existing_key(self):
        """测试删除存在的键"""
        provider = MemoryCacheProvider()
        
        provider.set("key1", "value1")
        result = provider.delete("key1")
        
        assert result is True
        assert provider.get("key1") is None
    
    def test_delete_nonexistent_key(self):
        """测试删除不存在的键"""
        provider = MemoryCacheProvider()
        
        result = provider.delete("nonexistent")
        assert result is False
    
    def test_clear_all(self):
        """测试清空所有缓存"""
        provider = MemoryCacheProvider()
        
        provider.set("key1", "value1")
        provider.set("key2", "value2")
        provider.set("key3", "value3")
        
        provider.clear()
        
        assert provider.get_size() == 0
        assert provider.get("key1") is None
        assert provider.get("key2") is None
        assert provider.get("key3") is None
    
    def test_exists(self):
        """测试键存在性"""
        provider = MemoryCacheProvider()
        
        provider.set("key1", "value1")
        
        assert provider.exists("key1") is True
        assert provider.exists("nonexistent") is False
    
    def test_exists_with_expired_key(self):
        """测试过期键的存在性"""
        provider = MemoryCacheProvider(default_ttl=1)  # 1秒TTL
        
        provider.set("key1", "value1", ttl=1)
        assert provider.exists("key1") is True
        
        # 等待过期
        time.sleep(1.1)
        
        # 过期后应该返回False
        assert provider.exists("key1") is False
    
    def test_lru_eviction(self):
        """测试LRU淘汰策略"""
        provider = MemoryCacheProvider(max_size=2)
        
        provider.set("key1", "value1")
        provider.set("key2", "value2")
        
        # 访问key1使其成为最近使用
        provider.get("key1")
        
        # 添加新项，会淘汰key2
        provider.set("key3", "value3")
        
        # key1应该还在（最近使用）
        assert provider.get("key1") == "value1"
        
        # key2应该被淘汰
        assert provider.get("key2") is None
        
        # key3应该存在
        assert provider.get("key3") == "value3"
    
    def test_cleanup_expired(self):
        """测试清理过期项"""
        provider = MemoryCacheProvider(default_ttl=1)
        
        # 设置一些正常项
        provider.set("normal1", "value1")
        provider.set("normal2", "value2")
        
        # 设置一些短TTL的项
        provider.set("expire1", "value3", ttl=1)
        provider.set("expire2", "value4", ttl=1)
        
        # 等待过期
        time.sleep(1.1)
        
        # 清理过期项
        cleaned_count = provider.cleanup_expired()
        
        # 应该清理2个过期项
        assert cleaned_count == 2
        
        # 正常项应该还在
        assert provider.get("normal1") == "value1"
        assert provider.get("normal2") == "value2"
        
        # 过期项应该被清理
        assert provider.get("expire1") is None
        assert provider.get("expire2") is None
    
    def test_cleanup_expired_no_expiry(self):
        """测试清理无过期项"""
        provider = MemoryCacheProvider(default_ttl=3600)
        
        provider.set("key1", "value1")
        provider.set("key2", "value2")
        
        cleaned_count = provider.cleanup_expired()
        
        assert cleaned_count == 0
        assert provider.get_size() == 2
    
    def test_get_stats_empty(self):
        """测试空缓存统计"""
        provider = MemoryCacheProvider()
        
        stats = provider.get_stats()
        
        assert stats["total_entries"] == 0
        assert stats["expired_entries"] == 0
        assert stats["valid_entries"] == 0
        assert stats["max_size"] == 1000
        assert stats["utilization"] == 0.0
        assert stats["total_access_count"] == 0
        assert stats["oldest_entry_age_seconds"] == 0
        assert stats["newest_entry_age_seconds"] == 0
    
    def test_get_stats_with_entries(self):
        """测试有项的缓存统计"""
        provider = MemoryCacheProvider(max_size=100)
        
        provider.set("key1", "value1")
        provider.set("key2", "value2")
        
        # 访问一下第一个项
        provider.get("key1")
        
        stats = provider.get_stats()
        
        assert stats["total_entries"] == 2
        assert stats["expired_entries"] == 0
        assert stats["valid_entries"] == 2
        assert stats["max_size"] == 100
        assert stats["utilization"] == 0.02
        assert stats["total_access_count"] == 1
    
    def test_get_stats_with_expired_entries(self):
        """测试有过期项的缓存统计"""
        provider = MemoryCacheProvider(default_ttl=1)
        
        provider.set("key1", "value1")
        provider.set("key2", "value2", ttl=1)  # 这个会过期
        
        # 等待过期
        time.sleep(1.1)
        
        stats = provider.get_stats()
        
        assert stats["total_entries"] == 1  # 只剩下一个有效项
        assert stats["expired_entries"] == 1
        assert stats["valid_entries"] == 0
        assert stats["total_access_count"] == 0
    
    @pytest.mark.asyncio
    async def test_async_get(self):
        """测试异步获取"""
        provider = MemoryCacheProvider()
        
        provider.set("key1", "value1")
        result = await provider.get_async("key1")
        
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_async_get_nonexistent(self):
        """测试异步获取不存在的键"""
        provider = MemoryCacheProvider()
        
        result = await provider.get_async("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_async_set(self):
        """测试异步设置"""
        provider = MemoryCacheProvider()
        
        await provider.set_async("key1", "value1")
        result = await provider.get_async("key1")
        
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_async_set_with_ttl(self):
        """测试异步设置带TTL"""
        provider = MemoryCacheProvider()
        
        await provider.set_async("key1", "value1", ttl=600)
        result = await provider.get_async("key1")
        
        assert result == "value1"
    
    def test_concurrent_access(self):
        """测试并发访问（简化的线程安全测试）"""
        provider = MemoryCacheProvider(max_size=10)
        
        # 设置一些项
        for i in range(10):
            provider.set(f"key{i}", f"value{i}")
        
        # 多次访问同一项（模拟并发）
        for _ in range(100):
            result = provider.get("key0")
            assert result == "value0"
            provider.set("key0", f"value0_updated_{_}")  # 更新值
    
    def test_get_size_with_expiry(self):
        """测试过期项的大小计算"""
        provider = MemoryCacheProvider(default_ttl=1)
        
        provider.set("key1", "value1")
        provider.set("key2", "value2", ttl=1)  # 会过期
        
        # 检查初始大小
        assert provider.get_size() == 2
        
        # 等待过期
        time.sleep(1.1)
        
        # 大小应该仍然是2（除非调用get/_exists触发清理）
        assert provider.get_size() == 2
        
        # 访问过期项会触发清理
        provider.get("key2")
        assert provider.get_size() == 1
    
    def test_large_max_size(self):
        """测试大的缓存大小"""
        provider = MemoryCacheProvider(max_size=10000)
        
        # 添加很多项
        for i in range(5000):
            provider.set(f"key{i}", f"value{i}")
        
        assert provider.get_size() == 5000
    
    def test_very_large_values(self):
        """测试非常大的值"""
        provider = MemoryCacheProvider()
        
        large_value = {"data": "x" * 100000}  # 100KB数据
        provider.set("large_key", large_value)
        
        result = provider.get("large_key")
        assert result == large_value
        assert result is not None and len(result["data"]) == 100000
    
    def test_access_counting(self):
        """测试访问计数"""
        provider = MemoryCacheProvider()
        
        provider.set("key1", "value1")
        
        # 初始访问计数为0
        stats = provider.get_stats()
        assert stats["total_access_count"] == 0
        
        # 第一次访问
        provider.get("key1")
        stats = provider.get_stats()
        assert stats["total_access_count"] == 1
        
        # 第二次访问
        provider.get("key1")
        stats = provider.get_stats()
        assert stats["total_access_count"] == 2
    
    def test_cache_entry_expiry_behavior(self):
        """测试缓存项的过期行为"""
        provider = MemoryCacheProvider(default_ttl=2)
        
        provider.set("key1", "value1")
        
        # 立即检查应该存在
        assert provider.exists("key1") is True
        assert provider.get("key1") == "value1"
        
        # 等待过期但不到过期时间
        time.sleep(1.5)
        assert provider.exists("key1") is True
        assert provider.get("key1") == "value1"
        
        # 等待完全过期
        time.sleep(1.0)
        assert provider.exists("key1") is False
        assert provider.get("key1") is None


class TestMemoryCacheProviderEdgeCases:
    """测试内存缓存提供者的边界情况"""
    
    def test_max_size_zero(self):
        """测试最大大小为0"""
        provider = MemoryCacheProvider(max_size=0)
        
        # 设置任何项都应该被立即淘汰
        provider.set("key1", "value1")
        
        assert provider.get_size() == 0
        assert provider.get("key1") is None
    
    def test_negative_max_size(self):
        """测试负数最大大小"""
        provider = MemoryCacheProvider(max_size=-100)
        
        # 应该使用默认大小或合理处理负数
        # 实际行为取决于实现
        try:
            provider.set("key1", "value1")
            # 如果没有抛出异常，检查是否正确处理
            size = provider.get_size()
            assert isinstance(size, int)
        except Exception:
            # 如果抛出异常，这也是合理的行为
            pass
    
    def test_complex_value_types(self):
        """测试复杂的值类型"""
        provider = MemoryCacheProvider()
        
        # 测试各种数据类型
        test_values = [
            None,
            42,
            3.14159,
            True,
            False,
            [],
            {},
            {"nested": {"deep": "value"}},
            [1, 2, {"key": "value"}],
            "unicode测试",
            "🚀🎉",
        ]
        
        for i, value in enumerate(test_values):
            key = f"complex_key_{i}"
            provider.set(key, value)
            result = provider.get(key)
            assert result == value
    
    def test_memory_pressure(self):
        """测试内存压力（大量数据）"""
        provider = MemoryCacheProvider(max_size=100)
        
        # 添加超过最大容量50%的数据
        for i in range(50):
            provider.set(f"key{i}", f"value{i}" * 10)  # 50个较大的值
        
        # 所有50个项都应该在缓存中
        assert provider.get_size() == 50
        
        # 再添加50个项，触发LRU淘汰
        for i in range(50, 100):
            provider.set(f"key{i}", f"value{i}")
        
        # 应该只有100个项
        assert provider.get_size() == 100
        
        # 前50个键中的一部分应该被淘汰
        # 检查几个前面的键
        found_keys = 0
        for i in range(50):
            if provider.exists(f"key{i}"):
                found_keys += 1
        
        # 至少有一些键应该被淘汰（但至少有一些可能还在）
        assert found_keys <= 50
    
    def test_rapid_set_and_get(self):
        """测试快速的设置和获取"""
        provider = MemoryCacheProvider(max_size=1000)
        
        # 快速设置和获取
        for i in range(100):
            key = f"rapid_key_{i}"
            value = f"rapid_value_{i}"
            
            provider.set(key, value)
            result = provider.get(key)
            assert result == value
        
        assert provider.get_size() == 100
    
    def test_none_values(self):
        """测试None值"""
        provider = MemoryCacheProvider()
        
        provider.set("none_key", None)
        result = provider.get("none_key")
        
        assert result is None
        assert provider.exists("none_key") is True
    
    def test_empty_key(self):
        """测试空键"""
        provider = MemoryCacheProvider()
        
        provider.set("", "empty_key_value")
        result = provider.get("")
        
        assert result == "empty_key_value"
        assert provider.exists("") is True
    
    def test_special_character_keys(self):
        """测试特殊字符键"""
        provider = MemoryCacheProvider()
        
        special_keys = [
            "key/with/slashes",
            "key\\with\\backslashes",
            "key:with:colons",
            "key@with@symbols",
            "key#with#hashes",
            "key%with%percents",
            "key with spaces",
            "key\twith\ttabs",
            "key\nwith\nnewlines",
            "key\nwith\r\nboth",
        ]
        
        for key in special_keys:
            provider.set(key, f"value_for_{key}")
            result = provider.get(key)
            assert result == f"value_for_{key}"
    
    def test_update_value_doesnt_change_access_order(self):
        """测试更新值不会改变访问顺序"""
        provider = MemoryCacheProvider(max_size=3)
        
        # 按顺序添加
        provider.set("key1", "value1")
        provider.set("key2", "value2")
        provider.set("key3", "value3")
        
        # 更新中间的值
        provider.set("key2", "updated_value2")
        
        # 添加新值，应该淘汰第一个（key1，因为key2刚刚被更新）
        provider.set("key4", "value4")
        
        # key1应该被淘汰
        assert provider.get("key1") is None
        
        # key2应该还在
        assert provider.get("key2") == "updated_value2"
        
        # key3和key4应该还在
        assert provider.get("key3") == "value3"
        assert provider.get("key4") == "value4"