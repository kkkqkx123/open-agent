"""
工具配置相关接口定义

定义了工具配置的核心业务接口和数据模型，确保模块间的松耦合设计。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from .base import ITool


@dataclass(kw_only=True)
class ToolConfig:
    """工具配置基类"""

    name: str
    description: str
    parameters_schema: Dict[str, Any]
    tool_type: str  # "native", "rest", "mcp"
    enabled: bool = True
    timeout: int = 30
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


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
class BuiltinToolConfig(ToolConfig):
    """内置工具配置 - 项目内置工具"""

    # 内置工具的配置
    function_path: Optional[str] = None  # 函数路径（用于动态加载）

    def __post_init__(self) -> None:
        """初始化后处理"""
        # 设置tool_type
        self.tool_type = "builtin"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'function_path': self.function_path,
        })
        return data


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
    auth_method: str = "api_key"  # "api_key", "api_key_header", "oauth", "none"
    headers: Dict[str, str] = field(default_factory=dict)
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
    refresh_interval: Optional[int] = None  # Schema刷新间隔（秒）
    dynamic_schema: bool = False

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


@dataclass(kw_only=True)
class ToolSetConfig:
    """工具集配置"""

    name: str
    description: str
    tools: List[str]  # 工具名称列表
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class IToolFactory(ABC):
    """工具工厂接口"""

    @abstractmethod
    def create_tool(self, tool_config: Union[Dict[str, Any], 'ToolConfig', 'NativeToolConfig', 'RestToolConfig', 'MCPToolConfig']) -> 'ITool':
        """创建工具实例"""
        pass

    @abstractmethod
    def register_tool_type(self, tool_type: str, tool_class: type) -> None:
        """注册工具类型"""
        pass

    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """获取支持的工具类型"""
        pass