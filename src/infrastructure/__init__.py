"""基础设施模块

提供依赖注入、配置加载、环境检查等基础功能。
"""

from .container import IDependencyContainer, DependencyContainer
from .config_loader import IConfigLoader, YamlConfigLoader
from .environment import IEnvironmentChecker, EnvironmentChecker
from .env_check_command import EnvironmentCheckCommand
from .architecture import ArchitectureChecker
from .test_container import TestContainer
from .exceptions import (
    InfrastructureError,
    ServiceNotRegisteredError,
    ServiceCreationError,
    CircularDependencyError,
    ConfigurationError,
    EnvironmentCheckError,
    ArchitectureViolationError
)
from .types import CheckResult, ServiceLifetime

__all__ = [
    "IDependencyContainer",
    "DependencyContainer",
    "IConfigLoader",
    "YamlConfigLoader",
    "IEnvironmentChecker",
    "EnvironmentChecker",
    "EnvironmentCheckCommand",
    "ArchitectureChecker",
    "TestContainer",
    "InfrastructureError",
    "ServiceNotRegisteredError",
    "ServiceCreationError",
    "CircularDependencyError",
    "ConfigurationError",
    "EnvironmentCheckError",
    "ArchitectureViolationError",
    "CheckResult",
    "ServiceLifetime"
]