"""会话存储单元测试"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from src.domain.sessions.store import FileSessionStore, MemorySessionStore, ISessionStore


class TestFileSessionStore:
    """文件会话存储测试类"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def file_store(self, temp_dir):
        """创建文件会话存储实例"""
        return FileSessionStore(temp_dir)

    @pytest.fixture
    def sample_session_data(self):
        """示例会话数据"""
        return {
            "metadata": {
                "session_id": "test-session-id",
                "workflow_config_path": "configs/workflows/test.yaml",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T01:00:00",
                "status": "active"
            },
            "state": {
                "messages": [],
                "tool_results": [],
                "current_step": "",
                "max_iterations": 10,
                "iteration_count": 0
            },
            "workflow_config": {"name": "test"}
        }

    def test_init(self, temp_dir):
        """测试初始化"""
        store = FileSessionStore(temp_dir)
        assert store.storage_path == temp_dir
        assert temp_dir.exists()

    def test_get_session_file(self, file_store):
        """测试获取会话文件路径"""
        session_id = "test-session-id"
        session_file = file_store._get_session_file(session_id)
        expected_path = file_store.storage_path / f"{session_id}.json"
        assert session_file == expected_path

    def test_save_session(self, file_store, sample_session_data):
        """测试保存会话"""
        session_id = "test-session-id"
        
        result = file_store.save_session(session_id, sample_session_data)
        
        assert result is True
        
        # 验证文件是否创建
        session_file = file_store._get_session_file(session_id)
        assert session_file.exists()
        
        # 验证文件内容
        with open(session_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data == sample_session_data

    def test_save_session_error(self, file_store, sample_session_data):
        """测试保存会话出错"""
        session_id = "test-session-id"
        
        # 模拟写入错误
        with patch('builtins.open', side_effect=IOError("写入失败")):
            result = file_store.save_session(session_id, sample_session_data)
            assert result is False

    def test_get_session(self, file_store, sample_session_data):
        """测试获取会话"""
        session_id = "test-session-id"
        
        # 先保存会话
        file_store.save_session(session_id, sample_session_data)
        
        # 获取会话
        result = file_store.get_session(session_id)
        
        assert result == sample_session_data

    def test_get_session_not_exists(self, file_store):
        """测试获取不存在的会话"""
        session_id = "non-existent-session"
        
        result = file_store.get_session(session_id)
        
        assert result is None

    def test_get_session_corrupted_file(self, file_store):
        """测试获取损坏的会话文件"""
        session_id = "corrupted-session"
        session_file = file_store._get_session_file(session_id)
        
        # 创建损坏的JSON文件
        with open(session_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json")
        
        result = file_store.get_session(session_id)
        
        assert result is None

    def test_delete_session(self, file_store, sample_session_data):
        """测试删除会话"""
        session_id = "test-session-id"
        
        # 先保存会话
        file_store.save_session(session_id, sample_session_data)
        
        # 删除会话
        result = file_store.delete_session(session_id)
        
        assert result is True
        
        # 验证文件是否删除
        session_file = file_store._get_session_file(session_id)
        assert not session_file.exists()

    def test_delete_session_not_exists(self, file_store):
        """测试删除不存在的会话"""
        session_id = "non-existent-session"
        
        result = file_store.delete_session(session_id)
        
        assert result is True  # 删除不存在的文件也返回True

    def test_delete_session_error(self, file_store, sample_session_data):
        """测试删除会话出错"""
        session_id = "test-session-id"
        
        # 先保存会话
        file_store.save_session(session_id, sample_session_data)
        
        # 模拟删除错误
        with patch.object(Path, 'unlink', side_effect=IOError("删除失败")):
            result = file_store.delete_session(session_id)
            assert result is False

    def test_list_sessions(self, file_store):
        """测试列出会话"""
        # 创建多个会话
        sessions_data = {
            "session1": {
                "metadata": {
                    "session_id": "session1",
                    "workflow_config_path": "configs/workflows/test1.yaml",
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T01:00:00",
                    "status": "active"
                }
            },
            "session2": {
                "metadata": {
                    "session_id": "session2",
                    "workflow_config_path": "configs/workflows/test2.yaml",
                    "created_at": "2023-01-02T00:00:00",
                    "updated_at": "2023-01-02T01:00:00",
                    "status": "completed"
                }
            }
        }
        
        for session_id, data in sessions_data.items():
            file_store.save_session(session_id, data)
        
        # 列出会话
        result = file_store.list_sessions()
        
        assert len(result) == 2
        
        # 验证会话信息
        session_ids = [s["session_id"] for s in result]
        assert "session1" in session_ids
        assert "session2" in session_ids

    def test_list_sessions_with_corrupted_file(self, file_store):
        """测试列出会话时跳过损坏的文件"""
        # 创建正常会话
        normal_data = {
            "metadata": {
                "session_id": "normal-session",
                "created_at": "2023-01-01T00:00:00"
            }
        }
        file_store.save_session("normal-session", normal_data)
        
        # 创建损坏的会话文件
        corrupted_file = file_store.storage_path / "corrupted-session.json"
        with open(corrupted_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json")
        
        # 列出会话
        result = file_store.list_sessions()
        
        assert len(result) == 1
        assert result[0]["session_id"] == "normal-session"

    def test_list_sessions_empty(self, file_store):
        """测试列出空会话列表"""
        result = file_store.list_sessions()
        assert result == []

    def test_session_exists(self, file_store, sample_session_data):
        """测试检查会话是否存在"""
        session_id = "test-session-id"
        
        # 会话不存在
        assert not file_store.session_exists(session_id)
        
        # 保存会话
        file_store.save_session(session_id, sample_session_data)
        
        # 会话存在
        assert file_store.session_exists(session_id)

    def test_atomic_save(self, file_store, sample_session_data):
        """测试原子性保存"""
        session_id = "test-session-id"
        
        # 模拟临时文件替换失败
        with patch.object(Path, 'replace', side_effect=IOError("替换失败")):
            result = file_store.save_session(session_id, sample_session_data)
            assert result is False
        
        # 验证临时文件被清理
        temp_file = file_store._get_session_file(session_id).with_suffix(".tmp")
        assert not temp_file.exists()


class TestMemorySessionStore:
    """内存会话存储测试类"""

    @pytest.fixture
    def memory_store(self):
        """创建内存会话存储实例"""
        return MemorySessionStore()

    @pytest.fixture
    def sample_session_data(self):
        """示例会话数据"""
        return {
            "metadata": {
                "session_id": "test-session-id",
                "workflow_config_path": "configs/workflows/test.yaml",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T01:00:00",
                "status": "active"
            },
            "state": {
                "messages": [],
                "tool_results": [],
                "current_step": "",
                "max_iterations": 10,
                "iteration_count": 0
            }
        }

    def test_init(self, memory_store):
        """测试初始化"""
        assert memory_store._sessions == {}

    def test_save_session(self, memory_store, sample_session_data):
        """测试保存会话"""
        session_id = "test-session-id"
        
        result = memory_store.save_session(session_id, sample_session_data)
        
        assert result is True
        assert session_id in memory_store._sessions
        assert memory_store._sessions[session_id] == sample_session_data

    def test_save_session_deep_copy(self, memory_store, sample_session_data):
        """测试保存会话时创建深拷贝"""
        session_id = "test-session-id"
        
        memory_store.save_session(session_id, sample_session_data)
        
        # 修改原始数据
        sample_session_data["metadata"]["status"] = "modified"
        
        # 验证存储的数据未受影响
        stored_data = memory_store.get_session(session_id)
        assert stored_data["metadata"]["status"] == "active"

    def test_save_session_error(self, memory_store):
        """测试保存会话出错"""
        session_id = "test-session-id"
        
        # 创建一个自定义字典类，其 deepcopy 方法会抛出异常
        class FailingDeepCopyDict(dict):
            def __deepcopy__(self, memo):
                raise Exception("深拷贝失败")
        
        # 使用自定义字典
        failing_dict = FailingDeepCopyDict()
        result = memory_store.save_session(session_id, failing_dict)
        assert result is False

    def test_get_session(self, memory_store, sample_session_data):
        """测试获取会话"""
        session_id = "test-session-id"
        
        # 保存会话
        memory_store.save_session(session_id, sample_session_data)
        
        # 获取会话
        result = memory_store.get_session(session_id)
        
        assert result == sample_session_data

    def test_get_session_not_exists(self, memory_store):
        """测试获取不存在的会话"""
        session_id = "non-existent-session"
        
        result = memory_store.get_session(session_id)
        
        assert result is None

    def test_delete_session(self, memory_store, sample_session_data):
        """测试删除会话"""
        session_id = "test-session-id"
        
        # 保存会话
        memory_store.save_session(session_id, sample_session_data)
        
        # 删除会话
        result = memory_store.delete_session(session_id)
        
        assert result is True
        assert session_id not in memory_store._sessions

    def test_delete_session_not_exists(self, memory_store):
        """测试删除不存在的会话"""
        session_id = "non-existent-session"
        
        result = memory_store.delete_session(session_id)
        
        assert result is False

    def test_list_sessions(self, memory_store):
        """测试列出会话"""
        # 创建多个会话
        sessions_data = {
            "session1": {
                "metadata": {
                    "session_id": "session1",
                    "workflow_config_path": "configs/workflows/test1.yaml",
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T01:00:00",
                    "status": "active"
                }
            },
            "session2": {
                "metadata": {
                    "session_id": "session2",
                    "workflow_config_path": "configs/workflows/test2.yaml",
                    "created_at": "2023-01-02T00:00:00",
                    "updated_at": "2023-01-02T01:00:00",
                    "status": "completed"
                }
            }
        }
        
        for session_id, data in sessions_data.items():
            memory_store.save_session(session_id, data)
        
        # 列出会话
        result = memory_store.list_sessions()
        
        assert len(result) == 2
        
        # 验证会话信息
        session_ids = [s["session_id"] for s in result]
        assert "session1" in session_ids
        assert "session2" in session_ids

    def test_list_sessions_empty(self, memory_store):
        """测试列出空会话列表"""
        result = memory_store.list_sessions()
        assert result == []

    def test_session_exists(self, memory_store, sample_session_data):
        """测试检查会话是否存在"""
        session_id = "test-session-id"
        
        # 会话不存在
        assert not memory_store.session_exists(session_id)
        
        # 保存会话
        memory_store.save_session(session_id, sample_session_data)
        
        # 会话存在
        assert memory_store.session_exists(session_id)

    def test_clear(self, memory_store, sample_session_data):
        """测试清除所有会话"""
        # 保存多个会话
        memory_store.save_session("session1", sample_session_data)
        memory_store.save_session("session2", sample_session_data)
        
        # 清除所有会话
        memory_store.clear()
        
        # 验证所有会话已清除
        assert memory_store._sessions == {}
        assert memory_store.list_sessions() == []


class TestISessionStore:
    """会话存储接口测试类"""

    def test_interface_methods(self):
        """测试接口方法定义"""
        # 验证接口定义了所有必需的方法
        assert hasattr(ISessionStore, 'save_session')
        assert hasattr(ISessionStore, 'get_session')
        assert hasattr(ISessionStore, 'delete_session')
        assert hasattr(ISessionStore, 'list_sessions')
        assert hasattr(ISessionStore, 'session_exists')
        
        # 验证方法是抽象方法
        assert getattr(ISessionStore.save_session, '__isabstractmethod__', False)
        assert getattr(ISessionStore.get_session, '__isabstractmethod__', False)
        assert getattr(ISessionStore.delete_session, '__isabstractmethod__', False)
        assert getattr(ISessionStore.list_sessions, '__isabstractmethod__', False)
        assert getattr(ISessionStore.session_exists, '__isabstractmethod__', False)