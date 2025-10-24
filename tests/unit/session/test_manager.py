"""会话管理器单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from src.application.sessions.manager import SessionManager, ISessionManager
from src.domain.sessions.store import ISessionStore
from src.application.sessions.git_manager import IGitManager
from src.application.workflow.manager import IWorkflowManager
from src.domain.workflow.config import WorkflowConfig
from src.domain.prompts.agent_state import AgentState, BaseMessage


class TestSessionManager:
    """会话管理器测试类"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_workflow_manager(self):
        """模拟工作流管理器"""
        manager = Mock(spec=IWorkflowManager)
        manager.load_workflow.return_value = "test_workflow_id"
        manager.create_workflow.return_value = Mock()
        manager.get_workflow_config.return_value = Mock(spec=WorkflowConfig)
        manager.get_workflow_config.return_value.to_dict.return_value = {"name": "test"}
        return manager

    @pytest.fixture
    def mock_session_store(self):
        """模拟会话存储"""
        store = Mock(spec=ISessionStore)
        store.save_session.return_value = True
        store.get_session.return_value = None
        store.delete_session.return_value = True
        store.list_sessions.return_value = []
        return store

    @pytest.fixture
    def mock_git_manager(self):
        """模拟Git管理器"""
        git_manager = Mock(spec=IGitManager)
        git_manager.init_repo.return_value = True
        git_manager.commit_changes.return_value = True
        git_manager.get_commit_history.return_value = []
        return git_manager

    @pytest.fixture
    def session_manager(self, mock_workflow_manager, mock_session_store, temp_dir):
        """创建会话管理器实例"""
        return SessionManager(
            workflow_manager=mock_workflow_manager,
            session_store=mock_session_store,
            storage_path=temp_dir
        )

    @pytest.fixture
    def session_manager_with_git(self, mock_workflow_manager, mock_session_store, mock_git_manager, temp_dir):
        """创建带Git管理器的会话管理器实例"""
        return SessionManager(
            workflow_manager=mock_workflow_manager,
            session_store=mock_session_store,
            git_manager=mock_git_manager,
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
        assert manager.git_manager is None
        assert manager.storage_path == temp_dir
        assert temp_dir.exists()

    def test_init_with_git(self, mock_workflow_manager, mock_session_store, mock_git_manager, temp_dir):
        """测试带Git管理器的初始化"""
        manager = SessionManager(
            workflow_manager=mock_workflow_manager,
            session_store=mock_session_store,
            git_manager=mock_git_manager,
            storage_path=temp_dir
        )
        
        assert manager.git_manager == mock_git_manager

    def test_create_session(self, session_manager, mock_workflow_manager, mock_session_store):
        """测试创建会话"""
        workflow_config_path = "configs/workflows/test.yaml"
        agent_config = {"name": "test_agent"}
        initial_state = AgentState()
        initial_state.add_message(BaseMessage(content="测试消息"))
        
        with patch.object(session_manager, '_generate_session_id', return_value="test-session-id"):
            session_id = session_manager.create_session(
                workflow_config_path=workflow_config_path,
                agent_config=agent_config,
                initial_state=initial_state
            )
        
        assert session_id == "test-session-id"
        
        # 验证工作流管理器调用
        mock_workflow_manager.load_workflow.assert_called_once_with(workflow_config_path)
        mock_workflow_manager.create_workflow.assert_called_once_with("test_workflow_id")
        
        # 验证会话存储调用
        mock_session_store.save_session.assert_called_once()
        call_args = mock_session_store.save_session.call_args[0]
        assert call_args[0] == "test-session-id"
        assert "metadata" in call_args[1]
        assert "state" in call_args[1]
        assert "workflow_config" in call_args[1]

    def test_create_session_with_git(self, session_manager_with_git, mock_workflow_manager, 
                                   mock_session_store, mock_git_manager):
        """测试带Git管理器创建会话"""
        workflow_config_path = "configs/workflows/test.yaml"
        
        with patch.object(session_manager_with_git, '_generate_session_id', return_value="test-session-id"):
            session_id = session_manager_with_git.create_session(
                workflow_config_path=workflow_config_path
            )
        
        # 验证Git管理器调用
        mock_git_manager.init_repo.assert_called_once()
        mock_git_manager.commit_changes.assert_called_once()

    def test_get_session(self, session_manager, mock_session_store):
        """测试获取会话"""
        session_id = "test-session-id"
        expected_session = {"metadata": {"session_id": session_id}}
        mock_session_store.get_session.return_value = expected_session
        
        result = session_manager.get_session(session_id)
        
        assert result == expected_session
        mock_session_store.get_session.assert_called_once_with(session_id)

    def test_restore_session(self, session_manager, mock_workflow_manager, mock_session_store):
        """测试恢复会话"""
        session_id = "test-session-id"
        session_data = {
            "metadata": {"workflow_id": "test_workflow_id"},
            "state": {
                "messages": [],
                "tool_results": [],
                "current_step": "",
                "max_iterations": 10,
                "iteration_count": 0,
                "workflow_name": "",
                "start_time": None,
                "errors": []
            }
        }
        mock_session_store.get_session.return_value = session_data
        
        workflow, state = session_manager.restore_session(session_id)
        
        assert workflow is not None
        assert isinstance(state, AgentState)
        mock_workflow_manager.create_workflow.assert_called_once_with("test_workflow_id")

    def test_restore_session_not_exists(self, session_manager, mock_session_store):
        """测试恢复不存在的会话"""
        session_id = "non-existent-session"
        mock_session_store.get_session.return_value = None
        
        with pytest.raises(ValueError, match=f"会话 {session_id} 不存在"):
            session_manager.restore_session(session_id)

    def test_save_session(self, session_manager, mock_session_store):
        """测试保存会话"""
        session_id = "test-session-id"
        workflow = Mock()
        state = AgentState()
        state.add_message(BaseMessage(content="测试消息"))
        
        session_data = {
            "metadata": {"session_id": session_id, "updated_at": "2023-01-01T00:00:00"},
            "state": {}
        }
        mock_session_store.get_session.return_value = session_data
        
        result = session_manager.save_session(session_id, workflow, state)
        
        assert result is True
        mock_session_store.save_session.assert_called_once()

    def test_save_session_not_exists(self, session_manager, mock_session_store):
        """测试保存不存在的会话"""
        session_id = "non-existent-session"
        workflow = Mock()
        state = AgentState()
        
        mock_session_store.get_session.return_value = None
        
        result = session_manager.save_session(session_id, workflow, state)
        
        assert result is False

    def test_delete_session(self, session_manager, mock_session_store, temp_dir):
        """测试删除会话"""
        session_id = "test-session-id"
        
        # 创建会话目录
        session_dir = temp_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        result = session_manager.delete_session(session_id)
        
        assert result is True
        mock_session_store.delete_session.assert_called_once_with(session_id)
        assert not session_dir.exists()

    def test_delete_session_error(self, session_manager, mock_session_store):
        """测试删除会话出错"""
        session_id = "test-session-id"
        mock_session_store.delete_session.side_effect = Exception("删除失败")
        
        result = session_manager.delete_session(session_id)
        
        assert result is False

    def test_list_sessions(self, session_manager, mock_session_store):
        """测试列出会话"""
        sessions = [
            {"session_id": "session1", "created_at": "2023-01-01T00:00:00"},
            {"session_id": "session2", "created_at": "2023-01-02T00:00:00"}
        ]
        mock_session_store.list_sessions.return_value = sessions
        
        result = session_manager.list_sessions()
        
        assert result == sessions
        assert result[0]["session_id"] == "session2"  # 按时间倒序
        assert result[1]["session_id"] == "session1"

    def test_get_session_history_with_git(self, session_manager_with_git, mock_git_manager):
        """测试获取会话历史（带Git）"""
        session_id = "test-session-id"
        expected_history = [
            {"timestamp": "2023-01-01T00:00:00", "message": "初始化会话"},
            {"timestamp": "2023-01-01T01:00:00", "message": "更新会话状态"}
        ]
        mock_git_manager.get_commit_history.return_value = expected_history
        
        result = session_manager_with_git.get_session_history(session_id)
        
        assert result == expected_history
        mock_git_manager.get_commit_history.assert_called_once()

    def test_get_session_history_without_git(self, session_manager, mock_session_store):
        """测试获取会话历史（无Git）"""
        session_id = "test-session-id"
        session_data = {
            "metadata": {
                "session_id": session_id,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T01:00:00"
            }
        }
        mock_session_store.get_session.return_value = session_data
        
        result = session_manager.get_session_history(session_id)
        
        assert len(result) == 1
        assert result[0]["timestamp"] == "2023-01-01T00:00:00"
        assert result[0]["message"] == "会话创建"

    def test_get_session_info(self, session_manager, mock_session_store):
        """测试获取会话信息"""
        session_id = "test-session-id"
        expected_info = {"metadata": {"session_id": session_id}}
        mock_session_store.get_session.return_value = expected_info
        
        result = session_manager.get_session_info(session_id)
        
        assert result == expected_info
        mock_session_store.get_session.assert_called_once_with(session_id)

    def test_session_exists(self, session_manager, mock_session_store):
        """测试检查会话是否存在"""
        session_id = "test-session-id"
        mock_session_store.get_session.return_value = {"metadata": {"session_id": session_id}}
        
        result = session_manager.session_exists(session_id)
        
        assert result is True
        mock_session_store.get_session.assert_called_once_with(session_id)

    def test_session_not_exists(self, session_manager, mock_session_store):
        """测试检查会话不存在"""
        session_id = "non-existent-session"
        mock_session_store.get_session.return_value = None
        
        result = session_manager.session_exists(session_id)
        
        assert result is False

    def test_generate_session_id(self, session_manager):
        """测试生成会话ID"""
        workflow_config_path = "configs/workflows/react_workflow.yaml"
        
        # 创建mock的datetime对象
        mock_now = Mock()
        mock_now.strftime.side_effect = lambda fmt: "251022" if fmt == "%y%m%d" else "174800"
        
        with patch('src.sessions.manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            with patch('src.sessions.manager.uuid') as mock_uuid:
                mock_uuid.uuid4.return_value.__str__.return_value = "1f73e8-1234-5678-9abc-def123456789"
                
                session_id = session_manager._generate_session_id(workflow_config_path)
                
                assert session_id == "react-251022-174800-1f73e8"

    def test_extract_workflow_name(self, session_manager):
        """测试提取工作流名称"""
        # 测试正常情况
        workflow_config_path = "configs/workflows/react_workflow.yaml"
        result = session_manager._extract_workflow_name(workflow_config_path)
        assert result == "react"
        
        # 测试带workflow后缀
        workflow_config_path = "configs/workflows/test_workflow.yaml"
        result = session_manager._extract_workflow_name(workflow_config_path)
        assert result == "test"
        
        # 测试异常情况
        workflow_config_path = ""
        result = session_manager._extract_workflow_name(workflow_config_path)
        assert result == "unknown"

    def test_serialize_state(self, session_manager):
        """测试序列化状态"""
        state = AgentState()
        state.add_message(BaseMessage(content="测试消息"))
        state.current_step = "测试步骤"
        state.workflow_name = "test_workflow"
        state.start_time = datetime(2023, 1, 1, 0, 0, 0)
        
        result = session_manager._serialize_state(state)
        
        assert "messages" in result
        assert "tool_results" in result
        assert "current_step" in result
        assert "max_iterations" in result
        assert "iteration_count" in result
        assert "workflow_name" in result
        assert "start_time" in result
        assert "errors" in result
        assert result["workflow_name"] == "test_workflow"
        assert result["start_time"] == "2023-01-01T00:00:00"

    def test_deserialize_state(self, session_manager):
        """测试反序列化状态"""
        state_data = {
            "messages": [
                {"type": "BaseMessage", "content": "测试消息"}
            ],
            "tool_results": [],
            "current_step": "测试步骤",
            "max_iterations": 10,
            "iteration_count": 0,
            "workflow_name": "test_workflow",
            "start_time": "2023-01-01T00:00:00",
            "errors": []
        }
        
        result = session_manager._deserialize_state(state_data)
        
        assert isinstance(result, AgentState)
        assert len(result.messages) == 1
        assert result.current_step == "测试步骤"
        assert result.workflow_name == "test_workflow"
        assert result.start_time == datetime(2023, 1, 1, 0, 0, 0)