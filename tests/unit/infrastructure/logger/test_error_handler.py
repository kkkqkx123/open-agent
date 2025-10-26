"""错误处理器单元测试"""

import pytest

from src.infrastructure.logger.error_handler import (
    ErrorType,
    ErrorContext,
    GlobalErrorHandler,
    get_global_error_handler,
    handle_error,
    register_error_handler,
    error_handler,
)


class TestErrorType:
    """错误类型测试类"""

    def test_error_type_values(self) -> None:
        """测试错误类型值"""
        assert ErrorType.USER_ERROR.value == "user_error"
        assert ErrorType.SYSTEM_ERROR.value == "system_error"
        assert ErrorType.FATAL_ERROR.value == "fatal_error"
        assert ErrorType.NETWORK_ERROR.value == "network_error"
        assert ErrorType.VALIDATION_ERROR.value == "validation_error"
        assert ErrorType.TIMEOUT_ERROR.value == "timeout_error"
        assert ErrorType.PERMISSION_ERROR.value == "permission_error"
        assert ErrorType.UNKNOWN_ERROR.value == "unknown_error"


class TestErrorContext:
    """错误上下文测试类"""

    def test_error_context_creation(self) -> None:
        """测试错误上下文创建"""
        error = ValueError("Test error")
        context = ErrorContext(
            error_type=ErrorType.USER_ERROR, error=error, context={"key": "value"}
        )

        assert context.error_type == ErrorType.USER_ERROR
        assert context.error == error
        assert context.context == {"key": "value"}
        assert context.traceback is not None
        assert context.timestamp is None  # 在处理时设置

    def test_error_context_to_dict(self) -> None:
        """测试错误上下文转换为字典"""
        error = ValueError("Test error")
        context = ErrorContext(
            error_type=ErrorType.USER_ERROR, error=error, context={"key": "value"}
        )

        result = context.to_dict()

        assert result["error_type"] == "user_error"
        assert result["error_class"] == "ValueError"
        assert result["error_message"] == "Test error"
        assert result["context"] == {"key": "value"}
        assert "traceback" in result


