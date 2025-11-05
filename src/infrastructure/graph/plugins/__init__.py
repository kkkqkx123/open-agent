"""插件系统模块

提供可扩展的插件架构，支持START、END节点和Hook功能扩展。
"""

from .interfaces import (
    IPlugin,
    IStartPlugin,
    IEndPlugin,
    IHookPlugin,  # 新增Hook插件接口
    PluginType,
    PluginStatus,
    PluginMetadata,
    PluginContext,
    HookContext,  # 新增Hook上下文
    HookPoint,    # 新增Hook执行点
    HookExecutionResult  # 新增Hook执行结果
)

from .registry import PluginRegistry
from .manager import PluginManager

__all__ = [
    "IPlugin",
    "IStartPlugin", 
    "IEndPlugin",
    "IHookPlugin",  # 新增
    "PluginType",
    "PluginStatus",
    "PluginMetadata",
    "PluginContext",
    "HookContext",  # 新增
    "HookPoint",    # 新增
    "HookExecutionResult",  # 新增
    "PluginRegistry",
    "PluginManager"
]