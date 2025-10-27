"""Thread集成测试"""

import asyncio
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from src.application.threads.session_thread_mapper import SessionThreadMapper, MemorySessionThreadMapper
from src.application.threads.query_manager import ThreadQueryManager
from src.application.sessions.manager import SessionManager
from src.domain.threads.interfaces import IThreadManager
from src.infrastructure.threads.metadata_store import MemoryThreadMetadataStore
from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore
from src.infrastructure.checkpoint.factory import CheckpointManager
from src.infrastructure.langgraph.sdk_adapter import CompleteLangGraphSDKAdapter
from src.infrastructure.threads.cache_manager import ThreadCacheManager, PerformanceMonitor


class MockThreadManager(IThreadManager):
    """模拟Thread管理器用于测试"""
    
    def __init__(self):
        self._threads = {}
        self._states = {}
        self._metadata = {}
    
    async def create_thread(self, graph_id: str, metadata: Dict[str, Any] = None) -> str:
        import uuid
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        self._threads[thread_id] = {
            "thread_id": thread_id,
            "graph_id": graph_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "metadata": metadata or {}
        }
        self._states[thread_id] = {}
        return thread_id
    
    async def get_thread_info(self, thread_id: str) -> Dict[str, Any]:
        return self._threads.get(thread_id)
    
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        if thread_id in self._threads:
            self._threads[thread_id]["status"] = status
            return True
        return False
    
    async def update_thread_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        if thread_id in self._threads:
            self._threads[thread_id]["metadata"].update(metadata)
            return True
        return False
    
    async def delete_thread(self, thread_id: str) -> bool:
        if thread_id in self._threads:
            del self._threads[thread_id]
            if thread_id in self._states:
                del self._states[thread_id]
            if thread_id in self._metadata:
                del self._metadata[thread_id]
            return True
        return False
    
    async def list_threads(self, filters=None, limit=None) -> list:
        return list(self._threads.values())
    
    async def thread_exists(self, thread_id: str) -> bool:
        return thread_id in self._threads
    
    async def get_thread_state(self, thread_id: str) -> Dict[str, Any]:
        return self._states.get(thread_id, {})
    
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        if thread_id in self._states:
            self._states[thread_id].update(state)
            return True
        return False


@pytest.fixture
def mock_thread_manager():
    """创建模拟Thread管理器"""
    return MockThreadManager()


@pytest.fixture
def memory_metadata_store():
    """创建内存元数据存储"""
    return MemoryThreadMetadataStore()


@pytest.fixture
def memory_checkpoint_store():
    """创建内存checkpoint存储"""
    return MemoryCheckpointStore()


@pytest.fixture
def checkpoint_manager(memory_checkpoint_store):
    """创建checkpoint管理器"""
    return CheckpointManager(memory_checkpoint_store)


@pytest.fixture
def session_manager():
    """创建session管理器"""
    # 使用临时目录进行测试
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    return SessionManager(temp_dir)


@pytest.fixture
def session_thread_mapper(
    session_manager, 
    mock_thread_manager,
    memory_metadata_store
):
    """创建session-thread映射器"""
    return MemorySessionThreadMapper(session_manager, mock_thread_manager)


@pytest.fixture
def query_manager(mock_thread_manager):
    """创建查询管理器"""
    return ThreadQueryManager(mock_thread_manager)


@pytest.fixture
def cache_manager():
    """创建缓存管理器"""
    return ThreadCacheManager(max_size=100, default_ttl=300)


@pytest.fixture
def sdk_adapter(
    session_thread_mapper,
    checkpoint_manager,
    mock_thread_manager,
    session_manager,
    query_manager
):
    """创建SDK适配器"""
    return CompleteLangGraphSDKAdapter(
        session_thread_mapper,
        checkpoint_manager,
        mock_thread_manager,
        session_manager,
        query_manager
    )


@pytest.mark.asyncio
async def test_thread_creation_and_mapping(
    sdk_adapter,
    session_thread_mapper,
    mock_thread_manager
):
    """测试Thread创建和映射功能"""
    # 创建thread
    result = await sdk_adapter.threads_create(
        graph_id="test_graph",
        metadata={"test": "value"},
        initial_state={"messages": [], "current_step": "start"}
    )
    
    assert "thread_id" in result
    assert "session_id" in result
    assert result["graph_id"] == "test_graph"
    
    thread_id = result["thread_id"]
    
    # 验证thread存在
    thread_info = await mock_thread_manager.get_thread_info(thread_id)
    assert thread_info is not None
    assert thread_info["graph_id"] == "test_graph"
    
    # 验证session-thread映射
    session_id = await session_thread_mapper.get_session_for_thread(thread_id)
    assert session_id is not None
    
    thread_id_from_session = await session_thread_mapper.get_thread_for_session(session_id)
    assert thread_id_from_session == thread_id


