"""SessionManager单元测试

测试多线程会话管理的核心功能。
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.application.sessions.manager import SessionManager, ISessionManager
from src.infrastructure.graph.state import AgentState
from src.infrastructure.graph.config import GraphConfig


class TestSessionManager:
    """SessionManager测试类"""
    
    @pytest.fixture
    def mock_workflow_manager(self):
        """模拟工作流管理器"""
        manager = Mock()
        manager.load_workflow.return_value = "test_workflow_id"
        manager.get_workflow_config.return_value = Mock()
        manager.get_workflow_summary.return_value = {
            "workflow_id": "test_workflow_id",
            "version": "1.0",
            "checksum": "test_checksum"
        }
        manager.create_workflow.return_value = Mock()
        return manager
    
    @pytest.fixture
    def mock_session_store(self):
        """模拟会话存储"""
        store = Mock()
        store.save_session = Mock()
        store.get_session.return_value = None
        store.delete_session.return_value = True
        store.list_sessions.return_value = []
        return store
    
    @pytest.fixture
    def mock_thread_manager(self):
        """模拟线程管理器"""
        manager = AsyncMock()
        manager.create_thread.return_value = "test_thread_id"
        manager.update_thread_state = AsyncMock()
        return manager
    
    @pytest.fixture
    def mock_state_manager(self):
        """模拟状态管理器"""
        manager = Mock()
        manager.serialize_state_dict.return_value = {}
        manager.deserialize_state_dict.return_value = {}
        return manager
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def session_manager(
        self,
        mock_workflow_manager,
        mock_session_store,
        mock_thread_manager,
        mock_state_manager,
        temp_dir
    ):
        """创建SessionManager实例"""
        return SessionManager(
            workflow_manager=mock_workflow_manager,
            session_store=mock_session_store,
            thread_manager=mock_thread_manager,
            state_manager=mock_state_manager,
            storage_path=temp_dir
        )
    
    def test_init(self, mock_workflow_manager, mock_session_store, temp_dir):
        """测试初始化"""
        manager = SessionManager(
            workflow_manager=mock_workflow_manager,
            session_store=mock_session_store,
            storage_path=temp_dir
        )
        
        assert manager.workflow_manager == mock_workflow_manager
        assert manager.session_store == mock_session_store
        assert manager.storage_path == temp_dir
        assert manager.storage_path.exists()
        assert manager.thread_manager is None
        assert manager.state_manager is None
    
    @pytest.mark.asyncio
    async def test_create_session_with_threads(
        self,
        session_manager,
        mock_workflow_manager,
        mock_session_store,
        mock_thread_manager,
        mock_state_manager
    ):
        """测试创建多线程会话"""
        workflow_configs = {
            "thread1": "test_config1.yaml",
            "thread2": "test_config2.yaml"
        }
        dependencies = {"thread2": ["thread1"]}
        agent_config = {"test": "config"}
        initial_states = {
            "thread1": AgentState(),
            "thread2": AgentState()
        }
        
        # 模拟配置文件存在
        with patch('pathlib.Path.exists', return_value=True):
            session_id = await session_manager.create_session_with_threads(
                workflow_configs=workflow_configs,
                dependencies=dependencies,
                agent_config=agent_config,
                initial_states=initial_states
            )
        
        # 验证返回的会话ID格式
        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        
        # 验证工作流加载
        assert mock_workflow_manager.load_workflow.call_count == 2
        
        # 验证线程创建
        assert mock_thread_manager.create_thread.call_count == 2
        
        # 验证状态更新
        assert mock_thread_manager.update_thread_state.call_count == 2
        
        # 验证会话保存
        mock_session_store.save_session.assert_called_once()
        
        # 验证会话数据结构
        call_args = mock_session_store.save_session.call_args[0]
        saved_session_id = call_args[0]
        saved_session_data = call_args[1]
        
        assert saved_session_id == session_id
        assert "metadata" in saved_session_data
        assert "state" in saved_session_data
        
        metadata = saved_session_data["metadata"]
        assert metadata["workflow_configs"] == workflow_configs
        assert metadata["dependencies"] == dependencies
        assert metadata["agent_config"] == agent_config
        assert "thread_info" in metadata
        assert len(metadata["thread_info"]) == 2
    
    @pytest.mark.asyncio
    async def test_create_session_with_threads_missing_config(
        self,
        session_manager,
        mock_workflow_manager,
        mock_session_store,
        mock_thread_manager
    ):
        """测试创建多线程会话时配置文件不存在"""
        workflow_configs = {
            "thread1": "missing_config.yaml"
        }
        
        # 模拟配置文件不存在
        with patch('pathlib.Path.exists', return_value=False):
            session_id = await session_manager.create_session_with_threads(
                workflow_configs=workflow_configs
            )
        
        # 验证仍然创建了会话，但没有线程
        assert session_id is not None
        mock_thread_manager.create_thread.assert_not_called()
        
        # 验证会话保存
        mock_session_store.save_session.assert_called_once()
        
        # 验证线程信息为空
        call_args = mock_session_store.save_session.call_args[0]
        saved_session_data = call_args[1]
        thread_info = saved_session_data["metadata"]["thread_info"]
        assert len(thread_info) == 0
    
    def test_create_session_backward_compatibility(
        self,
        session_manager,
        mock_workflow_manager,
        mock_session_store
    ):
        """测试向后兼容的单线程会话创建"""
        workflow_config_path = "test_config.yaml"
        agent_config = {"test": "config"}
        initial_state = AgentState()
        
        # 模拟配置文件存在
        with patch('pathlib.Path.exists', return_value=True):
            session_id = session_manager.create_session(
                workflow_config_path=workflow_config_path,
                agent_config=agent_config,
                initial_state=initial_state
            )
        
        # 验证返回的会话ID
        assert session_id is not None
        assert isinstance(session_id, str)
        
        # 验证工作流加载
        mock_workflow_manager.load_workflow.assert_called_once_with(workflow_config_path)
        
        # 验证会话保存
        mock_session_store.save_session.assert_called_once()
    
    def test_get_session(self, session_manager, mock_session_store):
        """测试获取会话"""
        session_id = "test_session_id"
        expected_session_data = {"metadata": {"test": "data"}}
        mock_session_store.get_session.return_value = expected_session_data
        
        result = session_manager.get_session(session_id)
        
        assert result == expected_session_data
        mock_session_store.get_session.assert_called_once_with(session_id)
    
    def test_get_session_not_found(self, session_manager, mock_session_store):
        """测试获取不存在的会话"""
        session_id = "nonexistent_session_id"
        mock_session_store.get_session.return_value = None
        
        result = session_manager.get_session(session_id)
        
        assert result is None
        mock_session_store.get_session.assert_called_once_with(session_id)
    
    def test_restore_session_success(
        self,
        session_manager,
        mock_workflow_manager,
        mock_session_store,
        mock_state_manager
    ):
        """测试成功恢复会话"""
        session_id = "test_session_id"
        config_path = "test_config.yaml"
        
        session_data = {
            "metadata": {
                "session_id": session_id,
                "workflow_config_path": config_path,
                "workflow_summary": {
                    "workflow_id": "test_workflow_id",
                    "version": "1.0",
                    "checksum": "test_checksum"
                }
            },
            "state": {"test": "state_data"}
        }
        
        mock_session_store.get_session.return_value = session_data
        
        # 模拟配置文件存在
        with patch('pathlib.Path.exists', return_value=True):
            workflow, state = session_manager.restore_session(session_id)
        
        # 验证返回的工作流和状态
        assert workflow is not None
        assert state is not None
        
        # 验证工作流加载和创建
        mock_workflow_manager.load_workflow.assert_called_once_with(config_path)
        mock_workflow_manager.create_workflow.assert_called_once()
        
        # 验证状态反序列化
        if mock_state_manager:
            mock_state_manager.deserialize_state_dict.assert_called()
    
    def test_restore_session_not_found(self, session_manager, mock_session_store):
        """测试恢复不存在的会话"""
        session_id = "nonexistent_session_id"
        mock_session_store.get_session.return_value = None
        
        with pytest.raises(ValueError, match=f"会话 {session_id} 不存在"):
            session_manager.restore_session(session_id)
    
    def test_restore_session_config_not_exists(
        self,
        session_manager,
        mock_session_store,
        mock_state_manager
    ):
        """测试恢复会话时配置文件不存在"""
        session_id = "test_session_id"
        config_path = "missing_config.yaml"
        
        session_data = {
            "metadata": {
                "session_id": session_id,
                "workflow_config_path": config_path
            },
            "state": {"test": "state_data"}
        }
        
        mock_session_store.get_session.return_value = session_data
        
        # 模拟配置文件不存在
        with patch('pathlib.Path.exists', return_value=False):
            workflow, state = session_manager.restore_session(session_id)
        
        # 验证返回的工作流为None，状态不为None
        assert workflow is None
        assert state is not None
        
        # 验证状态反序列化
        if mock_state_manager:
            mock_state_manager.deserialize_state_dict.assert_called()
    
    def test_save_session(
        self,
        session_manager,
        mock_session_store,
        mock_state_manager
    ):
        """测试保存会话"""
        session_id = "test_session_id"
        state = AgentState()
        workflow = Mock()
        
        # 模拟会话存在
        session_data = {
            "metadata": {"test": "data"},
            "state": {}
        }
        mock_session_store.get_session.return_value = session_data
        
        result = session_manager.save_session(session_id, state, workflow)
        
        assert result is True
        
        # 验证会话保存
        mock_session_store.save_session.assert_called_once()
        
        # 验证状态序列化
        if mock_state_manager:
            mock_state_manager.serialize_state_dict.assert_called()
    
    def test_save_session_not_exists(self, session_manager, mock_session_store):
        """测试保存不存在的会话"""
        session_id = "nonexistent_session_id"
        state = AgentState()
        
        mock_session_store.get_session.return_value = None
        
        result = session_manager.save_session(session_id, state)
        
        assert result is False
        mock_session_store.save_session.assert_not_called()
    
    def test_delete_session(
        self,
        session_manager,
        mock_session_store,
        temp_dir
    ):
        """测试删除会话"""
        session_id = "test_session_id"
        
        # 创建会话目录
        session_dir = temp_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        result = session_manager.delete_session(session_id)
        
        assert result is True
        
        # 验证会话存储删除
        mock_session_store.delete_session.assert_called_once_with(session_id)
        
        # 验证目录删除
        assert not session_dir.exists()
    
    def test_delete_session_not_exists(
        self,
        session_manager,
        mock_session_store
    ):
        """测试删除不存在的会话"""
        session_id = "nonexistent_session_id"
        
        mock_session_store.delete_session.return_value = False
        
        result = session_manager.delete_session(session_id)
        
        assert result is False
    
    def test_list_sessions(self, session_manager, mock_session_store):
        """测试列出会话"""
        sessions = [
            {"session_id": "session1", "created_at": "2023-01-01"},
            {"session_id": "session2", "created_at": "2023-01-02"}
        ]
        mock_session_store.list_sessions.return_value = sessions
        
        result = session_manager.list_sessions()
        
        assert len(result) == 2
        assert result[0]["session_id"] == "session2"  # 按时间倒序
        assert result[1]["session_id"] == "session1"
        
        mock_session_store.list_sessions.assert_called_once()
    
    def test_get_session_history_with_git_manager(
        self,
        session_manager,
        temp_dir
    ):
        """测试获取会话历史（有Git管理器）"""
        session_id = "test_session_id"
        
        # 创建模拟Git管理器
        mock_git_manager = Mock()
        mock_git_manager.get_commit_history.return_value = [
            {"timestamp": "2023-01-01", "message": "Initial commit"},
            {"timestamp": "2023-01-02", "message": "Update state"}
        ]
        session_manager.git_manager = mock_git_manager
        
        result = session_manager.get_session_history(session_id)
        
        assert len(result) == 2
        assert result[0]["message"] == "Initial commit"
        assert result[1]["message"] == "Update state"
        
        session_dir = temp_dir / session_id
        mock_git_manager.get_commit_history.assert_called_once_with(session_dir)
    
    def test_get_session_history_without_git_manager(
        self,
        session_manager,
        mock_session_store
    ):
        """测试获取会话历史（无Git管理器）"""
        session_id = "test_session_id"
        
        session_data = {
            "metadata": {
                "created_at": "2023-01-01T00:00:00"
            }
        }
        mock_session_store.get_session.return_value = session_data
        
        result = session_manager.get_session_history(session_id)
        
        assert len(result) == 1
        assert result[0]["message"] == "会话创建"
        assert result[0]["author"] == "system"
    
    def test_get_session_info(self, session_manager, mock_session_store):
        """测试获取会话信息"""
        session_id = "test_session_id"
        expected_info = {"session_id": session_id, "test": "data"}
        mock_session_store.get_session.return_value = expected_info
        
        result = session_manager.get_session_info(session_id)
        
        assert result == expected_info
        mock_session_store.get_session.assert_called_once_with(session_id)
    
    def test_session_exists(self, session_manager, mock_session_store):
        """测试检查会话是否存在"""
        session_id = "test_session_id"
        mock_session_store.get_session.return_value = {"test": "data"}
        
        result = session_manager.session_exists(session_id)
        
        assert result is True
        mock_session_store.get_session.assert_called_once_with(session_id)
    
    def test_session_not_exists(self, session_manager, mock_session_store):
        """测试检查会话不存在"""
        session_id = "nonexistent_session_id"
        mock_session_store.get_session.return_value = None
        
        result = session_manager.session_exists(session_id)
        
        assert result is False
        mock_session_store.get_session.assert_called_once_with(session_id)
    
    def test_save_session_with_metrics(
        self,
        session_manager,
        mock_session_store,
        mock_state_manager
    ):
        """测试保存会话状态和工作流指标"""
        session_id = "test_session_id"
        state = AgentState()
        workflow_metrics = {"test": "metrics"}
        workflow = Mock()
        
        # 模拟会话存在
        session_data = {
            "metadata": {"test": "data"},
            "state": {}
        }
        mock_session_store.get_session.return_value = session_data
        
        result = session_manager.save_session_with_metrics(
            session_id, state, workflow_metrics, workflow
        )
        
        assert result is True
        
        # 验证会话保存
        mock_session_store.save_session.assert_called_once()
        
        # 验证状态序列化
        if mock_state_manager:
            mock_state_manager.serialize_state_dict.assert_called()
        
        # 验证工作流指标保存
        call_args = mock_session_store.save_session.call_args[0]
        saved_session_data = call_args[1]
        assert "workflow_metrics" in saved_session_data
        assert saved_session_data["workflow_metrics"]["test"] == "metrics"
    
    @pytest.mark.asyncio
    async def test_add_thread(
        self,
        session_manager,
        mock_workflow_manager,
        mock_session_store,
        mock_thread_manager
    ):
        """测试向会话添加线程"""
        session_id = "test_session_id"
        thread_name = "new_thread"
        config_path = "new_config.yaml"
        
        # 模拟会话存在
        session_data = {
            "metadata": {
                "test": "data"
            },
            "state": {}
        }
        mock_session_store.get_session.return_value = session_data
        
        # 模拟配置文件存在
        with patch('pathlib.Path.exists', return_value=True):
            result = await session_manager.add_thread(session_id, thread_name, config_path)
        
        assert result is True
        
        # 验证工作流加载
        mock_workflow_manager.load_workflow.assert_called_once_with(config_path)
        
        # 验证线程创建
        mock_thread_manager.create_thread.assert_called_once()
        
        # 验证会话更新
        mock_session_store.save_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_thread_session_not_exists(
        self,
        session_manager,
        mock_session_store
    ):
        """测试向不存在的会话添加线程"""
        session_id = "nonexistent_session_id"
        thread_name = "new_thread"
        config_path = "new_config.yaml"
        
        mock_session_store.get_session.return_value = None
        
        result = await session_manager.add_thread(session_id, thread_name, config_path)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_add_thread_config_not_exists(
        self,
        session_manager,
        mock_session_store
    ):
        """测试添加线程时配置文件不存在"""
        session_id = "test_session_id"
        thread_name = "new_thread"
        config_path = "missing_config.yaml"
        
        # 模拟会话存在
        session_data = {"metadata": {"test": "data"}}
        mock_session_store.get_session.return_value = session_data
        
        # 模拟配置文件不存在
        with patch('pathlib.Path.exists', return_value=False):
            result = await session_manager.add_thread(session_id, thread_name, config_path)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_threads(
        self,
        session_manager,
        mock_session_store
    ):
        """测试获取会话的所有线程信息"""
        session_id = "test_session_id"
        thread_info = {
            "thread1": {
                "thread_id": "thread1_id",
                "config_path": "config1.yaml"
            },
            "thread2": {
                "thread_id": "thread2_id",
                "config_path": "config2.yaml"
            }
        }
        
        session_data = {
            "metadata": {
                "thread_info": thread_info
            }
        }
        mock_session_store.get_session.return_value = session_data
        
        result = await session_manager.get_threads(session_id)
        
        assert result == thread_info
        mock_session_store.get_session.assert_called_once_with(session_id)
    
    @pytest.mark.asyncio
    async def test_get_threads_session_not_exists(
        self,
        session_manager,
        mock_session_store
    ):
        """测试获取不存在会话的线程信息"""
        session_id = "nonexistent_session_id"
        
        mock_session_store.get_session.return_value = None
        
        result = await session_manager.get_threads(session_id)
        
        assert result == {}
    
    def test_generate_session_id(self, session_manager):
        """测试生成会话ID"""
        config_path = "test_workflow_config.yaml"
        
        session_id = session_manager._generate_session_id(config_path)
        
        # 验证格式：workflow名称-年月日-时分秒-uuid前6位
        parts = session_id.split('-')
        assert len(parts) == 4
        assert parts[0] == "testworkflowconfig"  # workflow名称
        assert len(parts[1]) == 6  # 年月日
        assert len(parts[2]) == 6  # 时分秒
        assert len(parts[3]) == 6  # uuid前6位
    
    def test_extract_workflow_name(self, session_manager):
        """测试从配置路径提取workflow名称"""
        # 测试正常路径
        config_path = "configs/workflows/react_workflow.yaml"
        name = session_manager._extract_workflow_name(config_path)
        assert name == "react"
        
        # 测试带下划线的路径
        config_path = "configs/workflows/test_workflow.yaml"
        name = session_manager._extract_workflow_name(config_path)
        assert name == "test"
        
        # 测试空路径
        name = session_manager._extract_workflow_name("")
        assert name == "unknown"
        
        # 测试None路径
        name = session_manager._extract_workflow_name(None)
        assert name == "unknown"
    
    def test_serialize_state(self, session_manager):
        """测试状态序列化"""
        state = AgentState()
        state["messages"] = [Mock(content="test", type="human")]
        state["tool_results"] = [{"tool_name": "test_tool", "success": True}]
        state["current_step"] = "test_step"
        state["max_iterations"] = 10
        state["iteration_count"] = 5
        state["workflow_name"] = "test_workflow"
        state["start_time"] = datetime.now().isoformat()
        state["errors"] = ["test_error"]
        
        result = session_manager._serialize_state(state)
        
        assert "messages" in result
        assert "tool_results" in result
        assert "current_step" in result
        assert "max_iterations" in result
        assert "iteration_count" in result
        assert "workflow_name" in result
        assert "start_time" in result
        assert "errors" in result
        
        assert result["current_step"] == "test_step"
        assert result["max_iterations"] == 10
        assert result["iteration_count"] == 5
        assert result["workflow_name"] == "test_workflow"
        assert result["errors"] == ["test_error"]
    
    def test_deserialize_state(self, session_manager):
        """测试状态反序列化"""
        state_data = {
            "messages": [
                {"type": "HumanMessage", "content": "test", "role": "human"}
            ],
            "tool_results": [
                {"tool_name": "test_tool", "success": True, "result": "result"}
            ],
            "current_step": "test_step",
            "max_iterations": 10,
            "iteration_count": 5,
            "workflow_name": "test_workflow",
            "start_time": "2023-01-01T00:00:00",
            "errors": ["test_error"]
        }
        
        result = session_manager._deserialize_state(state_data)
        
        assert isinstance(result, dict)
        assert "messages" in result
        assert "tool_results" in result
        assert "current_step" in result
        assert "max_iterations" in result
        assert "iteration_count" in result
        assert "workflow_name" in result
        assert "start_time" in result
        assert "errors" in result
        
        assert result["current_step"] == "test_step"
        assert result["max_iterations"] == 10
        assert result["iteration_count"] == 5
        assert result["workflow_name"] == "test_workflow"
        assert result["errors"] == ["test_error"]
        assert len(result["messages"]) == 1
        assert len(result["tool_results"]) == 1