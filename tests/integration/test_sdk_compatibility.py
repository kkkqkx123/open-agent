"""SDK兼容性集成测试"""

import asyncio
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.application.threads.query_manager import ThreadQueryManager
from .test_utils import MockSessionManager
from src.domain.threads.interfaces import IThreadManager
from src.infrastructure.threads.metadata_store import MemoryThreadMetadataStore
from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore
from src.application.checkpoint.manager import CheckpointManager
from src.infrastructure.langgraph.sdk_adapter import CompleteLangGraphSDKAdapter
from src.infrastructure.threads.cache_manager import ThreadCacheManager, PerformanceMonitor
from src.domain.checkpoint.config import CheckpointConfig


class MockThreadManager(IThreadManager):
    """模拟Thread管理器用于测试"""

    def __init__(self) -> None:
        self._threads: Dict[str, Dict[str, Any]] = {}
        self._states: Dict[str, Dict[str, Any]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        import uuid
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        self._threads[thread_id] = {
            "thread_id": thread_id,
            "graph_id": graph_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "metadata": metadata or {}
        }
        self._states[thread_id] = metadata.get("initial_state", {}) if metadata else {}
        return thread_id
    
    async def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]:
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
    
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> list[Dict[str, Any]]:
        if filters:
            # 简单的过滤实现
            result: list[Dict[str, Any]] = []
            for thread in self._threads.values():
                match = True
                if "status" in filters and thread.get("status") != filters["status"]:
                    match = False
                if match and limit:
                    if len(result) >= limit:
                        break
                if match:
                    result.append(thread)
            return result
        return list(self._threads.values())
    
    async def thread_exists(self, thread_id: str) -> bool:
        return thread_id in self._threads
    
    async def get_thread_state(self, thread_id: str) -> Dict[str, Any]:
        return self._states.get(thread_id, {})
    
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        if thread_id in self._states:
            self._states[thread_id].update(state)
        else:
            self._states[thread_id] = state
        return True

    async def fork_thread(
        self,
        source_thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        # 模拟fork thread功能
        import uuid
        new_thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        source_thread = self._threads.get(source_thread_id)
        if not source_thread:
            raise ValueError(f"源thread不存在: {source_thread_id}")
        
        # 复制源thread的信息
        self._threads[new_thread_id] = {
            "thread_id": new_thread_id,
            "graph_id": source_thread.get("graph_id", ""),
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "metadata": {
                "branch_name": branch_name,
                "source_thread_id": source_thread_id,
                "source_checkpoint_id": checkpoint_id,
                "branch_type": "fork",
                **(metadata or {})
            }
        }
        # 复制状态
        self._states[new_thread_id] = self._states.get(source_thread_id, {}).copy()
        return new_thread_id

    async def create_thread_snapshot(
        self,
        thread_id: str,
        snapshot_name: str,
        description: Optional[str] = None
    ) -> str:
        # 模拟创建thread快照功能
        import uuid
        snapshot_id = f"snapshot_{uuid.uuid4().hex[:8]}"
        return snapshot_id

    async def rollback_thread(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> bool:
        # 模拟回滚thread功能
        if thread_id in self._threads:
            return True
        return False

    async def get_thread_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        # 模拟获取thread历史记录功能
        return []
    
    async def create_thread_from_config(self, config_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """从配置文件创建Thread"""
        import uuid
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        graph_id = Path(config_path).stem  # 从配置文件名提取graph_id
        self._threads[thread_id] = {
            "thread_id": thread_id,
            "graph_id": graph_id,
            "config_path": config_path,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "metadata": metadata or {}
        }
        self._states[thread_id] = {}
        return thread_id

    async def execute_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行工作流"""
        if thread_id not in self._threads:
            raise ValueError(f"Thread不存在: {thread_id}")
        return {"success": True, "thread_id": thread_id, "state": self._states.get(thread_id, {})}

    async def stream_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:  # type: ignore
        """流式执行工作流"""
        if thread_id not in self._threads:
            raise ValueError(f"Thread不存在: {thread_id}")
        yield {"thread_id": thread_id, "state": self._states.get(thread_id, {})}


@pytest.fixture
def mock_thread_manager() -> MockThreadManager:
    """创建模拟Thread管理器"""
    return MockThreadManager()


@pytest.fixture
def memory_metadata_store() -> MemoryThreadMetadataStore:
    """创建内存元数据存储"""
    return MemoryThreadMetadataStore()


@pytest.fixture
def memory_checkpoint_store() -> MemoryCheckpointStore:
    """创建内存checkpoint存储"""
    return MemoryCheckpointStore()


@pytest.fixture
def checkpoint_manager(memory_checkpoint_store: MemoryCheckpointStore) -> CheckpointManager:
    """创建checkpoint管理器"""
    config = CheckpointConfig(
        enabled=True,
        storage_type="memory",
        auto_save=True,
        save_interval=1,
        max_checkpoints=100
    )
    return CheckpointManager(memory_checkpoint_store, config)


@pytest.fixture
def session_manager() -> MockSessionManager:
    """创建session管理器"""
    return MockSessionManager()


# Session-Thread映射器已删除，Session将直接管理多个Thread


@pytest.fixture
def query_manager(mock_thread_manager: MockThreadManager) -> ThreadQueryManager:
    """创建查询管理器"""
    return ThreadQueryManager(mock_thread_manager)


@pytest.fixture
def sdk_adapter(
    checkpoint_manager: CheckpointManager,
    mock_thread_manager: MockThreadManager,
    session_manager: MockSessionManager,
    query_manager: ThreadQueryManager
) -> CompleteLangGraphSDKAdapter:
    """创建SDK适配器"""
    return CompleteLangGraphSDKAdapter(
        checkpoint_manager,
        mock_thread_manager,
        session_manager,
        query_manager
    )


@pytest.mark.asyncio
async def test_sdk_threads_create_compatibility(sdk_adapter: CompleteLangGraphSDKAdapter) -> None:
    """测试threads_create方法的SDK兼容性"""
    # 测试基本创建
    result = await sdk_adapter.threads_create("test_graph_1")
    assert "thread_id" in result
    assert result["graph_id"] == "test_graph_1"
    assert "created_at" in result
    
    # 测试带metadata的创建
    result2 = await sdk_adapter.threads_create(
        "test_graph_2",
        metadata={"description": "test thread", "priority": "high"}
    )
    assert result2["graph_id"] == "test_graph_2"
    
    # 测试带初始状态的创建
    initial_state = {"messages": [{"type": "human", "content": "hello"}], "step": 0}
    result3 = await sdk_adapter.threads_create(
        "test_graph_3",
        initial_state=initial_state
    )
    assert result3["graph_id"] == "test_graph_3"
    
    # 验证初始状态被正确保存
    saved_state = await sdk_adapter.threads_get_state(result3["thread_id"])
    print(f"Saved state: {saved_state}")
    assert saved_state["messages"] == [{"type": "human", "content": "hello"}]
    assert saved_state["step"] == 0


@pytest.mark.asyncio
async def test_sdk_threads_get_state_compatibility(sdk_adapter: CompleteLangGraphSDKAdapter) -> None:
    """测试threads_get_state方法的SDK兼容性"""
    # 创建thread并设置状态
    result = await sdk_adapter.threads_create(
        "state_test_graph",
        initial_state={"value": 42, "messages": ["initial"]}
    )
    
    thread_id = result["thread_id"]
    
    # 获取最新状态
    state = await sdk_adapter.threads_get_state(thread_id)
    assert state["value"] == 42
    assert state["messages"] == ["initial"]
    
    # 更新状态
    await sdk_adapter.threads_update_state(
        thread_id,
        {"value": 100, "messages": ["initial", "updated"], "new_field": "test"}
    )
    
    # 再次获取状态，验证更新
    updated_state = await sdk_adapter.threads_get_state(thread_id)
    assert updated_state["value"] == 100
    assert "updated" in updated_state["messages"]
    assert updated_state["new_field"] == "test"


@pytest.mark.asyncio
async def test_sdk_threads_update_state_compatibility(sdk_adapter: CompleteLangGraphSDKAdapter) -> None:
    """测试threads_update_state方法的SDK兼容性"""
    # 创建thread
    result = await sdk_adapter.threads_create(
        "update_test_graph",
        initial_state={"counter": 0, "items": []}
    )
    
    thread_id = result["thread_id"]
    
    # 更新状态
    update_result = await sdk_adapter.threads_update_state(
        thread_id,
        {"counter": 1, "items": ["item1"]},
        metadata={"update_reason": "test", "step": 1}
    )
    
    assert update_result["success"] is True
    assert update_result["thread_id"] == thread_id
    assert "checkpoint_id" in update_result
    
    # 验证状态已更新
    new_state = await sdk_adapter.threads_get_state(thread_id)
    assert new_state["counter"] == 1
    assert new_state["items"] == ["item1"]
    
    # 再次更新
    update_result2 = await sdk_adapter.threads_update_state(
        thread_id,
        {"counter": 2, "items": ["item1", "item2"]},
        metadata={"update_reason": "test2", "step": 2}
    )
    
    assert update_result2["success"] is True
    assert update_result2["thread_id"] == thread_id
    
    # 验证状态再次更新
    final_state = await sdk_adapter.threads_get_state(thread_id)
    assert final_state["counter"] == 2
    assert final_state["items"] == ["item1", "item2"]


@pytest.mark.asyncio
async def test_sdk_threads_get_state_history_compatibility(sdk_adapter: CompleteLangGraphSDKAdapter) -> None:
    """测试threads_get_state_history方法的SDK兼容性"""
    # 创建thread
    result = await sdk_adapter.threads_create(
        "history_test_graph",
        initial_state={"history": [0]}
    )
    
    thread_id = result["thread_id"]
    
    # 添加几个状态更新以创建历史
    for i in range(1, 5):
        await sdk_adapter.threads_update_state(
            thread_id,
            {"history": list(range(i + 1)), "step": i}
        )
        await asyncio.sleep(0.01)  # 确保时间戳不同
    
    # 获取历史
    history = await sdk_adapter.threads_get_state_history(thread_id)
    
    # 验证历史记录数量（初始状态 + 4次更新）
    assert len(history) >= 5
    
    # 验证历史按时间倒序排列（最新在前）
    assert history[0]["values"]["step"] == 4  # 最新的步骤
    assert history[-1]["values"]["history"][0] == 0  # 最初的值
    
    # 测试限制返回数量
    limited_history = await sdk_adapter.threads_get_state_history(thread_id, limit=2)
    assert len(limited_history) == 2
    assert limited_history[0]["values"]["step"] == 4  # 仍然是最新的
    assert limited_history[1]["values"]["step"] == 3


@pytest.mark.asyncio
async def test_sdk_threads_list_compatibility(sdk_adapter: CompleteLangGraphSDKAdapter) -> None:
    """测试threads_list方法的SDK兼容性"""
    # 创建多个threads
    thread_ids = []
    for i in range(5):
        result = await sdk_adapter.threads_create(f"list_test_graph_{i}")
        thread_ids.append(result["thread_id"])
    
    # 列出所有threads
    all_threads = await sdk_adapter.threads_list()
    
    # 验证数量
    created_threads = [t for t in all_threads if any(tid in t["thread_id"] for tid in thread_ids)]
    assert len(created_threads) >= 5
    
    # 验证每个thread都有必要字段
    for thread in created_threads:
        assert "thread_id" in thread
        assert "graph_id" in thread
        assert "created_at" in thread
        assert "last_active" in thread


@pytest.mark.asyncio
async def test_sdk_threads_search_compatibility(sdk_adapter: CompleteLangGraphSDKAdapter) -> None:
    """测试threads_search方法的SDK兼容性"""
    # 创建带有不同元数据的threads
    thread_ids = []
    for i in range(6):
        metadata = {
            "category": f"cat_{i % 3}",  # cat_0, cat_1, cat_2 循环
            "priority": "high" if i < 3 else "low",
            "index": i
        }
        result = await sdk_adapter.threads_create(
            f"search_test_graph_{i}",
            metadata=metadata
        )
        thread_ids.append(result["thread_id"])
    
    # 按状态搜索
    active_threads = await sdk_adapter.threads_search(status="active")
    active_matching = [t for t in active_threads if t["thread_id"] in thread_ids]
    assert len(active_matching) >= 6
    
    # 按元数据搜索
    high_priority = await sdk_adapter.threads_search(
        metadata={"priority": "high"}
    )
    high_priority_matching = [t for t in high_priority if t["thread_id"] in thread_ids]
    assert len(high_priority_matching) >= 3  # 前3个是high priority
    
    # 按category搜索
    cat0_threads = await sdk_adapter.threads_search(
        metadata={"category": "cat_0"}
    )
    cat0_matching = [t for t in cat0_threads if t["thread_id"] in thread_ids]
    assert len(cat0_matching) >= 2  # 索引0和3是cat_0
    
    # 测试限制数量
    limited_result = await sdk_adapter.threads_search(
        metadata={"priority": "high"},
        limit=2
    )
    assert len(limited_result) <= 2


@pytest.mark.asyncio
async def test_sdk_threads_copy_compatibility(sdk_adapter: CompleteLangGraphSDKAdapter) -> None:
    """测试threads_copy方法的SDK兼容性"""
    # 创建原始thread
    original_result = await sdk_adapter.threads_create(
        "original_graph",
        metadata={"original": True, "category": "copy_test"},
        initial_state={"data": "original", "version": 1, "items": [1, 2, 3]}
    )
    
    original_thread_id = original_result["thread_id"]
    
    # 复制thread
    copy_result = await sdk_adapter.threads_copy(
        original_thread_id,
        new_metadata={"copied": True, "source": "test"}
    )
    
    copy_thread_id = copy_result["thread_id"]
    assert copy_thread_id != original_thread_id
    
    # 验证复制的thread有相同的初始状态
    original_state = await sdk_adapter.threads_get_state(original_thread_id)
    copy_state = await sdk_adapter.threads_get_state(copy_thread_id)
    
    assert original_state["data"] == copy_state["data"]
    assert original_state["version"] == copy_state["version"]
    assert original_state["items"] == copy_state["items"]
    
    # 验证复制的thread有正确的元数据
    copy_info = await sdk_adapter.query_manager.thread_manager.get_thread_info(copy_thread_id)
    assert copy_info is not None
    assert copy_info["metadata"]["copied"] is True
    assert copy_info["metadata"]["source"] == "test"
    assert copy_info["metadata"]["original"]  # 继承的元数据


@pytest.mark.asyncio
async def test_sdk_threads_delete_compatibility(sdk_adapter: CompleteLangGraphSDKAdapter) -> None:
    """测试threads_delete方法的SDK兼容性"""
    # 创建thread
    result = await sdk_adapter.threads_create(
        "delete_test_graph",
        initial_state={"will_be_deleted": True}
    )
    
    thread_id = result["thread_id"]
    
    # 验证thread存在
    all_threads = await sdk_adapter.threads_list()
    thread_exists_before = any(t["thread_id"] == thread_id for t in all_threads)
    assert thread_exists_before is True
    
    # 删除thread
    delete_success = await sdk_adapter.threads_delete(thread_id)
    assert delete_success is True
    
    # 验证thread不存在
    all_threads_after = await sdk_adapter.threads_list()
    thread_exists_after = any(t["thread_id"] == thread_id for t in all_threads_after)
    assert thread_exists_after is False


@pytest.mark.asyncio
async def test_sdk_threads_update_metadata_compatibility(sdk_adapter: CompleteLangGraphSDKAdapter) -> None:
    """测试threads_update_metadata方法的SDK兼容性"""
    # 创建thread
    result = await sdk_adapter.threads_create(
        "metadata_test_graph",
        metadata={"initial": "value", "category": "test"}
    )
    
    thread_id = result["thread_id"]
    
    # 更新元数据
    update_success = await sdk_adapter.threads_update_metadata(
        thread_id,
        {"updated_field": "new_value", "category": "updated_category"}
    )
    
    assert update_success is True
    
    # 验证元数据已更新
    thread_info = await sdk_adapter.query_manager.thread_manager.get_thread_info(thread_id)
    assert thread_info is not None
    metadata = thread_info["metadata"]
    
    assert metadata["initial"] == "value"  # 保留原始值
    assert metadata["updated_field"] == "new_value"  # 新增值
    assert metadata["category"] == "updated_category"  # 更新的值


@pytest.mark.asyncio
async def test_sdk_threads_stream_events_compatibility(sdk_adapter: CompleteLangGraphSDKAdapter) -> None:
    """测试threads_stream_events方法的SDK兼容性"""
    # 创建thread
    result = await sdk_adapter.threads_create(
        "stream_test_graph",
        initial_state={"event_counter": 0}
    )
    
    thread_id = result["thread_id"]
    
    # 添加一些状态更新以创建事件
    for i in range(3):
        await sdk_adapter.threads_update_state(
            thread_id,
            {"event_counter": i + 1, "event_id": f"event_{i}"}
        )
        await asyncio.sleep(0.01)
    
    # 测试流式获取事件
    events_collected = []
    async for event in sdk_adapter.threads_stream_events(thread_id):
        events_collected.append(event)
        if len(events_collected) >= 4:  # 初始 + 3次更新
            break
    
    # 验证事件数量
    assert len(events_collected) >= 4  # 至少有初始状态 + 3次更新
    
    # 验证事件结构
    for event in events_collected:
        assert "event" in event
        assert "thread_id" in event
        assert "checkpoint_id" in event
        assert "state" in event
        assert "metadata" in event
        assert "timestamp" in event
        assert event["thread_id"] == thread_id
        assert event["event"] == "checkpoint"
    
    # 验证事件按时间倒序排列（最新在前）
    assert events_collected[0]["state"]["event_counter"] >= events_collected[-1]["state"]["event_counter"]


@pytest.mark.asyncio
async def test_sdk_comprehensive_workflow(sdk_adapter: CompleteLangGraphSDKAdapter) -> None:
    """测试SDK综合工作流程的兼容性"""
    # 1. 创建thread
    create_result = await sdk_adapter.threads_create(
        "comprehensive_test",
        metadata={"workflow": "comprehensive", "version": "1.0"},
        initial_state={
            "messages": [{"role": "system", "content": "initialized"}],
            "context": {"step": 0, "attempts": 0}
        }
    )
    
    thread_id = create_result["thread_id"]
    assert thread_id is not None
    
    # 2. 更新状态几次
    for i in range(3):
        update_result = await sdk_adapter.threads_update_state(
            thread_id,
            {
                "messages": [
                    {"role": "system", "content": "initialized"},
                    {"role": f"step_{i}", "content": f"content_{i}"}
                ],
                "context": {"step": i + 1, "attempts": i + 1, "completed": i == 2}
            },
            metadata={"step": i + 1, "timestamp": datetime.now().isoformat()}
        )
        assert update_result["success"] is True
        await asyncio.sleep(0.01)  # 确保时间戳不同
    
    # 3. 获取最新状态
    latest_state = await sdk_adapter.threads_get_state(thread_id)
    assert latest_state["context"]["step"] == 3
    assert latest_state["context"]["completed"] is True
    
    # 4. 获取历史
    history = await sdk_adapter.threads_get_state_history(thread_id)
    assert len(history) >= 4  # 初始 + 3次更新
    
    # 5. 搜索threads
    search_results = await sdk_adapter.threads_search(
        metadata={"workflow": "comprehensive"}
    )
    matching_threads = [t for t in search_results if t["thread_id"] == thread_id]
    assert len(matching_threads) == 1
    
    # 6. 获取所有threads并验证
    all_threads = await sdk_adapter.threads_list()
    thread_in_list = next((t for t in all_threads if t["thread_id"] == thread_id), None)
    assert thread_in_list is not None
    assert thread_in_list["graph_id"] == "comprehensive_test"
    
    # 7. 复制thread
    copy_result = await sdk_adapter.threads_copy(
        thread_id,
        new_metadata={"copied_from_workflow": "comprehensive"}
    )
    copy_thread_id = copy_result["thread_id"]
    assert copy_thread_id != thread_id
    
    # 8. 验证复制的thread
    copy_state = await sdk_adapter.threads_get_state(copy_thread_id)
    assert copy_state["context"]["step"] == 3  # 应该复制最新状态
    
    # 9. 更新复制的thread以验证独立性
    await sdk_adapter.threads_update_state(
        copy_thread_id,
        {"context": {"step": 4, "copied_thread": True}}
    )
    
    # 验证原thread未受影响
    original_after_copy_update = await sdk_adapter.threads_get_state(thread_id)
    assert original_after_copy_update["context"]["step"] == 3  # 仍为3
    assert "copied_thread" not in original_after_copy_update["context"]
    
    # 验证复制thread已更新
    copy_after_update = await sdk_adapter.threads_get_state(copy_thread_id)
    assert copy_after_update["context"]["step"] == 4
    assert copy_after_update["context"]["copied_thread"] is True
    
    # 10. 流式获取事件
    event_count = 0
    async for event in sdk_adapter.threads_stream_events(thread_id, events=["checkpoint"]):
        event_count += 1
        if event_count >= 5:  # 限制获取数量
            break
    
    assert event_count >= 4  # 应该有多个事件
    
    # 11. 清理：删除复制的thread
    delete_success = await sdk_adapter.threads_delete(copy_thread_id)
    assert delete_success is True
    
    # 12. 验证原thread仍然存在
    final_state = await sdk_adapter.threads_get_state(thread_id)
    assert final_state["context"]["step"] == 3


@pytest.mark.asyncio
async def test_sdk_error_handling(sdk_adapter: CompleteLangGraphSDKAdapter) -> None:
    """测试SDK错误处理"""
    # 测试获取不存在thread的状态
    with pytest.raises(ValueError):
        await sdk_adapter.threads_get_state("nonexistent_thread_12345")
    
    # 测试更新不存在thread的状态
    with pytest.raises(RuntimeError):
        await sdk_adapter.threads_update_state("nonexistent_thread_12345", {"test": "value"})
    
    # 测试复制不存在的thread
    with pytest.raises(ValueError):
        await sdk_adapter.threads_copy("nonexistent_thread_12345")
    
    # 测试删除不存在的thread（应该返回False而不是抛出异常）
    delete_result = await sdk_adapter.threads_delete("nonexistent_thread_12345")
    assert delete_result is False