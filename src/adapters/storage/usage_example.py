"""存储适配器使用示例

展示如何使用新的存储适配器实现。
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from src.core.state.entities import StateSnapshot, StateHistoryEntry
from .factory import StorageAdapterFactory, AsyncStorageAdapterFactory, create_storage_adapter
from .sync_adapter import SyncStateStorageAdapter
from .async_adapter import AsyncStateStorageAdapter


def sync_usage_example():
    """同步适配器使用示例"""
    print("=== 同步适配器使用示例 ===")
    
    # 创建配置
    config: Dict[str, Any] = {
        "database_path": ":memory:"  # 使用内存数据库
    }
    
    # 创建同步适配器
    factory = StorageAdapterFactory()
    adapter = factory.create_adapter('sqlite', config)
    
    # 创建状态快照
    snapshot = StateSnapshot(
        snapshot_id="snap_001",
        agent_id="agent_001",
        domain_state={"counter": 42, "status": "active"},
        timestamp=datetime.now(),
        snapshot_name="Initial State"
    )
    
    # 保存快照
    success = adapter.save_snapshot(snapshot)
    print(f"保存快照: {success}")
    
    # 加载快照
    loaded_snapshot = adapter.load_snapshot("snap_001")
    print(f"加载快照: {loaded_snapshot}")
    
    # 创建历史记录条目
    history_entry = StateHistoryEntry(
        history_id="hist_001",
        agent_id="agent_001",
        timestamp=datetime.now(),
        action="state_change",
        state_diff={"counter": 43}
    )
    
    # 保存历史记录
    success = adapter.save_history_entry(history_entry)
    print(f"保存历史记录: {success}")
    
    # 获取历史记录
    history_entries = adapter.get_history_entries("agent_001")
    print(f"获取历史记录: {len(history_entries)} 条")
    
    # 获取统计信息
    stats = adapter.get_history_statistics()
    print(f"历史统计: {stats}")
    
    # 关闭连接
    adapter.close()


async def async_usage_example():
    """异步适配器使用示例"""
    print("=== 异步适配器使用示例 ===")
    
    # 创建配置
    config: Dict[str, Any] = {
        "database_path": ":memory:"  # 使用内存数据库
    }
    
    # 创建异步适配器
    factory = AsyncStorageAdapterFactory()
    adapter = await factory.create_adapter('sqlite', config)
    
    # 创建状态快照
    snapshot = StateSnapshot(
        snapshot_id="async_snap_001",
        agent_id="async_agent_001",
        domain_state={"counter": 100, "status": "running"},
        timestamp=datetime.now(),
        snapshot_name="Async Initial State"
    )
    
    # 保存快照
    success = await adapter.save_snapshot(snapshot)
    print(f"保存快照: {success}")
    
    # 加载快照
    loaded_snapshot = await adapter.load_snapshot("async_snap_001")
    print(f"加载快照: {loaded_snapshot}")
    
    # 创建历史记录条目
    history_entry = StateHistoryEntry(
        history_id="async_hist_001",
        agent_id="async_agent_001",
        timestamp=datetime.now(),
        action="async_state_change",
        state_diff={"counter": 101}
    )
    
    # 保存历史记录
    success = await adapter.save_history_entry(history_entry)
    print(f"保存历史记录: {success}")
    
    # 获取历史记录
    history_entries = await adapter.get_history_entries("async_agent_001")
    print(f"获取历史记录: {len(history_entries)} 条")
    
    # 获取统计信息
    stats = await adapter.get_history_statistics()
    print(f"历史统计: {stats}")
    
    # 关闭连接
    await adapter.close()


def factory_usage_example():
    """工厂使用示例"""
    print("=== 工厂使用示例 ===")
    
    # 创建配置
    config: Dict[str, Any] = {
        "database_path": ":memory:"
    }
    
    # 使用便捷函数创建同步适配器
    sync_adapter = create_storage_adapter('sqlite', config, async_mode=False)
    print(f"同步适配器类型: {type(sync_adapter)}")
    
    # 使用便捷函数创建异步适配器
    async_adapter = create_storage_adapter('sqlite', config, async_mode=True)
    print(f"异步适配器类型: {type(async_adapter)}")


async def main():
    """主函数"""
    # 运行同步示例
    sync_usage_example()
    
    # 运行异步示例
    await async_usage_example()
    
    # 运行工厂示例
    factory_usage_example()


if __name__ == "__main__":
    asyncio.run(main())