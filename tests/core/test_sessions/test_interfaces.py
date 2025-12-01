"""会话核心接口单元测试"""

import pytest
from abc import ABC, abstractmethod
from src.core.sessions.interfaces import (
    ISessionCore, ISessionValidator, ISessionStateTransition
)
from src.core.sessions.entities import SessionEntity, UserRequestEntity, UserInteractionEntity


class TestISessionCore:
    """ISessionCore接口的测试"""

    def test_isession_core_is_abstract(self):
        """测试ISessionCore是抽象类"""
        assert issubclass(ISessionCore, ABC)
        assert hasattr(ISessionCore, '__abstractmethods__')
        assert len(ISessionCore.__abstractmethods__) == 4  # create_session, validate_session_state, create_user_request, create_user_interaction

    def test_implementation_requires_abstract_methods(self):
        """测试实现类必须实现抽象方法"""
        class IncompleteSessionCore(ISessionCore):
            pass

        with pytest.raises(TypeError):
            IncompleteSessionCore()


class ConcreteSessionCore(ISessionCore):
    """ISessionCore的完整实现类，用于测试"""
    
    def create_session(self, user_id=None, metadata=None):
        return SessionEntity(session_id="session_123", user_id=user_id, metadata=metadata or {})
    
    def validate_session_state(self, session_data):
        return True
    
    def create_user_request(self, content, user_id=None, metadata=None):
        return UserRequestEntity(request_id="request_123", content=content, user_id=user_id, metadata=metadata or {})
    
    def create_user_interaction(self, session_id, interaction_type, content, thread_id=None, metadata=None):
        return UserInteractionEntity(
            interaction_id="interaction_123", 
            session_id=session_id, 
            interaction_type=interaction_type, 
            content=content,
            thread_id=thread_id, 
            metadata=metadata or {}
        )


class TestConcreteSessionCore:
    """ConcreteSessionCore类的测试"""

    def test_create_session(self):
        """测试创建会话"""
        core = ConcreteSessionCore()
        session = core.create_session(user_id="user_123", metadata={"key": "value"})
        
        assert isinstance(session, SessionEntity)
        assert session.user_id == "user_123"
        assert session.metadata == {"key": "value"}

    def test_validate_session_state(self):
        """测试验证会话状态"""
        core = ConcreteSessionCore()
        result = core.validate_session_state({"status": "active", "id": "session_123"})
        
        assert result is True

    def test_create_user_request(self):
        """测试创建用户请求"""
        core = ConcreteSessionCore()
        request = core.create_user_request("Hello", user_id="user_123", metadata={"key": "value"})
        
        assert isinstance(request, UserRequestEntity)
        assert request.content == "Hello"
        assert request.user_id == "user_123"
        assert request.metadata == {"key": "value"}

    def test_create_user_interaction(self):
        """测试创建用户交互"""
        core = ConcreteSessionCore()
        interaction = core.create_user_interaction(
            session_id="session_123",
            interaction_type="user_input",
            content="Hello",
            thread_id="thread_456",
            metadata={"key": "value"}
        )
        
        assert isinstance(interaction, UserInteractionEntity)
        assert interaction.session_id == "session_123"
        assert interaction.interaction_type == "user_input"
        assert interaction.content == "Hello"
        assert interaction.thread_id == "thread_456"
        assert interaction.metadata == {"key": "value"}


class TestISessionValidator:
    """ISessionValidator接口的测试"""

    def test_isession_validator_is_abstract(self):
        """测试ISessionValidator是抽象类"""
        assert issubclass(ISessionValidator, ABC)
        assert hasattr(ISessionValidator, '__abstractmethods__')
        assert len(ISessionValidator.__abstractmethods__) == 3  # validate_session_id, validate_user_request, validate_user_interaction

    def test_implementation_requires_abstract_methods(self):
        """测试实现类必须实现抽象方法"""
        class IncompleteSessionValidator(ISessionValidator):
            pass

        with pytest.raises(TypeError):
            IncompleteSessionValidator()


