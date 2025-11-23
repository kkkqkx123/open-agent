"""
工具配置模型

定义了各种工具类型的配置数据结构。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict


@dataclass
class ToolConfig:
    """工具配置基类"""

    name: str
    description: str
    parameters_schema: Dict[str, Any]
    tool_type: str  # "native", "rest", "mcp"
    enabled: bool = True
    timeout: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'description': self.description,
            'parameters_schema': self.parameters_schema,
            'tool_type': self.tool_type,
            'enabled': self.enabled,
            'timeout': self.timeout,
            'metadata': self.metadata,
        }


@dataclass(kw_only=True)
class NativeToolConfig(ToolConfig):
    """原生工具配置 (原rest) - 项目内实现"""

    # 原生工具的配置通常比较简单，大部分信息从函数推断
    function_path: Optional[str] = None  # 函数路径（用于动态加载）

    def __post_init__(self) -> None:
        """初始化后处理"""
        # 设置tool_type
        self.tool_type = "native"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'function_path': self.function_path,
        })
        return data


@dataclass(kw_only=True)
class RestToolConfig(ToolConfig):
    """REST工具配置 (原rest) - 外部API集成"""

    api_url: str
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    auth_method: str = "api_key"  # "api_key", "api_key_header", "oauth", "none"
    api_key: Optional[str] = None
    retry_count: int = 3
    retry_delay: float = 1.0

    def __post_init__(self) -> None:
        """初始化后处理"""
        # 设置tool_type
        self.tool_type = "rest"
        # 设置默认Content-Type
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'api_url': self.api_url,
            'method': self.method,
            'headers': self.headers,
            'auth_method': self.auth_method,
            'api_key': self.api_key,
            'retry_count': self.retry_count,
            'retry_delay': self.retry_delay,
        })
        return data


@dataclass(kw_only=True)
class MCPToolConfig(ToolConfig):
    """MCP工具配置 - 标准协议"""

    mcp_server_url: str
    dynamic_schema: bool = False
    refresh_interval: Optional[int] = None  # Schema刷新间隔（秒）

    def __post_init__(self) -> None:
        """初始化后处理"""
        # 设置tool_type
        self.tool_type = "mcp"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'mcp_server_url': self.mcp_server_url,
            'dynamic_schema': self.dynamic_schema,
            'refresh_interval': self.refresh_interval,
        })
        return data


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

    tools: List[Union[NativeToolConfig, RestToolConfig, MCPToolConfig]] = []
    tool_sets: List[ToolSetConfig] = []

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )


# 工具配置工厂函数
def create_native_tool_config(
    name: str,
    description: str,
    parameters_schema: Dict[str, Any],
    function_path: Optional[str] = None,
    timeout: int = 30,
    enabled: bool = True,
    **kwargs: Any,
) -> NativeToolConfig:
    """创建原生工具配置

    Args:
        name: 工具名称
        description: 工具描述
        parameters_schema: 参数Schema
        function_path: 函数路径
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
        function_path=function_path,
        timeout=timeout,
        enabled=enabled,
        **kwargs,
    )


def create_rest_tool_config(
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
    **kwargs: Any,
) -> RestToolConfig:
    """创建REST工具配置

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
        RestToolConfig: REST工具配置
    """
    return RestToolConfig(
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
    **kwargs: Any,
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


def create_tool_set_config(
    name: str, description: str, tools: List[str], enabled: bool = True, **kwargs: Any
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


