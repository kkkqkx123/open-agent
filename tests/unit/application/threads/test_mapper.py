"""Session-Thread映射器单元测试"""

import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from src.application.threads.session_thread_mapper import (
    ISessionThreadMapper,
    SessionThreadMapper,
    MemorySessionThreadMapper
)
from src.domain.threads.interfaces import IThreadManager
from src.application.sessions.manager import ISessionManager


class TestSessionThreadMapper:
    """Session-Thread映射器测试类"""
    
    @pytest.fixture
    def mock_session_manager(self):
        """模拟Session管理器"""
        manager = MagicMock(spec=ISessionManager)
        # 设置side_effect以支持所有测试场景
        # 注意：side_effect会按顺序返回值
        manager.create_session.side_effect = [
            "session_test123",  # 用于直接返回值的测试
            "session_test456",  # 用于save_and_load_mappings测试
            "session_1",        # 用于multiple_mappings测试
            "session_2",        # 用于multiple_mappings测试
            "session_test123",  # 用于其他需要特定返回值的测试
        ]
        return manager
    
    @pytest.fixture
    def mock_thread_manager(self):
        """模拟Thread管理器"""
        manager = AsyncMock(spec=IThreadManager)
        # 设置side_effect以支持所有测试场景
        manager.create_thread.side_effect = [
            "thread_test123",   # 用于直接返回值的测试
            "thread_test456",   # 用于save_and_load_mappings测试
            "thread_1",         # 用于multiple_mappings测试
            "thread_2",         # 用于multiple_mappings测试
            "thread_test123",   # 用于其他需要特定返回值的测试
        ]
        return manager
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def mapper(self, mock_session_manager, mock_thread_manager, temp_dir):
        """创建Session-Thread映射器实例"""
        # 修改mock以返回不同的值，避免覆盖
        mock_session_manager.create_session.side_effect = ["session_test123", "session_test456"]
        mock_thread_manager.create_thread.side_effect = ["thread_test123", "thread_test456"]
        
        mapper = SessionThreadMapper(mock_session_manager, mock_thread_manager, temp_dir)
        # 通过调用方法创建初始映射关系
        import asyncio
        # 使用asyncio.run_until_complete_or_timeout或直接调用
        # 但这里我们直接模拟已有的映射
        mapper._mappings["session_test123"] = "thread_test123"
        mapper._reverse_mappings["thread_test123"] = "session_test123"
        return mapper
    
    @pytest.fixture
    def memory_mapper(self, mock_session_manager, mock_thread_manager):
        """创建内存Session-Thread映射器实例"""
        # 重置mock以确保测试隔离
        memory_mapper = MemorySessionThreadMapper(mock_session_manager, mock_thread_manager)
        # 通过调用方法创建初始映射关系
        memory_mapper._mappings["session_test123"] = "thread_test123"
        memory_mapper._reverse_mappings["thread_test123"] = "session_test123"
        return memory_mapper
    
    @pytest.mark.asyncio
    async def test_create_session_with_thread_success(self, mapper, mock_session_manager, mock_thread_manager):
        """测试成功创建Session和Thread"""
        # 准备测试数据
        workflow_config_path = "configs/workflows/test_workflow.yaml"
        thread_metadata = {"name": "test_thread"}
        agent_config = {"model": "gpt-4"}
        initial_state = {"messages": []}
        
        # 执行测试
        session_id, thread_id = await mapper.create_session_with_thread(
            workflow_config_path,
            thread_metadata,
            agent_config,
            initial_state
        )
        
        # 验证结果
        assert session_id == "session_test123"
        assert thread_id == "thread_test123"
        
        # 验证调用
        mock_session_manager.create_session.assert_called_once_with(
            workflow_config_path,
            agent_config,
            initial_state
        )
        mock_thread_manager.create_thread.assert_called_once_with(
            "test_workflow",
            thread_metadata
        )
    
    @pytest.mark.asyncio
    async def test_create_session_with_thread_default_metadata(self, mapper, mock_session_manager, mock_thread_manager):
        """测试创建Session和Thread（使用默认元数据）"""
        # 准备测试数据
        workflow_config_path = "configs/workflows/test_workflow.yaml"
        
        # 执行测试
        session_id, thread_id = await mapper.create_session_with_thread(workflow_config_path)
        
        # 验证结果
        assert session_id == "session_test123"
        assert thread_id == "thread_test123"
        
        # 验证调用
        mock_session_manager.create_session.assert_called_once()
        mock_thread_manager.create_thread.assert_called_once_with(
            "test_workflow",
            {}
        )
    
    @pytest.mark.asyncio
    async def test_get_thread_for_session_exists(self, mapper):
        """测试获取存在的Session对应的Thread ID"""
        # 执行测试
        result = await mapper.get_thread_for_session("session_test123")
        
        # 验证结果
        assert result == "thread_test123"
    
    @pytest.mark.asyncio
    async def test_get_thread_for_session_not_exists(self, mapper):
        """测试获取不存在的Session对应的Thread ID"""
        # 执行测试
        result = await mapper.get_thread_for_session("nonexistent_session")
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_session_for_thread_exists(self, mapper):
        """测试获取存在的Thread对应的Session ID"""
        # 执行测试
        result = await mapper.get_session_for_thread("thread_test123")
        
        # 验证结果
        assert result == "session_test123"
    
    @pytest.mark.asyncio
    async def test_get_session_for_thread_not_exists(self, mapper):
        """测试获取不存在的Thread对应的Session ID"""
        # 执行测试
        result = await mapper.get_session_for_thread("nonexistent_thread")
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_mapping_success(self, mapper):
        """测试成功删除映射关系"""
        # 执行测试
        result = await mapper.delete_mapping("session_test123")
        
        # 验证结果
        assert result is True
        
        # 验证映射关系已删除
        assert await mapper.get_thread_for_session("session_test123") is None
        assert await mapper.get_session_for_thread("thread_test123") is None
    
    @pytest.mark.asyncio
    async def test_delete_mapping_not_exists(self, mapper):
        """测试删除不存在的映射关系"""
        # 执行测试
        result = await mapper.delete_mapping("nonexistent_session")
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_mappings(self, mapper):
        """测试列出所有映射关系"""
        # 执行测试
        result = await mapper.list_mappings()
        
        # 验证结果
        assert len(result) == 1
        assert result[0]["session_id"] == "session_test123"
        assert result[0]["thread_id"] == "thread_test123"
        assert "created_at" in result[0]
    
    @pytest.mark.asyncio
    async def test_mapping_exists_true(self, mapper):
        """测试映射关系存在（存在）"""
        # 执行测试
        result = await mapper.mapping_exists("session_test123", "thread_test123")
        
        # 验证结果
        assert result is True
    
    @pytest.mark.asyncio
    async def test_mapping_exists_false_wrong_session(self, mapper):
        """测试映射关系存在（错误的Session）"""
        # 执行测试
        result = await mapper.mapping_exists("wrong_session", "thread_test123")
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_mapping_exists_false_wrong_thread(self, mapper):
        """测试映射关系存在（错误的Thread）"""
        # 执行测试
        result = await mapper.mapping_exists("session_test123", "wrong_thread")
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_mapping_exists_false_both_wrong(self, mapper):
        """测试映射关系存在（两者都错误）"""
        # 执行测试
        result = await mapper.mapping_exists("wrong_session", "wrong_thread")
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_save_and_load_mappings(self, mapper, temp_dir):
        """测试保存和加载映射关系"""
        # 由于mock的side_effect顺序，第一次create_session_with_thread会使用"session_test123"
        # 这与初始映射相同，因此我们需要调用两次来创建2个不同的映射
        
        # 第一次调用会使用side_effect的第一个值，与初始映射相同，所以不增加映射数量
        await mapper.create_session_with_thread("configs/workflows/test2.yaml", {"name": "test2"})
        
        # 检查当前映射数量 - 仍然是1，因为新创建的与初始映射相同
        mappings = await mapper.list_mappings()
        assert len(mappings) == 1  # 仍然是1，因为新映射覆盖了旧映射
        
        # 再次调用，这次会使用side_effect的第二个值，创建新的映射
        await mapper.create_session_with_thread("configs/workflows/test3.yaml", {"name": "test3"})

        # 验证映射关系数量（现在应该有2个不同的映射）
        mappings = await mapper.list_mappings()
        assert len(mappings) == 2

        # 创建新的映射器实例，应该加载之前保存的映射关系
        new_mapper = SessionThreadMapper(
            mapper.session_manager,
            mapper.thread_manager,
            temp_dir
        )

        # 验证加载的映射关系
        loaded_mappings = await new_mapper.list_mappings()
        assert len(loaded_mappings) == 2

        # 验证映射关系内容
        loaded_session_ids = {m["session_id"] for m in loaded_mappings}
        loaded_thread_ids = {m["thread_id"] for m in loaded_mappings}

        assert "session_test123" in loaded_session_ids  # 初始映射
        assert "session_test456" in loaded_session_ids  # 新创建的映射
        assert "thread_test123" in loaded_thread_ids  # 初始映射
        assert "thread_test456" in loaded_thread_ids  # 新创建的映射
    
    @pytest.mark.asyncio
    async def test_extract_graph_id(self, mapper):
        """测试从工作流配置路径提取graph ID"""
        # 测试不同路径格式
        test_cases = [
            ("configs/workflows/test_workflow.yaml", "test_workflow"),
            ("configs/workflows/subdir/another_workflow.yaml", "another_workflow"),
            ("simple_workflow.yaml", "simple_workflow"),
            ("C:\\path\\to\\workflow\\windows_workflow.yaml", "windows_workflow")
        ]
        
        for path, expected_id in test_cases:
            result = mapper._extract_graph_id(path)
            assert result == expected_id, f"路径: {path}, 期望: {expected_id}, 实际: {result}"


