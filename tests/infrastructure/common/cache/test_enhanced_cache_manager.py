"""增强缓存管理器测试"""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.infrastructure.common.cache.enhanced_cache_manager import EnhancedCacheManager
from src.infrastructure.common.cache.cache_entry import CacheEntry, CacheStats


class TestEnhancedCacheManager:
    """增强缓存管理器测试类"""
    
    def setup_method(self):
        """设置测试环境"""
        self.cache = EnhancedCacheManager(max_size=3, default_ttl=60)
    
    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """测试设置和获取缓存"""
        await self.cache.set("key1", "value1")
        result = await self.cache.get("key1")
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        """测试获取不存在的键"""
        result = await self.cache.get("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_with_ttl(self):
        """测试设置带TTL的缓存"""
        await self.cache.set("key1", "value1", ttl=1)
        result = await self.cache.get("key1")
        assert result == "value1"
        
        # 等待过期
        await asyncio.sleep(1.1)
        result = await self.cache.get("key1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """测试LRU淘汰策略"""
        # 填满缓存
        await self.cache.set("key1", "value1")
        await self.cache.set("key2", "value2")
        await self.cache.set("key3", "value3")
        
        # 访问key1，使其成为最近使用
        await self.cache.get("key1")
        
        # 添加新项，应该淘汰key2（最久未使用）
        await self.cache.set("key4", "value4")
        
        assert await self.cache.get("key1") == "value1"  # 仍在缓存
        assert await self.cache.get("key2") is None     # 被淘汰
        assert await self.cache.get("key3") == "value3"  # 仍在缓存
        assert await self.cache.get("key4") == "value4"  # 新添加的
    
    @pytest.mark.asyncio
    async def test_remove(self):
        """测试移除缓存项"""
        await self.cache.set("key1", "value1")
        result = await self.cache.remove("key1")
        assert result == True
        
        result = await self.cache.get("key1")
        assert result is None
        
        # 移除不存在的键
        result = await self.cache.remove("nonexistent")
        assert result == False
    
    @pytest.mark.asyncio
    async def test_remove_by_pattern(self):
        """测试根据模式移除缓存项"""
        await self.cache.set("user:1", "user1")
        await self.cache.set("user:2", "user2")
        await self.cache.set("session:1", "session1")
        
        removed_count = await self.cache.remove_by_pattern(r"user:\d+")
        assert removed_count == 2
        
        assert await self.cache.get("user:1") is None
        assert await self.cache.get("user:2") is None
        assert await self.cache.get("session:1") == "session1"
    
    @pytest.mark.asyncio
    async def test_clear(self):
        """测试清空缓存"""
        await self.cache.set("key1", "value1")
        await self.cache.set("key2", "value2")
        
        await self.cache.clear()
        
        assert await self.cache.get("key1") is None
        assert await self.cache.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """测试清理过期项"""
        await self.cache.set("key1", "value1", ttl=1)
        await self.cache.set("key2", "value2", ttl=2)
        await self.cache.set("key3", "value3", ttl=3)
        
        # 等待key1过期
        await asyncio.sleep(1.1)
        
        cleaned_count = await self.cache.cleanup_expired()
        assert cleaned_count == 1
        
        assert await self.cache.get("key1") is None
        assert await self.cache.get("key2") == "value2"
        assert await self.cache.get("key3") == "value3"
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取统计信息"""
        # 初始统计
        stats = self.cache.get_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0
        
        # 添加一些操作
        await self.cache.set("key1", "value1")
        await self.cache.get("key1")  # 命中
        await self.cache.get("nonexistent")  # 未命中
        
        stats = self.cache.get_stats()
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["total_requests"] == 2
        assert stats["hit_rate"] == 0.5
    
    @pytest.mark.asyncio
    async def test_get_cache_info(self):
        """测试获取详细缓存信息"""
        await self.cache.set("key1", "value1", ttl=10)
        
        info = self.cache.get_cache_info()
        assert "key1" in info
        assert info["key1"]["access_count"] == 0
        assert info["key1"]["is_expired"] == False
        assert info["key1"]["ttl_remaining"] is not None
        assert info["key1"]["ttl_remaining"] > 0
    
    @pytest.mark.asyncio
    async def test_get_or_set(self):
        """测试get_or_set方法"""
        call_count = 0
        
        async def factory():
            nonlocal call_count
            call_count += 1
            return "factory_value"
        
        # 第一次调用，应该执行工厂函数
        result = await self.cache.get_or_set("key1", factory)
        assert result == "factory_value"
        assert call_count == 1
        
        # 第二次调用，应该从缓存获取
        result = await self.cache.get_or_set("key1", factory)
        assert result == "factory_value"
        assert call_count == 1  # 工厂函数没有被再次调用
    
    @pytest.mark.asyncio
    async def test_access_count(self):
        """测试访问计数"""
        await self.cache.set("key1", "value1")
        
        # 多次访问
        await self.cache.get("key1")
        await self.cache.get("key1")
        await self.cache.get("key1")
        
        info = self.cache.get_cache_info()
        assert info["key1"]["access_count"] == 3
    
    @pytest.mark.asyncio
    async def test_update_existing_key(self):
        """测试更新已存在的键"""
        await self.cache.set("key1", "value1")
        await self.cache.set("key1", "value2")  # 更新
        
        result = await self.cache.get("key1")
        assert result == "value2"
        
        stats = self.cache.get_stats()
        assert stats["size"] == 1  # 大小不变
    
    @pytest.mark.asyncio
    async def test_zero_max_size(self):
        """测试零最大大小"""
        cache = EnhancedCacheManager(max_size=0, default_ttl=60)
        await cache.set("key1", "value1")
        
        result = await cache.get("key1")
        assert result is None  # 不应该存储任何项
    
    @pytest.mark.asyncio
    async def test_zero_ttl(self):
        """测试零TTL（不过期）"""
        cache = EnhancedCacheManager(max_size=10, default_ttl=0)
        await cache.set("key1", "value1")
        
        # 等待一段时间，应该不过期
        await asyncio.sleep(0.1)
        result = await cache.get("key1")
        assert result == "value1"


class TestCacheEntry:
    """缓存条目测试类"""
    
    def test_cache_entry_creation(self):
        """测试缓存条目创建"""
        now = datetime.now()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.created_at == now
        assert entry.expires_at is None
        assert entry.access_count == 0
        assert entry.last_accessed == now
    
    def test_cache_entry_expiration(self):
        """测试缓存条目过期"""
        now = datetime.now()
        expired_entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            expires_at=now - timedelta(seconds=1)  # 已过期
        )
        
        valid_entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            expires_at=now + timedelta(seconds=1)  # 未过期
        )
        
        assert expired_entry.is_expired() == True
        assert valid_entry.is_expired() == False
    
    def test_cache_entry_access(self):
        """测试缓存条目访问"""
        now = datetime.now()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now
        )
        
        # 访问缓存项
        value = entry.access()
        assert value == "test_value"
        assert entry.access_count == 1
        assert entry.last_accessed > now
        
        # 再次访问
        entry.access()
        assert entry.access_count == 2
    
    def test_cache_entry_extend_ttl(self):
        """测试延长TTL"""
        now = datetime.now()
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now,
            expires_at=now + timedelta(seconds=10)
        )
        
        original_expires_at = entry.expires_at
        entry.extend_ttl(20)
        
        # TTL应该被延长
        assert entry.expires_at > original_expires_at
        
        # 测试无过期时间的条目
        no_expiry_entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=now
        )
        
        no_expiry_entry.extend_ttl(30)
        assert no_expiry_entry.expires_at is not None


class TestCacheStats:
    """缓存统计测试类"""
    
    def test_cache_stats_initialization(self):
        """测试缓存统计初始化"""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.total_requests == 0
        assert stats.hit_rate == 0.0
    
    def test_cache_stats_hit_rate(self):
        """测试命中率计算"""
        stats = CacheStats()
        
        # 无请求时
        assert stats.hit_rate == 0.0
        
        # 添加一些命中和未命中
        stats.record_hit()
        stats.record_hit()
        stats.record_miss()
        
        assert stats.hit_rate == 2/3
        assert stats.hits == 2
        assert stats.misses == 1
        assert stats.total_requests == 3
    
    def test_cache_stats_eviction(self):
        """测试淘汰记录"""
        stats = CacheStats()
        
        stats.record_eviction()
        stats.record_eviction()
        
        assert stats.evictions == 2
        assert stats.total_requests == 0  # 淘汰不计入总请求数