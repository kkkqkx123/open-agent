#!/usr/bin/env python3
"""测试异步重构后的存储架构（简化版）"""

import asyncio
import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 直接导入需要的模块，避免复杂的依赖
from src.infrastructure.common.cache.cache_manager import CacheManager
from src.infrastructure.common.storage.base_storage import BaseStorage


class TestStorage(BaseStorage):
    """测试存储实现"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._data = {}
    
    async def save(self, data: dict) -> bool:
        """保存数据"""
        self._data[data["id"]] = data
        return True
    
    async def load(self, id: str) -> dict:
        """加载数据"""
        return self._data.get(id)
    
    async def list(self, filters: dict) -> list:
        """列出数据"""
        return list(self._data.values())
    
    async def delete(self, id: str) -> bool:
        """删除数据"""
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