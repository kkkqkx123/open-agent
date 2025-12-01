"""Session-Thread关联实体单元测试"""

import pytest
from datetime import datetime
from src.core.sessions.association import SessionThreadAssociation
from src.core.common.exceptions.session_thread import AssociationNotFoundError


class TestSessionThreadAssociation:
    """SessionThreadAssociation类的测试"""

    def test_initialization_with_valid_data(self):
        """测试使用有效数据初始化"""
        association = SessionThreadAssociation(
            session_id="session_123",
            thread_id="thread_456",
            thread_name="test_thread"
        )
        
        assert association.session_id == "session_123"
        assert association.thread_id == "thread_456"
        assert association.thread_name == "test_thread"
        assert association.is_active is True
        assert association.association_type == "session_thread"
        assert isinstance(association.created_at, datetime)
        assert isinstance(association.updated_at, datetime)
        assert association.metadata == {}

    def test_initialization_with_empty_session_id_raises_error(self):
        """测试使用空session_id初始化时抛出错误"""
        with pytest.raises(AssociationNotFoundError):
            SessionThreadAssociation(
                session_id="",
                thread_id="thread_456",
                thread_name="test_thread"
            )

    def test_initialization_with_empty_thread_id_raises_error(self):
        """测试使用空thread_id初始化时抛出错误"""
        with pytest.raises(AssociationNotFoundError):
            SessionThreadAssociation(
                session_id="session_123",
                thread_id="",
                thread_name="test_thread"
            )

    def test_initialization_with_empty_thread_name_raises_error(self):
        """测试使用空thread_name初始化时抛出错误"""
        with pytest.raises(AssociationNotFoundError):
            SessionThreadAssociation(
                session_id="session_123",
                thread_id="thread_456",
                thread_name=""
            )

    def test_update_timestamp(self):
        """测试更新时间戳功能"""
        association = SessionThreadAssociation(
            session_id="session_123",
            thread_id="thread_456",
            thread_name="test_thread"
        )
        
        original_updated_at = association.updated_at
        # 简单延迟以确保时间戳不同
        import time
        time.sleep(0.01)
        
        association.update_timestamp()
        assert association.updated_at > original_updated_at

    def test_deactivate(self):
        """测试停用关联功能"""
        association = SessionThreadAssociation(
            session_id="session_123",
            thread_id="thread_456",
            thread_name="test_thread"
        )
        
        assert association.is_active is True
        association.deactivate()
        assert association.is_active is False

    def test_activate(self):
        """测试激活关联功能"""
        association = SessionThreadAssociation(
            session_id="session_123",
            thread_id="thread_456",
            thread_name="test_thread"
        )
        
        association.deactivate()  # 先停用
        assert association.is_active is False
        association.activate()   # 再激活
        assert association.is_active is True

    def test_update_metadata(self):
        """测试更新元数据功能"""
        association = SessionThreadAssociation(
            session_id="session_123",
            thread_id="thread_456",
            thread_name="test_thread"
        )
        
        original_updated_at = association.updated_at
        import time
        time.sleep(0.01)
        
        new_metadata = {"key1": "value1", "key2": "value2"}
        association.update_metadata(new_metadata)
        
        assert association.metadata == new_metadata
        assert association.updated_at > original_updated_at

    def test_to_dict(self):
        """测试转换为字典功能"""
        association = SessionThreadAssociation(
            session_id="session_123",
            thread_id="thread_456",
            thread_name="test_thread",
            metadata={"key": "value"}
        )
        
        result = association.to_dict()
        
        assert result["session_id"] == "session_123"
        assert result["thread_id"] == "thread_456"
        assert result["thread_name"] == "test_thread"
        assert result["is_active"] is True
        assert result["association_type"] == "session_thread"
        assert result["metadata"] == {"key": "value"}
        assert "created_at" in result
        assert "updated_at" in result

    def test_from_dict(self):
        """测试从字典创建实例功能"""
        original_data = {
            "association_id": "assoc_789",
            "session_id": "session_123",
            "thread_id": "thread_456",
            "thread_name": "test_thread",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_active": False,
            "association_type": "session_thread",
            "metadata": {"key": "value"}
        }
        
        association = SessionThreadAssociation.from_dict(original_data)
        
        assert association.association_id == "assoc_789"
        assert association.session_id == "session_123"
        assert association.thread_id == "thread_456"
        assert association.thread_name == "test_thread"
        assert association.is_active is False
        assert association.association_type == "session_thread"
        assert association.metadata == {"key": "value"}

    def test_from_dict_missing_fields(self):
        """测试从字典创建实例时缺少字段"""
        original_data = {
            "session_id": "session_123",
            "thread_id": "thread_456",
            "thread_name": "test_thread",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        association = SessionThreadAssociation.from_dict(original_data)
        
        assert association.session_id == "session_123"
        assert association.thread_id == "thread_456"
        assert association.thread_name == "test_thread"
        assert association.is_active is True  # 默认值
        assert association.association_type == "session_thread"  # 默认值

    def test_str_representation(self):
        """测试字符串表示"""
        association = SessionThreadAssociation(
            session_id="session_123",
            thread_id="thread_456",
            thread_name="test_thread"
        )
        
        str_repr = str(association)
        assert "session_123" in str_repr
        assert "thread_456" in str_repr
        assert "test_thread" in str_repr

    def test_repr_representation(self):
        """测试详细字符串表示"""
        association = SessionThreadAssociation(
            session_id="session_123",
            thread_id="thread_456",
            thread_name="test_thread"
        )
        
        repr_str = repr(association)
        assert "session_123" in repr_str
        assert "thread_456" in repr_str
        assert "test_thread" in repr_str
        assert "is_active=True" in repr_str