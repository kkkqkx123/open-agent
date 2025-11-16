"""测试重构后的checkpoint存储实现"""

import pytest
import tempfile
import os
from typing import Dict, Any

# 延迟导入，避免启动时的依赖问题
MemoryCheckpointStore = None
SQLiteCheckpointStore = None


def setup_module():
    """模块级设置，延迟导入"""
    global MemoryCheckpointStore, SQLiteCheckpointStore
    
    from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore
    from src.infrastructure.checkpoint.sqlite_store import SQLiteCheckpointStore


@pytest.fixture
def memory_store():
    """内存存储fixture"""
    if MemoryCheckpointStore is None:
        from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore
    
    store = MemoryCheckpointStore()
    yield store


@pytest.fixture
def sqlite_store():
    """SQLite存储fixture"""
    if SQLiteCheckpointStore is None:
        from src.infrastructure.checkpoint.sqlite_store import SQLiteCheckpointStore
    
    # 创建临时数据库文件
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    store = SQLiteCheckpointStore(sqlite_path=temp_db_path)
    
    yield store
    
    # 清理临时文件
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)


@pytest.mark.asyncio
async def test_memory_checkpoint_store_basic_operations(memory_store):
    """测试内存checkpoint存储的基本操作"""
    # 测试数据
    checkpoint_data = {
        'thread_id': 'test_thread_1',
        'workflow_id': 'test_workflow_1',
        'state_data': {'message': 'Hello, World!', 'step': 1},
        'metadata': {'user_id': 'user_1', 'timestamp': '2023-01-01T00:00Z'}
    }
    
    # 测试保存
    success = await memory_store.save(checkpoint_data)
    assert success is True
    
    # 测试加载
    loaded = await memory_store.load_by_thread('test_thread_1')
    assert loaded is not None
    assert loaded['thread_id'] == 'test_thread_1'
    assert loaded['workflow_id'] == 'test_workflow_1'
    assert loaded['state_data']['message'] == 'Hello, World!'
    
    # 测试列出
    listed = await memory_store.list_by_thread('test_thread_1')
    assert len(listed) == 1
    assert listed[0]['thread_id'] == 'test_thread_1'
    
    # 测试获取最新
    latest = await memory_store.get_latest('test_thread_1')
    assert latest is not None
    assert latest['thread_id'] == 'test_thread_1'
    
    # 测试获取工作流checkpoint
    workflow_checkpoints = await memory_store.get_checkpoints_by_workflow('test_thread_1', 'test_workflow_1')
    assert len(workflow_checkpoints) == 1
    assert workflow_checkpoints[0]['workflow_id'] == 'test_workflow_1'
    
    # 测试计数
    count = await memory_store.get_checkpoint_count('test_thread_1')
    assert count == 1


@pytest.mark.asyncio
async def test_sqlite_checkpoint_store_basic_operations(sqlite_store):
    """测试SQLite checkpoint存储的基本操作"""
    # 测试数据
    checkpoint_data = {
        'thread_id': 'test_thread_2',
        'workflow_id': 'test_workflow_2',
        'state_data': {'message': 'Hello from SQLite!', 'step': 2},
        'metadata': {'user_id': 'user_2', 'timestamp': '2023-01-01T00:00:00Z'}
    }
    
    # 测试保存
    success = await sqlite_store.save(checkpoint_data)
    assert success is True
    
    # 测试加载
    loaded = await sqlite_store.load_by_thread('test_thread_2')
    assert loaded is not None
    assert loaded['thread_id'] == 'test_thread_2'
    assert loaded['workflow_id'] == 'test_workflow_2'
    assert loaded['state_data']['message'] == 'Hello from SQLite!'
    
    # 测试列出
    listed = await sqlite_store.list_by_thread('test_thread_2')
    assert len(listed) == 1
    assert listed[0]['thread_id'] == 'test_thread_2'
    
    # 测试获取最新
    latest = await sqlite_store.get_latest('test_thread_2')
    assert latest is not None
    assert latest['thread_id'] == 'test_thread_2'
    
    # 测试获取工作流checkpoint
    workflow_checkpoints = await sqlite_store.get_checkpoints_by_workflow('test_thread_2', 'test_workflow_2')
    assert len(workflow_checkpoints) == 1
    assert workflow_checkpoints[0]['workflow_id'] == 'test_workflow_2'
    
    # 测试计数
    count = await sqlite_store.get_checkpoint_count('test_thread_2')
    assert count == 1


@pytest.mark.asyncio
async def test_checkpoint_store_cleanup(memory_store):
    """测试checkpoint存储清理功能"""
    # 添加多个checkpoint
    for i in range(3):
        checkpoint_data = {
            'thread_id': 'cleanup_test_thread',
            'workflow_id': f'workflow_{i}',
            'state_data': {'step': i},
            'metadata': {'index': i}
        }
        await memory_store.save(checkpoint_data)
    
    # 检查初始数量
    initial_count = await memory_store.get_checkpoint_count('cleanup_test_thread')
    assert initial_count == 3
    
    # 清理，保留2个
    deleted_count = await memory_store.cleanup_old_checkpoints('cleanup_test_thread', 2)
    assert deleted_count == 1  # 应该删除1个
    
    # 检查剩余数量
    final_count = await memory_store.get_checkpoint_count('cleanup_test_thread')
    assert final_count == 2
    
    # 检查剩余的checkpoint（应该是最新的2个）
    remaining = await memory_store.list_by_thread('cleanup_test_thread')
    assert len(remaining) == 2
    # 检查是否是按时间倒序排列的最新的2个
    assert remaining[0]['state_data']['step'] == 2 # 最新的
    assert remaining[1]['state_data']['step'] == 1  # 第二新的


@pytest.mark.asyncio
async def test_checkpoint_store_delete_operations(memory_store):
    """测试checkpoint存储删除操作"""
    # 添加多个checkpoint
    checkpoint_ids = []
    for i in range(3):
        checkpoint_data = {
            'thread_id': 'delete_test_thread',
            'workflow_id': f'workflow_{i}',
            'state_data': {'step': i},
            'metadata': {'index': i}
        }
        await memory_store.save(checkpoint_data)
        # 获取保存后的checkpoint ID
        listed = await memory_store.list_by_thread('delete_test_thread')
        if listed:
            checkpoint_ids.append(listed[0]['id'])  # 最新的一个
    
    # 检查初始数量
    initial_count = await memory_store.get_checkpoint_count('delete_test_thread')
    assert initial_count == 3
    
    # 删除特定checkpoint
    if checkpoint_ids:
        success = await memory_store.delete_by_thread('delete_test_thread', checkpoint_ids[0])
        assert success is True
        
        # 检查剩余数量
        after_delete_count = await memory_store.get_checkpoint_count('delete_test_thread')
        assert after_delete_count == 2
    
    # 删除整个thread的所有checkpoint
    success = await memory_store.delete_by_thread('delete_test_thread')
    assert success is True
    
    # 检查是否全部删除
    final_count = await memory_store.get_checkpoint_count('delete_test_thread')
    assert final_count == 0