"""测试SQLite checkpoint存储"""

import asyncio
from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore


async def test_sqlite_checkpoint():
    """测试SQLite checkpoint存储"""
    print("=== 测试SQLite checkpoint存储 ===")
    
    # 创建SQLite存储实例（使用内存数据库）
    sqlite_store = MemoryCheckpointStore(use_sqlite=True, sqlite_path=":memory:")
    
    # 测试保存checkpoint
    print("\n1. 测试保存checkpoint...")
    
    checkpoint_data = {
        'session_id': 'sqlite_session',
        'workflow_id': 'workflow_sqlite',
        'state_data': {'history': [0, 1, 2], 'step': 1},
        'metadata': {'test': True, 'step': 1}
    }
    
    success = await sqlite_store.save(checkpoint_data)
    print(f"保存checkpoint: {'成功' if success else '失败'}")
    
    # 列出所有checkpoint
    print("\n2. 列出所有checkpoint...")
    checkpoints = await sqlite_store.list_by_session('sqlite_session')
    print(f"找到 {len(checkpoints)} 个checkpoint")
    
    for i, cp in enumerate(checkpoints):
        print(f"Checkpoint {i}:")
        print(f"  ID: {cp.get('id')}")
        print(f"  Workflow ID: {cp.get('workflow_id')}")
        print(f"  State: {cp.get('state_data')}")
        print(f"  Created at: {cp.get('created_at')}")
        print()
    
    # 测试加载最新checkpoint
    print("\n3. 测试加载最新checkpoint...")
    latest_checkpoint = await sqlite_store.get_latest('sqlite_session')
    if latest_checkpoint:
        print(f"最新checkpoint状态: {latest_checkpoint.get('state_data')}")
    else:
        print("未找到最新checkpoint")
    
    print("\n=== SQLite存储测试完成 ===")


if __name__ == "__main__":
    asyncio.run(test_sqlite_checkpoint())