"""
工具类型模块

本模块提供基于状态管理的模块化工具系统实现，支持两种主要类别的工具：

1. 无状态工具 (Stateless Tools)
   - 内置工具 (Builtin Tool) - 简单的、无状态的Python函数实现

2. 有状态工具 (Stateful Tools)
   - 原生工具 (Native Tool) - 复杂的、有状态的项目内实现工具
   - REST工具 (Rest Tool) - 技术上有状态但业务逻辑上无状态的REST API调用工具
   - MCP工具 (MCP Tool) - 有状态的MCP服务器工具，适用于需要复杂状态管理的场景

每个工具类型都有对应的配置类和实现类，通过工具工厂统一创建和管理。
"""

from .builtin_tool import BuiltinTool
from .native_tool import NativeTool
from .rest_tool import RestTool
from .mcp_tool import MCPTool

__all__ = [
    "BuiltinTool",
    "NativeTool",
    "RestTool",
    "MCPTool",
]