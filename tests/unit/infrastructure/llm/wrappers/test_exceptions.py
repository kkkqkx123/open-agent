"""包装器异常类单元测试"""

import pytest
from src.infrastructure.llm.wrappers.exceptions import (
    WrapperError,
    TaskGroupWrapperError,
    PollingPoolWrapperError,
    WrapperFactoryError,
    WrapperConfigError,
    WrapperExecutionError
)
from src.infrastructure.llm.exceptions import LLMError


class TestWrapperExceptions:
    """包装器异常类测试"""
    
    def test_wrapper_error_inheritance(self):
        """测试WrapperError继承自LLMError"""
        error = WrapperError("Test error")
        
        assert isinstance(error, LLMError)
        assert str(error) == "Test error"
    
    def test_task_group_wrapper_error_inheritance(self):
        """测试TaskGroupWrapperError继承关系"""
        error = TaskGroupWrapperError("Task group error")
        
        assert isinstance(error, WrapperError)
        assert isinstance(error, LLMError)
        assert str(error) == "Task group error"
    
    def test_polling_pool_wrapper_error_inheritance(self):
        """测试PollingPoolWrapperError继承关系"""
        error = PollingPoolWrapperError("Polling pool error")
        
        assert isinstance(error, WrapperError)
        assert isinstance(error, LLMError)
        assert str(error) == "Polling pool error"
    
    def test_wrapper_factory_error_inheritance(self):
        """测试WrapperFactoryError继承关系"""
        error = WrapperFactoryError("Factory error")
        
        assert isinstance(error, WrapperError)
        assert isinstance(error, LLMError)
        assert str(error) == "Factory error"
    
    def test_wrapper_config_error_inheritance(self):
        """测试WrapperConfigError继承关系"""
        error = WrapperConfigError("Config error")
        
        assert isinstance(error, WrapperError)
        assert isinstance(error, LLMError)
        assert str(error) == "Config error"
    
    def test_wrapper_execution_error_inheritance(self):
        """测试WrapperExecutionError继承关系"""
        error = WrapperExecutionError("Execution error")
        
        assert isinstance(error, WrapperError)
        assert isinstance(error, LLMError)
        assert str(error) == "Execution error"
    
    def test_wrapper_error_attributes(self):
        """测试包装器异常属性"""
        # 测试基本异常属性
        error = WrapperError("Test message")
        assert str(error) == "Test message"
        assert "Test message" in repr(error)
    
    def test_task_group_wrapper_error_attributes(self):
        """测试任务组包装器异常属性"""
        error = TaskGroupWrapperError("Task group error message")
        assert str(error) == "Task group error message"
        assert "Task group error message" in repr(error)
    
    def test_polling_pool_wrapper_error_attributes(self):
        """测试轮询池包装器异常属性"""
        error = PollingPoolWrapperError("Polling pool error message")
        assert str(error) == "Polling pool error message"
        assert "Polling pool error message" in repr(error)
    
    def test_wrapper_factory_error_attributes(self):
        """测试包装器工厂异常属性"""
        error = WrapperFactoryError("Factory error message")
        assert str(error) == "Factory error message"
        assert "Factory error message" in repr(error)
    
    def test_wrapper_config_error_attributes(self):
        """测试包装器配置异常属性"""
        error = WrapperConfigError("Config error message")
        assert str(error) == "Config error message"
        assert "Config error message" in repr(error)
    
    def test_wrapper_execution_error_attributes(self):
        """测试包装器执行异常属性"""
        error = WrapperExecutionError("Execution error message")
        assert str(error) == "Execution error message"
        assert "Execution error message" in repr(error)
    
    def test_exception_hierarchy(self):
        """测试异常层级结构"""
        # 验证所有自定义异常都继承自WrapperError
        exceptions = [
            TaskGroupWrapperError,
            PollingPoolWrapperError,
            WrapperFactoryError,
            WrapperConfigError,
            WrapperExecutionError
        ]
        
        for exc_class in exceptions:
            assert issubclass(exc_class, WrapperError)
            assert issubclass(exc_class, LLMError)
    
    def test_exception_with_args(self):
        """测试带参数的异常"""
        # 测试带多个参数的异常
        error = WrapperError("Error message", "additional info")
        assert len(error.args) == 2
        assert error.args[0] == "Error message"
        assert error.args[1] == "additional info"
    
    def test_task_group_wrapper_error_with_args(self):
        """测试带参数的任务组包装器异常"""
        error = TaskGroupWrapperError("Task group error", 404, "Not Found")
        assert len(error.args) == 3
        assert error.args[0] == "Task group error"
    
    def test_polling_pool_wrapper_error_with_args(self):
        """测试带参数的轮询池包装器异常"""
        error = PollingPoolWrapperError("Polling error", {"code": 500})
        assert len(error.args) == 2
        assert error.args[0] == "Polling error"
    
    def test_wrapper_factory_error_with_args(self):
        """测试带参数的包装器工厂异常"""
        error = WrapperFactoryError("Factory error", ["item1", "item2"])
        assert len(error.args) == 2
        assert error.args[0] == "Factory error"
    
    def test_wrapper_config_error_with_args(self):
        """测试带参数的包装器配置异常"""
        error = WrapperConfigError("Config error", {"key": "value"})
        assert len(error.args) == 2
        assert error.args[0] == "Config error"
    
    def test_wrapper_execution_error_with_args(self):
        """测试带参数的包装器执行异常"""
        error = WrapperExecutionError("Execution error", Exception("inner"))
        assert len(error.args) == 2
        assert error.args[0] == "Execution error"