@pytest.mark.asyncio
async def test_thread_state_management(
    sdk_adapter,
    mock_thread_manager,
    checkpoint_manager
):
    """测试Thread状态管理"""
    # 创建thread
    result = await sdk_adapter.threads_create(
        graph_id="state_test_graph",
        initial_state={"messages": ["hello"], "step": 1}
    )
    
    thread_id = result["thread_id"]
    assert thread_id is not None
    
    # 获取初始状态
    initial_state = await sdk_adapter.threads_get_state(thread_id)
    assert initial_state["messages"] == ["hello"]
    assert initial_state["step"] == 1
    
    # 更新状态
    update_result = await sdk_adapter.threads_update_state(
        thread_id,
        {"messages": ["hello", "world"], "step": 2},
        metadata={"updated_by": "test"}
    )
    
    assert update_result["success"] is True
    assert update_result["thread_id"] == thread_id
    
    # 获取更新后的状态
    updated_state = await sdk_adapter.threads_get_state(thread_id)
    assert updated_state["messages"] == ["hello", "world"]
    assert updated_state["step"] == 2
    
    # 验证checkpoint被创建
    checkpoints = await checkpoint_manager.list_checkpoints(thread_id)
    assert len(checkpoints) >= 2  # 初始状态 + 更新状态


@pytest.mark.asyncio
async def test_thread_history(
    sdk_adapter,
    mock_thread_manager
):
    """测试Thread历史功能"""
    # 创建thread
    result = await sdk_adapter.threads_create(
        graph_id="history_test_graph",
        initial_state={"value": 0}
    )
    
    thread_id = result["thread_id"]
    
    # 更新几次状态以创建历史
    for i in range(1, 4):
        await sdk_adapter.threads_update_state(
            thread_id,
            {"value": i, "step": f"step_{i}"}
        )
        await asyncio.sleep(0.01)  # 确保时间戳不同
    
    # 获取历史
    history = await sdk_adapter.threads_get_state_history(thread_id)
    
    assert len(history) >= 3 # 初始 + 3次更新
    
    # 验证历史按时间倒序排列（最新在前）
    assert history[0]["values"]["value"] == 3  # 最新的值
    assert history[-1]["values"]["value"] == 0  # 最初的值


@pytest.mark.asyncio
async def test_thread_search_and_query(
    sdk_adapter,
    query_manager,
    mock_thread_manager
):
    """测试Thread搜索和查询功能"""
    # 创建多个threads用于测试搜索
    thread_ids = []
    for i in range(5):
        metadata = {"category": f"cat_{i % 2}", "index": i}
        if i == 0:
            metadata["special"] = True
        
        result = await sdk_adapter.threads_create(
            graph_id=f"search_test_graph_{i}",
            metadata=metadata,
            initial_state={"counter": i}
        )
        thread_ids.append(result["thread_id"])
    
    # 测试基本搜索
    search_results = await sdk_adapter.threads_search(status="active")
    assert len(search_results) >= 5
    
    # 测试带过滤条件的搜索
    cat0_results = await sdk_adapter.threads_search(
        metadata={"category": "cat_0"}
    )
    assert len(cat0_results) >= 3  # 应该有索引为0, 2, 4的threads
    
    # 测试高级搜索
    advanced_results = await query_manager.search_threads_advanced(
        text="special",
        sort_by="created_at",
        sort_order="desc"
    )
    assert advanced_results["total_count"] >= 1


@pytest.mark.asyncio
async def test_thread_copy(
    sdk_adapter,
    mock_thread_manager
):
    """测试Thread复制功能"""
    # 创建原始thread
    original_result = await sdk_adapter.threads_create(
        graph_id="original_graph",
        metadata={"original": True, "category": "test"},
        initial_state={"data": "original_data", "step": 1}
    )
    
    original_thread_id = original_result["thread_id"]
    
    # 复制thread
    copy_result = await sdk_adapter.threads_copy(
        original_thread_id,
        new_metadata={"copied": True}
    )
    
    copy_thread_id = copy_result["thread_id"]
    assert copy_thread_id != original_thread_id
    
    # 验证复制的thread具有相同的初始状态
    original_state = await sdk_adapter.threads_get_state(original_thread_id)
    copy_state = await sdk_adapter.threads_get_state(copy_thread_id)
    
    assert original_state["data"] == copy_state["data"]
    assert original_state["step"] == copy_state["step"]
    
    # 验证复制的thread具有正确的元数据
    copy_info = await mock_thread_manager.get_thread_info(copy_thread_id)
    assert copy_info is not None
    assert copy_info["metadata"]["copied"] is True
    assert copy_info["metadata"]["copied_from"] == original_thread_id


