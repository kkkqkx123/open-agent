"""错误处理器单元测试"""

import pytest

from src.logging.error_handler import (
    ErrorType,
    ErrorContext,
    GlobalErrorHandler,
    get_global_error_handler,
    handle_error,
    register_error_handler,
    error_handler
)


class TestErrorType:
    """错误类型测试类"""
    
    def test_error_type_values(self):
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
    
    def test_error_context_creation(self):
        """测试错误上下文创建"""
        error = ValueError("Test error")
        context = ErrorContext(
            error_type=ErrorType.USER_ERROR,
            error=error,
            context={"key": "value"}
        )
        
        assert context.error_type == ErrorType.USER_ERROR
        assert context.error == error
        assert context.context == {"key": "value"}
        assert context.traceback is not None
        assert context.timestamp is None  # 在处理时设置
    
    def test_error_context_to_dict(self):
        """测试错误上下文转换为字典"""
        error = ValueError("Test error")
        context = ErrorContext(
            error_type=ErrorType.USER_ERROR,
            error=error,
            context={"key": "value"}
        )
        
        # 设置时间戳
        import datetime
        context.timestamp = datetime.datetime.now()
        
        context_dict = context.to_dict()
        
        assert context_dict['error_type'] == "user_error"
        assert context_dict['error_class'] == "ValueError"
        assert context_dict['error_message'] == "Test error"
        assert context_dict['context'] == {"key": "value"}
        assert context_dict['traceback'] is not None
        assert context_dict['timestamp'] is not None


class TestGlobalErrorHandler:
    """全局错误处理器测试类"""
    
    def test_error_handler_creation(self):
        """测试错误处理器创建"""
        handler = GlobalErrorHandler()
        
        assert handler.max_history == 1000
        assert len(handler._error_handlers) > 0  # 有默认处理器
        assert len(handler._error_type_mapping) > 0  # 有默认映射
    
    def test_handle_error_with_default_handler(self):
        """测试使用默认处理器处理错误"""
        handler = GlobalErrorHandler()
        
        error = ValueError("Test error")
        message = handler.handle_error(ErrorType.USER_ERROR, error)
        
        assert "输入参数有误" in message
        assert "Test error" in message
    
    def test_handle_error_with_custom_handler(self):
        """测试使用自定义处理器处理错误"""
        handler = GlobalErrorHandler()
        
        # 注册自定义处理器
        def custom_handler(error):
            return f"自定义错误: {str(error)}"
        
        handler.register_error_handler(ValueError, custom_handler)
        
        error = ValueError("Test error")
        message = handler.handle_error(ErrorType.USER_ERROR, error)
        
        assert message == "自定义错误: Test error"
    
    def test_error_classification(self):
        """测试错误分类"""
        handler = GlobalErrorHandler()
        
        # 测试已知错误类型
        assert handler._classify_error(ValueError()) == ErrorType.USER_ERROR
        assert handler._classify_error(ConnectionError()) == ErrorType.NETWORK_ERROR
        assert handler._classify_error(TimeoutError()) == ErrorType.TIMEOUT_ERROR
        assert handler._classify_error(PermissionError()) == ErrorType.PERMISSION_ERROR
        
        # 测试未知错误类型
        class CustomError(Exception):
            pass
        
        assert handler._classify_error(CustomError()) == ErrorType.UNKNOWN_ERROR
    
    def test_wrap_with_error_handler(self):
        """测试用错误处理器包装函数"""
        handler = GlobalErrorHandler()
        
        @handler.wrap_with_error_handler
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(RuntimeError) as exc_info:
            failing_function()
        
        assert "输入参数有误" in str(exc_info.value)
        assert "Test error" in str(exc_info.value)
    
    def test_error_history(self):
        """测试错误历史"""
        handler = GlobalErrorHandler()
        
        # 处理一些错误
        handler.handle_error(ErrorType.USER_ERROR, ValueError("Error 1"))
        handler.handle_error(ErrorType.SYSTEM_ERROR, RuntimeError("Error 2"))
        
        # 获取错误历史
        history = handler.get_error_history()
        
        assert len(history) == 2
        assert history[0]['error_type'] == "user_error"
        assert history[0]['error_class'] == "ValueError"
        assert history[0]['error_message'] == "Error 1"
        
        assert history[1]['error_type'] == "system_error"
        assert history[1]['error_class'] == "RuntimeError"
        assert history[1]['error_message'] == "Error 2"
    
    def test_clear_error_history(self):
        """测试清除错误历史"""
        handler = GlobalErrorHandler()
        
        # 处理一些错误
        handler.handle_error(ErrorType.USER_ERROR, ValueError("Test error"))
        
        # 验证历史存在
        history = handler.get_error_history()
        assert len(history) == 1
        
        # 清除历史
        handler.clear_error_history()
        
        # 验证历史已清除
        history = handler.get_error_history()
        assert len(history) == 0
    
    def test_set_error_message(self):
        """测试设置错误消息"""
        handler = GlobalErrorHandler()
        
        # 设置自定义消息
        handler.set_error_message(ErrorType.USER_ERROR, "自定义用户错误: {error_message}")
        
        error = ValueError("Test error")
        message = handler.handle_error(ErrorType.USER_ERROR, error)
        
        assert message == "自定义用户错误: Test error"
    
    def test_register_error_type_mapping(self):
        """测试注册错误类型映射"""
        handler = GlobalErrorHandler()
        
        class CustomError(Exception):
            pass
        
        # 注册自定义映射
        handler.register_error_type_mapping(CustomError, ErrorType.FATAL_ERROR)
        
        error = CustomError("Test error")
        error_type = handler._classify_error(error)
        
        assert error_type == ErrorType.FATAL_ERROR
    
    def test_get_error_stats(self):
        """测试获取错误统计"""
        handler = GlobalErrorHandler()
        
        # 处理一些错误
        handler.handle_error(ErrorType.USER_ERROR, ValueError("Error 1"))
        handler.handle_error(ErrorType.USER_ERROR, TypeError("Error 2"))
        handler.handle_error(ErrorType.SYSTEM_ERROR, RuntimeError("Error 3"))
        
        # 获取统计
        stats = handler.get_error_stats()
        
        assert stats['total_errors'] == 3
        assert stats['error_types']['user_error'] == 2
        assert stats['error_types']['system_error'] == 1
        assert stats['error_classes']['ValueError'] == 1
        assert stats['error_classes']['TypeError'] == 1
        assert stats['error_classes']['RuntimeError'] == 1
        assert len(stats['recent_errors']) == 3


