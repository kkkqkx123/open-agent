"""简化版会话实体单元测试 - 避免循环导入"""

import pytest
import sys
from datetime import datetime

# 直接添加src到路径，避免复杂的导入
sys.path.insert(0, 'src')

# 为了绕过循环导入，我们直接测试实体类定义
def test_session_entity_basic():
    """测试Session实体基本功能"""
    # 动态导入，避免在模块级别导入导致循环依赖
    from src.core.sessions.entities import Session, SessionStatus
    
    # 测试SessionStatus枚举
    assert SessionStatus.ACTIVE == "active"
    assert SessionStatus.COMPLETED == "completed"
    assert SessionStatus.FAILED == "failed"
    
    # 测试Session创建
    session = Session(session_id="test_123")
    assert session.session_id == "test_123"
    assert session.status == SessionStatus.ACTIVE
    assert session.message_count == 0
    assert session.checkpoint_count == 0
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.updated_at, datetime)
    assert session.metadata == {}
    assert session.tags == []
    assert session.thread_ids == []

def test_session_entity_with_custom_values():
    """测试Session实体自定义值"""
    from src.core.sessions.entities import Session, SessionStatus
    
    test_time = datetime.now()
    session = Session(
        session_id="test_456",
        _status=SessionStatus.COMPLETED,
        message_count=10,
        checkpoint_count=5,
        _created_at=test_time,
        _updated_at=test_time,
        metadata={"key": "value"},
        tags=["tag1", "tag2"],
        thread_ids=["thread1", "thread2"]
    )
    
    assert session.session_id == "test_456"
    assert session.status == SessionStatus.COMPLETED
    assert session.message_count == 10
    assert session.checkpoint_count == 5
    assert session.created_at == test_time
    assert session.updated_at == test_time
    assert session.metadata == {"key": "value"}
    assert session.tags == ["tag1", "tag2"]
    assert session.thread_ids == ["thread1", "thread2"]

def test_session_entity_to_dict():
    """测试Session实体转字典功能"""
    from src.core.sessions.entities import Session, SessionStatus
    
    test_time = datetime.now()
    session = Session(
        session_id="test_789",
        _status=SessionStatus.FAILED,
        message_count=3,
        checkpoint_count=1,
        _created_at=test_time,
        _updated_at=test_time,
        metadata={"error": "test"},
        tags=["error"],
        thread_ids=["thread_error"]
    )
    
    result = session.to_dict()
    
    assert result['session_id'] == "test_789"
    assert result['status'] == SessionStatus.FAILED
    assert result['message_count'] == 3
    assert result['checkpoint_count'] == 1
    assert result['created_at'] == test_time.isoformat()
    assert result['updated_at'] == test_time.isoformat()
    assert result['metadata'] == {"error": "test"}
    assert result['tags'] == ["error"]
    assert result['thread_ids'] == ["thread_error"]

def test_session_entity_from_dict():
    """测试Session实体从字典创建"""
    from src.core.sessions.entities import Session, SessionStatus
    
    test_time = datetime.now()
    data = {
        "session_id": "test_from_dict",
        "status": "completed",
        "message_count": 7,
        "checkpoint_count": 2,
        "created_at": test_time.isoformat(),
        "updated_at": test_time.isoformat(),
        "metadata": {"source": "test"},
        "tags": ["from_dict"],
        "thread_ids": ["thread_from_dict"]
    }
    
    session = Session.from_dict(data)
    
    assert session.session_id == "test_from_dict"
    assert session.status == SessionStatus("completed")
    assert session.message_count == 7
    assert session.checkpoint_count == 2
    assert session.metadata == {"source": "test"}
    assert "from_dict" in session.tags
    assert "thread_from_dict" in session.thread_ids

def test_session_entity_update_timestamp():
    """测试Session实体更新时间戳"""
    from src.core.sessions.entities import Session
    
    session = Session(session_id="test_timestamp")
    original_time = session.updated_at
    
    import time
    time.sleep(0.01)  # 确保时间差异
    
    session.update_timestamp()
    assert session.updated_at > original_time

def test_session_entity_class_methods():
    """测试Session实体类方法"""
    from src.core.sessions.entities import Session, SessionStatus
    
    data = {
        "session_id": "test_class_methods",
        "status": "active",
        "message_count": 0,
        "checkpoint_count": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "metadata": {},
        "tags": [],
        "thread_ids": []
    }
    
    session = Session.from_dict(data)
    assert isinstance(session, Session)
    assert session.session_id == "test_class_methods"
    assert session.status == SessionStatus("active")

if __name__ == "__main__":
    test_session_entity_basic()
    test_session_entity_with_custom_values()
    test_session_entity_to_dict()
    test_session_entity_from_dict()
    test_session_entity_update_timestamp()
    test_session_entity_class_methods()
    print("所有简化版测试通过！")