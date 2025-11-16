#!/usr/bin/env python3
"""测试异步重构后的存储架构"""

import asyncio
import tempfile
from pathlib import Path

# 测试导入
from src.infrastructure.common.cache.cache_manager import CacheManager
from src.infrastructure.common.storage.base_storage import BaseStorage
from src.infrastructure.common.storage.history_storage_adapter import HistoryStorageAdapter
from src.application.history.manager import HistoryManager
from src.infrastructure.history.storage.file_storage import FileHistoryStorage
from src.domain.history.models import MessageRecord, MessageType
from src.domain.history.interfaces import IHistoryManager


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


async def test_history_storage_adapter():
    """测试历史存储适配器"""
    print("测试 HistoryStorageAdapter...")
    
    cache = CacheManager()
    storage = TestStorage(cache_manager=cache)
    adapter = HistoryStorageAdapter(storage, cache_manager=cache)
    
    # 测试记录消息
    record = MessageRecord(
        record_id="msg1",
        session_id="session1",
        message_type=MessageType.USER,
        content="测试消息"
    )
    
    await adapter.record_message(record)
    
    # 测试查询历史
    from src.domain.history.models import HistoryQuery
    query = HistoryQuery(session_id="session1")
    result = await adapter.query_history(query)
    
    assert len(result.records) == 1, f"期望1条记录，得到 {len(result.records)}"
    assert result.records[0]["content"] == "测试消息", "消息内容不匹配"
    
    print("✓ HistoryStorageAdapter 测试通过")


async def test_history_manager():
    """测试历史管理器"""
    print("测试 HistoryManager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建文件存储
        file_storage = FileHistoryStorage(Path(temp_dir))
        
        # 创建缓存管理器
        cache = CacheManager()
        
        # 创建历史管理器
        history_manager = HistoryManager(
            storage=file_storage,
            cache_manager=cache
        )
        
        # 测试记录消息
        record = MessageRecord(
            record_id="msg1",
            session_id="session1",
            message_type=MessageType.USER,
            content="测试消息"
        )
        
        await history_manager.record_message(record)
        
        # 测试获取统计
        stats = await history_manager.get_token_statistics("session1")
        assert "session_id" in stats, "统计信息应包含session_id"
        
        llm_stats = await history_manager.get_llm_statistics("session1")
        assert "session_id" in llm_stats, "LLM统计信息应包含session_id"
        
        print("✓ HistoryManager 测试通过")


async def main():
    """运行所有测试"""
    print("开始测试异步重构后的存储架构...\n")
    
    try:
        await test_cache_manager()
        await test_base_storage()
        await test_history_storage_adapter()
        await test_history_manager()
        
        print("\n✅ 所有测试通过！异步重构成功。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)