class TestGlobalErrorHandlerFunctions:
    """全局错误处理器函数测试类"""
    
    def test_get_global_error_handler(self):
        """测试获取全局错误处理器"""
        handler1 = get_global_error_handler()
        handler2 = get_global_error_handler()
        
        # 应该返回同一实例
        assert handler1 is handler2
    
    def test_handle_error_function(self):
        """测试处理错误函数"""
        error = ValueError("Test error")
        message = handle_error(ErrorType.USER_ERROR, error)
        
        assert "输入参数有误" in message
        assert "Test error" in message
    
    def test_register_error_handler_function(self):
        """测试注册错误处理器函数"""
        def custom_handler(error):
            return f"自定义处理: {str(error)}"
        
        register_error_handler(ValueError, custom_handler)
        
        error = ValueError("Test error")
        message = handle_error(ErrorType.USER_ERROR, error)
        
        assert message == "自定义处理: Test error"
    
    def test_error_handler_decorator(self):
        """测试错误处理装饰器"""
        @error_handler(ErrorType.USER_ERROR)
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(RuntimeError) as exc_info:
            failing_function()
        
        assert "输入参数有误" in str(exc_info.value)
        assert "Test error" in str(exc_info.value)
    
    def test_error_handler_decorator_with_auto_classification(self):
        """测试错误处理装饰器自动分类"""
        @error_handler()  # 不指定错误类型，自动分类
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(RuntimeError) as exc_info:
            failing_function()
        
        assert "输入参数有误" in str(exc_info.value)
        assert "Test error" in str(exc_info.value)
    
    def test_error_handler_decorator_with_specific_type(self):
        """测试错误处理装饰器指定类型"""
        @error_handler(ErrorType.NETWORK_ERROR)
        def failing_function():
            raise ConnectionError("Network error")
        
        with pytest.raises(RuntimeError) as exc_info:
            failing_function()
        
        assert "网络连接失败" in str(exc_info.value)