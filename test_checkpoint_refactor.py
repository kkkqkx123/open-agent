"""测试checkpoint重构后的代码"""

import asyncio
import tempfile
import os
from typing import Dict, Any

from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore
from src.infrastructure.checkpoint.sqlite_store import SQLiteCheckpointStore


async def test_memory_checkpoint_store():
    """测试内存checkpoint存储"""
    print("测试内存checkpoint存储...")
    
    # 创建内存存储实例
    store = MemoryCheckpointStore(max_checkpoints_per_thread=5)
    
    # 测试数据
    checkpoint_data = {
        'thread_id': 'test_thread_1',
        'workflow_id': 'test_workflow_1',
        'state_data': {'message': 'Hello, World!', 'step': 1},
        'metadata': {'user_id': 'user_1', 'timestamp': '2023-01-01T00:00:00Z'}
    }
    
    # 测试保存
    success = await store.save(checkpoint_data)
    print(f"保存结果: {success}")
    assert success, "保存应该成功"
    
    # 测试加载
    loaded = await store.load_by_thread('test_thread_1')
    print(f"加载结果: {loaded}")
    assert loaded is not None, "应该能加载到数据"
    assert loaded['thread_id'] == 'test_thread_1', "thread_id应该匹配"
    assert loaded['state_data']['message'] == 'Hello, World!', "状态数据应该匹配"
    
    # 测试列出
    checkpoints = await store.list_by_thread('test_thread_1')
    print(f"列出结果数量: {len(checkpoints)}")
    assert len(checkpoints) == 1, "应该有一个checkpoint"
    
    # 测试获取最新
    latest = await store.get_latest('test_thread_1')
    print(f"最新checkpoint: {latest}")
    assert latest is not None, "应该能获取最新checkpoint"
    
    # 测试删除
    delete_success = await store.delete_by_thread('test_thread_1')
    print(f"删除结果: {delete_success}")
    assert delete_success, "删除应该成功"
    
    # 验证删除后为空
    after_delete = await store.list_by_thread('test_thread_1')
    print(f"删除后列表长度: {len(after_delete)}")
    assert len(after_delete) == 0, "删除后应该为空"
    
    print("内存checkpoint存储测试通过！\n")


async def test_sqlite_checkpoint_store():
    """测试SQLite checkpoint存储"""
    print("测试SQLite checkpoint存储...")
    
    # 创建临时数据库文件
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        # 创建SQLite存储实例
        store = SQLiteCheckpointStore(sqlite_path=db_path)
        
        # 测试数据
        checkpoint_data = {
            'thread_id': 'test_thread_2',
            'workflow_id': 'test_workflow_2',
            'state_data': {'message': 'Hello from SQLite!', 'step': 2},
            'metadata': {'user_id': 'user_2', 'timestamp': '2023-01-01T00:00:01Z'}
        }
        
        # 测试保存
        success = await store.save(checkpoint_data)
        print(f"保存结果: {success}")
        assert success, "保存应该成功"
        
        # 测试加载
        loaded = await store.load_by_thread('test_thread_2')
        print(f"加载结果: {loaded}")
        assert loaded is not None, "应该能加载到数据"
        assert loaded['thread_id'] == 'test_thread_2', "thread_id应该匹配"
        assert loaded['state_data']['message'] == 'Hello from SQLite!', "状态数据应该匹配"
        
        # 测试列出
        checkpoints = await store.list_by_thread('test_thread_2')
        print(f"列出结果数量: {len(checkpoints)}")
        assert len(checkpoints) == 1, "应该有一个checkpoint"
        
        # 测试获取最新
        latest = await store.get_latest('test_thread_2')
        print(f"最新checkpoint: {latest}")
        assert latest is not None, "应该能获取最新checkpoint"
        
        # 测试删除
        delete_success = await store.delete_by_thread('test_thread_2')
        print(f"删除结果: {delete_success}")
        assert delete_success, "删除应该成功"
        
        # 验证删除后为空
        after_delete = await store.list_by_thread('test_thread_2')
        print(f"删除后列表长度: {len(after_delete)}")
        assert len(after_delete) == 0, "删除后应该为空"
        
        print("SQLite checkpoint存储测试通过！")
        
    finally:
        # 清理临时数据库文件
        if os.path.exists(db_path):
            os.unlink(db_path)


async def test_checkpoint_adapter():
    """测试LangGraph适配器"""
    print("\n测试LangGraph适配器...")
    
    from src.infrastructure.checkpoint.langgraph_adapter import LangGraphAdapter
    
    adapter = LangGraphAdapter()
    
    # 测试创建配置
    config = adapter.create_config('test_thread', 'test_checkpoint')
    print(f"配置创建: {config}")
    assert 'configurable' in config
    assert config['configurable']['thread_id'] == 'test_thread'
    
    # 测试创建checkpoint
    checkpoint = adapter.create_checkpoint(
        {'data': 'test_state'},
        'test_workflow',
        {'meta': 'test_metadata'}
    )
    print(f"Checkpoint创建: {checkpoint}")
    assert 'id' in checkpoint
    assert 'channel_values' in checkpoint
    assert checkpoint['channel_values']['workflow_id'] == 'test_workflow'
    
    # 测试提取状态
    extracted_state = adapter.extract_state(checkpoint)
    print(f"状态提取: {extracted_state}")
    assert extracted_state == {'data': 'test_state'}
    
    print("LangGraph适配器测试通过！")


async def main():
    """主测试函数"""
    print("开始测试重构后的checkpoint代码...\n")
    
    await test_memory_checkpoint_store()
    await test_sqlite_checkpoint_store()
    await test_checkpoint_adapter()
    
    print("\n所有测试通过！重构成功！")


if __name__ == "__main__":
    asyncio.run(main())