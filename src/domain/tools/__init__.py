"""
工具系统模块

提供统一的工具管理、执行和格式化功能，支持多种工具类型：
- 原生能力工具 (NativeTool)
- MCP工具 (MCPTool)
- 内置工具 (BuiltinTool)
"""

from .interfaces import IToolManager, IToolFormatter, IToolExecutor, ToolCall, ToolResult
from .base import BaseTool
from .types.native_tool import NativeTool
from .types.mcp_tool import MCPTool
from .types.builtin_tool import BuiltinTool

__all__ = [
    # 接口
    "IToolManager",
    "IToolFormatter",
    "IToolExecutor",
    "ToolCall",
    "ToolResult",
    # 基类
    "BaseTool",
    # 工具类型
    "NativeTool",
    "MCPTool",
    "BuiltinTool",
]