"""
工具相关异常定义
"""

from .core import CoreError


class ToolError(CoreError):
    """工具错误异常"""

    pass


class ToolRegistrationError(ToolError):
    """工具注册错误异常"""

    pass


class ToolExecutionError(ToolError):
    """工具执行错误异常"""

    pass
