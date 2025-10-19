"""基础设施模块异常定义"""


class InfrastructureError(Exception):
    """基础设施模块基础异常"""

    pass


class ServiceNotRegisteredError(InfrastructureError):
    """服务未注册异常"""

    pass


class ServiceCreationError(InfrastructureError):
    """服务创建异常"""

    pass


class CircularDependencyError(InfrastructureError):
    """循环依赖异常"""

    pass


class ConfigurationError(InfrastructureError):
    """配置错误异常"""

    pass


class EnvironmentCheckError(InfrastructureError):
    """环境检查异常"""

    pass


class ArchitectureViolationError(InfrastructureError):
    """架构违规异常"""

    pass
