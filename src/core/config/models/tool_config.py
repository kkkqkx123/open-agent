"""工具配置模型"""

from typing import Dict, Any, Optional, List
from pydantic import Field, field_validator

from .base import BaseConfig


class ToolConfig(BaseConfig):
    """工具配置模型"""
    
    # 基础配置
    name: str = Field(..., description="工具名称")
    description: Optional[str] = Field(None, description="工具描述")
    
    # 工具类型和实现
    tool_type: str = Field(..., description="工具类型：builtin, native, rest, mcp等")
    
    # 工具参数
    parameters_schema: Dict[str, Any] = Field(default_factory=dict, description="工具参数Schema")
    
    # 功能配置
    enabled: bool = Field(default=True, description="工具是否启用")
    
    # 实现特定配置
    function_path: Optional[str] = Field(None, description="本地函数路径")
    api_url: Optional[str] = Field(None, description="REST API URL")
    mcp_server_url: Optional[str] = Field(None, description="MCP服务器URL")
    
    # 元数据和分类
    category: Optional[str] = Field(None, description="工具分类")
    tags: List[str] = Field(default_factory=list, description="工具标签")
    
    # 配置
    version: Optional[str] = Field(None, description="工具版本")
    group: Optional[str] = Field(None, description="所属组名称")
    
    # 高级配置
    timeout: Optional[int] = Field(None, description="超时时间（秒）")
    retry_config: Dict[str, Any] = Field(default_factory=dict, description="重试配置")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    @field_validator("tool_type")
    @classmethod
    def validate_tool_type(cls, v: str) -> str:
        """验证工具类型"""
        allowed_types = ["builtin", "native", "rest", "mcp"]
        if v.lower() not in allowed_types:
            raise ValueError(f"工具类型必须是以下之一: {allowed_types}")
        return v.lower()
    
    @field_validator("api_url")
    @classmethod
    def validate_api_url(cls, v: Optional[str]) -> Optional[str]:
        """验证API URL"""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("API URL必须以http://或https://开头")
        return v
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取参数值"""
        return self.parameters_schema.get(key, default)
    
    def set_parameter(self, key: str, value: Any) -> None:
        """设置参数值"""
        self.parameters_schema[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据值"""
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据值"""
        self.metadata[key] = value
    
    def is_builtin(self) -> bool:
        """检查是否为内置工具"""
        return self.tool_type == "builtin"
    
    def is_rest(self) -> bool:
        """检查是否为REST工具"""
        return self.tool_type == "rest"
    
    def is_mcp(self) -> bool:
        """检查是否为MCP工具"""
        return self.tool_type == "mcp"


class ToolSetConfig(BaseConfig):
    """工具集配置模型"""
    
    # 基础配置
    name: str = Field(..., description="工具集名称")
    description: Optional[str] = Field(None, description="工具集描述")
    
    # 工具列表
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="工具列表")
    
    # 配置
    enabled: bool = Field(default=True, description="工具集是否启用")
    version: Optional[str] = Field(None, description="工具集版本")
    
    # 高级配置
    auto_discover: bool = Field(default=False, description="是否自动发现工具")
    discovery_paths: List[str] = Field(default_factory=list, description="发现路径")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据值"""
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据值"""
        self.metadata[key] = value
