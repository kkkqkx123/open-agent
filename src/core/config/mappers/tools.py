"""工具配置映射器

负责在基础设施层配置数据和Core层工具实体之间进行转换。
"""

from typing import Dict, Any, Optional, Union, List
import logging

from src.infrastructure.config.models.base import ConfigData
from src.infrastructure.config.models.tool import (
    ToolClientConfig, ToolSetClientConfig
)
from src.interfaces.tool.config import (
    ToolConfig, BuiltinToolConfig, NativeToolConfig, RestToolConfig, MCPToolConfig
)
from src.core.tools.config import ToolRegistryConfig

logger = logging.getLogger(__name__)


class ToolsConfigMapper:
    """工具配置映射器
    
    负责在基础设施层配置数据和Core层工具实体之间进行转换。
    """
    
    @staticmethod
    def config_data_to_tool_config(config_data: ConfigData) -> Union[ToolConfig, ToolRegistryConfig]:
        """将配置数据转换为工具配置实体
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            Union[ToolConfig, ToolRegistryConfig]: 工具配置实体
        """
        try:
            data = config_data.data
            
            # 判断是否为工具注册表配置
            if "tools" in data and "auto_discover" in data:
                return ToolsConfigMapper._config_data_to_registry_config(config_data)
            
            # 判断工具类型
            tool_type = data.get("tool_type", "native")
            
            if tool_type == "builtin":
                return ToolsConfigMapper._config_data_to_builtin_config(config_data)
            elif tool_type == "native":
                return ToolsConfigMapper._config_data_to_native_config(config_data)
            elif tool_type == "rest":
                return ToolsConfigMapper._config_data_to_rest_config(config_data)
            elif tool_type == "mcp":
                return ToolsConfigMapper._config_data_to_mcp_config(config_data)
            else:
                # 默认为原生工具
                return ToolsConfigMapper._config_data_to_native_config(config_data)
                
        except Exception as e:
            logger.error(f"配置数据转换为工具实体失败: {e}")
            raise ValueError(f"配置数据转换为工具实体失败: {e}")
    
    @staticmethod
    def tool_config_to_config_data(entity: Union[ToolConfig, ToolRegistryConfig]) -> ConfigData:
        """将工具配置实体转换为配置数据
        
        Args:
            entity: 工具配置实体
            
        Returns:
            ConfigData: 基础配置数据
        """
        try:
            if isinstance(entity, ToolRegistryConfig):
                data = ToolsConfigMapper._registry_config_to_dict(entity)
            elif isinstance(entity, NativeToolConfig):
                data = entity.to_dict()
            elif isinstance(entity, RestToolConfig):
                data = entity.to_dict()
            elif isinstance(entity, MCPToolConfig):
                data = entity.to_dict()
            else:
                # 默认处理
                data = entity.to_dict() if hasattr(entity, 'to_dict') else {}
                
            return ConfigData(data)
                
        except Exception as e:
            logger.error(f"工具实体转换为配置数据失败: {e}")
            raise ValueError(f"工具实体转换为配置数据失败: {e}")
    
    @staticmethod
    def config_data_to_tool_client_config(config_data: ConfigData) -> ToolClientConfig:
        """将配置数据转换为工具客户端配置
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            ToolClientConfig: 工具客户端配置
        """
        data = config_data.data
        
        # 构建重试配置
        retry_config = {}
        if data.get("retry_count"):
            retry_config["retry_count"] = data.get("retry_count", 3)
        if data.get("retry_delay"):
            retry_config["retry_delay"] = data.get("retry_delay", 1.0)
        
        return ToolClientConfig(
            name=data.get("name", ""),
            description=data.get("description", ""),
            tool_type=data.get("tool_type", "native"),
            function_path=data.get("function_path", ""),
            enabled=data.get("enabled", True),
            timeout=data.get("timeout", 30),
            metadata=data.get("metadata", {}),
            api_url=data.get("api_url"),
            mcp_server_url=data.get("mcp_server_url"),
            parameters_schema=data.get("parameters_schema", {}),
            retry_config=retry_config,
            category=data.get("category"),
            tags=data.get("tags", []),
            version=data.get("version"),
            group=data.get("group")
        )
    
    @staticmethod
    def tool_client_config_to_config_data(config: ToolClientConfig) -> ConfigData:
        """将工具客户端配置转换为配置数据
        
        Args:
            config: 工具客户端配置
            
        Returns:
            ConfigData: 基础配置数据
        """
        data = {
            "name": config.name,
            "description": config.description,
            "tool_type": config.tool_type,
            "function_path": config.function_path,
            "enabled": config.enabled,
            "timeout": config.timeout,
            "metadata": config.metadata,
            "parameters_schema": config.parameters_schema,
            "category": config.category,
            "tags": config.tags,
            "version": config.version,
            "group": config.group
        }
        
        # 添加特定类型的字段
        if config.api_url:
            data["api_url"] = config.api_url
        
        if config.mcp_server_url:
            data["mcp_server_url"] = config.mcp_server_url
        
        # 添加重试配置
        if config.retry_config:
            data.update(config.retry_config)
        
        return ConfigData(data)
    
    @staticmethod
    def config_data_to_tool_set_client_config(config_data: ConfigData) -> ToolSetClientConfig:
        """将配置数据转换为工具集客户端配置
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            ToolSetClientConfig: 工具集客户端配置
        """
        data = config_data.data
        
        # 转换工具配置列表
        tools = []
        if "tools" in data:
            for tool_data in data["tools"]:
                # 保持原始字典格式，因为ToolSetClientConfig期望List[Dict[str, Any]]
                tools.append(tool_data)
        
        return ToolSetClientConfig(
            name=data.get("name", ""),
            description=data.get("description", ""),
            tools=tools,
            enabled=data.get("enabled", True),
            version=data.get("version"),
            auto_discover=data.get("auto_discover", False),
            discovery_paths=data.get("discovery_paths", []),
            metadata=data.get("metadata", {})
        )
    
    @staticmethod
    def tool_set_client_config_to_config_data(config: ToolSetClientConfig) -> ConfigData:
        """将工具集客户端配置转换为配置数据
        
        Args:
            config: 工具集客户端配置
            
        Returns:
            ConfigData: 基础配置数据
        """
        # 转换工具配置列表
        tools = []
        for tool_config in config.tools:
            # tool_config已经是字典格式，直接使用
            tools.append(tool_config)
        
        data = {
            "name": config.name,
            "description": config.description,
            "tools": tools,
            "enabled": config.enabled,
            "version": config.version,
            "auto_discover": config.auto_discover,
            "discovery_paths": config.discovery_paths,
            "metadata": config.metadata
        }
        
        return ConfigData(data)
    
    @staticmethod
    def _config_data_to_registry_config(config_data: ConfigData) -> ToolRegistryConfig:
        """将配置数据转换为工具注册表配置"""
        data = config_data.data
        
        # 提取工具配置列表
        tools = []
        if "tools" in data:
            for tool_data in data["tools"]:
                tool_config_data = ConfigData(tool_data)
                tool_config = ToolsConfigMapper.config_data_to_tool_config(tool_config_data)
                if isinstance(tool_config, ToolConfig):
                    tools.append(tool_config)
        
        # 从配置数据中获取所有必需的字段，如果没有提供则抛出异常
        required_fields = [
            "auto_discover", "discovery_paths", "reload_on_change",
            "max_tools", "enable_caching", "cache_ttl",
            "allow_dynamic_loading", "validate_schemas", "sandbox_mode"
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"工具注册表配置缺少必需字段: {', '.join(missing_fields)}")
        
        return ToolRegistryConfig(
            auto_discover=data["auto_discover"],
            discovery_paths=data["discovery_paths"],
            reload_on_change=data["reload_on_change"],
            tools=tools,
            max_tools=data["max_tools"],
            enable_caching=data["enable_caching"],
            cache_ttl=data["cache_ttl"],
            allow_dynamic_loading=data["allow_dynamic_loading"],
            validate_schemas=data["validate_schemas"],
            sandbox_mode=data["sandbox_mode"]
        )
    
    @staticmethod
    def _config_data_to_builtin_config(config_data: ConfigData) -> BuiltinToolConfig:
        """将配置数据转换为内置工具配置"""
        data = config_data.data
        
        return BuiltinToolConfig(
            name=data["name"],
            description=data.get("description", ""),
            parameters_schema=data.get("parameters_schema", {}),
            tool_type="builtin",
            function_path=data.get("function_path", ""),
            enabled=data.get("enabled", True),
            timeout=data.get("timeout", 30),
            metadata=data.get("metadata", {})
        )
    
    @staticmethod
    def _config_data_to_native_config(config_data: ConfigData) -> NativeToolConfig:
        """将配置数据转换为原生工具配置"""
        data = config_data.data
        
        return NativeToolConfig(
            name=data["name"],
            description=data.get("description", ""),
            parameters_schema=data.get("parameters_schema", {}),
            tool_type="native",
            function_path=data.get("function_path", ""),
            enabled=data.get("enabled", True),
            timeout=data.get("timeout", 30),
            metadata=data.get("metadata", {})
        )
    
    @staticmethod
    def _config_data_to_rest_config(config_data: ConfigData) -> RestToolConfig:
        """将配置数据转换为REST工具配置"""
        data = config_data.data
        
        return RestToolConfig(
            name=data["name"],
            description=data.get("description", ""),
            parameters_schema=data.get("parameters_schema", {}),
            tool_type="rest",
            api_url=data["api_url"],
            method=data.get("method", "POST"),
            auth_method=data.get("auth_method", "api_key"),
            headers=data.get("headers", {}),
            api_key=data.get("api_key"),
            retry_count=data.get("retry_count", 3),
            retry_delay=data.get("retry_delay", 1.0),
            enabled=data.get("enabled", True),
            timeout=data.get("timeout", 30),
            metadata=data.get("metadata", {})
        )
    
    @staticmethod
    def _config_data_to_mcp_config(config_data: ConfigData) -> MCPToolConfig:
        """将配置数据转换为MCP工具配置"""
        data = config_data.data
        
        return MCPToolConfig(
            name=data["name"],
            description=data.get("description", ""),
            parameters_schema=data.get("parameters_schema", {}),
            tool_type="mcp",
            mcp_server_url=data["mcp_server_url"],
            refresh_interval=data.get("refresh_interval"),
            dynamic_schema=data.get("dynamic_schema", False),
            enabled=data.get("enabled", True),
            timeout=data.get("timeout", 30),
            metadata=data.get("metadata", {})
        )
    
    @staticmethod
    def _registry_config_to_dict(config: ToolRegistryConfig) -> Dict[str, Any]:
        """将工具注册表配置转换为字典"""
        # 转换工具配置列表
        tools = []
        for tool_config in config.tools:
            tools.append(tool_config.to_dict())
        
        return {
            "auto_discover": config.auto_discover,
            "discovery_paths": config.discovery_paths,
            "reload_on_change": config.reload_on_change,
            "tools": tools,
            "max_tools": config.max_tools,
            "enable_caching": config.enable_caching,
            "cache_ttl": config.cache_ttl,
            "allow_dynamic_loading": config.allow_dynamic_loading,
            "validate_schemas": config.validate_schemas,
            "sandbox_mode": config.sandbox_mode
        }