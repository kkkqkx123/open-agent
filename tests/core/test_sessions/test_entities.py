"""会话核心实体单元测试"""

import pytest
from datetime import datetime
from src.core.sessions.entities import (
    Session, SessionEntity, UserInteractionEntity, UserRequestEntity, SessionContext, SessionStatus
)


class TestSession:
    """Session类的测试"""

    def test_initialization_with_session_id(self):
        """测试使用session_id初始化"""
        session = Session(session_id="session_123")
        
        assert session.session_id == "session_id_123"  # 注意：因为__post_init__会设置uuid
        assert session.status == SessionStatus.ACTIVE
        assert session.message_count == 0
        assert session.checkpoint_count == 0
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)
        assert session.metadata == {}
        assert session.tags == []
        assert session.thread_ids == []

    def test_initialization_with_uuid_generation(self):
        """测试自动生成UUID"""
        session = Session(session_id="")  # 空ID应触发UUID生成
        
        assert session.session_id != ""
        assert len(session.session_id) > 0

    def test_initialization_with_string_status(self):
        """测试使用字符串状态初始化"""
        session = Session(
            session_id="session_123",
            _status="completed"
        )
        
        assert session.status == SessionStatus("completed")

    def test_to_dict(self):
        """测试转换为字典功能"""
        test_time = datetime.now()
        session = Session(
            session_id="session_123",
            _status=AbstractSessionStatus.ACTIVE,
            message_count=5,
            checkpoint_count=2,
            _created_at=test_time,
            _updated_at=test_time,
            metadata={"key": "value"},
            tags=["tag1", "tag2"],
            thread_ids=["thread_1", "thread_2"]
        )
        
        result = session.to_dict()
        
        assert result['session_id'] == "session_123"
        assert result['status'] == SessionStatus.ACTIVE.value
        assert result['message_count'] == 5
        assert result['checkpoint_count'] == 2
        assert result['created_at'] == test_time.isoformat()
        assert result['updated_at'] == test_time.isoformat()
        assert result['metadata'] == {"key": "value"}
        assert result['tags'] == ["tag1", "tag2"]
        assert result['thread_ids'] == ["thread_1", "thread_2"]

    def test_from_dict(self):
        """测试从字典创建实例功能"""
        test_time = datetime.now()
        data = {
            "session_id": "session_456",
            "status": "completed",
            "message_count": 10,
            "checkpoint_count": 3,
            "created_at": test_time.isoformat(),
            "updated_at": test_time.isoformat(),
            "metadata": {"key": "value"},
            "tags": ["tag1", "tag2"],
            "thread_ids": ["thread_1", "thread_2"]
        }
        
        session = Session.from_dict(data)
        
        assert session.session_id == "session_456"
        assert session.status == SessionStatus("completed")
        assert session.message_count == 10
        assert session.checkpoint_count == 3
        assert session.created_at == test_time
        assert session.updated_at == test_time
        assert session.metadata == {"key": "value"}
        assert session.tags == ["tag1", "tag2"]
        assert session.thread_ids == ["thread_1", "thread_2"]

    def test_update_timestamp(self):
        """测试更新时间戳功能"""
        session = Session(session_id="session_123")
        original_updated_at = session.updated_at
        
        import time
        time.sleep(0.01)  # 确保时间戳变化
        
        session.update_timestamp()
        assert session.updated_at > original_updated_at


