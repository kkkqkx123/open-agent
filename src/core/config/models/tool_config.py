"""工具配置模型"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from pydantic import Field, field_validator
from enum import Enum

from .base import BaseConfig


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


class ToolRegistryConfig(BaseConfig):
    """工具注册表配置"""
    
    # 基础配置
    auto_discover: bool = Field(default=False, description="是否自动发现工具")
    discovery_paths: List[str] = Field(default_factory=list, description="发现路径列表")
    reload_on_change: bool = Field(default=False, description="配置文件变化时是否自动重新加载")
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="显式配置的工具列表")
    
    # 工具管理配置
    max_tools: int = Field(default=100, description="允许加载的最大工具数量")
    enable_caching: bool = Field(default=True, description="是否启用工具配置缓存")
    cache_ttl: int = Field(default=3600, description="配置缓存的生存时间（秒）")
    
    # 安全配置
    allow_dynamic_loading: bool = Field(default=False, description="是否允许运行时动态加载工具")
    validate_schemas: bool = Field(default=True, description="是否验证工具参数模式")
    sandbox_mode: bool = Field(default=False, description="是否在沙盒模式下运行工具")
    
    def validate_business_rules(self) -> List[str]:
        """验证业务规则
        
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 验证工具数量限制
        if self.max_tools <= 0:
            errors.append("最大工具数量必须大于0")
        
        # 验证缓存TTL
        if self.cache_ttl <= 0:
            errors.append("缓存生存时间必须大于0")
        
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