@pytest.mark.asyncio
async def test_thread_deletion(
    sdk_adapter,
    session_thread_mapper,
    mock_thread_manager
):
    """测试Thread删除功能"""
    # 创建thread
    result = await sdk_adapter.threads_create(
        graph_id="delete_test_graph",
        initial_state={"data": "test"}
    )
    
    thread_id = result["thread_id"]
    session_id = result["session_id"]
    
    # 验证thread存在
    assert await mock_thread_manager.thread_exists(thread_id) is True
    assert await session_thread_mapper.get_thread_for_session(session_id) == thread_id
    
    # 删除thread
    delete_success = await sdk_adapter.threads_delete(thread_id)
    assert delete_success is True
    
    # 验证thread被删除
    assert await mock_thread_manager.thread_exists(thread_id) is False
    assert await session_thread_mapper.get_thread_for_session(session_id) is None


@pytest.mark.asyncio
async def test_cache_manager_functionality(cache_manager):
    """测试缓存管理器功能"""
    from src.infrastructure.threads.cache_manager import CacheEntryType
    
    # 测试设置和获取
    await cache_manager.set("test_key", {"data": "value"}, CacheEntryType.THREAD_STATE)
    
    value = await cache_manager.get("test_key")
    assert value == {"data": "value"}
    
    # 测试过期
    await cache_manager.set("expiring_key", "exp_value", CacheEntryType.THREAD_STATE, ttl=1)
    await asyncio.sleep(1.1)  # 等待过期
    
    expired_value = await cache_manager.get("expiring_key")
    assert expired_value is None
    
    # 测试指标
    metrics = await cache_manager.get_metrics()
    assert metrics["hits"] >= 1
    assert metrics["misses"] >= 1


@pytest.mark.asyncio
async def test_performance_monitor():
    """测试性能监控器"""
    monitor = PerformanceMonitor()
    
    # 记录一些操作
    monitor.record_operation("test_op", 0.1, success=True, metadata={"size": 100})
    monitor.record_operation("test_op", 0.2, success=True, metadata={"size": 200})
    monitor.record_operation("test_op", 0.05, success=False, metadata={"size": 50})
    
    stats = monitor.get_performance_stats()
    
    assert stats["total_operations"] == 3
    assert stats["success_rate"] == 2/3
    assert stats["average_duration"] == 0.35 / 3 # (0.1 + 0.2 + 0.05) / 3
    
    # 检查操作类型统计
    ops_by_type = stats["operations_by_type"]
    assert "test_op" in ops_by_type
    assert ops_by_type["test_op"]["count"] == 3


@pytest.mark.asyncio
async def test_sdk_adapter_comprehensive_workflow(
    sdk_adapter,
    session_thread_mapper,
    mock_thread_manager,
    checkpoint_manager
):
    """测试SDK适配器综合工作流程"""
    # 1. 创建thread
    create_result = await sdk_adapter.threads_create(
        graph_id="workflow_test",
        metadata={"workflow": "test", "version": "1.0"},
        initial_state={"messages": [], "context": {}}
    )
    
    thread_id = create_result["thread_id"]
    assert thread_id is not None
    
    # 2. 更新状态多次
    for i in range(3):
        update_result = await sdk_adapter.threads_update_state(
            thread_id,
            {
                "messages": [f"message_{i}"],
                "step": i,
                "context": {"iteration": i}
            },
            metadata={"step": i}
        )
        assert update_result["success"] is True
    
    # 3. 获取最新状态
    latest_state = await sdk_adapter.threads_get_state(thread_id)
    assert latest_state["step"] == 2  # 最后一步
    assert latest_state["messages"] == ["message_2"]
    
    # 4. 获取历史
    history = await sdk_adapter.threads_get_state_history(thread_id, limit=5)
    assert len(history) >= 4  # 初始 + 3次更新
    
    # 5. 搜索threads
    search_results = await sdk_adapter.threads_search(
        metadata={"workflow": "test"}
    )
    matching_threads = [t for t in search_results if t["thread_id"] == thread_id]
    assert len(matching_threads) == 1
    
    # 6. 复制thread
    copy_result = await sdk_adapter.threads_copy(thread_id)
    copy_thread_id = copy_result["thread_id"]
    assert copy_thread_id != thread_id
    
    # 7. 验证复制的thread状态
    copy_state = await sdk_adapter.threads_get_state(copy_thread_id)
    assert copy_state["step"] == 2  # 应该复制最新状态
    
    # 8. 删除复制的thread
    delete_success = await sdk_adapter.threads_delete(copy_thread_id)
    assert delete_success is True
    
    # 9. 验证原thread仍然存在
    original_exists = await mock_thread_manager.thread_exists(thread_id)
    assert original_exists is True
    
    # 10. 验证原thread状态未受影响
    final_state = await sdk_adapter.threads_get_state(thread_id)
    assert final_state["step"] == 2