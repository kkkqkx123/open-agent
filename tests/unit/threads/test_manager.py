"""Thread管理器单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.domain.threads.manager import ThreadManager
from src.domain.threads.interfaces import IThreadManager
from src.infrastructure.threads.metadata_store import IThreadMetadataStore
from src.application.checkpoint.interfaces import ICheckpointManager


class TestThreadManager:
    """Thread管理器测试类"""
    
    @pytest.fixture
    def mock_metadata_store(self):
        """模拟Thread元数据存储"""
        store = AsyncMock(spec=IThreadMetadataStore)
        return store
    
    @pytest.fixture
    def mock_checkpoint_manager(self):
        """模拟Checkpoint管理器"""
        manager = AsyncMock(spec=ICheckpointManager)
        return manager
    
    @pytest.fixture
    def thread_manager(self, mock_metadata_store, mock_checkpoint_manager):
        """创建Thread管理器实例"""
        return ThreadManager(mock_metadata_store, mock_checkpoint_manager)
    
    @pytest.mark.asyncio
    async def test_create_thread_success(self, thread_manager, mock_metadata_store, mock_checkpoint_manager):
        """测试成功创建Thread"""
        # 设置模拟返回值
        mock_metadata_store.save_metadata.return_value = True
        
        # 执行测试
        graph_id = "test_graph"
        metadata = {"name": "test_thread"}
        thread_id = await thread_manager.create_thread(graph_id, metadata)
        
        # 验证结果
        assert thread_id.startswith("thread_")
        assert len(thread_id) == len("thread_") + 8  # thread_ + 8位hex
        
        # 验证调用
        mock_metadata_store.save_metadata.assert_called_once()
        call_args = mock_metadata_store.save_metadata.call_args[0]
        saved_thread_id = call_args[0]
        saved_metadata = call_args[1]
        
        assert saved_thread_id == thread_id
        assert saved_metadata["graph_id"] == graph_id
        assert saved_metadata["name"] == "test_thread"
        assert saved_metadata["status"] == "active"
        assert "created_at" in saved_metadata
        assert "updated_at" in saved_metadata
    
    @pytest.mark.asyncio
    async def test_create_thread_failure(self, thread_manager, mock_metadata_store):
        """测试创建Thread失败"""
        # 设置模拟返回值
        mock_metadata_store.save_metadata.return_value = False
        
        # 执行测试并验证异常
        with pytest.raises(RuntimeError, match="创建Thread失败"):
            await thread_manager.create_thread("test_graph")
    
    @pytest.mark.asyncio
    async def test_get_thread_info_exists(self, thread_manager, mock_metadata_store, mock_checkpoint_manager):
        """测试获取存在的Thread信息"""
        # 设置模拟数据
        thread_id = "thread_test123"
        metadata = {
            "thread_id": thread_id,
            "graph_id": "test_graph",
            "status": "active",
            "created_at": "2023-01-01T00:00:00"
        }
        checkpoints = [
            {"id": "cp1", "created_at": "2023-01-01T01:00:00"},
            {"id": "cp2", "created_at": "2023-01-01T02:00:00"}
        ]
        latest_checkpoint = {"id": "cp2", "created_at": "2023-01-01T02:00:00"}
        
        mock_metadata_store.get_metadata.return_value = metadata
        mock_checkpoint_manager.list_checkpoints.return_value = checkpoints
        mock_checkpoint_manager.get_latest_checkpoint.return_value = latest_checkpoint
        
        # 执行测试
        result = await thread_manager.get_thread_info(thread_id)
        
        # 验证结果
        assert result["thread_id"] == thread_id
        assert result["graph_id"] == "test_graph"
        assert result["status"] == "active"
        assert result["checkpoint_count"] == 2
        assert result["latest_checkpoint_id"] == "cp2"
        assert result["latest_checkpoint_created_at"] == "2023-01-01T02:00:00"
    
    @pytest.mark.asyncio
    async def test_get_thread_info_not_exists(self, thread_manager, mock_metadata_store):
        """测试获取不存在的Thread信息"""
        # 设置模拟返回值
        mock_metadata_store.get_metadata.return_value = None
        
        # 执行测试
        result = await thread_manager.get_thread_info("nonexistent_thread")
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_thread_status_success(self, thread_manager, mock_metadata_store):
        """测试成功更新Thread状态"""
        # 设置模拟数据
        thread_id = "thread_test123"
        metadata = {
            "thread_id": thread_id,
            "graph_id": "test_graph",
            "status": "active",
            "created_at": "2023-01-01T00:00:00"
        }
        
        mock_metadata_store.get_metadata.return_value = metadata
        mock_metadata_store.save_metadata.return_value = True
        
        # 执行测试
        result = await thread_manager.update_thread_status(thread_id, "completed")
        
        # 验证结果
        assert result is True
        
        # 验证调用
        mock_metadata_store.save_metadata.assert_called_once()
        call_args = mock_metadata_store.save_metadata.call_args[0]
        saved_thread_id = call_args[0]
        saved_metadata = call_args[1]
        
        assert saved_thread_id == thread_id
        assert saved_metadata["status"] == "completed"
        assert "updated_at" in saved_metadata
    
    @pytest.mark.asyncio
    async def test_update_thread_status_not_exists(self, thread_manager, mock_metadata_store):
        """测试更新不存在的Thread状态"""
        # 设置模拟返回值
        mock_metadata_store.get_metadata.return_value = None
        
        # 执行测试
        result = await thread_manager.update_thread_status("nonexistent_thread", "completed")
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_thread_metadata_success(self, thread_manager, mock_metadata_store):
        """测试成功更新Thread元数据"""
        # 设置模拟数据
        thread_id = "thread_test123"
        metadata = {
            "thread_id": thread_id,
            "graph_id": "test_graph",
            "status": "active",
            "created_at": "2023-01-01T00:00:00"
        }
        
        mock_metadata_store.get_metadata.return_value = metadata
        mock_metadata_store.save_metadata.return_value = True
        
        # 执行测试
        updates = {"status": "completed", "description": "Updated thread"}
        result = await thread_manager.update_thread_metadata(thread_id, updates)
        
        # 验证结果
        assert result is True
        
        # 验证调用
        mock_metadata_store.save_metadata.assert_called_once()
        call_args = mock_metadata_store.save_metadata.call_args[0]
        saved_thread_id = call_args[0]
        saved_metadata = call_args[1]
        
        assert saved_thread_id == thread_id
        assert saved_metadata["status"] == "completed"
        assert saved_metadata["description"] == "Updated thread"
        assert saved_metadata["graph_id"] == "test_graph"  # 系统字段应保留
        assert saved_metadata["created_at"] == "2023-01-01T00:00:00"  # 系统字段应保留
        assert "updated_at" in saved_metadata
    
    @pytest.mark.asyncio
    async def test_delete_thread_success(self, thread_manager, mock_metadata_store, mock_checkpoint_manager):
        """测试成功删除Thread"""
        # 设置模拟数据
        thread_id = "thread_test123"
        metadata = {"thread_id": thread_id}
        checkpoints = [
            {"id": "cp1"},
            {"id": "cp2"}
        ]
        
        mock_metadata_store.get_metadata.return_value = metadata
        mock_checkpoint_manager.list_checkpoints.return_value = checkpoints
        mock_checkpoint_manager.delete_checkpoint.return_value = True
        mock_metadata_store.delete_metadata.return_value = True
        
        # 执行测试
        result = await thread_manager.delete_thread(thread_id)
        
        # 验证结果
        assert result is True
        
        # 验证调用
        assert mock_checkpoint_manager.delete_checkpoint.call_count == 2
        mock_checkpoint_manager.delete_checkpoint.assert_any_call(thread_id, "cp1")
        mock_checkpoint_manager.delete_checkpoint.assert_any_call(thread_id, "cp2")
        mock_metadata_store.delete_metadata.assert_called_once_with(thread_id)
    
    @pytest.mark.asyncio
    async def test_delete_thread_not_exists(self, thread_manager, mock_metadata_store):
        """测试删除不存在的Thread"""
        # 设置模拟返回值
        mock_metadata_store.get_metadata.return_value = None
        
        # 执行测试
        result = await thread_manager.delete_thread("nonexistent_thread")
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_threads_no_filters(self, thread_manager, mock_metadata_store):
        """测试列出所有Threads（无过滤）"""
        # 设置模拟数据
        threads = [
            {"thread_id": "thread1", "created_at": "2023-01-01T01:00:00"},
            {"thread_id": "thread2", "created_at": "2023-01-01T02:00:00"},
            {"thread_id": "thread3", "created_at": "2023-01-01T03:00:00"}
        ]
        
        mock_metadata_store.list_threads.return_value = threads
        
        # 执行测试
        result = await thread_manager.list_threads()
        
        # 验证结果
        assert len(result) == 3
        # 验证按创建时间倒序排列
        assert result[0]["thread_id"] == "thread3"
        assert result[1]["thread_id"] == "thread2"
        assert result[2]["thread_id"] == "thread1"
    
    @pytest.mark.asyncio
    async def test_list_threads_with_filters(self, thread_manager, mock_metadata_store):
        """测试列出Threads（带过滤）"""
        # 设置模拟数据
        threads = [
            {"thread_id": "thread1", "status": "active", "graph_id": "graph1"},
            {"thread_id": "thread2", "status": "completed", "graph_id": "graph1"},
            {"thread_id": "thread3", "status": "active", "graph_id": "graph2"}
        ]
        
        mock_metadata_store.list_threads.return_value = threads
        
        # 执行测试
        filters = {"status": "active"}
        result = await thread_manager.list_threads(filters)
        
        # 验证结果
        assert len(result) == 2
        assert all(t["status"] == "active" for t in result)
    
    @pytest.mark.asyncio
    async def test_list_threads_with_limit(self, thread_manager, mock_metadata_store):
        """测试列出Threads（带限制）"""
        # 设置模拟数据
        threads = [
            {"thread_id": "thread1", "created_at": "2023-01-01T01:00:00"},
            {"thread_id": "thread2", "created_at": "2023-01-01T02:00:00"},
            {"thread_id": "thread3", "created_at": "2023-01-01T03:00:00"}
        ]
        
        mock_metadata_store.list_threads.return_value = threads
        
        # 执行测试
        result = await thread_manager.list_threads(limit=2)
        
        # 验证结果
        assert len(result) == 2
        assert result[0]["thread_id"] == "thread3"
        assert result[1]["thread_id"] == "thread2"
    
    @pytest.mark.asyncio
    async def test_thread_exists_true(self, thread_manager, mock_metadata_store):
        """测试Thread存在（存在）"""
        # 设置模拟返回值
        mock_metadata_store.get_metadata.return_value = {"thread_id": "thread_test123"}
        
        # 执行测试
        result = await thread_manager.thread_exists("thread_test123")
        
        # 验证结果
        assert result is True
    
    @pytest.mark.asyncio
    async def test_thread_exists_false(self, thread_manager, mock_metadata_store):
        """测试Thread存在（不存在）"""
        # 设置模拟返回值
        mock_metadata_store.get_metadata.return_value = None
        
        # 执行测试
        result = await thread_manager.thread_exists("nonexistent_thread")
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_thread_state_exists(self, thread_manager, mock_metadata_store, mock_checkpoint_manager):
        """测试获取Thread状态（存在）"""
        # 设置模拟数据
        thread_id = "thread_test123"
        state_data = {"messages": [], "current_step": "processing"}
        latest_checkpoint = {
            "id": "cp1",
            "state_data": state_data
        }
        
        mock_metadata_store.get_metadata.return_value = {"thread_id": thread_id}
        mock_checkpoint_manager.get_latest_checkpoint.return_value = latest_checkpoint
        
        # 执行测试
        result = await thread_manager.get_thread_state(thread_id)
        
        # 验证结果
        assert result == state_data
    
    @pytest.mark.asyncio
    async def test_get_thread_state_not_exists(self, thread_manager, mock_metadata_store):
        """测试获取Thread状态（Thread不存在）"""
        # 设置模拟返回值
        mock_metadata_store.get_metadata.return_value = None
        
        # 执行测试
        result = await thread_manager.get_thread_state("nonexistent_thread")
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_thread_state_no_checkpoint(self, thread_manager, mock_metadata_store, mock_checkpoint_manager):
        """测试获取Thread状态（无checkpoint）"""
        # 设置模拟数据
        thread_id = "thread_test123"
        
        mock_metadata_store.get_metadata.return_value = {"thread_id": thread_id}
        mock_checkpoint_manager.get_latest_checkpoint.return_value = None
        
        # 执行测试
        result = await thread_manager.get_thread_state(thread_id)
        
        # 验证结果
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_update_thread_state_success(self, thread_manager, mock_metadata_store, mock_checkpoint_manager):
        """测试成功更新Thread状态"""
        # 设置模拟数据
        thread_id = "thread_test123"
        metadata = {
            "thread_id": thread_id,
            "total_steps": 5
        }
        state = {"messages": ["new message"], "current_step": "updated"}
        checkpoint_id = "new_cp1"
        
        mock_metadata_store.get_metadata.return_value = metadata
        mock_metadata_store.save_metadata.return_value = True
        mock_checkpoint_manager.create_checkpoint.return_value = checkpoint_id
        
        # 执行测试
        result = await thread_manager.update_thread_state(thread_id, state)
        
        # 验证结果
        assert result is True
        
        # 验证调用
        mock_checkpoint_manager.create_checkpoint.assert_called_once_with(
            thread_id,
            "default_workflow",
            state,
            metadata={"trigger_reason": "thread_state_update"}
        )
        mock_metadata_store.save_metadata.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_thread_state_not_exists(self, thread_manager, mock_metadata_store):
        """测试更新Thread状态（Thread不存在）"""
        # 设置模拟返回值
        mock_metadata_store.get_metadata.return_value = None
        
        # 执行测试
        result = await thread_manager.update_thread_state("nonexistent_thread", {})
        
        # 验证结果
        assert result is False