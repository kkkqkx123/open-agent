"""
容器接口统一导出
"""

from .core import IDependencyContainer, ServiceLifetime

__all__ = [
    "IDependencyContainer",
    "ServiceLifetime"
]