class TestGlobalErrorHandler:
    """全局错误处理器测试类"""

    def test_error_handler_creation(self) -> None:
        """测试错误处理器创建"""
        handler = GlobalErrorHandler()

        assert handler is not None
        assert handler.max_history == 1000
        assert len(handler._error_handlers) >= 3  # 默认处理器

    def test_handle_error_with_default_handler(self) -> None:
        """测试使用默认处理器处理错误"""
        handler = GlobalErrorHandler()

        error = ValueError("Test error")
        message = handler.handle_error(ErrorType.USER_ERROR, error)

        assert "输入参数有误" in message
        assert "Test error" in message

    def test_handle_error_with_custom_handler(self) -> None:
        """测试使用自定义处理器处理错误"""
        handler = GlobalErrorHandler()

        def custom_handler(error):
            return f"自定义处理: {str(error)}"

        handler.register_error_handler(ValueError, custom_handler)

        error = ValueError("Test error")
        message = handler.handle_error(ErrorType.USER_ERROR, error)

        assert message == "自定义处理: Test error"

    def test_error_classification(self) -> None:
        """测试错误分类"""
        handler = GlobalErrorHandler()

        # 测试已知错误类型
        assert handler._classify_error(ValueError("test")) == ErrorType.USER_ERROR
        assert handler._classify_error(TypeError("test")) == ErrorType.USER_ERROR
        assert (
            handler._classify_error(ConnectionError("test")) == ErrorType.NETWORK_ERROR
        )
        assert handler._classify_error(TimeoutError("test")) == ErrorType.TIMEOUT_ERROR

        # 测试未知错误类型
        assert handler._classify_error(Exception("test")) == ErrorType.UNKNOWN_ERROR

    def test_wrap_with_error_handler(self) -> None:
        """测试用错误处理器包装函数"""
        handler = GlobalErrorHandler()

        @handler.wrap_with_error_handler
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(RuntimeError) as exc_info:
            failing_function()

        assert "输入参数有误" in str(exc_info.value)
        assert "Test error" in str(exc_info.value)

    def test_error_history(self) -> None:
        """测试错误历史"""
        handler = GlobalErrorHandler()

        error1 = ValueError("Error 1")
        error2 = TypeError("Error 2")

        handler.handle_error(ErrorType.USER_ERROR, error1)
        handler.handle_error(ErrorType.USER_ERROR, error2)

        history = handler.get_error_history()

        assert len(history) == 2
        assert history[0]["error_message"] == "Error 1"
        assert history[1]["error_message"] == "Error 2"

    def test_clear_error_history(self) -> None:
        """测试清除错误历史"""
        handler = GlobalErrorHandler()

        error = ValueError("Test error")
        handler.handle_error(ErrorType.USER_ERROR, error)

        assert len(handler.get_error_history()) == 1

        handler.clear_error_history()

        assert len(handler.get_error_history()) == 0

    def test_set_error_message(self) -> None:
        """测试设置错误消息"""
        handler = GlobalErrorHandler()

        # 设置自定义错误消息
        handler.set_error_message(ErrorType.USER_ERROR, "用户错误：{error_message}")

        error = ValueError("Test error")
        message = handler.handle_error(ErrorType.USER_ERROR, error)

        assert message == "用户错误：Test error"

    def test_register_error_type_mapping(self) -> None:
        """测试注册错误类型映射"""
        handler = GlobalErrorHandler()

        # 注册新的错误类型映射
        handler.register_error_type_mapping(RuntimeError, ErrorType.SYSTEM_ERROR)

        assert handler._classify_error(RuntimeError("test")) == ErrorType.SYSTEM_ERROR

    def test_get_error_stats(self) -> None:
        """测试获取错误统计"""
        handler = GlobalErrorHandler()

        # 添加一些错误
        handler.handle_error(ErrorType.USER_ERROR, ValueError("Error 1"))
        handler.handle_error(ErrorType.USER_ERROR, TypeError("Error 2"))
        handler.handle_error(ErrorType.NETWORK_ERROR, ConnectionError("Error 3"))

        stats = handler.get_error_stats()

        assert stats["total_errors"] == 3
        assert stats["error_types"]["user_error"] == 2
        assert stats["error_types"]["network_error"] == 1
        assert "ValueError" in stats["error_classes"]
        assert "TypeError" in stats["error_classes"]
        assert "ConnectionError" in stats["error_classes"]


class TestGlobalErrorHandlerFunctions:
    """全局错误处理器函数测试类"""

    def test_get_global_error_handler(self) -> None:
        """测试获取全局错误处理器"""
        handler1 = get_global_error_handler()
        handler2 = get_global_error_handler()

        # 应该返回同一实例
        assert handler1 is handler2

    def test_handle_error_function(self) -> None:
        """测试处理错误函数"""
        error = ValueError("Test error")
        message = handle_error(ErrorType.USER_ERROR, error)

        assert "输入参数有误" in message
        assert "Test error" in message

    def test_register_error_handler_function(self) -> None:
        """测试注册错误处理器函数"""

        def custom_handler(error):
            return f"自定义处理: {str(error)}"

        register_error_handler(ValueError, custom_handler)

        error = ValueError("Test error")
        message = handle_error(ErrorType.USER_ERROR, error)

        assert message == "自定义处理: Test error"

    def test_error_handler_decorator(self) -> None:
        """测试错误处理装饰器"""

        @error_handler(ErrorType.USER_ERROR)
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(RuntimeError) as exc_info:
            failing_function()

        assert "自定义处理: Test error" in str(exc_info.value)

    def test_error_handler_decorator_with_auto_classification(self) -> None:
        """测试错误处理装饰器自动分类"""

        @error_handler()  # 不指定错误类型，自动分类
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(RuntimeError) as exc_info:
            failing_function()

        assert "自定义处理: Test error" in str(exc_info.value)

    def test_error_handler_decorator_with_specific_type(self) -> None:
        """测试错误处理装饰器指定类型"""

        @error_handler(ErrorType.NETWORK_ERROR)
        def failing_function():
            raise ConnectionError("Network error")

        with pytest.raises(RuntimeError) as exc_info:
            failing_function()

        assert "网络连接失败" in str(exc_info.value)
