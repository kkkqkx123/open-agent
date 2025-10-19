"""
工具配置模型

定义了各种工具类型的配置数据结构。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


@dataclass(kw_only=True)
class ToolConfig:
    """工具配置基类"""

    name: str
    description: str
    parameters_schema: Dict[str, Any]
    tool_type: str  # "native", "mcp", "builtin"
    enabled: bool = True
    timeout: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NativeToolConfig(ToolConfig):
    """原生工具配置"""

    api_url: str
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    auth_method: str = "api_key"  # "api_key", "api_key_header", "oauth", "none"
    api_key: Optional[str] = None
    retry_count: int = 3
    retry_delay: float = 1.0

    def __post_init__(self):
        """初始化后处理"""
        # 设置tool_type
        self.tool_type = "native"
        # 设置默认Content-Type
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"


@dataclass
class MCPToolConfig(ToolConfig):
    """MCP工具配置"""

    mcp_server_url: str
    dynamic_schema: bool = False
    refresh_interval: Optional[int] = None  # Schema刷新间隔（秒）

    def __post_init__(self):
        """初始化后处理"""
        # 设置tool_type
        self.tool_type = "mcp"


@dataclass
class BuiltinToolConfig(ToolConfig):
    """内置工具配置"""

    # 内置工具的配置通常比较简单，大部分信息从函数推断
    function_path: Optional[str] = None  # 函数路径（用于动态加载）

    def __post_init__(self):
        """初始化后处理"""
        # 设置tool_type
        self.tool_type = "builtin"


@dataclass
class ToolSetConfig:
    """工具集配置"""

    name: str
    description: str
    tools: List[str]  # 工具名称列表
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolRegistryConfig(BaseModel):
    """工具注册表配置"""

    tools: List[Union[NativeToolConfig, MCPToolConfig, BuiltinToolConfig]] = []
    tool_sets: List[ToolSetConfig] = []

    class Config:
        """Pydantic配置"""

        arbitrary_types_allowed = True


# 工具配置工厂函数
def create_native_tool_config(
    name: str,
    api_url: str,
    description: str,
    parameters_schema: Dict[str, Any],
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    auth_method: str = "api_key",
    api_key: Optional[str] = None,
    timeout: int = 30,
    enabled: bool = True,
    **kwargs,
) -> NativeToolConfig:
    """创建原生工具配置

    Args:
        name: 工具名称
        api_url: API URL
        description: 工具描述
        parameters_schema: 参数Schema
        method: HTTP方法
        headers: HTTP头
        auth_method: 认证方法
        api_key: API密钥
        timeout: 超时时间
        enabled: 是否启用
        **kwargs: 其他参数

    Returns:
        NativeToolConfig: 原生工具配置
    """
    return NativeToolConfig(
        name=name,
        description=description,
        parameters_schema=parameters_schema,
        api_url=api_url,
        method=method,
        headers=headers or {},
        auth_method=auth_method,
        api_key=api_key,
        timeout=timeout,
        enabled=enabled,
        **kwargs,
    )


def create_mcp_tool_config(
    name: str,
    mcp_server_url: str,
    description: str,
    parameters_schema: Dict[str, Any],
    dynamic_schema: bool = False,
    timeout: int = 30,
    enabled: bool = True,
    **kwargs,
) -> MCPToolConfig:
    """创建MCP工具配置

    Args:
        name: 工具名称
        mcp_server_url: MCP服务器URL
        description: 工具描述
        parameters_schema: 参数Schema
        dynamic_schema: 是否动态获取Schema
        timeout: 超时时间
        enabled: 是否启用
        **kwargs: 其他参数

    Returns:
        MCPToolConfig: MCP工具配置
    """
    return MCPToolConfig(
        name=name,
        description=description,
        parameters_schema=parameters_schema,
        mcp_server_url=mcp_server_url,
        dynamic_schema=dynamic_schema,
        timeout=timeout,
        enabled=enabled,
        **kwargs,
    )


def create_builtin_tool_config(
    name: str,
    description: str,
    parameters_schema: Dict[str, Any],
    function_path: Optional[str] = None,
    timeout: int = 30,
    enabled: bool = True,
    **kwargs,
) -> BuiltinToolConfig:
    """创建内置工具配置

    Args:
        name: 工具名称
        description: 工具描述
        parameters_schema: 参数Schema
        function_path: 函数路径
        timeout: 超时时间
        enabled: 是否启用
        **kwargs: 其他参数

    Returns:
        BuiltinToolConfig: 内置工具配置
    """
    return BuiltinToolConfig(
        name=name,
        description=description,
        parameters_schema=parameters_schema,
        function_path=function_path,
        timeout=timeout,
        enabled=enabled,
        **kwargs,
    )


def create_tool_set_config(
    name: str, description: str, tools: List[str], enabled: bool = True, **kwargs
) -> ToolSetConfig:
    """创建工具集配置

    Args:
        name: 工具集名称
        description: 工具集描述
        tools: 工具名称列表
        enabled: 是否启用
        **kwargs: 其他参数

    Returns:
        ToolSetConfig: 工具集配置
    """
    return ToolSetConfig(
        name=name, description=description, tools=tools, enabled=enabled, **kwargs
    )
