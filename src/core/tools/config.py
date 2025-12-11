"""
工具配置模型

定义各种工具类型的配置数据结构。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from src.interfaces.tool.config import ToolConfig


class ToolType(Enum):
    """工具类型枚举
    
    基于状态管理的模块化工具系统，支持两种主要类别：
    
    1. 无状态工具 (Stateless Tools)
       - BUILTIN: 简单的、无状态的Python函数实现
    
    2. 有状态工具 (Stateful Tools)
       - NATIVE: 复杂的、有状态的项目内实现工具
       - REST: 技术上有状态但业务逻辑上无状态的REST API调用工具
       - MCP: 有状态的MCP服务器工具，适用于需要复杂状态管理的场景
    """
    BUILTIN = "builtin"      # 无状态内置工具
    NATIVE = "native"        # 有状态原生工具
    REST = "rest"           # REST工具（业务逻辑上无状态，技术上使用状态管理器）
    MCP = "mcp"            # 有状态MCP工具


@dataclass(kw_only=True)
class ToolRegistryConfig:
    """工具注册表配置"""
    
    # 基础配置
    auto_discover: bool
    discovery_paths: List[str]
    reload_on_change: bool
    tools: List[ToolConfig]
    
    # 工具管理配置
    max_tools: int
    enable_caching: bool
    cache_ttl: int
    
    # 安全配置
    allow_dynamic_loading: bool
    validate_schemas: bool
    sandbox_mode: bool