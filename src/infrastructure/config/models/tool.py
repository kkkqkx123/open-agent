"""工具配置数据模型

提供工具客户端所需的基础配置数据结构，位于基础设施层。
不包含业务逻辑，仅作为数据容器。
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ToolClientConfig(BaseModel):
    """工具客户端配置数据模型
    
    包含工具客户端所需的所有配置属性的基础数据结构。
    不包含业务逻辑，仅作为数据容器。
    """
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolClientConfig":
        """从字典创建配置"""
        return cls(**data)


class ToolSetClientConfig(BaseModel):
    """工具集客户端配置数据模型"""
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolSetClientConfig":
        """从字典创建配置"""
        return cls(**data)


__all__ = [
    "ToolClientConfig",
    "ToolSetClientConfig"
]