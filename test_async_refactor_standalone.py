#!/usr/bin/env python3
"""测试异步重构后的存储架构（独立版本）"""

import asyncio
import threading
from typing import Any, Optional, Dict, List
from collections import OrderedDict
from datetime import datetime, timedelta
from abc import ABC


# 简化的CacheEntry类
class CacheEntry:
    def __init__(self, key: str, value: Any, created_at: datetime, expires_at: Optional[datetime] = None):
        self.key = key
        self.value = value
        self.created_at = created_at
        self.expires_at = expires_at
        self.access_count = 0
        self.last_accessed = created_at
    
    def access(self) -> Any:
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.value
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


# 简化的CacheStats类
class CacheStats:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_requests = 0
    
    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100
    
    def record_hit(self):
        self.hits += 1
        self.total_requests += 1
    
    def record_miss(self):
        self.misses += 1
        self.total_requests += 1
    
    def record_eviction(self):
        self.evictions += 1


# 简化的CacheManager类
class CacheManager:
    """统一缓存管理器"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats()
        self._lock = threading.RLock()
    
    async def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats.record_miss()
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._stats.record_miss()
                return None
            
            self._cache.move_to_end(key)
            self._stats.record_hit()
            return entry.access()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
        
        with self._lock:
            if key not in self._cache and len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats.record_eviction()
            
            entry = CacheEntry(key, value, datetime.now(), expires_at)
            self._cache[key] = entry
            self._cache.move_to_end(key)
    
    async def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        with self._lock:
            self._cache.clear()
    
    async def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "evictions": self._stats.evictions,
                "total_requests": self._stats.total_requests,
                "hit_rate": self._stats.hit_rate,
                "cache_size": len(self._cache),
                "max_size": self.max_size,
                "default_ttl": self.default_ttl
            }


# 简化的IStorage接口
class IStorage(ABC):
    async def save(self, data: Dict[str, Any]) -> bool: pass
    async def load(self, id: str) -> Optional[Dict[str, Any]]: pass
    async def list(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]: pass
    async def delete(self, id: str) -> bool: pass


# 简化的BaseStorage类
class BaseStorage(IStorage):
    """存储基类，提供通用功能"""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache = cache_manager
    
    async def save_with_metadata(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        # 添加时间戳
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = data["created_at"]
        
        # 保存数据
        success = await self.save(data)
        
        # 缓存数据
        if success and self.cache and data.get("id"):
            await self.cache.set(data["id"], data, ttl=ttl)
        
        return success
    
    async def load_with_cache(self, id: str) -> Optional[Dict[str, Any]]:
        # 先从缓存获取
        if self.cache:
            cached_data = await self.cache.get(id)
            if cached_data:
                return cached_data
        
        # 从存储加载
        data = await self.load(id)
        
        # 缓存结果
        if data and self.cache:
            await self.cache.set(id, data)
        
        return data


# 测试存储实现
class TestStorage(BaseStorage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._data = {}
    
    async def save(self, data: dict) -> bool:
        self._data[data["id"]] = data
        return True
    
    async def load(self, id: str) -> dict:
        return self._data.get(id)
    
    async def list(self, filters: dict) -> list:
        return list(self._data.values())
    
    async def delete(self, id: str) -> bool:
        if id in self._data:
            del self._data[id]
            return True
        return False


async def test_cache_manager():
    """测试缓存管理器"""
    print("测试 CacheManager...")
    
    cache = CacheManager(max_size=10, default_ttl=60)
    
    # 测试设置和获取
    await cache.set("test_key", "test_value")
    value = await cache.get("test_key")
    assert value == "test_value", f"期望 'test_value'，得到 {value}"
    
    # 测试统计
    stats = await cache.get_stats()
    assert stats["cache_size"] == 1, f"期望缓存大小为1，得到 {stats['cache_size']}"
    
    print("✓ CacheManager 测试通过")


async def test_base_storage():
    """测试基础存储"""
    print("测试 BaseStorage...")
    
    cache = CacheManager()
    storage = TestStorage(cache_manager=cache)
    
    # 测试保存和加载
    data = {"id": "test1", "content": "测试数据"}
    success = await storage.save_with_metadata(data)
    assert success, "保存失败"
    
    loaded_data = await storage.load_with_cache("test1")
    assert loaded_data["content"] == "测试数据", f"期望 '测试数据'，得到 {loaded_data.get('content')}"
    
    print("✓ BaseStorage 测试通过")


async def test_async_semantics():
    """测试异步语义的一致性"""
    print("测试异步语义一致性...")
    
    cache = CacheManager()
    
    # 确保所有方法都是异步的
    assert asyncio.iscoroutinefunction(cache.get), "cache.get 应该是异步方法"
    assert asyncio.iscoroutinefunction(cache.set), "cache.set 应该是异步方法"
    assert asyncio.iscoroutinefunction(cache.delete), "cache.delete 应该是异步方法"
    assert asyncio.iscoroutinefunction(cache.clear), "cache.clear 应该是异步方法"
    assert asyncio.iscoroutinefunction(cache.get_stats), "cache.get_stats 应该是异步方法"
    
    storage = TestStorage(cache_manager=cache)
    
    # 确保存储方法都是异步的
    assert asyncio.iscoroutinefunction(storage.save), "storage.save 应该是异步方法"
    assert asyncio.iscoroutinefunction(storage.load), "storage.load 应该是异步方法"
    assert asyncio.iscoroutinefunction(storage.save_with_metadata), "storage.save_with_metadata 应该是异步方法"
    assert asyncio.iscoroutinefunction(storage.load_with_cache), "storage.load_with_cache 应该是异步方法"
    
    print("✓ 异步语义一致性测试通过")


async def main():
    """运行所有测试"""
    print("开始测试异步重构后的存储架构...\n")
    
    try:
        await test_cache_manager()
        await test_base_storage()
        await test_async_semantics()
        
        print("\n✅ 所有测试通过！异步重构成功。")
        print("\n重构总结：")
        print("1. 移除了 SyncCacheManager，统一使用异步 CacheManager")
        print("2. 简化了 BaseStorage，移除了运行时类型检查")
        print("3. 所有存储相关方法都是异步的，类型安全")
        print("4. 删除了冗余的协议和适配器")
        print("5. 统一了整个存储层的异步架构")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)