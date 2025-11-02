"""Checkpoint管理器测试

测试checkpoint管理器的功能。
"""

import pytest
from unittest.mock import AsyncMock, Mock
from src.application.checkpoint.manager import CheckpointManager, DefaultCheckpointPolicy
from src.domain.checkpoint.config import CheckpointConfig
from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore
from src.domain.checkpoint.serializer import DefaultCheckpointSerializer


class TestDefaultCheckpointPolicy:
    """默认checkpoint策略测试类"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return CheckpointConfig(
            enabled=True,
            auto_save=True,
            save_interval=2,
            trigger_conditions=["tool_call", "error"]
        )
    
    @pytest.fixture
    def policy(self, config):
        """创建策略实例"""
        return DefaultCheckpointPolicy(config)
    
    def test_should_save_checkpoint_enabled(self, policy):
        """测试启用时应该保存checkpoint"""
        result = policy.should_save_checkpoint(
            "session-1", "workflow-1", {}, {"trigger_reason": "tool_call"}
        )
        assert result is True
    
    def test_should_save_checkpoint_disabled(self, policy):
        """测试禁用时不应该保存checkpoint"""
        policy.config.enabled = False
        
        result = policy.should_save_checkpoint(
            "session-1", "workflow-1", {}, {"trigger_reason": "tool_call"}
        )
        assert result is False
    
    def test_should_save_checkpoint_trigger_condition(self, policy):
        """测试触发条件匹配"""
        result = policy.should_save_checkpoint(
            "session-1", "workflow-1", {}, {"trigger_reason": "tool_call"}
        )
        assert result is True
        
        result = policy.should_save_checkpoint(
            "session-1", "workflow-1", {}, {"trigger_reason": "error"}
        )
        assert result is True
        
        result = policy.should_save_checkpoint(
            "session-1", "workflow-1", {}, {"trigger_reason": "other"}
        )
        assert result is False
    
    def test_should_save_checkpoint_step_interval(self, policy):
        """测试步数间隔触发"""
        # 第一次不应该触发（步数不足）
        result = policy.should_save_checkpoint(
            "session-1", "workflow-1", {}, {"trigger_reason": "other"}
        )
        assert result is False
        
        # 第二次应该触发（达到间隔）
        result = policy.should_save_checkpoint(
            "session-1", "workflow-1", {}, {"trigger_reason": "other"}
        )
        assert result is True
        
        # 第三次不应该触发（步数不足）
        result = policy.should_save_checkpoint(
            "session-1", "workflow-1", {}, {"trigger_reason": "other"}
        )
        assert result is False
    
    def test_get_checkpoint_metadata(self, policy):
        """测试获取checkpoint元数据"""
        metadata = policy.get_checkpoint_metadata(
            "session-1", "workflow-1", {}, 
            {"trigger_reason": "tool_call", "node_name": "analysis"}
        )
        
        assert metadata["thread_id"] == "session-1"
        assert metadata["workflow_id"] == "workflow-1"
        assert metadata["step_count"] == 1
        assert metadata["node_name"] == "analysis"
        assert metadata["trigger_reason"] == "tool_call"
        assert "checkpoint_id" in metadata
        assert "created_at" in metadata


class TestCheckpointManager:
    """Checkpoint管理器测试类"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return CheckpointConfig(
            enabled=True,
            storage_type="memory",
            auto_save=True,
            save_interval=2,
            max_checkpoints=5
        )
    
    @pytest.fixture
    def store(self):
        """创建内存存储"""
        serializer = DefaultCheckpointSerializer()
        return MemoryCheckpointStore(serializer)
    
    @pytest.fixture
    def manager(self, store, config):
        """创建checkpoint管理器"""
        return CheckpointManager(store, config)
    
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
    async def test_create_checkpoint(self, manager, sample_state):
        """测试创建checkpoint"""
        checkpoint_id = await manager.create_checkpoint(
            "session-1", "workflow-1", sample_state, {"node": "analysis"}
        )
        
        assert checkpoint_id is not None
        assert isinstance(checkpoint_id, str)
    
    @pytest.mark.asyncio
    async def test_get_checkpoint(self, manager, sample_state):
        """测试获取checkpoint"""
        # 先创建checkpoint
        checkpoint_id = await manager.create_checkpoint(
            "session-1", "workflow-1", sample_state
        )
        
        # 获取checkpoint
        checkpoint = await manager.get_checkpoint("session-1", checkpoint_id)
        assert checkpoint is not None
        assert checkpoint["thread_id"] == "session-1"
        assert checkpoint["workflow_id"] == "workflow-1"
    
    @pytest.mark.asyncio
    async def test_get_checkpoint_not_found(self, manager):
        """测试获取不存在的checkpoint"""
        checkpoint = await manager.get_checkpoint("session-1", "non-existent")
        assert checkpoint is None
    
    @pytest.mark.asyncio
    async def test_list_checkpoints(self, manager, sample_state):
        """测试列出checkpoint"""
        thread_id = "session-1"
        
        # 创建多个checkpoint
        for i in range(3):
            await manager.create_checkpoint(
                thread_id, "workflow-1", sample_state, {"step": i}
            )
        
        # 列出checkpoint
        checkpoints = await manager.list_checkpoints(thread_id)
        assert len(checkpoints) == 3
        
        # 验证按时间倒序排列
        for i in range(len(checkpoints) - 1):
            assert checkpoints[i]["created_at"] >= checkpoints[i + 1]["created_at"]
    
    @pytest.mark.asyncio
    async def test_delete_checkpoint(self, manager, sample_state):
        """测试删除checkpoint"""
        # 先创建checkpoint
        checkpoint_id = await manager.create_checkpoint(
            "session-1", "workflow-1", sample_state
        )
        
        # 验证checkpoint存在
        checkpoints = await manager.list_checkpoints("session-1")
        assert len(checkpoints) == 1
        
        # 删除checkpoint
        result = await manager.delete_checkpoint("session-1", checkpoint_id)
        assert result is True
        
        # 验证checkpoint已删除
        checkpoints = await manager.list_checkpoints("session-1")
        assert len(checkpoints) == 0
    
    @pytest.mark.asyncio
    async def test_get_latest_checkpoint(self, manager, sample_state):
        """测试获取最新checkpoint"""
        thread_id = "session-1"
        
        # 创建多个checkpoint
        for i in range(3):
            await manager.create_checkpoint(
                thread_id, "workflow-1", sample_state, {"step": i}
            )
        
        # 获取最新checkpoint
        latest = await manager.get_latest_checkpoint(thread_id)
        assert latest is not None
        assert latest["metadata"]["step"] == 2  # 最后一个创建的
    
    @pytest.mark.asyncio
    async def test_get_latest_checkpoint_empty(self, manager):
        """测试获取不存在会话的最新checkpoint"""
        latest = await manager.get_latest_checkpoint("non-existent")
        assert latest is None
    
    @pytest.mark.asyncio
    async def test_restore_from_checkpoint(self, manager, sample_state):
        """测试从checkpoint恢复状态"""
        # 先创建checkpoint
        checkpoint_id = await manager.create_checkpoint(
            "session-1", "workflow-1", sample_state
        )
        
        # 恢复状态
        restored_state = await manager.restore_from_checkpoint("session-1", checkpoint_id)
        assert restored_state is not None
        assert hasattr(restored_state, 'messages')
        assert hasattr(restored_state, 'current_step')
    
    @pytest.mark.asyncio
    async def test_auto_save_checkpoint(self, manager, sample_state):
        """测试自动保存checkpoint"""
        # 触发条件匹配
        checkpoint_id = await manager.auto_save_checkpoint(
            "session-1", "workflow-1", sample_state, "tool_call"
        )
        assert checkpoint_id is not None
        
        # 验证checkpoint已保存
        checkpoints = await manager.list_checkpoints("session-1")
        assert len(checkpoints) == 1
    
    @pytest.mark.asyncio
    async def test_auto_save_checkpoint_no_trigger(self, manager, sample_state):
        """测试自动保存checkpoint不触发"""
        # 触发条件不匹配
        checkpoint_id = await manager.auto_save_checkpoint(
            "session-1", "workflow-1", sample_state, "other_reason"
        )
        assert checkpoint_id is None
        
        # 验证没有保存checkpoint
        checkpoints = await manager.list_checkpoints("session-1")
        assert len(checkpoints) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_checkpoints(self, manager, sample_state):
        """测试清理checkpoint"""
        thread_id = "session-1"
        
        # 创建5个checkpoint
        for i in range(5):
            await manager.create_checkpoint(
                thread_id, "workflow-1", sample_state, {"step": i}
            )
        
        # 保留最新的3个
        deleted_count = await manager.cleanup_checkpoints(thread_id, 3)
        assert deleted_count == 2
        
        # 验证只剩3个checkpoint
        checkpoints = await manager.list_checkpoints(thread_id)
        assert len(checkpoints) == 3
    
    @pytest.mark.asyncio
    async def test_get_checkpoints_by_workflow(self, manager, sample_state):
        """测试获取指定工作流的checkpoint"""
        thread_id = "session-1"
        
        # 创建不同工作流的checkpoint
        for workflow_id in ["workflow-1", "workflow-2", "workflow-1"]:
            await manager.create_checkpoint(
                thread_id, workflow_id, sample_state, {"node": "test"}
            )
        
        # 获取workflow-1的checkpoint
        workflow1_checkpoints = await manager.get_checkpoints_by_workflow(
            thread_id, "workflow-1"
        )
        assert len(workflow1_checkpoints) == 2
        
        # 获取workflow-2的checkpoint
        workflow2_checkpoints = await manager.get_checkpoints_by_workflow(
            thread_id, "workflow-2"
        )
        assert len(workflow2_checkpoints) == 1
    
    @pytest.mark.asyncio
    async def test_get_checkpoint_count(self, manager, sample_state):
        """测试获取checkpoint数量"""
        thread_id = "session-1"
        
        # 初始数量为0
        count = await manager.get_checkpoint_count(thread_id)
        assert count == 0
        
        # 创建3个checkpoint
        for i in range(3):
            await manager.create_checkpoint(
                thread_id, "workflow-1", sample_state, {"step": i}
            )
        
        # 验证数量
        count = await manager.get_checkpoint_count(thread_id)
        assert count == 3
    
    def test_get_langgraph_checkpointer(self, manager):
        """测试获取LangGraph原生的checkpointer"""
        checkpointer = manager.get_langgraph_checkpointer()
        assert checkpointer is not None
        
        # 验证是InMemorySaver实例
        from langgraph.checkpoint.memory import InMemorySaver
        assert isinstance(checkpointer, InMemorySaver)
    
    @pytest.mark.asyncio
    async def test_create_checkpoint_failure(self, manager):
        """测试创建checkpoint失败"""
        # 使用无效的状态数据
        with pytest.raises(Exception):
            await manager.create_checkpoint("session-1", "workflow-1", None)
    
    @pytest.mark.asyncio
    async def test_disabled_manager(self, sample_state):
        """测试禁用的管理器"""
        config = CheckpointConfig(enabled=False)
        store = MemoryCheckpointStore()
        manager = CheckpointManager(store, config)
        
        # 自动保存应该不触发
        checkpoint_id = await manager.auto_save_checkpoint(
            "session-1", "workflow-1", sample_state, "tool_call"
        )
        assert checkpoint_id is None


