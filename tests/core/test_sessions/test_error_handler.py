"""Sessions模块错误处理器单元测试"""

import pytest
from unittest.mock import Mock, patch
from src.core.sessions.error_handler import (
    SessionErrorHandler, SessionOperationHandler
)
from src.core.common.exceptions.session_thread import (
    SessionThreadException, SessionNotFoundError, ThreadNotFoundError,
    AssociationNotFoundError, SessionThreadInconsistencyError,
    TransactionRollbackError, WorkflowExecutionError, SynchronizationError,
    ConfigurationValidationError
)


class TestSessionErrorHandler:
    """SessionErrorHandler类的测试"""

    def test_can_handle_session_thread_exception(self):
        """测试可以处理SessionThreadException"""
        handler = SessionErrorHandler()
        error = SessionThreadException("test error")
        assert handler.can_handle(error) is True

    def test_can_handle_session_not_found_error(self):
        """测试可以处理SessionNotFoundError"""
        handler = SessionErrorHandler()
        error = SessionNotFoundError("session_123")
        assert handler.can_handle(error) is True

    def test_can_handle_thread_not_found_error(self):
        """测试可以处理ThreadNotFoundError"""
        handler = SessionErrorHandler()
        error = ThreadNotFoundError("thread_123")
        assert handler.can_handle(error) is True

    def test_can_handle_association_not_found_error(self):
        """测试可以处理AssociationNotFoundError"""
        handler = SessionErrorHandler()
        error = AssociationNotFoundError("session_123", "thread_456")
        assert handler.can_handle(error) is True

    def test_can_handle_session_thread_inconsistency_error(self):
        """测试可以处理SessionThreadInconsistencyError"""
        handler = SessionErrorHandler()
        error = SessionThreadInconsistencyError("inconsistency")
        assert handler.can_handle(error) is True

    def test_can_handle_transaction_rollback_error(self):
        """测试可以处理TransactionRollbackError"""
        handler = SessionErrorHandler()
        error = TransactionRollbackError("rollback")
        assert handler.can_handle(error) is True

    def test_can_handle_workflow_execution_error(self):
        """测试可以处理WorkflowExecutionError"""
        handler = SessionErrorHandler()
        error = WorkflowExecutionError("execution")
        assert handler.can_handle(error) is True

    def test_can_handle_synchronization_error(self):
        """测试可以处理SynchronizationError"""
        handler = SessionErrorHandler()
        error = SynchronizationError("sync")
        assert handler.can_handle(error) is True

    def test_can_handle_configuration_validation_error(self):
        """测试可以处理ConfigurationValidationError"""
        handler = SessionErrorHandler()
        error = ConfigurationValidationError("validation")
        assert handler.can_handle(error) is True

    def test_can_handle_value_error(self):
        """测试可以处理ValueError"""
        handler = SessionErrorHandler()
        error = ValueError("validation error")
        assert handler.can_handle(error) is True

    def test_can_handle_other_exceptions(self):
        """测试不能处理其他异常"""
        handler = SessionErrorHandler()
        error = RuntimeError("runtime error")
        assert handler.can_handle(error) is False

    def test_enhance_context_with_session_not_found_error(self):
        """测试增强上下文 - SessionNotFoundError"""
        handler = SessionErrorHandler()
        error = SessionNotFoundError("session_123")
        context = {"operation": "test"}
        enhanced_context = handler._enhance_context(error, context)
        
        assert enhanced_context["module"] == "sessions"
        assert enhanced_context["session_id"] == "session_123"

    def test_enhance_context_with_thread_not_found_error(self):
        """测试增强上下文 - ThreadNotFoundError"""
        handler = SessionErrorHandler()
        error = ThreadNotFoundError("thread_123")
        context = {"operation": "test"}
        enhanced_context = handler._enhance_context(error, context)
        
        assert enhanced_context["module"] == "sessions"
        assert enhanced_context["thread_id"] == "thread_123"

    def test_enhance_context_with_association_not_found_error(self):
        """测试增强上下文 - AssociationNotFoundError"""
        handler = SessionErrorHandler()
        error = AssociationNotFoundError("session_123", "thread_456")
        context = {"operation": "test"}
        enhanced_context = handler._enhance_context(error, context)
        
        assert enhanced_context["module"] == "sessions"
        assert enhanced_context["association_id"] == "unknown"  # 因为AssociationNotFoundError没有association_id属性

    def test_enhance_context_with_value_error(self):
        """测试增强上下文 - ValueError"""
        handler = SessionErrorHandler()
        error = ValueError("session_id cannot be empty")
        context = {"operation": "test"}
        enhanced_context = handler._enhance_context(error, context)
        
        assert enhanced_context["module"] == "sessions"
        assert enhanced_context["validation_field"] == "session_id"

    def test_enhance_context_with_empty_context(self):
        """测试增强空上下文"""
        handler = SessionErrorHandler()
        error = SessionNotFoundError("session_123")
        enhanced_context = handler._enhance_context(error)
        
        assert enhanced_context["module"] == "sessions"
        assert enhanced_context["session_id"] == "session_123"


