"""全面测试SQLite checkpoint存储"""

import asyncio
from src.infrastructure.checkpoint.sqlite_store import SQLiteCheckpointStore


async def test_sqlite_full():
    """全面测试SQLite存储"""
    print("=== 全面测试SQLite checkpoint存储 ===")
    
    # 创建SQLite存储实例（使用内存数据库）
    sqlite_store = SQLiteCheckpointStore(sqlite_path=":memory:")
    
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
    
    # 等待一小段时间确保数据写入
    await asyncio.sleep(0.1)
    
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
        print(f"最新checkpoint ID: {latest_checkpoint.get('id')}")
    else:
        print("未找到最新checkpoint")
    
    # 保存第二个checkpoint
    print("\n4. 测试保存第二个checkpoint...")
    checkpoint_data2 = {
        'session_id': 'sqlite_session',
        'workflow_id': 'workflow_sqlite',
        'state_data': {'history': [0, 1, 2, 3], 'step': 2},
        'metadata': {'test': True, 'step': 2}
    }
    
    success2 = await sqlite_store.save(checkpoint_data2)
    print(f"保存第二个checkpoint: {'成功' if success2 else '失败'}")
    
    # 再次列出所有checkpoint
    print("\n5. 再次列出所有checkpoint...")
    checkpoints = await sqlite_store.list_by_session('sqlite_session')
    print(f"找到 {len(checkpoints)} 个checkpoint")
    
    for i, cp in enumerate(checkpoints):
        print(f"Checkpoint {i}:")
        print(f"  ID: {cp.get('id')}")
        print(f"  Workflow ID: {cp.get('workflow_id')}")
        print(f"  State: {cp.get('state_data')}")
        print(f"  Step: {cp.get('metadata', {}).get('step')}")
        print(f"  Created at: {cp.get('created_at')}")
        print()
    
    # 测试获取最新checkpoint
    print("\n6. 测试获取最新checkpoint...")
    latest_checkpoint = await sqlite_store.get_latest('sqlite_session')
    if latest_checkpoint:
        print(f"最新checkpoint状态: {latest_checkpoint.get('state_data')}")
        print(f"最新checkpoint步骤: {latest_checkpoint.get('metadata', {}).get('step')}")
    else:
        print("未找到最新checkpoint")
    
    # 测试按工作流获取
    print("\n7. 测试按工作流获取checkpoint...")
    workflow_checkpoints = await sqlite_store.get_checkpoints_by_workflow('sqlite_session', 'workflow_sqlite')
    print(f"找到 {len(workflow_checkpoints)} 个workflow_sqlite的checkpoint")
    
    print("\n=== SQLite存储全面测试完成 ===")


if __name__ == "__main__":
    asyncio.run(test_sqlite_full())