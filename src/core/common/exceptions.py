"""
核心模块通用异常定义

定义核心模块使用的异常类型。
"""


class CoreError(Exception):
    """核心模块基础异常"""

    pass


class ServiceError(CoreError):
    """服务错误异常"""

    pass


class ValidationError(CoreError):
    """验证错误异常"""

    pass


class ConfigurationError(CoreError):
    """配置错误异常"""

    pass


class DependencyError(CoreError):
    """依赖错误异常"""

    pass


class ToolError(CoreError):
    """工具错误异常"""

    pass


class ToolRegistrationError(ToolError):
    """工具注册错误异常"""

    pass


class ToolExecutionError(ToolError):
    """工具执行错误异常"""

    pass
