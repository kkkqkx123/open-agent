"""
核心模块基础异常定义
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