class TestSessionEntity:
    """SessionEntity类的测试"""

    def test_initialization(self):
        """测试初始化"""
        entity = SessionEntity(
            session_id="session_123",
            user_id="user_456",
            thread_ids=["thread_1", "thread_2"],
            status="active"
        )
        
        assert entity.session_id == "session_123"
        assert entity.user_id == "user_456"
        assert entity.thread_ids == ["thread_1", "thread_2"]
        assert entity.status == "active"
        assert isinstance(entity.created_at, datetime)
        assert isinstance(entity.updated_at, datetime)
        assert entity.metadata == {}

    def test_initialization_with_uuid_generation(self):
        """测试自动生成UUID"""
        entity = SessionEntity(session_id="")  # 空ID应触发UUID生成
        
        assert entity.session_id != ""
        assert len(entity.session_id) > 0

    def test_add_thread(self):
        """测试添加线程"""
        entity = SessionEntity(session_id="session_123", thread_ids=[])
        original_updated_at = entity.updated_at
        
        import time
        time.sleep(0.01)
        
        entity.add_thread("thread_456")
        
        assert "thread_456" in entity.thread_ids
        assert entity.updated_at > original_updated_at

    def test_add_thread_duplicate(self):
        """测试添加重复线程"""
        entity = SessionEntity(session_id="session_123", thread_ids=["thread_1"])
        original_updated_at = entity.updated_at
        
        import time
        time.sleep(0.01)
        
        entity.add_thread("thread_1")  # 重复添加
        
        assert entity.thread_ids == ["thread_1"]  # 应保持不变
        assert entity.updated_at == original_updated_at  # 时间戳未更新

    def test_remove_thread(self):
        """测试移除线程"""
        entity = SessionEntity(session_id="session_123", thread_ids=["thread_1", "thread_2"])
        original_updated_at = entity.updated_at
        
        import time
        time.sleep(0.01)
        
        entity.remove_thread("thread_1")
        
        assert "thread_1" not in entity.thread_ids
        assert entity.updated_at > original_updated_at

    def test_remove_thread_not_exists(self):
        """测试移除不存在的线程"""
        entity = SessionEntity(session_id="session_123", thread_ids=["thread_1"])
        original_updated_at = entity.updated_at
        
        import time
        time.sleep(0.01)
        
        entity.remove_thread("thread_2")  # 不存在的线程
        
        assert entity.thread_ids == ["thread_1"]  # 应保持不变
        assert entity.updated_at == original_updated_at  # 时间戳未更新

    def test_update_status(self):
        """测试更新状态"""
        entity = SessionEntity(session_id="session_123", status="active")
        original_updated_at = entity.updated_at
        
        import time
        time.sleep(0.01)
        
        entity.update_status("completed")
        
        assert entity.status == "completed"
        assert entity.updated_at > original_updated_at

    def test_update_metadata(self):
        """测试更新元数据"""
        entity = SessionEntity(session_id="session_123", metadata={"key1": "value1"})
        original_updated_at = entity.updated_at
        
        import time
        time.sleep(0.01)
        
        entity.update_metadata({"key2": "value2"})
        
        assert entity.metadata["key1"] == "value1"
        assert entity.metadata["key2"] == "value2"
        assert entity.updated_at > original_updated_at

    def test_is_active(self):
        """测试是否活跃检查"""
        active_entity = SessionEntity(session_id="session_123", status="active")
        inactive_entity = SessionEntity(session_id="session_456", status="inactive")
        
        assert active_entity.is_active() is True
        assert inactive_entity.is_active() is False

    def test_to_dict(self):
        """测试转换为字典功能"""
        test_time = datetime.now()
        entity = SessionEntity(
            session_id="session_123",
            user_id="user_456",
            thread_ids=["thread_1", "thread_2"],
            status="active",
            created_at=test_time,
            updated_at=test_time,
            metadata={"key": "value"}
        )
        
        result = entity.to_dict()
        
        assert result["session_id"] == "session_123"
        assert result["user_id"] == "user_456"
        assert result["thread_ids"] == ["thread_1", "thread_2"]
        assert result["status"] == "active"
        assert result["created_at"] == test_time.isoformat()
        assert result["updated_at"] == test_time.isoformat()
        assert result["metadata"] == {"key": "value"}

    def test_from_dict(self):
        """测试从字典创建实例功能"""
        test_time = datetime.now()
        data = {
            "session_id": "session_456",
            "user_id": "user_789",
            "thread_ids": ["thread_3", "thread_4"],
            "status": "completed",
            "created_at": test_time.isoformat(),
            "updated_at": test_time.isoformat(),
            "metadata": {"key": "value"}
        }
        
        entity = SessionEntity.from_dict(data)
        
        assert entity.session_id == "session_456"
        assert entity.user_id == "user_789"
        assert entity.thread_ids == ["thread_3", "thread_4"]
        assert entity.status == "completed"
        assert entity.created_at == test_time
        assert entity.updated_at == test_time
        assert entity.metadata == {"key": "value"}


