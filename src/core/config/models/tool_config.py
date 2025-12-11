"""工具配置模型"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from pydantic import Field, field_validator

from .base import BaseConfig
from ..mappers.tool import ToolConfigMapper

if TYPE_CHECKING:
    from src.infrastructure.config.models import ConfigData


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
    
    # 业务逻辑方法
    def validate_business_rules(self) -> List[str]:
        """验证业务规则
        
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 验证必需字段
        if not self.name:
            errors.append("工具名称不能为空")
        
        if not self.tool_type:
            errors.append("工具类型不能为空")
        
        # 验证工具类型特定配置
        if self.tool_type == "rest" and not self.api_url:
            errors.append("REST工具必须提供API URL")
        
        if self.tool_type == "mcp" and not self.mcp_server_url:
            errors.append("MCP工具必须提供MCP服务器URL")
        
        if self.tool_type == "native" and not self.function_path:
            errors.append("本地工具必须提供函数路径")
        
        # 验证超时配置
        if self.timeout is not None and self.timeout <= 0:
            errors.append("超时时间必须大于0")
        
        return errors
    
    def is_valid(self) -> bool:
        """检查配置是否有效
        
        Returns:
            是否有效
        """
        return len(self.validate_business_rules()) == 0
    
    # 转换方法
    @classmethod
    def from_config_data(cls, config_data: "ConfigData") -> "ToolConfig":
        """从基础配置数据创建领域模型
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            Tool领域模型
        """
        return ToolConfigMapper.config_data_to_tool_config(config_data)
    
    def to_config_data(self) -> "ConfigData":
        """转换为基础配置数据
        
        Returns:
            基础配置数据
        """
        return ToolConfigMapper.tool_config_to_config_data(self)
    
    def get_client_config(self) -> Dict[str, Any]:
        """获取客户端配置
        
        Returns:
            客户端配置字典
        """
        config = {
            "name": self.name,
            "description": self.description,
            "tool_type": self.tool_type,
            "parameters_schema": self.parameters_schema,
            "enabled": self.enabled,
            "category": self.category,
            "tags": self.tags,
            "version": self.version,
            "group": self.group,
            "timeout": self.timeout,
            "retry_config": self.retry_config,
            "metadata": self.metadata
        }
        
        # 添加工具类型特定配置
        if self.function_path:
            config["function_path"] = self.function_path
        
        if self.api_url:
            config["api_url"] = self.api_url
        
        if self.mcp_server_url:
            config["mcp_server_url"] = self.mcp_server_url
        
        return config
    
    def is_builtin(self) -> bool:
        """检查是否为内置工具"""
        return self.tool_type == "builtin"
    
    def is_native(self) -> bool:
        """检查是否为本地工具"""
        return self.tool_type == "native"
    
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
    
    # 业务逻辑方法
    def validate_business_rules(self) -> List[str]:
        """验证业务规则
        
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 验证必需字段
        if not self.name:
            errors.append("工具集名称不能为空")
        
        # 验证工具列表
        if not self.tools and not self.auto_discover:
            errors.append("工具集必须包含工具或启用自动发现")
        
        # 验证发现路径
        if self.auto_discover and not self.discovery_paths:
            errors.append("启用自动发现时必须提供发现路径")
        
        return errors
    
    def is_valid(self) -> bool:
        """检查配置是否有效
        
        Returns:
            是否有效
        """
        return len(self.validate_business_rules()) == 0
    
    # 转换方法
    @classmethod
    def from_config_data(cls, config_data: "ConfigData") -> "ToolSetConfig":
        """从基础配置数据创建领域模型
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            ToolSet领域模型
        """
        return ToolConfigMapper.config_data_to_tool_set_config(config_data)
    
    def to_config_data(self) -> "ConfigData":
        """转换为基础配置数据
        
        Returns:
            基础配置数据
        """
        return ToolConfigMapper.tool_set_config_to_config_data(self)
    
    def get_client_config(self) -> Dict[str, Any]:
        """获取客户端配置
        
        Returns:
            客户端配置字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.tools,
            "enabled": self.enabled,
            "version": self.version,
            "auto_discover": self.auto_discover,
            "discovery_paths": self.discovery_paths,
            "metadata": self.metadata
        }
