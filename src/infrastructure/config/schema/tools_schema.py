"""
工具配置模式

定义工具模块的配置模式和验证规则，与配置加载模块集成。
"""

from typing import Dict, Any, List, Optional
import logging
from .base_schema import BaseSchema
from src.infrastructure.validation.result import ValidationResult
from src.interfaces.config import IConfigLoader

logger = logging.getLogger(__name__)


class ToolsSchema(BaseSchema):
    """工具配置模式
    
    定义工具配置的结构和验证规则，与配置加载模块集成。
    """
    
    def __init__(self, config_loader: Optional[IConfigLoader] = None):
        """初始化工具配置模式
        
        Args:
            config_loader: 配置加载器，用于动态加载配置模式
        """
        super().__init__()
        self.config_loader = config_loader
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证工具配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        # 判断是工具配置还是工具注册表配置
        if "tools" in config and "auto_discover" in config:
            errors = self.validate_registry_config(config)
        else:
            errors = self.validate_tool_config(config)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
    
    def get_tool_config_schema(self) -> Dict[str, Any]:
        """获取工具配置模式
        
        Returns:
            工具配置模式字典
        """
        # 尝试从缓存获取
        if "tool_config" in self._schema_cache:
            return self._schema_cache["tool_config"]
        
        # 尝试从配置文件加载
        schema = self._load_schema_from_config("tool_config")
        
        if schema is None:
            # 如果无法从配置加载，使用基础模式
            schema = self._get_base_tool_config_schema()
        
        # 缓存模式
        self._schema_cache["tool_config"] = schema
        return schema
    
    def get_registry_config_schema(self) -> Dict[str, Any]:
        """获取工具注册表配置模式
        
        Returns:
            工具注册表配置模式字典
        """
        # 尝试从缓存获取
        if "registry_config" in self._schema_cache:
            return self._schema_cache["registry_config"]
        
        # 尝试从配置文件加载
        schema = self._load_schema_from_config("registry_config")
        
        if schema is None:
            # 如果无法从配置加载，使用基础模式
            schema = self._get_base_registry_config_schema()
        
        # 缓存模式
        self._schema_cache["registry_config"] = schema
        return schema
    
    def get_toolset_config_schema(self) -> Dict[str, Any]:
        """获取工具集配置模式
        
        Returns:
            工具集配置模式字典
        """
        # 尝试从缓存获取
        if "toolset_config" in self._schema_cache:
            return self._schema_cache["toolset_config"]
        
        # 尝试从配置文件加载
        schema = self._load_schema_from_config("toolset_config")
        
        if schema is None:
            # 如果无法从配置加载，使用基础模式
            schema = self._get_base_toolset_config_schema()
        
        # 缓存模式
        self._schema_cache["toolset_config"] = schema
        return schema
    
    def _load_schema_from_config(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """从配置文件加载模式
        
        Args:
            schema_name: 模式名称
            
        Returns:
            模式字典或None
        """
        if not self.config_loader:
            return None
        
        try:
            # 尝试加载模式配置文件
            schema_path = f"config/schema/tools/{schema_name}"
            schema_config = self.config_loader.load(schema_path)
            
            if schema_config and "schema" in schema_config:
                logger.debug(f"从配置文件加载模式: {schema_name}")
                return schema_config["schema"]
            
        except Exception as e:
            logger.debug(f"无法从配置文件加载模式 {schema_name}: {e}")
        
        return None
    
    def _get_base_tool_config_schema(self) -> Dict[str, Any]:
        """获取基础工具配置模式
        
        Returns:
            基础工具配置模式字典
        """
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": "工具配置",
            "description": "单个工具的配置定义",
            "required": ["name", "description", "parameters_schema", "tool_type"],
            "properties": {
                "name": {
                    "type": "string",
                    "title": "工具名称",
                    "description": "工具的唯一标识名称"
                },
                "description": {
                    "type": "string",
                    "title": "工具描述",
                    "description": "工具功能的详细描述"
                },
                "parameters_schema": {
                    "type": "object",
                    "title": "参数模式",
                    "description": "工具参数的JSON Schema定义"
                },
                "tool_type": {
                    "type": "string",
                    "title": "工具类型",
                    "description": "工具的实现类型",
                    "enum": ["builtin", "native", "rest", "mcp"]
                },
                "enabled": {
                    "type": "boolean",
                    "title": "是否启用",
                    "description": "是否启用此工具"
                },
                "timeout": {
                    "type": "integer",
                    "title": "超时时间",
                    "description": "工具执行的超时时间（秒）",
                    "minimum": 1
                },
                "metadata": {
                    "type": "object",
                    "title": "元数据",
                    "description": "工具的额外元数据信息"
                }
            }
        }
    
    def _get_base_registry_config_schema(self) -> Dict[str, Any]:
        """获取基础工具注册表配置模式
        
        Returns:
            基础工具注册表配置模式字典
        """
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": "工具注册表配置",
            "description": "工具注册表的全局配置",
            "properties": {
                "auto_discover": {
                    "type": "boolean",
                    "title": "自动发现",
                    "description": "是否自动发现工具"
                },
                "discovery_paths": {
                    "type": "array",
                    "title": "发现路径",
                    "description": "工具发现的路径列表",
                    "items": {"type": "string"}
                },
                "reload_on_change": {
                    "type": "boolean",
                    "title": "变化时重新加载",
                    "description": "配置文件变化时是否自动重新加载"
                },
                "tools": {
                    "type": "array",
                    "title": "工具列表",
                    "description": "显式配置的工具列表",
                    "items": {"type": "object"}
                },
                "max_tools": {
                    "type": "integer",
                    "title": "最大工具数",
                    "description": "允许加载的最大工具数量",
                    "minimum": 1
                },
                "enable_caching": {
                    "type": "boolean",
                    "title": "启用缓存",
                    "description": "是否启用工具配置缓存"
                },
                "cache_ttl": {
                    "type": "integer",
                    "title": "缓存生存时间",
                    "description": "配置缓存的生存时间（秒）",
                    "minimum": 1
                },
                "allow_dynamic_loading": {
                    "type": "boolean",
                    "title": "允许动态加载",
                    "description": "是否允许运行时动态加载工具"
                },
                "validate_schemas": {
                    "type": "boolean",
                    "title": "验证模式",
                    "description": "是否验证工具参数模式"
                },
                "sandbox_mode": {
                    "type": "boolean",
                    "title": "沙盒模式",
                    "description": "是否在沙盒模式下运行工具"
                }
            }
        }
    
    def _get_base_toolset_config_schema(self) -> Dict[str, Any]:
        """获取基础工具集配置模式
        
        Returns:
            基础工具集配置模式字典
        """
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": "工具集配置",
            "description": "工具集的配置定义",
            "required": ["name", "description", "tools"],
            "properties": {
                "name": {
                    "type": "string",
                    "title": "工具集名称",
                    "description": "工具集的唯一标识名称"
                },
                "description": {
                    "type": "string",
                    "title": "工具集描述",
                    "description": "工具集功能的详细描述"
                },
                "tools": {
                    "type": "array",
                    "title": "工具列表",
                    "description": "工具集中包含的工具名称列表",
                    "items": {"type": "string"},
                    "minItems": 1
                },
                "enabled": {
                    "type": "boolean",
                    "title": "是否启用",
                    "description": "是否启用此工具集"
                },
                "metadata": {
                    "type": "object",
                    "title": "元数据",
                    "description": "工具集的额外元数据信息"
                }
            }
        }
    
    def validate_tool_config(self, config: Dict[str, Any]) -> List[str]:
        """验证工具配置
        
        Args:
            config: 工具配置数据
            
        Returns:
            验证错误列表
        """
        # 基础验证
        errors = []
        
        # 验证必需字段
        if "name" not in config:
            errors.append("缺少必需字段: name")
        elif not config["name"]:
            errors.append("工具名称不能为空")
        
        if "description" not in config:
            errors.append("缺少必需字段: description")
        
        if "parameters_schema" not in config:
            errors.append("缺少必需字段: parameters_schema")
        elif not isinstance(config["parameters_schema"], dict):
            errors.append("parameters_schema 必须是字典类型")
        
        if "tool_type" not in config:
            errors.append("缺少必需字段: tool_type")
        elif config["tool_type"] not in ["builtin", "native", "rest", "mcp"]:
            errors.append(f"无效的工具类型: {config['tool_type']}")
        
        # 工具类型特定验证
        tool_type = config.get("tool_type", "native")
        
        if tool_type in ["builtin", "native"]:
            if "function_path" not in config:
                errors.append(f"{tool_type}工具缺少必需字段: function_path")
        elif tool_type == "rest":
            if "api_url" not in config:
                errors.append("REST工具缺少必需字段: api_url")
        elif tool_type == "mcp":
            if "mcp_server_url" not in config:
                errors.append("MCP工具缺少必需字段: mcp_server_url")
        
        return errors
    
    def validate_registry_config(self, config: Dict[str, Any]) -> List[str]:
        """验证工具注册表配置
        
        Args:
            config: 工具注册表配置数据
            
        Returns:
            验证错误列表
        """
        errors = []
        
        # 验证工具列表
        if "tools" in config:
            if not isinstance(config["tools"], list):
                errors.append("tools 必须是数组类型")
            else:
                for i, tool in enumerate(config["tools"]):
                    tool_errors = self.validate_tool_config(tool)
                    errors.extend([f"工具 {i}: {e}" for e in tool_errors])
        
        return errors
    
    def validate_toolset_config(self, config: Dict[str, Any]) -> List[str]:
        """验证工具集配置
        
        Args:
            config: 工具集配置数据
            
        Returns:
            验证错误列表
        """
        errors = []
        
        # 验证必需字段
        if "name" not in config:
            errors.append("缺少必需字段: name")
        
        if "tools" not in config:
            errors.append("缺少必需字段: tools")
        elif not isinstance(config["tools"], list):
            errors.append("tools 必须是数组类型")
        elif len(config["tools"]) == 0:
            errors.append("tools 列表不能为空")
        
        return errors