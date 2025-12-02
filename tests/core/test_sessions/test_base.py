"""Session基础抽象类单元测试"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from src.core.sessions.base import SessionBase
from src.core.common.exceptions.session_thread import AssociationNotFoundError


class MockSessionBase(SessionBase):
    """用于测试的SessionBase模拟类"""
    
    def validate(self) -> bool:
        """模拟验证方法"""
        return True
    
    def to_dict(self) -> dict:
        """模拟转换为字典方法"""
        return self.get_session_data()


class TestSessionBase:
    """SessionBase类的测试"""

    def test_initialization_with_session_data(self):
        """测试使用会话数据初始化"""
        session_data = {
            "id": "session_123",
            "status": "active",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "metadata": {"key": "value"},
            "config": {"setting": "value"},
            "state": {"data": "value"},
            "message_count": 5,
            "checkpoint_count": 2
        }
        
        session = MockSessionBase(session_data)
        
        assert session.id == "session_123"
        assert session.status == "active"
        assert session.metadata == {"key": "value"}
        assert session.config == {"setting": "value"}
        assert session.state == {"data": "value"}
        assert session.message_count == 5
        assert session.checkpoint_count == 2

    def test_id_property(self):
        """测试ID属性"""
        session_data = {"id": "session_456"}
        session = MockSessionBase(session_data)
        assert session.id == "session_456"

    def test_status_property(self):
        """测试状态属性"""
        session_data = {"status": "inactive"}
        session = MockSessionBase(session_data)
        assert session.status == "inactive"

    def test_graph_id_property(self):
        """测试图ID属性"""
        session_data = {"graph_id": "graph_789"}
        session = MockSessionBase(session_data)
        assert session.graph_id == "graph_789"

    def test_thread_id_property(self):
        """测试线程ID属性"""
        session_data = {"thread_id": "thread_abc"}
        session = MockSessionBase(session_data)
        assert session.thread_id == "thread_abc"

    def test_created_at_property_with_datetime(self):
        """测试创建时间属性（datetime对象）"""
        now = datetime.now()
        session_data = {"created_at": now}
        session = MockSessionBase(session_data)
        assert session.created_at == now

    def test_created_at_property_with_isoformat_string(self):
        """测试创建时间属性（ISO格式字符串）"""
        now = datetime.now()
        session_data = {"created_at": now.isoformat()}
        session = MockSessionBase(session_data)
        assert session.created_at.isoformat() == now.isoformat()

    def test_updated_at_property(self):
        """测试更新时间属性"""
        now = datetime.now()
        session_data = {"updated_at": now}
        session = MockSessionBase(session_data)
        assert session.updated_at == now

    def test_metadata_property(self):
        """测试元数据属性"""
        session_data = {"metadata": {"key1": "value1", "key2": "value2"}}
        session = MockSessionBase(session_data)
        assert session.metadata == {"key1": "value1", "key2": "value2"}

    def test_config_property(self):
        """测试配置属性"""
        session_data = {"config": {"setting1": "value1", "setting2": "value2"}}
        session = MockSessionBase(session_data)
        assert session.config == {"setting1": "value1", "setting2": "value2"}

    def test_state_property_with_session_state(self):
        """测试状态属性（带会话状态对象）"""
        mock_state = Mock()
        mock_state.to_dict.return_value = {'data': {'state_key': 'state_value'}}
        session_data = {"state": {"data": "original_value"}}
        session = MockSessionBase(session_data, session_state=mock_state)
        assert session.state == {"state_key": "state_value"}

    def test_state_property_without_session_state(self):
        """测试状态属性（不带会话状态对象）"""
        session_data = {"state": {"data": "value"}}
        session = MockSessionBase(session_data)
        assert session.state == {"data": "value"}

    def test_state_setter_with_session_state(self):
        """测试状态设置器（带会话状态对象）"""
        mock_state = Mock()
        session_data = {"state": {}}
        session = MockSessionBase(session_data, session_state=mock_state)
        session.state = {"new_state": "value"}
        assert mock_state.set_data.called
        assert session._session_data["state"] == {"new_state": "value"}

    def test_state_setter_without_session_state(self):
        """测试状态设置器（不带会话状态对象）"""
        session_data = {"state": {}}
        session = MockSessionBase(session_data)
        session.state = {"new_state": "value"}
        assert session._session_data["state"] == {"new_state": "value"}

    def test_message_count_property_with_session_state(self):
        """测试消息计数属性（带会话状态对象）"""
        mock_state = Mock()
        mock_state.message_count = 10
        session_data = {"message_count": 5}
        session = MockSessionBase(session_data, session_state=mock_state)
        assert session.message_count == 10

    def test_message_count_property_without_session_state(self):
        """测试消息计数属性（不带会话状态对象）"""
        session_data = {"message_count": 5}
        session = MockSessionBase(session_data)
        assert session.message_count == 5

    def test_message_count_setter_with_session_state(self):
        """测试消息计数设置器（带会话状态对象）"""
        mock_state = Mock()
        session_data = {"message_count": 0}
        session = MockSessionBase(session_data, session_state=mock_state)
        session.message_count = 15
        # 检查是否尝试设置私有属性
        assert session._session_data["message_count"] == 15

    def test_message_count_setter_without_session_state(self):
        """测试消息计数设置器（不带会话状态对象）"""
        session_data = {"message_count": 0}
        session = MockSessionBase(session_data)
        session.message_count = 15
        assert session._session_data["message_count"] == 15

    def test_checkpoint_count_property_with_session_state(self):
        """测试检查点计数属性（带会话状态对象）"""
        mock_state = Mock()
        mock_state.checkpoint_count = 7
        session_data = {"checkpoint_count": 3}
        session = MockSessionBase(session_data, session_state=mock_state)
        assert session.checkpoint_count == 7

    def test_checkpoint_count_property_without_session_state(self):
        """测试检查点计数属性（不带会话状态对象）"""
        session_data = {"checkpoint_count": 3}
        session = MockSessionBase(session_data)
        assert session.checkpoint_count == 3

    def test_checkpoint_count_setter_with_session_state(self):
        """测试检查点计数设置器（带会话状态对象）"""
        mock_state = Mock()
        session_data = {"checkpoint_count": 0}
        session = MockSessionBase(session_data, session_state=mock_state)
        session.checkpoint_count = 8
        assert session._session_data["checkpoint_count"] == 8

    def test_checkpoint_count_setter_without_session_state(self):
        """测试检查点计数设置器（不带会话状态对象）"""
        session_data = {"checkpoint_count": 0}
        session = MockSessionBase(session_data)
        session.checkpoint_count = 8
        assert session._session_data["checkpoint_count"] == 8

    def test_get_session_data(self):
        """测试获取会话数据"""
        session_data = {"id": "session_123", "status": "active"}
        session = MockSessionBase(session_data)
        result = session.get_session_data()
        assert result == {"id": "session_123", "status": "active"}

    def test_update_session_data(self):
        """测试更新会话数据"""
        session_data = {"id": "session_123", "status": "active", "message_count": 5}
        session = MockSessionBase(session_data)
        
        new_data = {"status": "inactive", "checkpoint_count": 3}
        session.update_session_data(new_data)
        
        assert session._session_data["status"] == "inactive"
        assert session._session_data["checkpoint_count"] == 3
        assert session._session_data["id"] == "session_123"  # 保持不变

    def test_increment_message_count_with_session_state(self):
        """测试增加消息计数（带会话状态对象）"""
        mock_state = Mock()
        session_data = {"message_count": 5}
        session = MockSessionBase(session_data, session_state=mock_state)
        session.increment_message_count()
        assert mock_state.increment_message_count.called

    def test_increment_message_count_without_session_state(self):
        """测试增加消息计数（不带会话状态对象）"""
        session_data = {"message_count": 5}
        session = MockSessionBase(session_data)
        session.increment_message_count()
        assert session._session_data["message_count"] == 6

    def test_increment_checkpoint_count_with_session_state(self):
        """测试增加检查点计数（带会话状态对象）"""
        mock_state = Mock()
        session_data = {"checkpoint_count": 2}
        session = MockSessionBase(session_data, session_state=mock_state)
        session.increment_checkpoint_count()
        assert mock_state.increment_checkpoint_count.called

    def test_increment_checkpoint_count_without_session_state(self):
        """测试增加检查点计数（不带会话状态对象）"""
        session_data = {"checkpoint_count": 2}
        session = MockSessionBase(session_data)
        session.increment_checkpoint_count()
        assert session._session_data["checkpoint_count"] == 3

    def test_add_thread_with_session_state(self):
        """测试添加线程（带会话状态对象）"""
        mock_state = Mock()
        session_data = {"thread_ids": ["thread_1"]}
        session = MockSessionBase(session_data, session_state=mock_state)
        session.add_thread("thread_2")
        assert mock_state.add_thread.called

    def test_add_thread_without_session_state(self):
        """测试添加线程（不带会话状态对象）"""
        session_data = {"thread_ids": ["thread_1"]}
        session = MockSessionBase(session_data)
        session.add_thread("thread_2")
        assert "thread_2" in session._session_data["thread_ids"]
        assert len(session._session_data["thread_ids"]) == 2

    def test_remove_thread_with_session_state(self):
        """测试移除线程（带会话状态对象）"""
        mock_state = Mock()
        session_data = {"thread_ids": ["thread_1", "thread_2"]}
        session = MockSessionBase(session_data, session_state=mock_state)
        session.remove_thread("thread_1")
        assert mock_state.remove_thread.called

    def test_remove_thread_without_session_state(self):
        """测试移除线程（不带会话状态对象）"""
        session_data = {"thread_ids": ["thread_1", "thread_2"]}
        session = MockSessionBase(session_data)
        session.remove_thread("thread_1")
        assert "thread_1" not in session._session_data["thread_ids"]
        assert len(session._session_data["thread_ids"]) == 1

    def test_update_config_with_session_state(self):
        """测试更新配置（带会话状态对象）"""
        mock_state = Mock()
        session_data = {"config": {"setting1": "value1"}}
        session = MockSessionBase(session_data, session_state=mock_state)
        session.update_config({"setting2": "value2"})
        assert mock_state.update_config.called

    def test_update_config_without_session_state(self):
        """测试更新配置（不带会话状态对象）"""
        session_data = {"config": {"setting1": "value1"}}
        session = MockSessionBase(session_data)
        session.update_config({"setting2": "value2"})
        assert session._session_data["config"]["setting1"] == "value1"
        assert session._session_data["config"]["setting2"] == "value2"

    def test_get_session_summary_with_session_state(self):
        """测试获取会话摘要（带会话状态对象）"""
        mock_state = Mock()
        mock_state.get_session_summary.return_value = {
            "session_id": "session_123",
            "user_id": "user_456",
            "message_count": 10,
            "checkpoint_count": 5,
            "thread_count": 2,
            "thread_ids": ["thread_1", "thread_2"],
            "config_keys": ["key1", "key2"],
            "state_keys": ["state1", "state2"]
        }
        
        session_data = {"id": "session_123"}
        session = MockSessionBase(session_data, session_state=mock_state)
        summary = session.get_session_summary()
        assert summary["session_id"] == "session_123"

    def test_get_session_summary_without_session_state(self):
        """测试获取会话摘要（不带会话状态对象）"""
        session_data = {
            "id": "session_123",
            "user_id": "user_456",
            "message_count": 10,
            "checkpoint_count": 5,
            "thread_ids": ["thread_1", "thread_2"],
            "config": {"key1": "value1", "key2": "value2"},
            "state": {"state1": "value1", "state2": "value2"}
        }
        session = MockSessionBase(session_data)
        summary = session.get_session_summary()
        
        assert summary["session_id"] == "session_123"
        assert summary["user_id"] == "user_456"
        assert summary["message_count"] == 10
        assert summary["checkpoint_count"] == 5
        assert summary["thread_count"] == 2
        assert "thread_1" in summary["thread_ids"]
        assert "key1" in summary["config_keys"]
        assert "state1" in summary["state_keys"]