"""包装器异常类"""

from .llm import LLMError


class WrapperError(LLMError):
    """包装器错误基类"""
    pass


class TaskGroupWrapperError(WrapperError):
    """任务组包装器错误"""
    pass


class PollingPoolWrapperError(WrapperError):
    """轮询池包装器错误"""
    pass


class WrapperFactoryError(WrapperError):
    """包装器工厂错误"""
    pass


class WrapperConfigError(WrapperError):
    """包装器配置错误"""
    pass


class WrapperExecutionError(WrapperError):
    """包装器执行错误"""
    pass