class TestUserInteractionEntity:
    """UserInteractionEntity类的测试"""

    def test_initialization(self):
        """测试初始化"""
        entity = UserInteractionEntity(
            interaction_id="interaction_123",
            session_id="session_456",
            thread_id="thread_789",
            interaction_type="user_input",
            content="Hello, world!",
            metadata={"key": "value"}
        )
        
        assert entity.interaction_id == "interaction_123"
        assert entity.session_id == "session_456"
        assert entity.thread_id == "thread_789"
        assert entity.interaction_type == "user_input"
        assert entity.content == "Hello, world!"
        assert entity.metadata == {"key": "value"}
        assert isinstance(entity.timestamp, datetime)

    def test_initialization_with_uuid_generation(self):
        """测试自动生成UUID"""
        entity = UserInteractionEntity(
            interaction_id="",  # 空ID应触发UUID生成
            session_id="session_456",
            content="Hello"
        )
        
        assert entity.interaction_id != ""
        assert len(entity.interaction_id) > 0

    def test_to_dict(self):
        """测试转换为字典功能"""
        test_time = datetime.now()
        entity = UserInteractionEntity(
            interaction_id="interaction_123",
            session_id="session_456",
            thread_id="thread_789",
            interaction_type="user_input",
            content="Hello, world!",
            metadata={"key": "value"},
            timestamp=test_time
        )
        
        result = entity.to_dict()
        
        assert result["interaction_id"] == "interaction_123"
        assert result["session_id"] == "session_456"
        assert result["thread_id"] == "thread_789"
        assert result["interaction_type"] == "user_input"
        assert result["content"] == "Hello, world!"
        assert result["metadata"] == {"key": "value"}
        assert result["timestamp"] == test_time.isoformat()

    def test_from_dict(self):
        """测试从字典创建实例功能"""
        test_time = datetime.now()
        data = {
            "interaction_id": "interaction_456",
            "session_id": "session_789",
            "thread_id": "thread_abc",
            "interaction_type": "system_response",
            "content": "System response",
            "metadata": {"key": "value"},
            "timestamp": test_time.isoformat()
        }
        
        entity = UserInteractionEntity.from_dict(data)
        
        assert entity.interaction_id == "interaction_456"
        assert entity.session_id == "session_789"
        assert entity.thread_id == "thread_abc"
        assert entity.interaction_type == "system_response"
        assert entity.content == "System response"
        assert entity.metadata == {"key": "value"}
        assert entity.timestamp == test_time


class TestUserRequestEntity:
    """UserRequestEntity类的测试"""

    def test_initialization(self):
        """测试初始化"""
        entity = UserRequestEntity(
            request_id="request_123",
            user_id="user_456",
            content="Hello, world!",
            metadata={"key": "value"}
        )
        
        assert entity.request_id == "request_123"
        assert entity.user_id == "user_456"
        assert entity.content == "Hello, world!"
        assert entity.metadata == {"key": "value"}
        assert isinstance(entity.timestamp, datetime)

    def test_initialization_with_uuid_generation(self):
        """测试自动生成UUID"""
        entity = UserRequestEntity(
            request_id="",  # 空ID应触发UUID生成
            content="Hello"
        )
        
        assert entity.request_id != ""
        assert len(entity.request_id) > 0

    def test_to_dict(self):
        """测试转换为字典功能"""
        test_time = datetime.now()
        entity = UserRequestEntity(
            request_id="request_123",
            user_id="user_456",
            content="Hello, world!",
            metadata={"key": "value"},
            timestamp=test_time
        )
        
        result = entity.to_dict()
        
        assert result["request_id"] == "request_123"
        assert result["user_id"] == "user_456"
        assert result["content"] == "Hello, world!"
        assert result["metadata"] == {"key": "value"}
        assert result["timestamp"] == test_time.isoformat()

    def test_from_dict(self):
        """测试从字典创建实例功能"""
        test_time = datetime.now()
        data = {
            "request_id": "request_456",
            "user_id": "user_789",
            "content": "User request",
            "metadata": {"key": "value"},
            "timestamp": test_time.isoformat()
        }
        
        entity = UserRequestEntity.from_dict(data)
        
        assert entity.request_id == "request_456"
        assert entity.user_id == "user_789"
        assert entity.content == "User request"
        assert entity.metadata == {"key": "value"}
        assert entity.timestamp == test_time


class TestSessionContext:
    """SessionContext类的测试"""

    def test_initialization(self):
        """测试初始化"""
        context = SessionContext(
            session_id="session_123",
            user_id="user_456",
            thread_ids=["thread_1", "thread_2"],
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={"key": "value"}
        )
        
        assert context.session_id == "session_123"
        assert context.user_id == "user_456"
        assert context.thread_ids == ["thread_1", "thread_2"]
        assert context.status == "active"
        assert isinstance(context.created_at, datetime)
        assert isinstance(context.updated_at, datetime)
        assert context.metadata == {"key": "value"}