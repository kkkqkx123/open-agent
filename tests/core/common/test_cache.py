"""cache.py 单元测试"""

import asyncio
import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# 使用标准导入方式，conftest.py已经设置了正确的路径
from src.core.common.cache import (
    CacheEntry,
    CacheStats,
    CacheManager,
    get_global_cache_manager,
    clear_cache,
    ConfigCache,
    LLMCache,
    GraphCache,
    config_cached,
    llm_cached,
    graph_cached,
    simple_cached
)


class TestCacheEntry:
    """测试 CacheEntry 类"""
    
    def test_cache_entry_creation(self):
        """测试缓存条目创建"""
        import time
        now = time.time()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.access_count == 0
        assert entry.last_accessed == now  # __post_init__ 会将last_accessed设为created_at
    
    def test_cache_entry_is_expired(self):
        """测试缓存条目过期"""
        import time
        now = time.time()
        # 未设置过期时间，不应该过期
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now
        )
        assert not entry.is_expired()
        
        # 设置过去时间，应该过期
        past_time = now - 1.0
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            expires_at=past_time
        )
        assert entry.is_expired()
        
        # 设置未来时间，不应该过期
        future_time = now + 10.0
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            expires_at=future_time
        )
        assert not entry.is_expired()
    
    def test_cache_entry_access(self):
        """测试缓存条目访问"""
        import time
        now = time.time()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now
        )
        
        initial_count = entry.access_count
        result = entry.access()
        current_time = time.time()
        
        assert result == "test_value"
        assert entry.access_count == initial_count + 1
        # 检查最后访问时间是否更新（注意：entry.last_accessed在__post_init__中初始化为created_at，访问时更新）
        assert entry.last_accessed is not None and entry.last_accessed >= now
    
    def test_cache_entry_extend_ttl(self):
        """测试延长TTL"""
        import time
        now = time.time()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now
        )
        
        # 初始没有过期时间
        assert entry.expires_at is None
        
        # 延长TTL
        entry.extend_ttl(10)
        current_time = time.time()
        assert entry.expires_at is not None
        assert entry.expires_at >= current_time


class TestCacheStats:
    """测试 CacheStats 类"""
    
    def test_cache_stats_initialization(self):
        """测试缓存统计初始化"""
        stats = CacheStats()
        
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.total_requests == 0
        assert stats.hit_rate == 0.0
    
    def test_cache_stats_record_hit(self):
        """测试记录命中"""
        stats = CacheStats()
        stats.record_hit()
        
        assert stats.hits == 1
        assert stats.total_requests == 1
        assert stats.hit_rate == 1.0
    
    def test_cache_stats_record_miss(self):
        """测试记录未命中"""
        stats = CacheStats()
        stats.record_miss()
        
        assert stats.misses == 1
        assert stats.total_requests == 1
        assert stats.hit_rate == 0.0
    
    def test_cache_stats_record_eviction(self):
        """测试记录淘汰"""
        stats = CacheStats()
        stats.record_eviction()
        
        assert stats.evictions == 1
    
    def test_cache_stats_hit_rate(self):
        """测试命中率计算"""
        stats = CacheStats()
        stats.record_hit()
        stats.record_hit()
        stats.record_miss()
        
        assert stats.hits == 2
        assert stats.misses == 1
        assert stats.total_requests == 3
        assert stats.hit_rate == 2.0 / 3.0


