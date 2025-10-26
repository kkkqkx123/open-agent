"""组件组装器异常定义"""


class AssemblyError(Exception):
    """组件组装错误基类"""
    pass


class ComponentNotFoundError(AssemblyError):
    """组件未找到错误"""
    pass


class DependencyResolutionError(AssemblyError):
    """依赖解析错误"""
    pass


class CircularDependencyError(AssemblyError):
    """循环依赖错误"""
    pass


class ConfigurationError(AssemblyError):
    """配置错误"""
    pass


class LifecycleError(AssemblyError):
    """生命周期管理错误"""
    pass