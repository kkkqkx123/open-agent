"""
内存缓存单元测试
"""

import pytest
import asyncio
import time
from datetime import timedelta

from src.services.prompts.cache.memory_cache import (
    MemoryPromptCache,
    MemoryCacheEntry,
    LRUEvictionPolicy,
    LFUEvictionPolicy,
    PickleSerializer
)
from src.interfaces.prompts.cache import ICacheEntry
from src.core.common.exceptions.prompts import PromptCacheError


class TestMemoryCacheEntry:
    """内存缓存条目测试"""
    
    def test_creation_without_ttl(self):
        """测试创建无TTL的条目"""
        entry = MemoryCacheEntry("key", "value")
        
        assert entry.key == "key"
        assert entry.value == "value"
        assert entry.expires_at is None
        assert entry.access_count == 0
        assert not entry.is_expired()
    
    def test_creation_with_ttl(self):
        """测试创建有TTL的条目"""
        ttl = timedelta(seconds=10)
        entry = MemoryCacheEntry("key", "value", ttl)
        
        assert entry.key == "key"
        assert entry.value == "value"
        assert entry.expires_at is not None
        assert not entry.is_expired()
    
    def test_expired_entry(self):
        """测试过期条目"""
        ttl = timedelta(milliseconds=1)
        entry = MemoryCacheEntry("key", "value", ttl)
        
        # 等待过期
        time.sleep(0.01)
        assert entry.is_expired()
    
    def test_touch(self):
        """测试更新访问信息"""
        entry = MemoryCacheEntry("key", "value")
        original_accessed = entry.last_accessed
        
        time.sleep(0.01)
        entry.touch()
        
        assert entry.access_count == 1
        assert entry.last_accessed > original_accessed


class TestLRUEvictionPolicy:
    """LRU淘汰策略测试"""
    
    def test_select_victim(self):
        """测试选择淘汰对象"""
        policy = LRUEvictionPolicy()
        
        # 创建不同访问时间的条目
        entries = []
        for i in range(3):
            entry = MemoryCacheEntry(f"key_{i}", f"value_{i}")
            entry.touch()
            entries.append(entry)
        
        # 等待一段时间，让第一个条目成为最久未访问的
        time.sleep(0.01)
        entries[1].touch()  # 访问第二个条目
        
        victim = policy.select_victim(entries)
        assert victim.key == "key_0"  # 应该选择最久未访问的
    
    def test_select_victim_empty(self):
        """测试空列表选择淘汰对象"""
        policy = LRUEvictionPolicy()
        victim = policy.select_victim([])
        assert victim is None


class TestLFUEvictionPolicy:
    """LFU淘汰策略测试"""
    
    def test_select_victim(self):
        """测试选择淘汰对象"""
        policy = LFUEvictionPolicy()
        
        # 创建不同访问次数的条目
        entries = []
        for i in range(3):
            entry = MemoryCacheEntry(f"key_{i}", f"value_{i}")
            # 设置不同的访问次数
            for _ in range(i):
                entry.touch()
            entries.append(entry)
        
        victim = policy.select_victim(entries)
        assert victim.key == "key_0"  # 应该选择访问次数最少的
    
    def test_select_victim_same_frequency(self):
        """测试相同访问频率时的选择"""
        policy = LFUEvictionPolicy()
        
        # 创建相同访问次数的条目
        entries = []
        for i in range(3):
            entry = MemoryCacheEntry(f"key_{i}", f"value_{i}")
            entry.touch()
            entries.append(entry)
        
        # 等待一段时间，让第一个条目成为最久未访问的
        time.sleep(0.01)
        entries[1].touch()  # 访问第二个条目
        
        victim = policy.select_victim(entries)
        assert victim.key == "key_0"  # 应该选择最久未访问的


class TestPickleSerializer:
    """Pickle序列化器测试"""
    
    def test_serialize_deserialize(self):
        """测试序列化和反序列化"""
        serializer = PickleSerializer()
        original_value = {"key": "value", "number": 42}
        
        serialized = serializer.serialize(original_value)
        deserialized = serializer.deserialize(serialized)
        
        assert deserialized == original_value
    
    def test_serialize_complex_object(self):
        """测试序列化复杂对象"""
        serializer = PickleSerializer()
        
        class TestClass:
            def __init__(self, value):
                self.value = value
        
        original = TestClass("test")
        serialized = serializer.serialize(original)
        deserialized = serializer.deserialize(serialized)
        
        assert deserialized.value == original.value
    
    def test_serialize_error(self):
        """测试序列化错误"""
        serializer = PickleSerializer()
        
        # 创建无法序列化的对象
        class UnserializableClass:
            def __getstate__(self):
                raise TypeError("Cannot serialize")
        
        with pytest.raises(PromptCacheError):
            serializer.serialize(UnserializableClass())
    
    def test_deserialize_error(self):
        """测试反序列化错误"""
        serializer = PickleSerializer()
        
        with pytest.raises(PromptCacheError):
            serializer.deserialize(b"invalid pickle data")