class TestCacheManager:
    """测试 CacheManager 类"""
    
    @pytest.mark.asyncio
    async def test_cache_manager_initialization(self):
        """测试缓存管理器初始化"""
        manager = CacheManager(max_size=100, default_ttl=60)
        
        assert manager.max_size == 100
        assert manager.default_ttl == 60
        assert not manager.enable_serialization
        assert manager.serialization_format == "json"
    
    # 移除不存在的get_cache方法测试
    
    @pytest.mark.asyncio
    async def test_cache_manager_set_get(self):
        """测试设置和获取缓存值"""
        manager = CacheManager()
        
        # 设置值
        await manager.set('test_key', 'test_value', ttl=10)
        
        # 获取值
        value = await manager.get('test_key')
        assert value == 'test_value'
    
    @pytest.mark.asyncio
    async def test_cache_manager_with_ttl(self):
        """测试TTL功能"""
        manager = CacheManager()
        
        # 设置一个立即过期的值
        await manager.set('expired_key', 'expired_value', ttl=1)
        
        # 立即获取，应该存在
        value = await manager.get('expired_key')
        assert value == 'expired_value'
        
        # 等待一段时间让其过期
        await asyncio.sleep(0.02)
        
        # 再次获取，应该不存在
        value = await manager.get('expired_key')
        assert value is None
    
    @pytest.mark.asyncio
    async def test_cache_manager_delete(self):
        """测试删除缓存项"""
        manager = CacheManager()
        
        # 设置值
        await manager.set('delete_key', 'delete_value')
        
        # 确认值存在
        value = await manager.get('delete_key')
        assert value == 'delete_value'
        
        # 删除值
        success = await manager.delete('delete_key')
        assert success
        
        # 确认值不存在
        value = await manager.get('delete_key')
        assert value is None
    
    @pytest.mark.asyncio
    async def test_cache_manager_exists(self):
        """测试检查缓存项是否存在"""
        manager = CacheManager()
        
        # 不存在的键
        exists = await manager.exists('nonexistent_key')
        assert not exists
        
        # 设置值
        await manager.set('exist_key', 'exist_value')
        
        # 存在的键
        exists = await manager.exists('exist_key')
        assert exists
        
        # 设置一个立即过期的值
        await manager.set('expired_key', 'expired_value', ttl=1)
        await asyncio.sleep(1.1)
        
        # 过期的键
        exists = await manager.exists('expired_key')
        assert not exists
    
    @pytest.mark.asyncio
    async def test_cache_manager_clear(self):
        """测试清空缓存"""
        manager = CacheManager()
        
        # 设置一些值
        await manager.set('key1', 'value1')
        await manager.set('key2', 'value2')
        
        # 确认值存在
        assert await manager.get('key1') == 'value1'
        assert await manager.get('key2') == 'value2'
        
        # 清空
        await manager.clear()
        
        # 确认值不存在
        assert await manager.get('key1') is None
        assert await manager.get('key2') is None
    
    @pytest.mark.asyncio
    async def test_cache_manager_stats(self):
        """测试缓存统计"""
        manager = CacheManager()
        
        # 获取初始统计
        initial_stats = await manager.get_stats()
        assert initial_stats["hits"] == 0
        assert initial_stats["misses"] == 0
        
        # 执行一些操作
        await manager.set('stat_key', 'stat_value')
        await manager.get('stat_key')  # 命中
        await manager.get('nonexistent')  # 未命中
        
        # 获取更新后的统计
        updated_stats = await manager.get_stats()
        assert updated_stats["hits"] == 1
        assert updated_stats["misses"] == 1
        assert updated_stats["total_requests"] == 2
    
    @pytest.mark.asyncio
    async def test_cache_manager_cleanup_expired(self):
        """测试清理过期缓存项"""
        manager = CacheManager()
        
        # 设置一个立即过期的值
        await manager.set('cleanup_key', 'cleanup_value', ttl=1)
        await asyncio.sleep(1.1)
        
        # 清理过期项
        cleanup_count = await manager.cleanup_expired()
        assert cleanup_count == 1
        
        # 确认值不存在
        value = await manager.get('cleanup_key')
        assert value is None
    
    @pytest.mark.asyncio
    async def test_cache_manager_get_all_keys(self):
        """测试获取所有缓存键"""
        manager = CacheManager()
        
        # 设置一些值
        await manager.set('key1', 'value1')
        await manager.set('key2', 'value2')
        
        # 获取所有键
        keys = await manager.get_all_keys()
        assert 'key1' in keys
        assert 'key2' in keys
        assert len(keys) == 2
    
    @pytest.mark.asyncio
    async def test_cache_manager_get_many_set_many(self):
        """测试批量获取和设置"""
        manager = CacheManager()
        
        # 批量设置
        items = {
            'batch_key1': 'batch_value1',
            'batch_key2': 'batch_value2',
            'batch_key3': 'batch_value3'
        }
        await manager.set_many(items)
        
        # 批量获取
        keys = ['batch_key1', 'batch_key2', 'batch_key3', 'nonexistent']
        results = await manager.get_many(keys)
        
        assert results['batch_key1'] == 'batch_value1'
        assert results['batch_key2'] == 'batch_value2'
        assert results['batch_key3'] == 'batch_value3'
        assert 'nonexistent' not in results
        assert len(results) == 3


class TestGlobalCacheFunctions:
    """测试全局缓存函数"""
    
    def test_get_global_cache_manager(self):
        """测试获取全局缓存管理器"""
        manager1 = get_global_cache_manager()
        manager2 = get_global_cache_manager()
        
        assert manager1 is manager2
    
    # 移除不存在的get_cache函数测试，因为当前实现中没有这个函数


class TestSpecializedCaches:
    """测试专用缓存类"""
    
    def test_config_cache(self):
        """测试配置缓存"""
        cache = ConfigCache()
        cache.put('config_key', 'config_value')
        
        value = cache.get('config_key')
        assert value == 'config_value'
    
    def test_llm_cache(self):
        """测试LLM缓存"""
        cache = LLMCache()
        cache.put('llm_key', 'llm_value')
        
        value = cache.get('llm_key')
        assert value == 'llm_value'
    
    def test_graph_cache(self):
        """测试图缓存"""
        cache = GraphCache()
        cache.put('graph_key', 'graph_value')
        
        value = cache.get('graph_key')
        assert value == 'graph_value'


class TestCacheDecorators:
    """测试缓存装饰器"""
    
    @pytest.mark.asyncio
    async def test_config_cached_decorator(self):
        """测试配置缓存装饰器"""
        call_count = 0
        
        @config_cached(maxsize=10, ttl=60)
        def get_config_value(key):
            nonlocal call_count
            call_count += 1
            return f"value_{key}_{call_count}"
        
        # 第一次调用
        result1 = get_config_value("test")
        assert result1 == "value_test_1"
        assert call_count == 1
        
        # 第二次调用相同参数，应该从缓存获取
        result2 = get_config_value("test")
        assert result2 == "value_test_1"
        assert call_count == 1  # 调用次数未增加
    
    @pytest.mark.asyncio
    async def test_llm_cached_decorator(self):
        """测试LLM缓存装饰器"""
        call_count = 0
        
        @llm_cached(maxsize=10, ttl=60)
        def get_llm_result(prompt):
            nonlocal call_count
            call_count += 1
            return f"result_{prompt}_{call_count}"
        
        # 第一次调用
        result1 = get_llm_result("hello")
        assert result1 == "result_hello_1"
        assert call_count == 1
        
        # 第二次调用相同参数，应该从缓存获取
        result2 = get_llm_result("hello")
        assert result2 == "result_hello_1"
        assert call_count == 1  # 调用次数未增加


if __name__ == "__main__":
    pytest.main([__file__])