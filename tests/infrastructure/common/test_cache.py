"""缓存模块单元测试

测试基础设施层缓存系统的基本功能。
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch

from src.infrastructure.common.cache import (
    CacheManager,
    CacheEntry,
    CacheStats,
    BaseCache,
    ConfigCache,
    LLMCache,
    GraphCache,
    get_global_cache_manager,
    clear_cache,
    config_cached,
    llm_cached,
    graph_cached,
    simple_cached,
)


class TestCacheEntry:
    """测试缓存条目"""

    def test_cache_entry_creation(self):
        """测试缓存条目创建"""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=1000.0,
            expires_at=2000.0,
            access_count=0,
        )
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.created_at == 1000.0
        assert entry.expires_at == 2000.0
        assert entry.access_count == 0
        assert entry.last_accessed == 1000.0  # 由 __post_init__ 设置

    def test_cache_entry_is_expired(self):
        """测试缓存条目过期检查"""
        # 未过期
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=time.time() - 10,
            expires_at=time.time() + 10,
        )
        assert not entry.is_expired()

        # 已过期
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=time.time() - 20,
            expires_at=time.time() - 10,
        )
        assert entry.is_expired()

        # 无过期时间
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=time.time(),
            expires_at=None,
        )
        assert not entry.is_expired()

    def test_cache_entry_access(self):
        """测试缓存条目访问"""
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=1000.0,
            expires_at=None,
            access_count=5,
            last_accessed=1000.0,
        )
        with patch('time.time', return_value=1500.0):
            result = entry.access()
            assert result == "value"
            assert entry.access_count == 6
            assert entry.last_accessed == 1500.0

    def test_cache_entry_extend_ttl(self):
        """测试延长TTL"""
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=1000.0,
            expires_at=1500.0,
        )
        with patch('time.time', return_value=1400.0):
            entry.extend_ttl(200)
            assert entry.expires_at == 1600.0  # max(1500, 1400+200) = 1600

        # 无过期时间的情况
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=1000.0,
            expires_at=None,
        )
        with patch('time.time', return_value=1400.0):
            entry.extend_ttl(200)
            assert entry.expires_at == 1600.0  # 1400+200


class TestCacheStats:
    """测试缓存统计"""

    def test_cache_stats_creation(self):
        """测试缓存统计创建"""
        stats = CacheStats(hits=5, misses=3, evictions=2, total_requests=8)
        assert stats.hits == 5
        assert stats.misses == 3
        assert stats.evictions == 2
        assert stats.total_requests == 8

    def test_cache_stats_hit_rate(self):
        """测试命中率计算"""
        stats = CacheStats(hits=3, misses=1, total_requests=4)
        assert stats.hit_rate == 0.75

        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_cache_stats_record(self):
        """测试记录方法"""
        stats = CacheStats()
        stats.record_hit()
        assert stats.hits == 1
        assert stats.total_requests == 1

        stats.record_miss()
        assert stats.misses == 1
        assert stats.total_requests == 2

        stats.record_eviction()
        assert stats.evictions == 1


class TestCacheManager:
    """测试缓存管理器"""

    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器实例"""
        return CacheManager(max_size=5, default_ttl=10)

    @pytest.mark.asyncio
    async def test_cache_manager_initialization(self, cache_manager):
        """测试缓存管理器初始化"""
        assert cache_manager.max_size == 5
        assert cache_manager.default_ttl == 10
        assert cache_manager.enable_serialization is False
        assert cache_manager.serialization_format == "json"
        assert cache_manager._cache_entries == {}
        assert isinstance(cache_manager._stats, CacheStats)

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache_manager):
        """测试设置和获取缓存"""
        await cache_manager.set("key1", "value1")
        value = await cache_manager.get("key1")
        assert value == "value1"

        # 获取不存在的键
        value = await cache_manager.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_ttl(self, cache_manager):
        """测试缓存TTL"""
        await cache_manager.set("key1", "value1", ttl=1)
        value = await cache_manager.get("key1")
        assert value == "value1"

        # 等待过期
        await asyncio.sleep(1.1)
        value = await cache_manager.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_delete(self, cache_manager):
        """测试删除缓存"""
        await cache_manager.set("key1", "value1")
        deleted = await cache_manager.delete("key1")
        assert deleted is True
        value = await cache_manager.get("key1")
        assert value is None

        # 删除不存在的键
        deleted = await cache_manager.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_cache_clear(self, cache_manager):
        """测试清空缓存"""
        await cache_manager.set("key1", "value1")
        await cache_manager.set("key2", "value2", cache_name="other")
        await cache_manager.clear("default")
        value = await cache_manager.get("key1")
        assert value is None
        # 其他缓存应不受影响
        value = await cache_manager.get("key2", cache_name="other")
        assert value == "value2"

        await cache_manager.clear()
        value = await cache_manager.get("key2", cache_name="other")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_exists(self, cache_manager):
        """测试检查缓存是否存在"""
        await cache_manager.set("key1", "value1")
        exists = await cache_manager.exists("key1")
        assert exists is True

        exists = await cache_manager.exists("nonexistent")
        assert exists is False

        # 过期后应返回False
        await cache_manager.set("key2", "value2", ttl=0.1)
        await asyncio.sleep(0.2)
        exists = await cache_manager.exists("key2")
        assert exists is False

    @pytest.mark.asyncio
    async def test_cache_stats_tracking(self, cache_manager):
        """测试缓存统计跟踪"""
        await cache_manager.set("key1", "value1")
        await cache_manager.get("key1")  # 命中
        await cache_manager.get("key2")  # 未命中
        stats = await cache_manager.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["total_requests"] == 2
        assert stats["hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_cache_cleanup_expired(self, cache_manager):
        """测试清理过期缓存"""
        await cache_manager.set("key1", "value1", ttl=0.1)
        await cache_manager.set("key2", "value2", ttl=10)
        await asyncio.sleep(0.2)
        cleaned = await cache_manager.cleanup_expired()
        assert cleaned == 1
        value = await cache_manager.get("key1")
        assert value is None
        value = await cache_manager.get("key2")
        assert value == "value2"

    @pytest.mark.asyncio
    async def test_cache_get_all_keys(self, cache_manager):
        """测试获取所有缓存键"""
        await cache_manager.set("key1", "value1")
        await cache_manager.set("key2", "value2")
        keys = await cache_manager.get_all_keys()
        assert set(keys) == {"key1", "key2"}

    @pytest.mark.asyncio
    async def test_cache_get_many(self, cache_manager):
        """测试批量获取"""
        await cache_manager.set("key1", "value1")
        await cache_manager.set("key2", "value2")
        result = await cache_manager.get_many(["key1", "key2", "key3"])
        assert result == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_cache_set_many(self, cache_manager):
        """测试批量设置"""
        items = {"key1": "value1", "key2": "value2"}
        await cache_manager.set_many(items)
        value1 = await cache_manager.get("key1")
        value2 = await cache_manager.get("key2")
        assert value1 == "value1"
        assert value2 == "value2"

    @pytest.mark.asyncio
    async def test_cache_eviction(self, cache_manager):
        """测试缓存淘汰（LRU）"""
        # 设置最大大小为3
        manager = CacheManager(max_size=3)
        await manager.set("key1", "value1")
        await manager.set("key2", "value2")
        await manager.set("key3", "value3")
        await manager.set("key4", "value4")  # 应淘汰key1
        value = await manager.get("key1")
        assert value is None
        value = await manager.get("key4")
        assert value == "value4"

    @pytest.mark.asyncio
    async def test_cache_with_serialization(self):
        """测试带序列化的缓存"""
        manager = CacheManager(enable_serialization=True)
        # 序列化器可能无法导入，我们模拟一下
        with patch('src.infrastructure.common.serialization.Serializer') as MockSerializer:
            mock_serializer = Mock()
            mock_serializer.serialize.return_value = 'serialized_value'
            mock_serializer.deserialize.return_value = 'deserialized_value'
            manager._serializer = mock_serializer
            await manager.set("key1", {"complex": "object"})
            mock_serializer.serialize.assert_called_once()
            value = await manager.get("key1")
            mock_serializer.deserialize.assert_called_once()
            assert value == 'deserialized_value'


class TestBaseCache:
    """测试基础缓存类"""

    def test_base_cache_creation(self):
        """测试基础缓存创建"""
        cache = BaseCache(cache_name="test", default_ttl=60)
        assert cache._cache_name == "test"
        assert cache._default_ttl == 60

    def test_base_cache_get_put(self):
        """测试基础缓存的同步获取和设置"""
        cache = BaseCache(cache_name="test", default_ttl=60)
        # 模拟异步管理器
        with patch.object(cache._manager, 'get') as mock_get:
            mock_get.return_value = "cached_value"
            value = cache.get("key1")
            assert value == "cached_value"
            mock_get.assert_called_once_with("key1", "test")

        with patch.object(cache._manager, 'set') as mock_set:
            cache.put("key1", "value1")
            mock_set.assert_called_once_with("key1", "value1", 60, "test")

    def test_base_cache_remove_clear(self):
        """测试基础缓存的删除和清空"""
        cache = BaseCache(cache_name="test", default_ttl=60)
        with patch.object(cache._manager, 'delete') as mock_delete:
            mock_delete.return_value = True
            result = cache.remove("key1")
            assert result is True
            mock_delete.assert_called_once_with("key1", "test")

        with patch.object(cache._manager, 'clear') as mock_clear:
            cache.clear()
            mock_clear.assert_called_once_with("test")


class TestSpecializedCaches:
    """测试专用缓存类"""

    def test_config_cache(self):
        """测试配置缓存"""
        cache = ConfigCache()
        assert cache._cache_name == "config"
        assert cache._default_ttl == 7200

    def test_llm_cache(self):
        """测试LLM缓存"""
        cache = LLMCache()
        assert cache._cache_name == "llm"
        assert cache._default_ttl == 3600

    def test_graph_cache(self):
        """测试图缓存"""
        cache = GraphCache()
        assert cache._cache_name == "graph"
        assert cache._default_ttl == 1800


class TestGlobalCache:
    """测试全局缓存"""

    def test_get_global_cache_manager(self):
        """测试获取全局缓存管理器"""
        manager1 = get_global_cache_manager()
        manager2 = get_global_cache_manager()
        assert manager1 is manager2  # 单例

    def test_clear_cache_function(self):
        """测试清除缓存函数"""
        with patch('src.infrastructure.common.cache.get_global_cache_manager') as mock_get:
            mock_manager = Mock()
            mock_get.return_value = mock_manager
            clear_cache("test_cache")
            mock_manager.clear_cache.assert_called_once_with("test_cache")


class TestCacheDecorators:
    """测试缓存装饰器"""

    @pytest.mark.asyncio
    async def test_config_cached_decorator(self):
        """测试配置缓存装饰器"""
        call_count = 0

        @config_cached()
        async def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # 第一次调用应执行函数
        result = await expensive_func(5)
        assert result == 10
        assert call_count == 1

        # 第二次调用相同参数应使用缓存
        result = await expensive_func(5)
        assert result == 10
        assert call_count == 1  # 未增加

        # 不同参数应再次执行
        result = await expensive_func(7)
        assert result == 14
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_llm_cached_decorator(self):
        """测试LLM缓存装饰器"""
        call_count = 0

        @llm_cached()
        async def llm_func(prompt):
            nonlocal call_count
            call_count += 1
            return f"Response to {prompt}"

        result = await llm_func("hello")
        assert "Response to hello" in result
        assert call_count == 1

        result = await llm_func("hello")
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_simple_cached_decorator(self):
        """测试简单缓存装饰器"""
        call_count = 0

        @simple_cached("my_cache")
        async def my_func(x):
            nonlocal call_count
            call_count += 1
            return x + 1

        result = await my_func(10)
        assert result == 11
        assert call_count == 1

        result = await my_func(10)
        assert call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])