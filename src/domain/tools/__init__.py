"""
工具系统模块

提供统一的工具管理、执行和格式化功能，支持多种工具类型：
- 原生能力工具 (NativeTool)
- MCP工具 (MCPTool)
- 内置工具 (BuiltinTool)
"""

from .interfaces import (
    ITool, 
    IToolRegistry, 
    IToolFormatter, 
    IToolExecutor, 
    IToolFactory,
    ToolCall, 
    ToolResult
)
from .base import BaseTool
from .types.native_tool import NativeTool
from .types.mcp_tool import MCPTool
from .types.builtin_tool import SyncBuiltinTool, AsyncBuiltinTool, BuiltinToolFactory
from .factory import ToolFactory, ToolConfig, get_global_factory, set_global_factory, create_tool

__all__ = [
    # 接口
    "ITool",
    "IToolRegistry",
    "IToolFormatter",
    "IToolExecutor",
    "IToolFactory",
    "ToolCall",
    "ToolResult",
    # 基类
    "BaseTool",
    # 工具类型
    "NativeTool",
    "MCPTool",
    "SyncBuiltinTool",
    "AsyncBuiltinTool",
    "BuiltinToolFactory",
    # 工厂
    "ToolFactory",
    "ToolConfig",
    "get_global_factory",
    "set_global_factory",
    "create_tool",
    
]