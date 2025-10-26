"""组件组装器模块

提供配置驱动的组件组装功能，支持自动依赖解析和生命周期管理。
"""

from .interfaces import IComponentAssembler
from .assembler import ComponentAssembler
from .exceptions import AssemblyError

__all__ = [
    "IComponentAssembler",
    "ComponentAssembler",
    "AssemblyError"
]