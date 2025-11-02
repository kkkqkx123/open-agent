"""内存checkpoint存储测试

测试内存checkpoint存储的功能。
"""

import pytest
from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore
from src.domain.checkpoint.serializer import DefaultCheckpointSerializer


class TestMemoryCheckpointStore:
    """内存checkpoint存储测试类"""
    
    @pytest.fixture
    def store(self):
        """创建内存存储实例"""
        serializer = DefaultCheckpointSerializer()
        return MemoryCheckpointStore(serializer=serializer)
    
    @pytest.fixture
    def sample_state(self):
        """创建示例状态"""
        class MockState:
            def __init__(self):
                self.messages = [{"role": "user", "content": "hello"}]
                self.current_step = "analysis"
                self.iteration_count = 1
        
        return MockState()
    
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
    async def test_clear(self, store, sample_state):
        """测试清空所有checkpoint"""
        # 保存一些checkpoint
        for i in range(3):
            checkpoint_data = {
                'thread_id': f'session-{i}',
                'workflow_id': 'test-workflow',
                'state_data': sample_state,
                'metadata': {'step': i}
            }
            await store.save(checkpoint_data)
        
        # 验证有checkpoint
        count = await store.get_checkpoint_count('session-0')
        assert count == 1
        
        # 清空所有checkpoint
        store.clear()
        
        # 验证已清空
        count = await store.get_checkpoint_count('session-0')
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_get_langgraph_checkpointer(self, store):
        """测试获取LangGraph原生的checkpointer"""
        checkpointer = store.get_langgraph_checkpointer()
        assert checkpointer is not None
        
        # 验证是InMemorySaver实例
        from langgraph.checkpoint.memory import InMemorySaver
        assert isinstance(checkpointer, InMemorySaver)
    