class TestMemoryPromptCache:
    """内存提示词缓存测试"""
    
    @pytest.fixture
    def cache(self):
        """创建缓存实例"""
        return MemoryPromptCache(max_size=3, default_ttl=timedelta(seconds=1))
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """测试设置和获取"""
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        
        assert value == "value1"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        """测试获取不存在的键"""
        value = await cache.get("nonexistent")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_exists(self, cache):
        """测试检查键是否存在"""
        await cache.set("key1", "value1")
        
        assert await cache.exists("key1")
        assert not await cache.exists("nonexistent")
    
    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """测试删除"""
        await cache.set("key1", "value1")
        
        assert await cache.delete("key1")
        assert not await cache.exists("key1")
        assert not await cache.delete("nonexistent")
    
    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """测试清空"""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        await cache.clear()
        
        assert not await cache.exists("key1")
        assert not await cache.exists("key2")
    
    @pytest.mark.asyncio
    async def test_ttl(self, cache):
        """测试TTL"""
        await cache.set("key1", "value1", timedelta(seconds=0.1))
        
        # 应该存在
        assert await cache.exists("key1")
        
        # 等待过期
        await asyncio.sleep(0.2)
        
        # 应该已过期
        assert not await cache.exists("key1")
    
    @pytest.mark.asyncio
    async def test_get_ttl(self, cache):
        """测试获取TTL"""
        await cache.set("key1", "value1", timedelta(seconds=1))
        
        ttl = await cache.get_ttl("key1")
        assert ttl is not None
        assert ttl.total_seconds() > 0
        
        # 不存在的键
        ttl = await cache.get_ttl("nonexistent")
        assert ttl is None
    
    @pytest.mark.asyncio
    async def test_set_ttl(self, cache):
        """测试设置TTL"""
        await cache.set("key1", "value1")
        
        # 设置TTL
        success = await cache.set_ttl("key1", timedelta(seconds=0.1))
        assert success
        
        # 等待过期
        await asyncio.sleep(0.2)
        
        # 应该已过期
        assert not await cache.exists("key1")
    
    @pytest.mark.asyncio
    async def test_get_keys(self, cache):
        """测试获取键列表"""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("test_key", "value3")
        
        # 获取所有键
        keys = await cache.get_keys()
        assert set(keys) == {"key1", "key2", "test_key"}
        
        # 模式匹配
        keys = await cache.get_keys("key*")
        assert set(keys) == {"key1", "key2"}
        
        keys = await cache.get_keys("test_*")
        assert set(keys) == {"test_key"}
    
    @pytest.mark.asyncio
    async def test_get_size(self, cache):
        """测试获取缓存大小"""
        assert await cache.get_size() == 0
        
        await cache.set("key1", "value1")
        assert await cache.get_size() == 1
        
        await cache.set("key2", "value2")
        assert await cache.get_size() == 2
    
    @pytest.mark.asyncio
    async def test_get_stats(self, cache):
        """测试获取统计信息"""
        stats = await cache.get_stats()
        
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0
        assert stats["size"] == 0
        assert stats["max_size"] == 3
        
        # 添加一些数据
        await cache.set("key1", "value1")
        await cache.get("key1")  # 命中
        await cache.get("nonexistent")  # 未命中
        
        stats = await cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["size"] == 1
    
    @pytest.mark.asyncio
    async def test_eviction(self, cache):
        """测试淘汰机制"""
        # 填满缓存
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        # 访问key1，使其成为最近使用的
        await cache.get("key1")
        
        # 添加新键，应该淘汰最久未使用的（key2或key3）
        await cache.set("key4", "value4")
        
        # 缓存大小应该仍然是3
        assert await cache.get_size() == 3
        assert await cache.exists("key1")
        assert await cache.exists("key4")
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, cache):
        """测试并发访问"""
        async def worker(worker_id):
            for i in range(10):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}"
                await cache.set(key, value)
                retrieved = await cache.get(key)
                assert retrieved == value
        
        # 创建多个并发任务
        tasks = [worker(i) for i in range(5)]
        await asyncio.gather(*tasks)
        
        # 验证所有数据都存在
        stats = await cache.get_stats()
        assert stats["size"] <= cache._max_size  # 可能发生了淘汰
    
    @pytest.mark.asyncio
    async def test_custom_eviction_policy(self):
        """测试自定义淘汰策略"""
        lfu_policy = LFUEvictionPolicy()
        cache = MemoryPromptCache(max_size=2, eviction_policy=lfu_policy)
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        # 多次访问key1
        for _ in range(5):
            await cache.get("key1")
        
        # 添加新键，应该淘汰访问次数少的key2
        await cache.set("key3", "value3")
        
        assert await cache.exists("key1")
        assert await cache.exists("key3")
        assert not await cache.exists("key2")