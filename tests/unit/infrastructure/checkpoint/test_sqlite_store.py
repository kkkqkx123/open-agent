"""SQLite checkpoint存储测试

测试SQLite checkpoint存储的功能。
"""

import pytest
import tempfile
import os
from pathlib import Path
from src.infrastructure.checkpoint.sqlite_store import SQLiteCheckpointStore
from infrastructure.config.service.checkpoint_service import CheckpointConfigService


class TestSQLiteCheckpointStore:
    """SQLite checkpoint存储测试类"""
    
    @pytest.fixture
    def temp_db_path(self):
        """创建临时数据库文件路径"""
        # 确保测试目录存在
        test_dir = Path("storage/test")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False, dir=test_dir) as tmp:
            db_path = tmp.name
        yield db_path
        # 清理临时文件
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def store(self, temp_db_path):
        """创建SQLite存储实例"""
        return SQLiteCheckpointStore(temp_db_path)
    
    @pytest.fixture
    def store_with_config_service(self, temp_db_path):
        """创建使用配置服务的SQLite存储实例"""
        config_service = CheckpointConfigService()
        return SQLiteCheckpointStore(temp_db_path, config_service=config_service)
    
    @pytest.fixture
    def sample_state(self):
        """创建示例状态（可序列化的字典）"""
        return {
            "messages": [{"role": "user", "content": "hello"}],
            "current_step": "analysis",
            "iteration_count": 1
        }
    
    @pytest.mark.asyncio
    async def test_save_checkpoint(self, store, sample_state):
        """测试保存checkpoint"""
        checkpoint_data = {
            'thread_id': 'test-session',
            'workflow_id': 'test-workflow',
            'state_data': sample_state,
            'metadata': {'node': 'analysis'}
        }
        
        result = await store.save(checkpoint_data)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_load_by_thread(self, store, sample_state):
        """测试根据会话ID加载checkpoint"""
        # 先保存checkpoint
        checkpoint_data = {
            'thread_id': 'test-session',
            'workflow_id': 'test-workflow',
            'state_data': sample_state,
            'metadata': {'node': 'analysis'}
        }
        await store.save(checkpoint_data)
        
        # 加载checkpoint
        loaded = await store.load_by_thread('test-session')
        assert loaded is not None
        assert loaded['thread_id'] == 'test-session'
        assert loaded['workflow_id'] == 'test-workflow'
        assert loaded['metadata']['node'] == 'analysis'
    
    @pytest.mark.asyncio
    async def test_load_by_thread_with_checkpoint_id(self, store, sample_state):
        """测试根据会话ID和checkpoint ID加载checkpoint"""
        # 先保存checkpoint
        checkpoint_data = {
            'thread_id': 'test-session',
            'workflow_id': 'test-workflow',
            'state_data': sample_state,
            'metadata': {'node': 'analysis'}
        }
        await store.save(checkpoint_data)
        
        # 获取checkpoint列表
        checkpoints = await store.list_by_thread('test-session')
        assert len(checkpoints) == 1
        
        checkpoint_id = checkpoints[0]['id']
        
        # 加载特定checkpoint
        loaded = await store.load_by_thread('test-session', checkpoint_id)
        assert loaded is not None
        assert loaded['id'] == checkpoint_id
    
    @pytest.mark.asyncio
    async def test_list_by_thread(self, store, sample_state):
        """测试列出会话的所有checkpoint"""
        thread_id = 'test-session'
        
        # 保存多个checkpoint
        for i in range(3):
            checkpoint_data = {
                'thread_id': thread_id,
                'workflow_id': 'test-workflow',
                'state_data': sample_state,
                'metadata': {'step': i}
            }
            await store.save(checkpoint_data)
        
        # 列出checkpoint
        checkpoints = await store.list_by_thread(thread_id)
        assert len(checkpoints) == 3
        
        # 验证按时间倒序排列
        for i in range(len(checkpoints) - 1):
            assert checkpoints[i]['created_at'] >= checkpoints[i + 1]['created_at']
    
    @pytest.mark.asyncio
    async def test_delete_by_thread(self, store, sample_state):
        """测试根据会话ID删除checkpoint"""
        # 先保存checkpoint
        checkpoint_data = {
            'thread_id': 'test-session',
            'workflow_id': 'test-workflow',
            'state_data': sample_state,
            'metadata': {'node': 'analysis'}
        }
        await store.save(checkpoint_data)
        
        # 验证checkpoint存在
        checkpoints = await store.list_by_thread('test-session')
        assert len(checkpoints) == 1
        
        # 删除checkpoint
        result = await store.delete_by_thread('test-session')
        assert result is True
        
        # 验证checkpoint已删除
        checkpoints = await store.list_by_thread('test-session')
        assert len(checkpoints) == 0
    
    @pytest.mark.asyncio
    async def test_delete_by_thread_with_checkpoint_id(self, store, sample_state):
        """测试根据会话ID和checkpoint ID删除特定checkpoint"""
        thread_id = 'test-session'
        
        # 保存多个checkpoint
        for i in range(3):
            checkpoint_data = {
                'thread_id': thread_id,
                'workflow_id': 'test-workflow',
                'state_data': sample_state,
                'metadata': {'step': i}
            }
            await store.save(checkpoint_data)
        
        # 获取checkpoint列表
        checkpoints = await store.list_by_thread(thread_id)
        assert len(checkpoints) == 3
        
        # 删除第二个checkpoint
        checkpoint_id = checkpoints[1]['id']
        result = await store.delete_by_thread(thread_id, checkpoint_id)
        assert result is True
        
        # 验证只剩2个checkpoint
        remaining_checkpoints = await store.list_by_thread(thread_id)
        assert len(remaining_checkpoints) == 2
        assert checkpoint_id not in [cp['id'] for cp in remaining_checkpoints]
    
    @pytest.mark.asyncio
    async def test_get_latest(self, store, sample_state):
        """测试获取最新checkpoint"""
        thread_id = 'test-session'
        
        # 保存多个checkpoint
        for i in range(3):
            checkpoint_data = {
                'thread_id': thread_id,
                'workflow_id': 'test-workflow',
                'state_data': sample_state,
                'metadata': {'step': i}
            }
            await store.save(checkpoint_data)
        
        # 获取最新checkpoint
        latest = await store.get_latest(thread_id)
        assert latest is not None
        assert latest['metadata']['step'] == 2  # 最后一个保存的
    
    @pytest.mark.asyncio
    async def test_get_latest_empty(self, store):
        """测试获取不存在会话的最新checkpoint"""
        latest = await store.get_latest('non-existent-session')
        assert latest is None
    
    @pytest.mark.asyncio
    async def test_cleanup_old_checkpoints(self, store, sample_state):
        """测试清理旧checkpoint"""
        thread_id = 'test-session'
        
        # 保存5个checkpoint
        for i in range(5):
            checkpoint_data = {
                'thread_id': thread_id,
                'workflow_id': 'test-workflow',
                'state_data': sample_state,
                'metadata': {'step': i}
            }
            await store.save(checkpoint_data)
        
        # 保留最新的3个
        deleted_count = await store.cleanup_old_checkpoints(thread_id, 3)
        assert deleted_count == 2
        
        # 验证只剩3个checkpoint
        remaining_checkpoints = await store.list_by_thread(thread_id)
        assert len(remaining_checkpoints) == 3
    
    @pytest.mark.asyncio
    async def test_get_checkpoints_by_workflow(self, store, sample_state):
        """测试获取指定工作流的checkpoint"""
        thread_id = 'test-session'
        
        # 保存不同工作流的checkpoint
        for workflow_id in ['workflow-1', 'workflow-2', 'workflow-1']:
            checkpoint_data = {
                'thread_id': thread_id,
                'workflow_id': workflow_id,
                'state_data': sample_state,
                'metadata': {'node': 'test'}
            }
            await store.save(checkpoint_data)
        
        # 获取workflow-1的checkpoint
        workflow1_checkpoints = await store.get_checkpoints_by_workflow(thread_id, 'workflow-1')
        assert len(workflow1_checkpoints) == 2
        
        # 获取workflow-2的checkpoint
        workflow2_checkpoints = await store.get_checkpoints_by_workflow(thread_id, 'workflow-2')
        assert len(workflow2_checkpoints) == 1
    
    @pytest.mark.asyncio
    async def test_get_checkpoint_count(self, store, sample_state):
        """测试获取checkpoint数量"""
        thread_id = 'test-session'
        
        # 初始数量为0
        count = await store.get_checkpoint_count(thread_id)
        assert count == 0
        
        # 保存3个checkpoint
        for i in range(3):
            checkpoint_data = {
                'thread_id': thread_id,
                'workflow_id': 'test-workflow',
                'state_data': sample_state,
                'metadata': {'step': i}
            }
            await store.save(checkpoint_data)
        
        # 验证数量
        count = await store.get_checkpoint_count(thread_id)
        assert count == 3
    
    @pytest.mark.asyncio
    async def test_persistence_across_instances(self, temp_db_path, sample_state):
        """测试跨实例的持久化"""
        # 第一个实例保存checkpoint
        store1 = SQLiteCheckpointStore(temp_db_path)
        checkpoint_data = {
            'thread_id': 'test-session',
            'workflow_id': 'test-workflow',
            'state_data': sample_state,
            'metadata': {'node': 'analysis'}
        }
        await store1.save(checkpoint_data)
        
        # 第二个实例读取checkpoint
        store2 = SQLiteCheckpointStore(temp_db_path)
        checkpoints = await store2.list_by_thread('test-session')
        assert len(checkpoints) == 1
        assert checkpoints[0]['workflow_id'] == 'test-workflow'
    
    @pytest.mark.asyncio
    async def test_metadata_handling(self, store, sample_state):
        """测试metadata处理"""
        checkpoint_data = {
            'thread_id': 'test-session',
            'workflow_id': 'test-workflow',
            'state_data': sample_state,
            'metadata': {
                'node': 'analysis',
                'step': 1,
                'custom_data': {'key': 'value'}
            }
        }
        
        await store.save(checkpoint_data)
        
        # 加载checkpoint并验证metadata
        loaded = await store.load_by_thread('test-session')
        assert loaded is not None
        assert loaded['metadata']['node'] == 'analysis'
        assert loaded['metadata']['step'] == 1
        assert loaded['metadata']['custom_data']['key'] == 'value'
    
    @pytest.mark.asyncio
    async def test_state_serialization(self, store, sample_state):
        """测试状态序列化和反序列化"""
        checkpoint_data = {
            'thread_id': 'test-session',
            'workflow_id': 'test-workflow',
            'state_data': sample_state,
            'metadata': {'node': 'analysis'}
        }
        
        await store.save(checkpoint_data)
        
        # 加载checkpoint并验证状态
        loaded = await store.load_by_thread('test-session')
        assert loaded is not None
        
        # 验证状态数据正确恢复
        state_data = loaded['state_data']
        assert state_data["messages"] == [{"role": "user", "content": "hello"}]
        assert state_data["current_step"] == "analysis"
        assert state_data["iteration_count"] == 1
    
    @pytest.mark.asyncio
    async def test_multiple_sessions(self, store, sample_state):
        """测试多个会话的隔离性"""
        # 为不同会话保存checkpoint
        for thread_id in ['session-1', 'session-2', 'session-3']:
            checkpoint_data = {
                'thread_id': thread_id,
                'workflow_id': 'test-workflow',
                'state_data': sample_state,
                'metadata': {'session': thread_id}
            }
            await store.save(checkpoint_data)
        
        # 验证每个会话只有一个checkpoint
        for thread_id in ['session-1', 'session-2', 'session-3']:
            checkpoints = await store.list_by_thread(thread_id)
            assert len(checkpoints) == 1
            assert checkpoints[0]['metadata']['session'] == thread_id
    
    @pytest.mark.asyncio
    async def test_empty_metadata(self, store, sample_state):
        """测试空metadata的处理"""
        checkpoint_data = {
            'thread_id': 'test-session',
            'workflow_id': 'test-workflow',
            'state_data': sample_state,
            'metadata': {}
        }
        
        await store.save(checkpoint_data)
        
        # 加载checkpoint
        loaded = await store.load_by_thread('test-session')
        assert loaded is not None
        # 验证metadata包含自动添加的字段
        assert 'workflow_id' in loaded['metadata']
        assert 'state_data' in loaded['metadata']
        # 验证原始metadata为空字典时，只包含自动添加的字段
        assert len(loaded['metadata']) == 2
        assert 'workflow_id' in loaded['metadata']
        assert 'state_data' in loaded['metadata']
        # 验证原始metadata为空字典时，只包含自动添加的字段
        assert len(loaded['metadata']) == 2
    
    @pytest.mark.asyncio
    async def test_config_service_integration(self, store_with_config_service, sample_state):
        """测试配置服务集成"""
        checkpoint_data = {
            'thread_id': 'test-session',
            'workflow_id': 'test-workflow',
            'state_data': sample_state,
            'metadata': {'node': 'analysis'}
        }
        
        result = await store_with_config_service.save(checkpoint_data)
        assert result is True
        
        loaded = await store_with_config_service.load_by_thread('test-session')
        assert loaded is not None
        assert loaded['workflow_id'] == 'test-workflow'
        assert loaded['metadata']['node'] == 'analysis'
    
    @pytest.mark.asyncio
    async def test_no_metadata(self, store, sample_state):
        """测试没有metadata的处理"""
        checkpoint_data = {
            'thread_id': 'test-session',
            'workflow_id': 'test-workflow',
            'state_data': sample_state
        }
        
        await store.save(checkpoint_data)
        
        # 加载checkpoint
        loaded = await store.load_by_thread('test-session')
        assert loaded is not None
        # 验证metadata包含自动添加的字段
        assert 'workflow_id' in loaded['metadata']
        assert 'state_data' in loaded['metadata']
        # 验证原始metadata为空字典时，只包含自动添加的字段
        assert len(loaded['metadata']) == 2
        assert 'workflow_id' in loaded['metadata']
        assert 'state_data' in loaded['metadata']
        # 验证原始metadata为空字典时，只包含自动添加的字段
        assert len(loaded['metadata']) == 2