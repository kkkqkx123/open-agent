"""
工具配置模式

定义工具模块的配置模式和验证规则。
"""

from typing import Dict, Any, List
from .base_schema import BaseSchema
from src.interfaces.common_domain import ValidationResult


class ToolsSchema(BaseSchema):
    """工具配置模式
    
    定义工具配置的结构和验证规则。
    """
    
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
                    "description": "工具的唯一标识名称",
                    "minLength": 1,
                    "maxLength": 100,
                    "pattern": "^[a-zA-Z][a-zA-Z0-9_-]*$"
                },
                "description": {
                    "type": "string",
                    "title": "工具描述",
                    "description": "工具功能的详细描述",
                    "minLength": 1,
                    "maxLength": 500
                },
                "parameters_schema": {
                    "type": "object",
                    "title": "参数模式",
                    "description": "工具参数的JSON Schema定义",
                    "properties": {
                        "type": {"type": "string"},
                        "properties": {"type": "object"},
                        "required": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "tool_type": {
                    "type": "string",
                    "title": "工具类型",
                    "description": "工具的实现类型",
                    "enum": ["builtin", "native", "rest", "mcp"],
                    "default": "native"
                },
                "enabled": {
                    "type": "boolean",
                    "title": "是否启用",
                    "description": "是否启用此工具",
                    "default": True
                },
                "timeout": {
                    "type": "integer",
                    "title": "超时时间",
                    "description": "工具执行的超时时间（秒）",
                    "minimum": 1,
                    "maximum": 3600,
                    "default": 30
                },
                "metadata": {
                    "type": "object",
                    "title": "元数据",
                    "description": "工具的额外元数据信息",
                    "additionalProperties": True
                }
            },
            "allOf": [
                {
                    "if": {"properties": {"tool_type": {"const": "builtin"}}},
                    "then": {
                        "properties": {
                            "function_path": {
                                "type": "string",
                                "title": "函数路径",
                                "description": "内置工具函数的导入路径",
                                "minLength": 1
                            }
                        },
                        "required": ["function_path"]
                    }
                },
                {
                    "if": {"properties": {"tool_type": {"const": "native"}}},
                    "then": {
                        "properties": {
                            "function_path": {
                                "type": "string",
                                "title": "函数路径",
                                "description": "原生工具函数的导入路径",
                                "minLength": 1
                            },
                            "state_config": {
                                "type": "object",
                                "title": "状态配置",
                                "description": "状态管理器配置",
                                "properties": {
                                    "manager_type": {
                                        "type": "string",
                                        "enum": ["memory", "persistent", "session", "distributed"],
                                        "default": "memory"
                                    },
                                    "ttl": {"type": "integer", "minimum": 0},
                                    "auto_cleanup": {"type": "boolean", "default": True},
                                    "cleanup_interval": {"type": "integer", "minimum": 1, "default": 300}
                                }
                            },
                            "business_config": {
                                "type": "object",
                                "title": "业务状态配置",
                                "description": "业务状态管理配置",
                                "properties": {
                                    "max_history_size": {"type": "integer", "minimum": 1, "default": 1000},
                                    "max_state_size": {"type": "integer", "minimum": 1, "default": 1048576},
                                    "state_compression": {"type": "boolean", "default": False},
                                    "versioning": {"type": "boolean", "default": True},
                                    "max_versions": {"type": "integer", "minimum": 1, "default": 10},
                                    "auto_save": {"type": "boolean", "default": True}
                                }
                            },
                            "state_injection": {
                                "type": "boolean",
                                "title": "状态注入",
                                "description": "是否自动注入状态参数",
                                "default": True
                            },
                            "state_parameter_name": {
                                "type": "string",
                                "title": "状态参数名称",
                                "description": "状态参数的名称",
                                "default": "state"
                            }
                        },
                        "required": ["function_path"]
                    }
                },
                {
                    "if": {"properties": {"tool_type": {"const": "rest"}}},
                    "then": {
                        "properties": {
                            "api_url": {
                                "type": "string",
                                "title": "API URL",
                                "description": "REST API的端点URL",
                                "format": "uri",
                                "minLength": 1
                            },
                            "method": {
                                "type": "string",
                                "title": "HTTP方法",
                                "description": "HTTP请求方法",
                                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                                "default": "POST"
                            },
                            "headers": {
                                "type": "object",
                                "title": "请求头",
                                "description": "HTTP请求头",
                                "additionalProperties": {"type": "string"}
                            },
                            "auth_method": {
                                "type": "string",
                                "title": "认证方法",
                                "description": "API认证方法",
                                "enum": ["api_key", "api_key_header", "oauth", "none"],
                                "default": "api_key"
                            },
                            "api_key": {
                                "type": "string",
                                "title": "API密钥",
                                "description": "API认证密钥"
                            },
                            "retry_count": {
                                "type": "integer",
                                "title": "重试次数",
                                "description": "请求失败时的重试次数",
                                "minimum": 0,
                                "maximum": 10,
                                "default": 3
                            },
                            "retry_delay": {
                                "type": "number",
                                "title": "重试延迟",
                                "description": "重试之间的延迟时间（秒）",
                                "minimum": 0,
                                "maximum": 60,
                                "default": 1.0
                            },
                            "state_config": {
                                "type": "object",
                                "title": "状态配置",
                                "description": "连接状态管理配置",
                                "properties": {
                                    "manager_type": {
                                        "type": "string",
                                        "enum": ["memory", "persistent", "session", "distributed"],
                                        "default": "memory"
                                    },
                                    "ttl": {"type": "integer", "minimum": 0},
                                    "auto_cleanup": {"type": "boolean", "default": True},
                                    "cleanup_interval": {"type": "integer", "minimum": 1, "default": 300}
                                }
                            }
                        },
                        "required": ["api_url"]
                    }
                },
                {
                    "if": {"properties": {"tool_type": {"const": "mcp"}}},
                    "then": {
                        "properties": {
                            "mcp_server_url": {
                                "type": "string",
                                "title": "MCP服务器URL",
                                "description": "MCP服务器的连接URL",
                                "format": "uri",
                                "minLength": 1
                            },
                            "dynamic_schema": {
                                "type": "boolean",
                                "title": "动态模式",
                                "description": "是否动态获取工具模式",
                                "default": False
                            },
                            "refresh_interval": {
                                "type": "integer",
                                "title": "刷新间隔",
                                "description": "模式刷新间隔（秒）",
                                "minimum": 1,
                                "maximum": 86400
                            },
                            "state_config": {
                                "type": "object",
                                "title": "状态配置",
                                "description": "MCP连接状态管理配置",
                                "properties": {
                                    "manager_type": {
                                        "type": "string",
                                        "enum": ["memory", "persistent", "session", "distributed"],
                                        "default": "memory"
                                    },
                                    "ttl": {"type": "integer", "minimum": 0},
                                    "auto_cleanup": {"type": "boolean", "default": True},
                                    "cleanup_interval": {"type": "integer", "minimum": 1, "default": 300}
                                }
                            }
                        },
                        "required": ["mcp_server_url"]
                    }
                }
            ]
        }
    
    def get_registry_config_schema(self) -> Dict[str, Any]:
        """获取工具注册表配置模式
        
        Returns:
            工具注册表配置模式字典
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
                    "description": "是否自动发现工具",
                    "default": True
                },
                "discovery_paths": {
                    "type": "array",
                    "title": "发现路径",
                    "description": "工具发现的路径列表",
                    "items": {
                        "type": "string",
                        "minLength": 1
                    },
                    "default": []
                },
                "reload_on_change": {
                    "type": "boolean",
                    "title": "变化时重新加载",
                    "description": "配置文件变化时是否自动重新加载",
                    "default": False
                },
                "tools": {
                    "type": "array",
                    "title": "工具列表",
                    "description": "显式配置的工具列表",
                    "items": {
                        "$ref": "#/definitions/tool_config"
                    },
                    "default": []
                },
                "max_tools": {
                    "type": "integer",
                    "title": "最大工具数",
                    "description": "允许加载的最大工具数量",
                    "minimum": 1,
                    "maximum": 10000,
                    "default": 1000
                },
                "enable_caching": {
                    "type": "boolean",
                    "title": "启用缓存",
                    "description": "是否启用工具配置缓存",
                    "default": True
                },
                "cache_ttl": {
                    "type": "integer",
                    "title": "缓存生存时间",
                    "description": "配置缓存的生存时间（秒）",
                    "minimum": 1,
                    "maximum": 86400,
                    "default": 300
                },
                "allow_dynamic_loading": {
                    "type": "boolean",
                    "title": "允许动态加载",
                    "description": "是否允许运行时动态加载工具",
                    "default": True
                },
                "validate_schemas": {
                    "type": "boolean",
                    "title": "验证模式",
                    "description": "是否验证工具参数模式",
                    "default": True
                },
                "sandbox_mode": {
                    "type": "boolean",
                    "title": "沙盒模式",
                    "description": "是否在沙盒模式下运行工具",
                    "default": False
                }
            },
            "definitions": {
                "tool_config": {
                    "$ref": "#/definitions/tool_base_config"
                }
            },
            "definitions": {
                "tool_base_config": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "description": {"type": "string"},
                        "parameters_schema": {"type": "object"},
                        "tool_type": {
                            "type": "string",
                            "enum": ["builtin", "native", "rest", "mcp"]
                        },
                        "enabled": {"type": "boolean"},
                        "timeout": {"type": "integer", "minimum": 1},
                        "metadata": {"type": "object"}
                    },
                    "required": ["name", "description", "parameters_schema", "tool_type"]
                }
            }
        }
    
    def get_toolset_config_schema(self) -> Dict[str, Any]:
        """获取工具集配置模式
        
        Returns:
            工具集配置模式字典
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
                    "description": "工具集的唯一标识名称",
                    "minLength": 1,
                    "maxLength": 100,
                    "pattern": "^[a-zA-Z][a-zA-Z0-9_-]*$"
                },
                "description": {
                    "type": "string",
                    "title": "工具集描述",
                    "description": "工具集功能的详细描述",
                    "minLength": 1,
                    "maxLength": 500
                },
                "tools": {
                    "type": "array",
                    "title": "工具列表",
                    "description": "工具集中包含的工具名称列表",
                    "items": {
                        "type": "string",
                        "minLength": 1
                    },
                    "minItems": 1
                },
                "enabled": {
                    "type": "boolean",
                    "title": "是否启用",
                    "description": "是否启用此工具集",
                    "default": True
                },
                "metadata": {
                    "type": "object",
                    "title": "元数据",
                    "description": "工具集的额外元数据信息",
                    "additionalProperties": True
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