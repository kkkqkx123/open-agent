"""插件系统模块

提供可扩展的插件架构，支持START和END节点的功能扩展。
"""

from .interfaces import (
    IPlugin,
    IStartPlugin,
    IEndPlugin,
    PluginType,
    PluginStatus,
    PluginMetadata,
    PluginContext
)

from .registry import PluginRegistry
from .manager import PluginManager

__all__ = [
    "IPlugin",
    "IStartPlugin", 
    "IEndPlugin",
    "PluginType",
    "PluginStatus",
    "PluginMetadata",
    "PluginContext",
    "PluginRegistry",
    "PluginManager"
]