class TestMemorySessionThreadMapper:
    """内存Session-Thread映射器测试类"""
    
    @pytest.fixture
    def mock_session_manager(self):
        """模拟Session管理器"""
        manager = MagicMock(spec=ISessionManager)
        # 设置side_effect以支持所有测试场景
        # 注意：side_effect会按顺序返回值
        manager.create_session.side_effect = [
            "session_test123",  # 用于直接返回值的测试
            "session_test456",  # 用于save_and_load_mappings测试
            "session_1",        # 用于multiple_mappings测试
            "session_2",        # 用于multiple_mappings测试
            "session_test123",  # 用于其他需要特定返回值的测试
        ]
        return manager
    
    @pytest.fixture
    def mock_thread_manager(self):
        """模拟Thread管理器"""
        manager = AsyncMock(spec=IThreadManager)
        # 设置side_effect以支持所有测试场景
        manager.create_thread.side_effect = [
            "thread_test123",   # 用于直接返回值的测试
            "thread_test456",   # 用于save_and_load_mappings测试
            "thread_1",         # 用于multiple_mappings测试
            "thread_2",         # 用于multiple_mappings测试
            "thread_test123",   # 用于其他需要特定返回值的测试
        ]
        return manager
    
    @pytest.fixture
    def memory_mapper(self, mock_session_manager, mock_thread_manager):
        """创建内存Session-Thread映射器实例"""
        # 重置mock以确保测试隔离
        memory_mapper = MemorySessionThreadMapper(mock_session_manager, mock_thread_manager)
        # 通过调用方法创建初始映射关系
        memory_mapper._mappings["session_test123"] = "thread_test123"
        memory_mapper._reverse_mappings["thread_test123"] = "session_test123"
        return memory_mapper
    
    @pytest.mark.asyncio
    async def test_create_session_with_thread_success(self, memory_mapper, mock_session_manager, mock_thread_manager):
        """测试成功创建Session和Thread"""
        # 准备测试数据
        workflow_config_path = "configs/workflows/test_workflow.yaml"
        thread_metadata = {"name": "test_thread"}
        agent_config = {"model": "gpt-4"}
        initial_state = {"messages": []}
        
        # 执行测试
        session_id, thread_id = await memory_mapper.create_session_with_thread(
            workflow_config_path,
            thread_metadata,
            agent_config,
            initial_state
        )
        
        # 验证结果
        assert session_id == "session_test123"
        assert thread_id == "thread_test123"
        
        # 验证调用
        mock_session_manager.create_session.assert_called_once_with(
            workflow_config_path,
            agent_config,
            initial_state
        )
        mock_thread_manager.create_thread.assert_called_once_with(
            "test_workflow",
            thread_metadata
        )
    
    @pytest.mark.asyncio
    async def test_get_thread_for_session_exists(self, memory_mapper):
        """测试获取存在的Session对应的Thread ID"""
        # 执行测试
        result = await memory_mapper.get_thread_for_session("session_test123")
        
        # 验证结果
        assert result == "thread_test123"
    
    @pytest.mark.asyncio
    async def test_get_thread_for_session_not_exists(self, memory_mapper):
        """测试获取不存在的Session对应的Thread ID"""
        # 执行测试
        result = await memory_mapper.get_thread_for_session("nonexistent_session")
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_session_for_thread_exists(self, memory_mapper):
        """测试获取存在的Thread对应的Session ID"""
        # 执行测试
        result = await memory_mapper.get_session_for_thread("thread_test123")
        
        # 验证结果
        assert result == "session_test123"
    
    @pytest.mark.asyncio
    async def test_get_session_for_thread_not_exists(self, memory_mapper):
        """测试获取不存在的Thread对应的Session ID"""
        # 执行测试
        result = await memory_mapper.get_session_for_thread("nonexistent_thread")
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_mapping_success(self, memory_mapper):
        """测试成功删除映射关系"""
        # 执行测试
        result = await memory_mapper.delete_mapping("session_test123")
        
        # 验证结果
        assert result is True
        
        # 验证映射关系已删除
        assert await memory_mapper.get_thread_for_session("session_test123") is None
        assert await memory_mapper.get_session_for_thread("thread_test123") is None
    
    @pytest.mark.asyncio
    async def test_delete_mapping_not_exists(self, memory_mapper):
        """测试删除不存在的映射关系"""
        # 执行测试
        result = await memory_mapper.delete_mapping("nonexistent_session")
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_mappings(self, memory_mapper):
        """测试列出所有映射关系"""
        # 执行测试
        result = await memory_mapper.list_mappings()
        
        # 验证结果
        assert len(result) == 1
        assert result[0]["session_id"] == "session_test123"
        assert result[0]["thread_id"] == "thread_test123"
        assert "created_at" in result[0]
    
    @pytest.mark.asyncio
    async def test_mapping_exists_true(self, memory_mapper):
        """测试映射关系存在（存在）"""
        # 执行测试
        result = await memory_mapper.mapping_exists("session_test123", "thread_test123")
        
        # 验证结果
        assert result is True
    
    @pytest.mark.asyncio
    async def test_mapping_exists_false(self, memory_mapper):
        """测试映射关系存在（不存在）"""
        # 执行测试
        result = await memory_mapper.mapping_exists("wrong_session", "wrong_thread")
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_multiple_mappings(self, memory_mapper, mock_session_manager, mock_thread_manager):
        """测试多个映射关系"""
        # 设置不同的返回值
        mock_session_manager.create_session.side_effect = ["session_1", "session_2"]
        mock_thread_manager.create_thread.side_effect = ["thread_1", "thread_2"]
        
        # 创建多个映射关系
        await memory_mapper.create_session_with_thread("workflow1.yaml", {"name": "test1"})
        await memory_mapper.create_session_with_thread("workflow2.yaml", {"name": "test2"})
        
        # 验证所有映射关系（初始1个 + 新增2个 = 3个）
        mappings = await memory_mapper.list_mappings()
        assert len(mappings) == 3
        
        session_ids = {m["session_id"] for m in mappings}
        thread_ids = {m["thread_id"] for m in mappings}
        
        assert "session_1" in session_ids
        assert "session_2" in session_ids
        assert "thread_1" in thread_ids
        assert "thread_2" in thread_ids
        
        # 验证映射关系正确
        assert await memory_mapper.get_thread_for_session("session_1") == "thread_1"
        assert await memory_mapper.get_thread_for_session("session_2") == "thread_2"
        assert await memory_mapper.get_session_for_thread("thread_1") == "session_1"
        assert await memory_mapper.get_session_for_thread("thread_2") == "session_2"
    
    @pytest.mark.asyncio
    async def test_clear(self, memory_mapper, mock_session_manager, mock_thread_manager):
        """测试清空所有映射关系"""
        # 创建多个映射关系
        mock_session_manager.create_session.side_effect = ["session_1", "session_2"]
        mock_thread_manager.create_thread.side_effect = ["thread_1", "thread_2"]
        
        await memory_mapper.create_session_with_thread("workflow1.yaml", {"name": "test1"})
        await memory_mapper.create_session_with_thread("workflow2.yaml", {"name": "test2"})
        
        # 验证映射关系存在（初始1个 + 新增2个 = 3个）
        mappings = await memory_mapper.list_mappings()
        assert len(mappings) == 3
        
        # 清空映射关系
        memory_mapper.clear()
        
        # 验证映射关系已清空
        mappings = await memory_mapper.list_mappings()
        assert len(mappings) == 0
        
        assert await memory_mapper.get_thread_for_session("session_1") is None
        assert await memory_mapper.get_thread_for_session("session_2") is None
        assert await memory_mapper.get_session_for_thread("thread_1") is None
        assert await memory_mapper.get_session_for_thread("thread_2") is None
    
    @pytest.mark.asyncio
    async def test_extract_graph_id(self, memory_mapper):
        """测试从工作流配置路径提取graph ID"""
        # 测试不同路径格式
        test_cases = [
            ("configs/workflows/test_workflow.yaml", "test_workflow"),
            ("configs/workflows/subdir/another_workflow.yaml", "another_workflow"),
            ("simple_workflow.yaml", "simple_workflow"),
            ("C:\\path\\to\\workflow\\windows_workflow.yaml", "windows_workflow")
        ]
        
        for path, expected_id in test_cases:
            result = memory_mapper._extract_graph_id(path)
            assert result == expected_id, f"路径: {path}, 期望: {expected_id}, 实际: {result}"