class ConcreteSessionValidator(ISessionValidator):
    """ISessionValidator的完整实现类，用于测试"""
    
    def validate_session_id(self, session_id):
        return session_id is not None and len(session_id) > 0
    
    def validate_user_request(self, request):
        return request.content is not None and len(request.content) > 0
    
    def validate_user_interaction(self, interaction):
        return interaction.session_id is not None and len(interaction.session_id) > 0


class TestConcreteSessionValidator:
    """ConcreteSessionValidator类的测试"""

    def test_validate_session_id(self):
        """测试验证会话ID"""
        validator = ConcreteSessionValidator()
        
        assert validator.validate_session_id("valid_id") is True
        assert validator.validate_session_id("") is False
        assert validator.validate_session_id(None) is False

    def test_validate_user_request(self):
        """测试验证用户请求"""
        validator = ConcreteSessionValidator()
        request = UserRequestEntity(request_id="request_123", content="Hello")
        
        assert validator.validate_user_request(request) is True
        
        empty_request = UserRequestEntity(request_id="request_123", content="")
        assert validator.validate_user_request(empty_request) is False

    def test_validate_user_interaction(self):
        """测试验证用户交互"""
        validator = ConcreteSessionValidator()
        interaction = UserInteractionEntity(interaction_id="interaction_123", session_id="session_123", content="Hello")
        
        assert validator.validate_user_interaction(interaction) is True
        
        empty_interaction = UserInteractionEntity(interaction_id="interaction_123", session_id="", content="Hello")
        assert validator.validate_user_interaction(empty_interaction) is False


class TestISessionStateTransition:
    """ISessionStateTransition接口的测试"""

    def test_isession_state_transition_is_abstract(self):
        """测试ISessionStateTransition是抽象类"""
        assert issubclass(ISessionStateTransition, ABC)
        assert hasattr(ISessionStateTransition, '__abstractmethods__')
        assert len(ISessionStateTransition.__abstractmethods__) == 2  # can_transition, get_valid_transitions

    def test_implementation_requires_abstract_methods(self):
        """测试实现类必须实现抽象方法"""
        class IncompleteSessionStateTransition(ISessionStateTransition):
            pass

        with pytest.raises(TypeError):
            IncompleteSessionStateTransition()


class ConcreteSessionStateTransition(ISessionStateTransition):
    """ISessionStateTransition的完整实现类，用于测试"""
    
    def can_transition(self, current_status, target_status):
        valid_transitions = {
            "active": ["inactive", "completed", "paused"],
            "inactive": ["active", "completed"],
            "completed": ["active"],
            "paused": ["active", "completed"]
        }
        return target_status in valid_transitions.get(current_status, [])

    def get_valid_transitions(self, current_status):
        valid_transitions = {
            "active": ["inactive", "completed", "paused"],
            "inactive": ["active", "completed"],
            "completed": ["active"],
            "paused": ["active", "completed"]
        }
        return valid_transitions.get(current_status, [])


class TestConcreteSessionStateTransition:
    """ConcreteSessionStateTransition类的测试"""

    def test_can_transition(self):
        """测试状态转换检查"""
        transitioner = ConcreteSessionStateTransition()
        
        assert transitioner.can_transition("active", "inactive") is True
        assert transitioner.can_transition("active", "completed") is True
        assert transitioner.can_transition("active", "unknown") is False
        assert transitioner.can_transition("unknown", "active") is False

    def test_get_valid_transitions(self):
        """测试获取有效转换列表"""
        transitioner = ConcreteSessionStateTransition()
        
        valid_transitions = transitioner.get_valid_transitions("active")
        assert "inactive" in valid_transitions
        assert "completed" in valid_transitions
        assert "paused" in valid_transitions
        assert "active" not in valid_transitions  # 不能转换到自身（如果不在列表中）
        
        unknown_transitions = transitioner.get_valid_transitions("unknown")
        assert unknown_transitions == []