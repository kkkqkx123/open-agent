"""Thread检查点适配器测试"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.interfaces.threads.checkpoint import (
    IThreadCheckpointStorage,
    IThreadCheckpointManager,
    IThreadCheckpointSerializer,
    IThreadCheckpointPolicy
)
from src.interfaces.threads.checkpoint_adapter import (
    LegacyCheckpointStoreAdapter,
    LegacyCheckpointManagerAdapter,
    LegacyCheckpointSerializerAdapter,
    LegacyCheckpointPolicyAdapter,
    CheckpointCompatibilityWrapper,
    NewToLegacyStorageAdapter,
    NewToLegacyManagerAdapter
)
from src.core.threads.checkpoints.storage.models import (
    ThreadCheckpoint,
    CheckpointStatus,
    CheckpointType
)
from src.interfaces.checkpoint import (
    ICheckpointStore,
    ICheckpointManager,
    ICheckpointSerializer,
    ICheckpointPolicy
)


class TestLegacyCheckpointStoreAdapter:
    """旧检查点存储适配器测试"""
    
    @pytest.fixture
    def legacy_store(self):
        """创建模拟的旧存储"""
        store = Mock(spec=ICheckpointStore)
        store.save = AsyncMock(return_value="checkpoint_123")
        store.load_by_thread = AsyncMock(return_value={
            "id": "checkpoint_123",
            "thread_id": "thread_456",
            "state_data": {"key": "value"},
            "status": "active",
            "checkpoint_type": "auto",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "size_bytes": 100,
            "restore_count": 0
        })
        store.list_by_thread = AsyncMock(return_value=[])
        store.delete_by_thread = AsyncMock(return_value=True)
        store.get_latest = AsyncMock(return_value=None)
        store.cleanup_old_checkpoints = AsyncMock(return_value=0)
        return store
    
    @pytest.fixture
    def adapter(self, legacy_store):
        """创建适配器"""
        return LegacyCheckpointStoreAdapter(legacy_store)
    
    @pytest.fixture
    def thread_checkpoint(self):
        """创建Thread检查点"""
        return ThreadCheckpoint(
            id="checkpoint_123",
            thread_id="thread_456",
            state_data={"key": "value"}
        )
    
    @pytest.mark.asyncio
    async def test_save_checkpoint(self, adapter, legacy_store, thread_checkpoint):
        """测试保存检查点"""
        result = await adapter.save_checkpoint("thread_456", thread_checkpoint)
        
        assert result == "checkpoint_123"
        legacy_store.save.assert_called_once()
        
        # 验证传递的数据格式
        call_args = legacy_store.save.call_args[0][0]
        assert call_args["id"] == "checkpoint_123"
        assert call_args["thread_id"] == "thread_456"
        assert call_args["state_data"] == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_load_checkpoint(self, adapter, legacy_store):
        """测试加载检查点"""
        result = await adapter.load_checkpoint("thread_456", "checkpoint_123")
        
        assert result is not None
        assert result.id == "checkpoint_123"
        assert result.thread_id == "thread_456"
        assert result.state_data == {"key": "value"}
        
        legacy_store.load_by_thread.assert_called_once_with("thread_456", "checkpoint_123")
    
    @pytest.mark.asyncio
    async def test_list_checkpoints(self, adapter, legacy_store):
        """测试列出检查点"""
        legacy_store.list_by_thread.return_value = [{
            "id": "checkpoint_123",
            "thread_id": "thread_456",
            "state_data": {"key": "value"},
            "status": "active",
            "checkpoint_type": "auto",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "size_bytes": 100,
            "restore_count": 0
        }]
        
        result = await adapter.list_checkpoints("thread_456")
        
        assert len(result) == 1
        assert result[0].id == "checkpoint_123"
        assert result[0].thread_id == "thread_456"
        
        legacy_store.list_by_thread.assert_called_once_with("thread_456")
    
    @pytest.mark.asyncio
    async def test_delete_checkpoint(self, adapter, legacy_store):
        """测试删除检查点"""
        result = await adapter.delete_checkpoint("thread_456", "checkpoint_123")
        
        assert result is True
        legacy_store.delete_by_thread.assert_called_once_with("thread_456", "checkpoint_123")
    
    @pytest.mark.asyncio
    async def test_get_latest_checkpoint(self, adapter, legacy_store):
        """测试获取最新检查点"""
        legacy_store.get_latest.return_value = {
            "id": "checkpoint_123",
            "thread_id": "thread_456",
            "state_data": {"key": "value"},
            "status": "active",
            "checkpoint_type": "auto",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "size_bytes": 100,
            "restore_count": 0
        }
        
        result = await adapter.get_latest_checkpoint("thread_456")
        
        assert result is not None
        assert result.id == "checkpoint_123"
        
        legacy_store.get_latest.assert_called_once_with("thread_456")
    
    @pytest.mark.asyncio
    async def test_cleanup_old_checkpoints(self, adapter, legacy_store):
        """测试清理旧检查点"""
        result = await adapter.cleanup_old_checkpoints("thread_456", 5)
        
        assert result == 0
        legacy_store.cleanup_old_checkpoints.assert_called_once_with("thread_456", 5)
    
    @pytest.mark.asyncio
    async def test_get_checkpoint_statistics(self, adapter, legacy_store):
        """测试获取检查点统计"""
        legacy_store.list_by_thread.return_value = [{
            "id": "checkpoint_123",
            "thread_id": "thread_456",
            "state_data": {"key": "value"},
            "status": "active",
            "checkpoint_type": "auto",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "size_bytes": 100,
            "restore_count": 0
        }]
        
        result = await adapter.get_checkpoint_statistics("thread_456")
        
        assert result.total_checkpoints == 1
        assert result.active_checkpoints == 1
        assert result.total_size_bytes == 100


class TestCheckpointCompatibilityWrapper:
    """检查点兼容性包装器测试"""
    
    @pytest.fixture
    def new_storage(self):
        """创建新的存储接口模拟"""
        storage = Mock(spec=IThreadCheckpointStorage)
        storage.save_checkpoint = AsyncMock(return_value="checkpoint_123")
        return storage
    
    @pytest.fixture
    def new_manager(self):
        """创建新的管理器接口模拟"""
        manager = Mock(spec=IThreadCheckpointManager)
        manager.create_checkpoint = AsyncMock(return_value="checkpoint_123")
        return manager
    
    def test_create_legacy_storage_adapter(self, new_storage):
        """测试创建兼容的存储适配器"""
        adapter = CheckpointCompatibilityWrapper.create_legacy_storage_adapter(new_storage)
        
        assert hasattr(adapter, 'save')
        assert hasattr(adapter, 'load_by_thread')
        assert hasattr(adapter, 'list_by_thread')
    
    def test_create_legacy_manager_adapter(self, new_manager):
        """测试创建兼容的管理器适配器"""
        adapter = CheckpointCompatibilityWrapper.create_legacy_manager_adapter(new_manager)
        
        assert hasattr(adapter, 'create_checkpoint')
        assert hasattr(adapter, 'get_checkpoint')
        assert hasattr(adapter, 'list_checkpoints')


class TestNewToLegacyStorageAdapter:
    """新到旧存储适配器测试"""
    
    @pytest.fixture
    def new_storage(self):
        """创建新的存储接口模拟"""
        storage = Mock(spec=IThreadCheckpointStorage)
        storage.save_checkpoint = AsyncMock(return_value="checkpoint_123")
        storage.load_checkpoint = AsyncMock(return_value=None)
        storage.list_checkpoints = AsyncMock(return_value=[])
        storage.delete_checkpoint = AsyncMock(return_value=True)
        storage.get_latest_checkpoint = AsyncMock(return_value=None)
        storage.cleanup_old_checkpoints = AsyncMock(return_value=0)
        return storage
    
    @pytest.fixture
    def adapter(self, new_storage):
        """创建适配器"""
        return NewToLegacyStorageAdapter(new_storage)
    
    @pytest.fixture
    def checkpoint_data(self):
        """创建检查点数据"""
        return {
            "id": "checkpoint_123",
            "thread_id": "thread_456",
            "state_data": {"key": "value"},
            "status": "active",
            "checkpoint_type": "auto",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "size_bytes": 100,
            "restore_count": 0
        }
    
    @pytest.mark.asyncio
    async def test_save(self, adapter, new_storage, checkpoint_data):
        """测试保存"""
        result = await adapter.save(checkpoint_data)
        
        assert result == "checkpoint_123"
        new_storage.save_checkpoint.assert_called_once()
        
        # 验证调用参数
        call_args = new_storage.save_checkpoint.call_args[0]
        assert call_args[0] == "thread_456"  # thread_id
        assert isinstance(call_args[1], ThreadCheckpoint)  # checkpoint
    
    @pytest.mark.asyncio
    async def test_load_by_thread(self, adapter, new_storage):
        """测试根据thread加载"""
        checkpoint = ThreadCheckpoint(
            id="checkpoint_123",
            thread_id="thread_456",
            state_data={"key": "value"}
        )
        new_storage.load_checkpoint.return_value = checkpoint
        
        result = await adapter.load_by_thread("thread_456", "checkpoint_123")
        
        assert result is not None
        assert result["id"] == "checkpoint_123"
        
        new_storage.load_checkpoint.assert_called_once_with("thread_456", "checkpoint_123")
    
    @pytest.mark.asyncio
    async def test_load_by_thread_without_checkpoint_id(self, adapter, new_storage):
        """测试根据thread加载（无checkpoint_id）"""
        checkpoint = ThreadCheckpoint(
            id="checkpoint_123",
            thread_id="thread_456",
            state_data={"key": "value"}
        )
        new_storage.get_latest_checkpoint.return_value = checkpoint
        
        result = await adapter.load_by_thread("thread_456")
        
        assert result is not None
        assert result["id"] == "checkpoint_123"
        
        new_storage.get_latest_checkpoint.assert_called_once_with("thread_456")
    
    @pytest.mark.asyncio
    async def test_list_by_thread(self, adapter, new_storage):
        """测试列出thread的所有检查点"""
        checkpoint = ThreadCheckpoint(
            id="checkpoint_123",
            thread_id="thread_456",
            state_data={"key": "value"}
        )
        new_storage.list_checkpoints.return_value = [checkpoint]
        
        result = await adapter.list_by_thread("thread_456")
        
        assert len(result) == 1
        assert result[0]["id"] == "checkpoint_123"
        
        new_storage.list_checkpoints.assert_called_once_with("thread_456")
    
    @pytest.mark.asyncio
    async def test_delete_by_thread(self, adapter, new_storage):
        """测试删除thread的检查点"""
        result = await adapter.delete_by_thread("thread_456", "checkpoint_123")
        
        assert result is True
        new_storage.delete_checkpoint.assert_called_once_with("thread_456", "checkpoint_123")
    
    @pytest.mark.asyncio
    async def test_delete_by_thread_all(self, adapter, new_storage):
        """测试删除thread的所有检查点"""
        checkpoint = ThreadCheckpoint(
            id="checkpoint_123",
            thread_id="thread_456",
            state_data={"key": "value"}
        )
        new_storage.list_checkpoints.return_value = [checkpoint]
        
        result = await adapter.delete_by_thread("thread_456")
        
        assert result is True
        new_storage.list_checkpoints.assert_called_once_with("thread_456")
        new_storage.delete_checkpoint.assert_called_once_with("thread_456", "checkpoint_123")
    
    @pytest.mark.asyncio
    async def test_get_latest(self, adapter, new_storage):
        """测试获取最新检查点"""
        checkpoint = ThreadCheckpoint(
            id="checkpoint_123",
            thread_id="thread_456",
            state_data={"key": "value"}
        )
        new_storage.get_latest_checkpoint.return_value = checkpoint
        
        result = await adapter.get_latest("thread_456")
        
        assert result is not None
        assert result["id"] == "checkpoint_123"
        
        new_storage.get_latest_checkpoint.assert_called_once_with("thread_456")
    
    @pytest.mark.asyncio
    async def test_cleanup_old_checkpoints(self, adapter, new_storage):
        """测试清理旧检查点"""
        result = await adapter.cleanup_old_checkpoints("thread_456", 5)
        
        assert result == 0
        new_storage.cleanup_old_checkpoints.assert_called_once_with("thread_456", 5)
    
    @pytest.mark.asyncio
    async def test_get_checkpoints_by_workflow(self, adapter, new_storage):
        """测试获取工作流的所有检查点"""
        checkpoint = ThreadCheckpoint(
            id="checkpoint_123",
            thread_id="thread_456",
            state_data={"key": "value"}
        )
        new_storage.list_checkpoints.return_value = [checkpoint]
        
        result = await adapter.get_checkpoints_by_workflow("thread_456", "workflow_789")
        
        assert len(result) == 1
        assert result[0]["id"] == "checkpoint_123"
        
        new_storage.list_checkpoints.assert_called_once_with("thread_456")