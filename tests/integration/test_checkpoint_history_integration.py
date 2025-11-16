"""Checkpoint与History模块集成测试"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from src.application.checkpoint.manager import CheckpointManager
from src.application.history.manager import HistoryManager
from src.infrastructure.common.serialization.serializer import Serializer
from src.infrastructure.common.cache.cache_manager import CacheManager
from src.infrastructure.common.monitoring.performance_monitor import PerformanceMonitor
from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore
from src.infrastructure.history.storage.file_storage import FileHistoryStorage
from src.domain.checkpoint.config import CheckpointConfig
from src.domain.history.models import MessageRecord, MessageType


class TestCheckpointHistoryIntegration:
    """Checkpoint与History模块集成测试"""
    
    @pytest.fixture
    async def setup_components(self):
        """设置测试组件"""
        # 创建临时目录用于历史存储
        temp_dir = tempfile.mkdtemp()
        history_path = Path(temp_dir)
        
        # 创建公用组件
        serializer = Serializer()
        cache_manager = CacheManager(default_ttl=300)
        performance_monitor = PerformanceMonitor()
        
        # 创建存储
        checkpoint_store = MemoryCheckpointStore(
            universal_serializer=serializer,
            cache_manager=cache_manager,
            performance_monitor=performance_monitor
        )
        history_storage = FileHistoryStorage(history_path)
        
        # 创建checkpoint配置
        checkpoint_config = CheckpointConfig(
            enabled=True,
            storage_type="memory",
            auto_save=True,
            save_interval=1,
            max_checkpoints=100
        )
        
        # 创建管理器
        checkpoint_manager = CheckpointManager(
            checkpoint_store=checkpoint_store,
            config=checkpoint_config,
            serializer=serializer,
            cache_manager=cache_manager,
            performance_monitor=performance_monitor
        )
        
        history_manager = HistoryManager(
            storage=history_storage,
            serializer=serializer,
            cache_manager=cache_manager,
            performance_monitor=performance_monitor,
            use_sync_cache=True  # 使用同步缓存适配器
        )
        
        yield checkpoint_manager, history_manager, performance_monitor, temp_dir
        
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_shared_components_usage(self, setup_components):
        """测试共享组件使用"""
        checkpoint_manager, history_manager, monitor, _ = setup_components
        
        # 测试序列化器共享
        test_data = {"test": "data", "timestamp": datetime.now()}
        serialized = checkpoint_manager.serializer.serialize(test_data)
        deserialized = history_manager.serializer.deserialize(serialized)
        assert deserialized["test"] == test_data["test"]
        
        # 测试缓存共享
        cache_key = "test_key"
        await checkpoint_manager.cache.set(cache_key, test_data)

        # 检查点管理器使用异步缓存，历史管理器使用同步缓存适配器
        cached_data = await history_manager.cache.get(cache_key)
        assert cached_data == test_data
        
        # 测试性能监控共享
        operation_id = monitor.start_operation("test_operation")
        monitor.end_operation(operation_id, "test_operation", True)
        
        stats = monitor.get_stats("test_operation")
        assert stats["total_operations"] == 1
        assert stats["successful_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_checkpoint_history_workflow(self, setup_components):
        """测试Checkpoint与History工作流"""
        checkpoint_manager, history_manager, monitor, _ = setup_components
        
        thread_id = "test_thread"
        workflow_id = "test_workflow"
        session_id = "test_session"
        
        # 1. 创建checkpoint
        state = {"step": 1, "data": "test"}
        checkpoint_id = await checkpoint_manager.create_checkpoint(
            thread_id, workflow_id, state
        )
        
        # 2. 记录历史消息
        message = MessageRecord(
            record_id=checkpoint_manager.id_generator.generate_id(),
            session_id=session_id,
            timestamp=datetime.now(),
            record_type="message",
            message_type=MessageType.USER,
            content="Test message",
            metadata={"checkpoint_id": checkpoint_id}
        )
        
        await history_manager.record_message(message)
        
        # 3. 验证性能指标
        checkpoint_stats = monitor.get_stats("create_checkpoint")
        history_stats = monitor.get_stats("record_message")
        
        assert checkpoint_stats["total_operations"] == 1
        assert history_stats["total_operations"] == 1
        
        # 4. 验证数据一致性
        retrieved_checkpoint = await checkpoint_manager.get_checkpoint(thread_id, checkpoint_id)
        assert retrieved_checkpoint is not None
        assert retrieved_checkpoint["workflow_id"] == workflow_id
        
        # 5. 验证历史记录
        from src.domain.history.models import HistoryQuery
        query = HistoryQuery(session_id=session_id)
        result = await history_manager.query_history(query)
        assert len(result.records) == 1
        assert result.records[0].content == "Test message"
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, setup_components):
        """测试性能监控集成"""
        checkpoint_manager, history_manager, monitor, _ = setup_components
        
        # 执行多个操作
        for i in range(5):
            # 创建checkpoint
            state = {"step": i, "data": f"test_{i}"}
            await checkpoint_manager.create_checkpoint(
                f"thread_{i}", f"workflow_{i}", state
            )
            
            # 记录历史消息
            message = MessageRecord(
                record_id=checkpoint_manager.id_generator.generate_id(),
                session_id=f"session_{i}",
                timestamp=datetime.now(),
                record_type="message",
                message_type=MessageType.USER,
                content=f"Test message {i}"
            )
            await history_manager.record_message(message)
        
        # 验证性能统计
        checkpoint_stats = monitor.get_stats("create_checkpoint")
        history_stats = monitor.get_stats("record_message")
        
        assert checkpoint_stats["total_operations"] == 5
        assert checkpoint_stats["successful_operations"] == 5
        assert checkpoint_stats["success_rate"] == 1.0
        
        assert history_stats["total_operations"] == 5
        assert history_stats["successful_operations"] == 5
        assert history_stats["success_rate"] == 1.0
        
        # 验证慢操作检测
        slow_operations = monitor.get_slow_operations(threshold=0.0)  # 获取所有操作
        assert len(slow_operations) >= 10  # 至少有10个操作（5个checkpoint + 5个history）
    
    @pytest.mark.asyncio
    async def test_cache_integration(self, setup_components):
        """测试缓存集成"""
        checkpoint_manager, history_manager, monitor, _ = setup_components
        
        thread_id = "cache_test_thread"
        workflow_id = "cache_test_workflow"
        
        # 1. 创建checkpoint
        state = {"step": 1, "data": "cache_test"}
        checkpoint_id = await checkpoint_manager.create_checkpoint(
            thread_id, workflow_id, state
        )
        
        # 2. 从缓存获取checkpoint
        cached_checkpoint = await checkpoint_manager.cache.get(checkpoint_id)
        assert cached_checkpoint is not None
        assert cached_checkpoint["workflow_id"] == workflow_id
        
        # 3. 验证缓存命中
        retrieved_checkpoint = await checkpoint_manager.get_checkpoint(thread_id, checkpoint_id)
        assert retrieved_checkpoint is not None
        
        # 检查性能指标中的缓存命中
        get_stats = monitor.get_stats("get_checkpoint")
        assert get_stats["total_operations"] == 1
        assert get_stats["successful_operations"] == 1
    
    @pytest.mark.asyncio
    async def test_id_generation_consistency(self, setup_components):
        """测试ID生成一致性"""
        checkpoint_manager, history_manager, _, _ = setup_components
        
        # 测试不同类型的ID生成
        session_id = checkpoint_manager.id_generator.generate_session_id()
        thread_id = checkpoint_manager.id_generator.generate_thread_id()
        checkpoint_id = checkpoint_manager.id_generator.generate_checkpoint_id()
        workflow_id = checkpoint_manager.id_generator.generate_workflow_id()
        
        # 验证ID格式
        assert session_id.startswith("session_")
        assert thread_id.startswith("thread_")
        assert checkpoint_id.startswith("checkpoint_")
        assert workflow_id.startswith("workflow_")
        
        # 验证ID唯一性
        ids = [session_id, thread_id, checkpoint_id, workflow_id]
        assert len(ids) == len(set(ids))  # 所有ID都是唯一的
    
    @pytest.mark.asyncio
    async def test_metadata_normalization(self, setup_components):
        """测试元数据标准化"""
        checkpoint_manager, history_manager, _, _ = setup_components
        
        # 测试checkpoint元数据标准化
        metadata = {
            "user_id": 123,  # 数字
            "tags": ["tag1", "tag2"],  # 列表
            "nested": {"key": "value"},  # 嵌套字典
            "timestamp": datetime.now()  # 时间戳
        }
        
        thread_id = "metadata_test_thread"
        workflow_id = "metadata_test_workflow"
        state = {"step": 1}
        
        checkpoint_id = await checkpoint_manager.create_checkpoint(
            thread_id, workflow_id, state, metadata
        )
        
        # 获取checkpoint并验证元数据
        checkpoint = await checkpoint_manager.get_checkpoint(thread_id, checkpoint_id)
        assert checkpoint is not None
        assert "metadata" in checkpoint
        assert checkpoint["metadata"]["user_id"] == 123
        assert checkpoint["metadata"]["tags"] == ["tag1", "tag2"]
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, setup_components):
        """测试错误处理集成"""
        checkpoint_manager, history_manager, monitor, _ = setup_components
        
        # 测试checkpoint错误处理
        try:
            # 尝试使用无效的thread_id
            await checkpoint_manager.create_checkpoint("", "workflow", {})
            assert False, "应该抛出异常"
        except Exception:
            pass  # 预期的异常
        
        # 验证错误被记录在性能监控中
        checkpoint_stats = monitor.get_stats("create_checkpoint")
        assert checkpoint_stats["total_operations"] == 1
        assert checkpoint_stats["failed_operations"] == 1
        assert checkpoint_stats["success_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, setup_components):
        """测试并发操作"""
        checkpoint_manager, history_manager, monitor, _ = setup_components
        
        # 创建多个并发任务
        async def create_checkpoint(index):
            return await checkpoint_manager.create_checkpoint(
                f"thread_{index}", f"workflow_{index}", {"step": index}
            )
        
        async def record_message(index):
            message = MessageRecord(
                record_id=checkpoint_manager.id_generator.generate_id(),
                session_id=f"session_{index}",
                timestamp=datetime.now(),
                record_type="message",
                message_type=MessageType.USER,
                content=f"Concurrent message {index}"
            )
            await history_manager.record_message(message)
        
        # 并发执行操作
        tasks = []
        for i in range(10):
            tasks.append(create_checkpoint(i))
            tasks.append(record_message(i))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证结果
        successful_checkpoints = [r for r in results[:10] if not isinstance(r, Exception)]
        assert len(successful_checkpoints) == 10
        
        # 验证性能统计
        checkpoint_stats = monitor.get_stats("create_checkpoint")
        history_stats = monitor.get_stats("record_message")
        
        assert checkpoint_stats["total_operations"] == 10
        assert history_stats["total_operations"] == 10