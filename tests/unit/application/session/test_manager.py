"""会话管理器单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
import json
import hashlib

from src.application.sessions.manager import SessionManager, ISessionManager
from src.domain.sessions.store import ISessionStore
from src.application.sessions.git_manager import IGitManager
from src.application.workflow.manager import IWorkflowManager
from src.domain.workflow.config import WorkflowConfig
from src.application.workflow.state import AgentState, BaseMessage


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
        
        # 模拟工作流配置
        mock_config = Mock(spec=WorkflowConfig)
        mock_config.version = "1.0.0"
        mock_config.to_dict.return_value = {"name": "test", "version": "1.0.0"}
        manager.get_workflow_config.return_value = mock_config
        
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
        
        # 模拟配置文件校验和计算
        with patch('builtins.open', mock_open(read_data=b'test config content')):
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
        assert "workflow_config" not in call_args[1]  # 确保没有保存完整配置
        
        # 验证增强的元数据
        metadata = call_args[1]["metadata"]
        assert "workflow_config_path" in metadata
        assert "workflow_summary" in metadata
        assert metadata["workflow_summary"]["name"] == "test"
        assert metadata["workflow_summary"]["version"] == "1.0.0"

    def test_create_session_with_git(self, session_manager_with_git, mock_workflow_manager, 
                                   mock_session_store, mock_git_manager):
        """测试带Git管理器创建会话"""
        workflow_config_path = "configs/workflows/test.yaml"
        
        with patch('builtins.open', mock_open(read_data=b'test config content')):
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

    def test_restore_session_with_config_path(self, session_manager, mock_workflow_manager, mock_session_store):
        """测试使用配置路径恢复会话"""
        session_id = "test-session-id"
        workflow_config_path = "configs/workflows/test.yaml"
        
        # 计算正确的校验和
        test_content = b'test config content'
        expected_checksum = hashlib.md5(test_content).hexdigest()
        
        session_data = {
            "metadata": {
                "session_id": session_id,
                "workflow_config_path": workflow_config_path,
                "workflow_summary": {
                    "workflow_id": "old_workflow_id",
                    "name": "test_workflow",
                    "version": "1.0.0",
                    "checksum": expected_checksum
                }
            },
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
        
        # 模拟配置文件存在
        with patch('pathlib.Path.exists', return_value=True):
            # 模拟配置文件校验和计算
            with patch('builtins.open', mock_open(read_data=b'test config content')):
                # 模拟工作流管理器重新加载工作流
                mock_workflow_manager.load_workflow.return_value = "new_workflow_id"
                mock_workflow_manager.create_workflow.return_value = Mock()
                
                workflow, state = session_manager.restore_session(session_id)
        
        assert workflow is not None
        assert isinstance(state, AgentState)
        
        # 验证使用了配置路径重新加载
        mock_workflow_manager.load_workflow.assert_called_with(workflow_config_path)
        mock_workflow_manager.create_workflow.assert_called_with("new_workflow_id")

    def test_restore_session_fallback_to_original_id(self, session_manager, mock_workflow_manager, mock_session_store):
        """测试回退到原始workflow_id"""
        session_id = "test-session-id"
        workflow_config_path = "configs/workflows/test.yaml"
        
        # 计算正确的校验和
        test_content = b'test config content'
        expected_checksum = hashlib.md5(test_content).hexdigest()
        
        session_data = {
            "metadata": {
                "session_id": session_id,
                "workflow_config_path": workflow_config_path,
                "workflow_summary": {
                    "workflow_id": "original_workflow_id",
                    "name": "test_workflow",
                    "version": "1.0.0",
                    "checksum": expected_checksum
                }
            },
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
        
        # 模拟配置文件存在但加载失败
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=b'test config content')):
                # 第一次加载失败，第二次使用原始ID成功
                mock_workflow_manager.load_workflow.side_effect = [Exception("加载失败"), None]
                mock_workflow_manager.create_workflow.return_value = Mock()
                
                workflow, state = session_manager.restore_session(session_id)
        
        assert workflow is not None
        assert isinstance(state, AgentState)
        
        # 验证最终使用了原始workflow_id
        mock_workflow_manager.create_workflow.assert_called_with("original_workflow_id")

    def test_restore_session_final_fallback(self, session_manager, mock_workflow_manager, mock_session_store):
        """测试最终回退策略"""
        session_id = "test-session-id"
        workflow_config_path = "configs/workflows/test.yaml"
        
        # 计算正确的校验和
        test_content = b'test config content'
        expected_checksum = hashlib.md5(test_content).hexdigest()
        
        session_data = {
            "metadata": {
                "session_id": session_id,
                "workflow_config_path": workflow_config_path,
                "workflow_summary": {
                    "workflow_id": "original_workflow_id",
                    "name": "test_workflow",
                    "version": "1.0.0",
                    "checksum": expected_checksum
                }
            },
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
        
        # 模拟配置文件存在
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=b'test config content')):
                # 前两次都失败，第三次成功
                mock_workflow_manager.load_workflow.side_effect = [
                    Exception("第一次失败"), 
                    None  # 第三次成功
                ]
                mock_workflow_manager.create_workflow.side_effect = [
                    Exception("创建失败"),  # 第二次失败
                    Mock()  # 第三次成功
                ]
                
                # 模拟更新会话元数据
                mock_session_store.save_session.return_value = True
                
                workflow, state = session_manager.restore_session(session_id)
        
        assert workflow is not None
        assert isinstance(state, AgentState)
        
        # 验证最终重新加载并更新了元数据
        assert mock_workflow_manager.load_workflow.call_count == 2
        mock_session_store.save_session.assert_called()

    def test_restore_session_all_strategies_fail(self, session_manager, mock_workflow_manager, mock_session_store):
        """测试所有恢复策略都失败"""
        session_id = "test-session-id"
        workflow_config_path = "configs/workflows/test.yaml"
        
        # 计算正确的校验和
        test_content = b'test config content'
        expected_checksum = hashlib.md5(test_content).hexdigest()
        
        session_data = {
            "metadata": {
                "session_id": session_id,
                "workflow_config_path": workflow_config_path,
                "workflow_summary": {
                    "workflow_id": "original_workflow_id",
                    "name": "test_workflow",
                    "version": "1.0.0",
                    "checksum": expected_checksum
                }
            },
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
        
        # 模拟配置文件存在
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=b'test config content')):
                # 所有策略都失败
                mock_workflow_manager.load_workflow.side_effect = Exception("总是失败")
                mock_workflow_manager.create_workflow.side_effect = Exception("总是失败")
                
                with pytest.raises(ValueError, match="无法恢复会话"):
                    session_manager.restore_session(session_id)

    def test_restore_session_config_file_not_exists(self, session_manager, mock_session_store):
        """测试配置文件不存在的情况"""
        session_id = "test-session-id"
        workflow_config_path = "configs/workflows/nonexistent.yaml"
        
        session_data = {
            "metadata": {
                "session_id": session_id,
                "workflow_config_path": workflow_config_path,
                "workflow_summary": {
                    "workflow_id": "original_workflow_id",
                    "name": "test_workflow",
                    "version": "1.0.0",
                    "checksum": "abc123"
                }
            },
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
        
        # 模拟配置文件不存在
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="工作流配置文件不存在"):
                session_manager.restore_session(session_id)

    def test_validate_workflow_consistency(self, session_manager, mock_workflow_manager):
        """测试工作流配置一致性验证"""
        # 计算正确的校验和
        test_content = b'test config content'
        expected_checksum = hashlib.md5(test_content).hexdigest()
        
        metadata = {
            "workflow_config_path": "configs/workflows/test.yaml",
            "workflow_summary": {
                "version": "1.0.0",
                "checksum": expected_checksum
            }
        }
        workflow_id = "test_workflow_id"
        
        # 模拟配置文件
        with patch('builtins.open', mock_open(read_data=test_content)):
            # 配置一致的情况
            mock_config = Mock(spec=WorkflowConfig)
            mock_config.version = "1.0.0"
            mock_workflow_manager.get_workflow_config.return_value = mock_config
            mock_workflow_manager.get_workflow_summary.return_value = {
                "version": "1.0.0",
                "checksum": expected_checksum
            }
            
            result = session_manager._validate_workflow_consistency(metadata, workflow_id)
            assert result is True
            
            # 版本不一致的情况
            mock_config.version = "2.0.0"
            result = session_manager._validate_workflow_consistency(metadata, workflow_id)
            assert result is False
            
            # 配置不存在的情况
            mock_workflow_manager.get_workflow_config.return_value = None
            mock_workflow_manager.get_workflow_summary.return_value = None
            result = session_manager._validate_workflow_consistency(metadata, workflow_id)
            assert result is False

    def test_calculate_config_checksum(self, session_manager):
        """测试配置文件校验和计算"""
        config_path = "configs/workflows/test.yaml"
        test_content = b"test config content"
        expected_checksum = hashlib.md5(test_content).hexdigest()
        
        with patch('builtins.open', mock_open(read_data=test_content)):
            result = session_manager._calculate_config_checksum(config_path)
            assert result == expected_checksum
        
        # 测试文件读取失败的情况
        with patch('builtins.open', side_effect=Exception("读取失败")):
            result = session_manager._calculate_config_checksum(config_path)
            assert result == ""

    def test_update_session_workflow_info(self, session_manager, mock_workflow_manager, mock_session_store):
        """测试更新会话工作流信息"""
        session_id = "test-session-id"
        new_workflow_id = "new_workflow_id"
        workflow_config_path = "configs/workflows/test.yaml"
        
        session_data = {
            "metadata": {
                "session_id": session_id,
                "workflow_config_path": workflow_config_path,
                "workflow_summary": {
                    "workflow_id": "old_workflow_id",
                    "name": "test_workflow",
                    "version": "1.0.0",
                    "checksum": "old_checksum"
                }
            },
            "state": {}
        }
        mock_session_store.get_session.return_value = session_data
        
        # 模拟新的工作流摘要
        workflow_summary = {
            "workflow_id": new_workflow_id,
            "name": "test_workflow",
            "version": "2.0.0",
            "checksum": "new_checksum"
        }
        mock_workflow_manager.get_workflow_summary.return_value = workflow_summary
        
        session_manager._update_session_workflow_info(session_id, new_workflow_id)
        
        # 验证会话数据被更新
        mock_session_store.save_session.assert_called_once()
        call_args = mock_session_store.save_session.call_args[0]
        updated_data = call_args[1]
        
        assert updated_data["metadata"]["workflow_summary"]["workflow_id"] == new_workflow_id
        assert updated_data["metadata"]["workflow_summary"]["version"] == "2.0.0"
        assert "recovery_info" in updated_data["metadata"]
        assert updated_data["metadata"]["recovery_info"]["reason"] == "workflow_recovery"

    def test_log_recovery_failure(self, session_manager, mock_session_store, temp_dir):
        """测试恢复失败日志记录"""
        session_id = "test-session-id"
        error = Exception("测试错误")
        
        # 创建恢复日志目录
        log_dir = temp_dir / "recovery_logs"
        log_dir.mkdir(exist_ok=True)
        
        session_manager._log_recovery_failure(session_id, error)
        
        # 验证恢复尝试计数
        assert session_manager._get_recovery_attempts(session_id) == 1
        
        # 验证日志文件被创建
        log_file = log_dir / f"{session_id}_recovery.log"
        assert log_file.exists()
        
        # 验证日志内容
        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
            log_data = json.loads(log_content.strip())
            
        assert log_data["session_id"] == session_id
        assert log_data["error_type"] == "Exception"
        assert log_data["error_message"] == "测试错误"
        assert log_data["recovery_attempts"] == 1

    def test_restore_session_not_exists(self, session_manager, mock_session_store):
        """测试恢复不存在的会话"""
        session_id = "non-existent-session"
        mock_session_store.get_session.return_value = None
        
        with pytest.raises(ValueError, match=f"会话 {session_id} 不存在"):
            session_manager.restore_session(session_id)

    def test_save_session(self, session_manager, mock_session_store):
        """测试保存会话"""
        session_id = "test-session-id"
        state = AgentState()
        state.add_message(BaseMessage(content="测试消息"))
        
        session_data = {
            "metadata": {"session_id": session_id, "updated_at": "2023-01-01T00:00:00"},
            "state": {}
        }
        mock_session_store.get_session.return_value = session_data
        
        result = session_manager.save_session(session_id, state)
        
        assert result is True
        mock_session_store.save_session.assert_called_once()

    def test_save_session_not_exists(self, session_manager, mock_session_store):
        """测试保存不存在的会话"""
        session_id = "non-existent-session"
        state = AgentState()
        
        mock_session_store.get_session.return_value = None
        
        result = session_manager.save_session(session_id, state)
        
        assert result is False

    def test_delete_session(self, session_manager, mock_session_store, temp_dir):
        """测试删除会话"""
        session_id = "test-session-id"
        
        # 创建会话目录
        session_dir = temp_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        # 添加恢复尝试记录
        session_manager._recovery_attempts[session_id] = 3
        
        result = session_manager.delete_session(session_id)
        
        assert result is True
        mock_session_store.delete_session.assert_called_once_with(session_id)
        assert not session_dir.exists()
        assert session_id not in session_manager._recovery_attempts

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
        
        with patch('src.application.sessions.manager.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            with patch('src.application.sessions.manager.uuid') as mock_uuid:
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

    def test_get_recovery_attempts(self, session_manager):
        """测试获取恢复尝试次数"""
        session_id = "test-session-id"
        
        # 初始状态
        assert session_manager._get_recovery_attempts(session_id) == 0
        
        # 添加尝试记录
        session_manager._recovery_attempts[session_id] = 3
        assert session_manager._get_recovery_attempts(session_id) == 3

    def test_save_session_with_metrics(self, session_manager, mock_session_store):
        """测试保存会话状态和工作流指标"""
        session_id = "test-session-id"
        state = AgentState()
        state.add_message(BaseMessage(content="测试消息"))
        workflow_metrics = {
            "execution_time": 5.2,
            "nodes_executed": 3,
            "success": True
        }
        
        session_data = {
            "metadata": {"session_id": session_id, "updated_at": "2023-01-01T00:00:00"},
            "state": {}
        }
        mock_session_store.get_session.return_value = session_data
        
        result = session_manager.save_session_with_metrics(session_id, state, workflow_metrics)
        
        assert result is True
        mock_session_store.save_session.assert_called_once()
        
        # 验证工作流指标被保存
        call_args = mock_session_store.save_session.call_args[0]
        saved_data = call_args[1]
        assert "workflow_metrics" in saved_data
        assert saved_data["workflow_metrics"]["execution_time"] == 5.2
        assert saved_data["workflow_metrics"]["nodes_executed"] == 3
        assert saved_data["workflow_metrics"]["success"] is True

    def test_save_session_with_metrics_not_exists(self, session_manager, mock_session_store):
        """测试保存不存在的会话（带指标）"""
        session_id = "non-existent-session"
        state = AgentState()
        workflow_metrics = {"execution_time": 1.0}
        
        mock_session_store.get_session.return_value = None
        
        result = session_manager.save_session_with_metrics(session_id, state, workflow_metrics)
        
        assert result is False

    def test_create_session_with_workflow_summary(self, session_manager, mock_workflow_manager, mock_session_store):
        """测试创建会话时保存工作流摘要"""
        workflow_config_path = "configs/workflows/test.yaml"
        
        # 模拟工作流摘要
        workflow_summary = {
            "workflow_id": "test_workflow_id",
            "name": "test_workflow",
            "version": "1.0.0",
            "description": "测试工作流",
            "config_path": workflow_config_path,
            "checksum": "abc123",
            "loaded_at": "2023-01-01T00:00:00",
            "last_used": None,
            "usage_count": 0
        }
        mock_workflow_manager.get_workflow_summary.return_value = workflow_summary
        
        with patch.object(session_manager, '_generate_session_id', return_value="test-session-id"):
            session_id = session_manager.create_session(workflow_config_path=workflow_config_path)
        
        assert session_id == "test-session-id"
        
        # 验证工作流摘要被保存
        mock_session_store.save_session.assert_called_once()
        call_args = mock_session_store.save_session.call_args[0]
        saved_data = call_args[1]
        
        assert "workflow_summary" in saved_data["metadata"]
        assert saved_data["metadata"]["workflow_summary"]["name"] == "test_workflow"
        assert saved_data["metadata"]["workflow_summary"]["version"] == "1.0.0"
        # 确保没有保存完整的workflow_config
        assert "workflow_config" not in saved_data

    def test_restore_session_with_workflow_summary_fallback(self, session_manager, mock_workflow_manager, mock_session_store):
        """测试使用工作流摘要回退恢复会话"""
        session_id = "test-session-id"
        workflow_config_path = "configs/workflows/test.yaml"
        
        # 模拟工作流摘要
        workflow_summary = {
            "workflow_id": "original_workflow_id",
            "name": "test_workflow",
            "version": "1.0.0"
        }
        
        session_data = {
            "metadata": {
                "session_id": session_id,
                "workflow_config_path": workflow_config_path,
                "workflow_summary": workflow_summary
            },
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
        
        # 模拟配置文件存在但加载失败
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=b'test config content')):
                # 第一次加载失败，第二次使用摘要中的workflow_id成功
                mock_workflow_manager.load_workflow.side_effect = [Exception("加载失败"), None]
                mock_workflow_manager.create_workflow.return_value = Mock()
                
                workflow, state = session_manager.restore_session(session_id)
        
        assert workflow is not None
        assert isinstance(state, AgentState)
        
        # 验证最终使用了摘要中的workflow_id
        mock_workflow_manager.create_workflow.assert_called_with("original_workflow_id")