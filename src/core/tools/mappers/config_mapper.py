"""
工具配置映射器

负责在配置数据和工具业务实体之间进行转换。
"""

from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import logging

from src.interfaces.config import IConfigMapper, ValidationResult
from src.interfaces.common_domain import ValidationResult as CommonValidationResult
from src.interfaces.tool.config import (
    ToolConfig, BuiltinToolConfig, NativeToolConfig, RestToolConfig, MCPToolConfig
)
from src.core.tools.config import ToolRegistryConfig

logger = logging.getLogger(__name__)


class ToolsConfigMapper(IConfigMapper):
    """工具配置映射器
    
    负责在配置字典和工具业务实体之间进行转换。
    """
    
    def dict_to_entity(self, config_data: Dict[str, Any]) -> Union[ToolConfig, ToolRegistryConfig]:
        """将配置字典转换为业务实体
        
        Args:
            config_data: 配置字典数据
            
        Returns:
            Union[ToolConfig, ToolRegistryConfig]: 工具配置实体
        """
        try:
            # 判断是否为工具注册表配置
            if "tools" in config_data and "auto_discover" in config_data:
                return self._dict_to_registry_config(config_data)
            
            # 判断工具类型
            tool_type = config_data.get("tool_type", "native")
            
            if tool_type == "builtin":
                return self._dict_to_builtin_config(config_data)
            elif tool_type == "native":
                return self._dict_to_native_config(config_data)
            elif tool_type == "rest":
                return self._dict_to_rest_config(config_data)
            elif tool_type == "mcp":
                return self._dict_to_mcp_config(config_data)
            else:
                # 默认为原生工具
                return self._dict_to_native_config(config_data)
                
        except Exception as e:
            logger.error(f"配置字典转换为实体失败: {e}")
            raise ValueError(f"配置字典转换为实体失败: {e}")
    
    def entity_to_dict(self, entity: Union[ToolConfig, ToolRegistryConfig]) -> Dict[str, Any]:
        """将业务实体转换为配置字典
        
        Args:
            entity: 业务实体实例
            
        Returns:
            Dict[str, Any]: 配置字典数据
        """
        try:
            if isinstance(entity, ToolRegistryConfig):
                return self._registry_config_to_dict(entity)
            elif isinstance(entity, NativeToolConfig):
                return self._native_config_to_dict(entity)
            elif isinstance(entity, RestToolConfig):
                return self._rest_config_to_dict(entity)
            elif isinstance(entity, MCPToolConfig):
                return self._mcp_config_to_dict(entity)
            else:
                # 默认处理
                return entity.to_dict() if hasattr(entity, 'to_dict') else {}
                
        except Exception as e:
            logger.error(f"实体转换为配置字典失败: {e}")
            raise ValueError(f"实体转换为配置字典失败: {e}")
    
    def validate_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """验证配置数据
        
        Args:
            config_data: 配置字典数据
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        
        try:
            # 基础字段验证
            if "name" not in config_data:
                errors.append("缺少必需字段: name")
            elif not config_data["name"] or not str(config_data["name"]).strip():
                errors.append("工具名称不能为空")
            
            if "description" not in config_data:
                warnings.append("缺少字段: description")
            
            if "tool_type" not in config_data:
                warnings.append("缺少字段: tool_type，将使用默认值 'native'")
            
            # 工具类型特定验证
            tool_type = config_data.get("tool_type", "native")
            
            if tool_type == "builtin":
                errors.extend(self._validate_builtin_config(config_data))
            elif tool_type == "native":
                errors.extend(self._validate_native_config(config_data))
            elif tool_type == "rest":
                errors.extend(self._validate_rest_config(config_data))
            elif tool_type == "mcp":
                errors.extend(self._validate_mcp_config(config_data))
            
            # 参数模式验证
            if "parameters_schema" in config_data:
                if not isinstance(config_data["parameters_schema"], dict):
                    errors.append("parameters_schema 必须是字典类型")
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"配置验证失败: {e}"],
                warnings=warnings
            )
    
    def _dict_to_registry_config(self, config_data: Dict[str, Any]) -> ToolRegistryConfig:
        """将配置字典转换为工具注册表配置"""
        # 提取工具配置列表
        tools = []
        if "tools" in config_data:
            for tool_data in config_data["tools"]:
                tool_config = self.dict_to_entity(tool_data)
                if isinstance(tool_config, ToolConfig):
                    tools.append(tool_config)
        
        # 从配置数据中获取所有必需的字段，如果没有提供则抛出异常
        required_fields = [
            "auto_discover", "discovery_paths", "reload_on_change",
            "max_tools", "enable_caching", "cache_ttl",
            "allow_dynamic_loading", "validate_schemas", "sandbox_mode"
        ]
        
        missing_fields = [field for field in required_fields if field not in config_data]
        if missing_fields:
            raise ValueError(f"工具注册表配置缺少必需字段: {', '.join(missing_fields)}")
        
        return ToolRegistryConfig(
            auto_discover=config_data["auto_discover"],
            discovery_paths=config_data["discovery_paths"],
            reload_on_change=config_data["reload_on_change"],
            tools=tools,
            max_tools=config_data["max_tools"],
            enable_caching=config_data["enable_caching"],
            cache_ttl=config_data["cache_ttl"],
            allow_dynamic_loading=config_data["allow_dynamic_loading"],
            validate_schemas=config_data["validate_schemas"],
            sandbox_mode=config_data["sandbox_mode"]
        )
    
    def _dict_to_builtin_config(self, config_data: Dict[str, Any]) -> BuiltinToolConfig:
        """将配置字典转换为内置工具配置"""
        return BuiltinToolConfig(
            name=config_data["name"],
            description=config_data.get("description", ""),
            parameters_schema=config_data.get("parameters_schema", {}),
            tool_type="builtin",
            function_path=config_data.get("function_path", ""),
            enabled=config_data.get("enabled", True),
            timeout=config_data.get("timeout", 30),
            metadata=config_data.get("metadata", {})
        )
    
    def _dict_to_native_config(self, config_data: Dict[str, Any]) -> NativeToolConfig:
        """将配置字典转换为原生工具配置"""
        return NativeToolConfig(
            name=config_data["name"],
            description=config_data.get("description", ""),
            parameters_schema=config_data.get("parameters_schema", {}),
            tool_type="native",
            function_path=config_data.get("function_path", ""),
            enabled=config_data.get("enabled", True),
            timeout=config_data.get("timeout", 30),
            metadata=config_data.get("metadata", {})
        )
    
    def _dict_to_rest_config(self, config_data: Dict[str, Any]) -> RestToolConfig:
        """将配置字典转换为REST工具配置"""
        return RestToolConfig(
            name=config_data["name"],
            description=config_data.get("description", ""),
            parameters_schema=config_data.get("parameters_schema", {}),
            tool_type="rest",
            api_url=config_data["api_url"],
            method=config_data.get("method", "POST"),
            auth_method=config_data.get("auth_method", "api_key"),
            headers=config_data.get("headers", {}),
            api_key=config_data.get("api_key"),
            retry_count=config_data.get("retry_count", 3),
            retry_delay=config_data.get("retry_delay", 1.0),
            enabled=config_data.get("enabled", True),
            timeout=config_data.get("timeout", 30),
            metadata=config_data.get("metadata", {})
        )
    
    def _dict_to_mcp_config(self, config_data: Dict[str, Any]) -> MCPToolConfig:
        """将配置字典转换为MCP工具配置"""
        return MCPToolConfig(
            name=config_data["name"],
            description=config_data.get("description", ""),
            parameters_schema=config_data.get("parameters_schema", {}),
            tool_type="mcp",
            mcp_server_url=config_data["mcp_server_url"],
            refresh_interval=config_data.get("refresh_interval"),
            dynamic_schema=config_data.get("dynamic_schema", False),
            enabled=config_data.get("enabled", True),
            timeout=config_data.get("timeout", 30),
            metadata=config_data.get("metadata", {})
        )
    
    def _registry_config_to_dict(self, config: ToolRegistryConfig) -> Dict[str, Any]:
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
    
    def _native_config_to_dict(self, config: NativeToolConfig) -> Dict[str, Any]:
        """将原生工具配置转换为字典"""
        return config.to_dict()
    
    def _rest_config_to_dict(self, config: RestToolConfig) -> Dict[str, Any]:
        """将REST工具配置转换为字典"""
        return config.to_dict()
    
    def _mcp_config_to_dict(self, config: MCPToolConfig) -> Dict[str, Any]:
        """将MCP工具配置转换为字典"""
        return config.to_dict()
    
    def _validate_builtin_config(self, config_data: Dict[str, Any]) -> List[str]:
        """验证内置工具配置"""
        errors = []
        
        if "function_path" not in config_data:
            errors.append("内置工具缺少必需字段: function_path")
        
        return errors
    
    def _validate_native_config(self, config_data: Dict[str, Any]) -> List[str]:
        """验证原生工具配置"""
        errors = []
        
        if "function_path" not in config_data:
            errors.append("原生工具缺少必需字段: function_path")
        
        return errors
    
    def _validate_rest_config(self, config_data: Dict[str, Any]) -> List[str]:
        """验证REST工具配置"""
        errors = []
        
        if "api_url" not in config_data:
            errors.append("REST工具缺少必需字段: api_url")
        elif not config_data["api_url"] or not str(config_data["api_url"]).strip():
            errors.append("API URL不能为空")
        
        return errors
    
    def _validate_mcp_config(self, config_data: Dict[str, Any]) -> List[str]:
        """验证MCP工具配置"""
        errors = []
        
        if "mcp_server_url" not in config_data:
            errors.append("MCP工具缺少必需字段: mcp_server_url")
        elif not config_data["mcp_server_url"] or not str(config_data["mcp_server_url"]).strip():
            errors.append("MCP服务器URL不能为空")
        
        return errors
    


# 便捷函数
def get_tools_config_mapper() -> ToolsConfigMapper:
    """获取工具配置映射器实例
    
    Returns:
        ToolsConfigMapper: 工具配置映射器实例
    """
    return ToolsConfigMapper()


# 向后兼容别名
ToolConfigMapper = ToolsConfigMapper