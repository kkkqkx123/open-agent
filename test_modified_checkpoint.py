"""测试修改后的checkpoint存储实现"""

import asyncio
from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore


async def test_modified_checkpoint():
    """测试修改后的checkpoint存储"""
    print("=== 测试修改后的MemoryCheckpointStore ===")
    
    # 创建存储实例
    memory_checkpoint_store = MemoryCheckpointStore()
    
    # 测试保存多个checkpoint
    print("\n1. 测试保存多个checkpoint...")
    
    # 保存第一个checkpoint
    checkpoint_data_1 = {
        'session_id': 'test_session_1',
        'workflow_id': 'workflow_1',
        'state_data': {'history': [0, 1, 2], 'step': 1},
        'metadata': {'test': True, 'step': 1}
    }
    
    success_1 = await memory_checkpoint_store.save(checkpoint_data_1)
    print(f"保存第一个checkpoint: {'成功' if success_1 else '失败'}")
    
    # 保存第二个checkpoint
    checkpoint_data_2 = {
        'session_id': 'test_session_1',
        'workflow_id': 'workflow_1',
        'state_data': {'history': [0, 1, 2, 3], 'step': 2},
        'metadata': {'test': True, 'step': 2}
    }
    
    success_2 = await memory_checkpoint_store.save(checkpoint_data_2)
    print(f"保存第二个checkpoint: {'成功' if success_2 else '失败'}")
    
    # 列出所有checkpoint
    print("\n2. 列出所有checkpoint...")
    checkpoints = await memory_checkpoint_store.list_by_session('test_session_1')
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
    latest_checkpoint = await memory_checkpoint_store.get_latest('test_session_1')
    if latest_checkpoint:
        print(f"最新checkpoint状态: {latest_checkpoint.get('state_data')}")
    else:
        print("未找到最新checkpoint")
    
    # 测试按ID加载checkpoint
    print("\n4. 测试按ID加载checkpoint...")
    if checkpoints:
        first_checkpoint_id = checkpoints[-1].get('id')  # 获取第一个checkpoint的ID
        specific_checkpoint = await memory_checkpoint_store.load_by_session('test_session_1', first_checkpoint_id)
        if specific_checkpoint:
            print(f"按ID加载成功: {specific_checkpoint.get('state_data')}")
        else:
            print("按ID加载失败")
    
    # 测试SQLite存储
    print("\n5. 测试SQLite存储...")
    try:
        sqlite_store = MemoryCheckpointStore(use_sqlite=True, sqlite_path=":memory:")
        sqlite_checkpoint_data = {
            'session_id': 'sqlite_session',
            'workflow_id': 'workflow_sqlite',
            'state_data': {'history': [0], 'step': 0},
            'metadata': {'test': True}
        }
        
        sqlite_success = await sqlite_store.save(sqlite_checkpoint_data)
        print(f"SQLite存储: {'成功' if sqlite_success else '失败'}")
        
        sqlite_checkpoints = await sqlite_store.list_by_session('sqlite_session')
        print(f"SQLite存储找到 {len(sqlite_checkpoints)} 个checkpoint")
    except Exception as e:
        print(f"SQLite存储测试失败: {e}")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    asyncio.run(test_modified_checkpoint())