class TestSessionOperationHandler:
    """SessionOperationHandler类的测试"""

    def test_safe_session_creation_success(self):
        """测试安全Session创建 - 成功"""
        def creation_func(user_id):
            return f"session_for_{user_id}"
        
        result = SessionOperationHandler.safe_session_creation(
            creation_func, user_id="user_123"
        )
        
        assert result == "session_for_user_123"

    def test_safe_session_operation_success(self):
        """测试安全Session操作 - 成功"""
        def operation_func(session_id):
            return f"result_for_{session_id}"
        
        result = SessionOperationHandler.safe_session_operation(
            operation_func, session_id="session_123"
        )
        
        assert result == "result_for_session_123"

    def test_safe_session_operation_with_fallback(self):
        """测试安全Session操作 - 使用降级"""
        def operation_func(session_id):
            raise SessionNotFoundError(session_id)
        
        def fallback_func(session_id):
            return f"fallback_for_{session_id}"
        
        result = SessionOperationHandler.safe_session_operation(
            operation_func, 
            session_id="session_123", 
            fallback_func=fallback_func
        )
        
        assert result == "fallback_for_session_123"

    def test_safe_session_operation_without_fallback_raises_error(self):
        """测试安全Session操作 - 无降级时抛出错误"""
        def operation_func(session_id):
            raise SessionNotFoundError(session_id)
        
        with pytest.raises(SessionNotFoundError):
            SessionOperationHandler.safe_session_operation(
                operation_func, 
                session_id="session_123"
            )

    def test_safe_association_creation_success(self):
        """测试安全关联创建 - 成功"""
        def creation_func(session_id, thread_id, thread_name):
            return f"assoc_{session_id}_{thread_id}_{thread_name}"
        
        result = SessionOperationHandler.safe_association_creation(
            creation_func,
            session_id="session_123",
            thread_id="thread_456",
            thread_name="test_thread"
        )
        
        assert result == "assoc_session_123_thread_456_test_thread"

    def test_safe_association_creation_with_empty_session_id_raises_error(self):
        """测试安全关联创建 - 空session_id抛出错误"""
        def creation_func(session_id, thread_id, thread_name):
            return f"assoc_{session_id}_{thread_id}_{thread_name}"
        
        with pytest.raises(AssociationNotFoundError):
            SessionOperationHandler.safe_association_creation(
                creation_func,
                session_id="",
                thread_id="thread_456",
                thread_name="test_thread"
            )

    def test_safe_association_creation_with_empty_thread_id_raises_error(self):
        """测试安全关联创建 - 空thread_id抛出错误"""
        def creation_func(session_id, thread_id, thread_name):
            return f"assoc_{session_id}_{thread_id}_{thread_name}"
        
        with pytest.raises(AssociationNotFoundError):
            SessionOperationHandler.safe_association_creation(
                creation_func,
                session_id="session_123",
                thread_id="",
                thread_name="test_thread"
            )

    def test_safe_association_creation_with_empty_thread_name_raises_error(self):
        """测试安全关联创建 - 空thread_name抛出错误"""
        def creation_func(session_id, thread_id, thread_name):
            return f"assoc_{session_id}_{thread_id}_{thread_name}"
        
        with pytest.raises(AssociationNotFoundError):
            SessionOperationHandler.safe_association_creation(
                creation_func,
                session_id="session_123",
                thread_id="thread_456",
                thread_name=""
            )

    def test_safe_user_interaction_success(self):
        """测试安全用户交互 - 成功"""
        def interaction_func(session_id, interaction_type, content, thread_id):
            return f"interaction_{session_id}_{interaction_type}"
        
        result = SessionOperationHandler.safe_user_interaction(
            interaction_func,
            session_id="session_123",
            interaction_type="user_input",
            content="Hello"
        )
        
        assert result == "interaction_session_123_user_input"

    def test_safe_session_state_update_success(self):
        """测试安全Session状态更新 - 成功"""
        def update_func(session_id, new_status):
            return True
        
        result = SessionOperationHandler.safe_session_state_update(
            update_func,
            session_id="session_123",
            new_status="completed"
        )
        
        assert result is True

    def test_safe_session_state_update_returns_none_defaults_to_false(self):
        """测试安全Session状态更新 - 返回None时默认为False"""
        def update_func(session_id, new_status):
            return None  # 返回None
        
        result = SessionOperationHandler.safe_session_state_update(
            update_func,
            session_id="session_123",
            new_status="completed"
        )
        
        assert result is False

    def test_safe_session_state_update_exception_returns_false(self):
        """测试安全Session状态更新 - 异常时返回False"""
        def update_func(session_id, new_status):
            raise Exception("Update failed")
        
        result = SessionOperationHandler.safe_session_state_update(
            update_func,
            session_id="session_123",
            new_status="completed"
        )
        
        assert result is False