class TestCheckpointManagerIntegration:
    """Checkpoint管理器集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整的工作流"""
        # 创建管理器
        config = CheckpointConfig(
            storage_type="memory",
            auto_save=True,
            save_interval=2,
            max_checkpoints=3
        )
        store = MemoryCheckpointStore()
        manager = CheckpointManager(store, config)
        
        # 模拟工作流状态
        class WorkflowState:
            def __init__(self):
                self.messages = []
                self.current_step = "start"
                self.iteration_count = 0
        
        state = WorkflowState()
        thread_id = "test-session"
        workflow_id = "test-workflow"
        
        # 执行工作流步骤
        for step in range(5):
            state.current_step = f"step-{step}"
            state.iteration_count = step
            state.messages.append({"role": "system", "content": f"Step {step}"})
            
            # 自动保存checkpoint
            checkpoint_id = await manager.auto_save_checkpoint(
                thread_id, workflow_id, state, f"step_complete"
            )
            
            if checkpoint_id:
                print(f"Checkpoint saved: {checkpoint_id}")
        
        # 验证checkpoint数量（最多3个）
        checkpoints = await manager.list_checkpoints(thread_id)
        assert len(checkpoints) <= 3
        
        # 恢复最新状态
        latest = await manager.get_latest_checkpoint(thread_id)
        assert latest is not None
        
        restored_state = await manager.restore_from_checkpoint(
            thread_id, latest["id"]
        )
        assert restored_state is not None
        assert restored_state.iteration_count >= 3  # 应该是较新的状态