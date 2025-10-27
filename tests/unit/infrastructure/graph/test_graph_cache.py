"""图缓存单元测试"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import Any, Dict, Optional
from dataclasses import dataclass

from src.infrastructure.graph.graph_cache import (
    CacheEvictionPolicy,
    CacheEntry,
    GraphCache,
    create_graph_cache,
    calculate_config_hash
)


class TestCacheEvictionPolicy:
    """缓存淘汰策略枚举测试"""

    def test_eviction_policy_values(self):
        """测试缓存淘汰策略枚举值"""
        assert CacheEvictionPolicy.LRU.value == "lru"
        assert CacheEvictionPolicy.LFU.value == "lfu"
        assert CacheEvictionPolicy.TTL.value == "ttl"

    def test_eviction_policy_members(self):
        """测试缓存淘汰策略枚举成员"""
        assert CacheEvictionPolicy.LRU.name == "LRU"
        assert CacheEvictionPolicy.LFU.name == "LFU"
        assert CacheEvictionPolicy.TTL.name == "TTL"


class TestCacheEntry:
    """缓存条目测试"""

    def test_init(self):
        """测试初始化"""
        graph = Mock()
        entry = CacheEntry(
            graph=graph,
            config_hash="test_hash",
            created_at=123456.789,
            last_accessed=123456.789,
            access_count=5,
            size_bytes=1024
        )
        assert entry.graph == graph
        assert entry.config_hash == "test_hash"
        assert entry.created_at == 123456.789
        assert entry.last_accessed == 123456.789
        assert entry.access_count == 5
        assert entry.size_bytes == 1024

    def test_is_expired(self):
        """测试是否过期"""
        current_time = time.time()
        entry = CacheEntry(
            graph=Mock(),
            config_hash="test_hash",
            created_at=current_time - 100,  # 100秒前
            last_accessed=current_time - 100
        )
        
        # 未过期
        assert not entry.is_expired(200)  # TTL为200秒
        
        # 已过期
        assert entry.is_expired(50)  # TTL为50秒

    def test_update_access(self):
        """测试更新访问信息"""
        entry = CacheEntry(
            graph=Mock(),
            config_hash="test_hash",
            created_at=time.time(),
            last_accessed=time.time() - 10,
            access_count=5
        )
        
        initial_access_count = entry.access_count
        initial_last_accessed = entry.last_accessed
        
        entry.update_access()
        
        assert entry.access_count == initial_access_count + 1
        assert entry.last_accessed > initial_last_accessed


class TestGraphCache:
    """图缓存测试"""

    @pytest.fixture
    def cache(self):
        """创建图缓存实例"""
        return GraphCache(max_size=3, ttl_seconds=3600, eviction_policy=CacheEvictionPolicy.LRU)

    def test_init(self):
        """测试初始化"""
        cache = GraphCache()
        assert cache._max_size == 100
        assert cache._ttl_seconds == 3600
        assert cache._eviction_policy == CacheEvictionPolicy.LRU
        assert cache._enable_compression is True
        assert isinstance(cache._cache, dict)
        assert isinstance(cache._access_frequency, dict)
        assert cache._stats["hits"] == 0
        assert cache._stats["misses"] == 0
        assert cache._stats["evictions"] == 0
        assert cache._stats["total_requests"] == 0
        assert cache._stats["memory_saved"] == 0

    def test_get_graph_not_found(self, cache):
        """测试获取不存在的图"""
        result = cache.get_graph("nonexistent_hash")
        assert result is None
        assert cache._stats["misses"] == 1
        assert cache._stats["total_requests"] == 1

    def test_get_graph_expired(self, cache):
        """测试获取已过期的图"""
        # 添加一个过期的图
        expired_time = time.time() - 4000  # 4000秒前，超过默认TTL
        graph = Mock()
        entry = CacheEntry(
            graph=graph,
            config_hash="expired_hash",
            created_at=expired_time,
            last_accessed=expired_time
        )
        cache._cache["expired_hash"] = entry
        
        result = cache.get_graph("expired_hash")
        assert result is None
        assert "expired_hash" not in cache._cache  # 确认已移除
        assert cache._stats["misses"] == 1

    def test_get_graph_success(self, cache):
        """测试成功获取图"""
        # 添加一个图
        graph = Mock()
        entry = CacheEntry(
            graph=graph,
            config_hash="test_hash",
            created_at=time.time(),
            last_accessed=time.time()
        )
        cache._cache["test_hash"] = entry
        
        result = cache.get_graph("test_hash")
        assert result == graph
        assert cache._stats["hits"] == 1
        assert cache._stats["total_requests"] == 1
        assert cache._access_frequency["test_hash"] == 1

    def test_cache_graph_within_limit(self, cache):
        """测试缓存图（未超过限制）"""
        graph = Mock()
        cache.cache_graph("test_hash", graph)
        
        assert "test_hash" in cache._cache
        assert cache._cache["test_hash"].graph == graph
        assert len(cache._cache) == 1

    def test_cache_graph_exceeds_limit_lru(self):
        """测试缓存图超过限制（LRU策略）"""
        cache = GraphCache(max_size=2, eviction_policy=CacheEvictionPolicy.LRU)
        
        # 添加3个图，超过限制
        graph1 = Mock()
        graph2 = Mock()
        graph3 = Mock()
        
        cache.cache_graph("hash1", graph1)
        cache.cache_graph("hash2", graph2)
        cache.cache_graph("hash3", graph3)  # 这会触发淘汰
        
        # 检查是否只有2个条目
        assert len(cache._cache) == 2
        # hash1应该被移除（最久未使用）
        assert "hash1" not in cache._cache
        # hash2和hash3应该存在
        assert "hash2" in cache._cache
        assert "hash3" in cache._cache

    def test_cache_graph_exceeds_limit_lfu(self):
        """测试缓存图超过限制（LFU策略）"""
        cache = GraphCache(max_size=2, eviction_policy=CacheEvictionPolicy.LFU)
        
        # 添加3个图，超过限制
        graph1 = Mock()
        graph2 = Mock()
        graph3 = Mock()
        
        cache.cache_graph("hash1", graph1)
        cache.cache_graph("hash2", graph2)
        cache.cache_graph("hash3", graph3)  # 这会触发淘汰
        
        # 检查是否只有2个条目
        assert len(cache._cache) == 2

    def test_invalidate_by_pattern(self, cache):
        """测试按模式失效缓存"""
        # 添加几个图
        cache.cache_graph("test_pattern_1", Mock())
        cache.cache_graph("test_pattern_2", Mock())
        cache.cache_graph("other_pattern", Mock())
        
        # 按模式失效
        count = cache.invalidate_by_pattern("test_pattern_*")
        
        assert count == 2
        assert "test_pattern_1" not in cache._cache
        assert "test_pattern_2" not in cache._cache
        assert "other_pattern" in cache._cache

    def test_invalidate_by_hash(self, cache):
        """测试按哈希失效缓存"""
        cache.cache_graph("test_hash", Mock())
        
        # 失效特定哈希
        result = cache.invalidate_by_hash("test_hash")
        
        assert result is True
        assert "test_hash" not in cache._cache
        
        # 失效不存在的哈希
        result = cache.invalidate_by_hash("nonexistent_hash")
        assert result is False

    def test_clear(self, cache):
        """测试清除所有缓存"""
        cache.cache_graph("hash1", Mock())
        cache.cache_graph("hash2", Mock())
        
        cache.clear()
        
        assert len(cache._cache) == 0
        assert len(cache._access_frequency) == 0

    def test_get_cache_stats(self, cache):
        """测试获取缓存统计信息"""
        # 添加一些图
        cache.cache_graph("hash1", Mock())
        cache.cache_graph("hash2", Mock())
        
        # 获取统计信息
        stats = cache.get_cache_stats()
        
        assert "size" in stats
        assert "max_size" in stats
        assert "hit_rate" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "evictions" in stats
        assert "total_requests" in stats
        assert "memory_usage_bytes" in stats
        assert "memory_saved_bytes" in stats
        assert "eviction_policy" in stats
        assert "ttl_seconds" in stats

    def test_get_cache_entries(self, cache):
        """测试获取缓存条目信息"""
        # 添加一些图
        cache.cache_graph("hash1", Mock())
        cache.cache_graph("hash2", Mock())
        
        # 获取条目信息
        entries = cache.get_cache_entries()
        
        assert len(entries) == 2
        for entry in entries:
            assert "config_hash" in entry
            assert "created_at" in entry
            assert "last_accessed" in entry
            assert "access_count" in entry
            assert "size_bytes" in entry
            assert "is_expired" in entry

    def test_optimize_cache(self, cache):
        """测试优化缓存"""
        # 添加一个过期的图
        expired_time = time.time() - 4000  # 4000秒前，超过默认TTL
        graph = Mock()
        entry = CacheEntry(
            graph=graph,
            config_hash="expired_hash",
            created_at=expired_time,
            last_accessed=expired_time
        )
        cache._cache["expired_hash"] = entry
        
        # 添加一个未过期的图
        cache.cache_graph("valid_hash", Mock())
        
        # 优化缓存
        result = cache.optimize_cache()
        
        assert result["expired_removed"] == 1
        assert result["final_size"] == 1
        assert "expired_hash" not in cache._cache
        assert "valid_hash" in cache._cache

    def test_estimate_graph_size(self, cache):
        """测试估算图大小"""
        graph = Mock()
        size = cache._estimate_graph_size(graph)
        assert isinstance(size, int)
        assert size >= 0


class TestUtilityFunctions:
    """工具函数测试"""

    def test_create_graph_cache(self):
        """测试创建图缓存"""
        cache = create_graph_cache(
            max_size=50,
            ttl_seconds=1800,
            eviction_policy="lru",
            enable_compression=False
        )
        assert isinstance(cache, GraphCache)
        assert cache._max_size == 50
        assert cache._ttl_seconds == 1800
        assert cache._eviction_policy == CacheEvictionPolicy.LRU
        assert cache._enable_compression is False

    def test_calculate_config_hash(self):
        """测试计算配置哈希"""
        config1 = {"name": "test", "value": 42}
        config2 = {"value": 42, "name": "test"}  # 不同顺序但相同内容
        
        hash1 = calculate_config_hash(config1)
        hash2 = calculate_config_hash(config2)
        
        # 相同内容应产生相同哈希
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 32  # MD5哈希长度

    def test_calculate_config_hash_different_content(self):
        """测试不同内容产生不同哈希"""
        config1 = {"name": "test1", "value": 42}
        config2 = {"name": "test2", "value": 42}
        
        hash1 = calculate_config_hash(config1)
        hash2 = calculate_config_hash(config2)
        
        # 不同内容应产生不同哈希
        assert hash1 != hash2