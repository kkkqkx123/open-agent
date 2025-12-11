"""LLM配置模式

定义LLM模块的配置验证模式和规则。
"""

from typing import Dict, Any, List, Optional
import logging

from .base_schema import BaseSchema
from src.interfaces.common_domain import ValidationResult

logger = logging.getLogger(__name__)


class LLMSchema(BaseSchema):
    """LLM配置模式
    
    定义LLM模块配置的验证规则和模式。
    """
    
    def __init__(self):
        """初始化LLM配置模式"""
        self.schema_definition = self._build_schema_definition()
        logger.debug("LLM配置模式初始化完成")
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证LLM配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 1. 验证顶级结构
        structure_errors, structure_warnings = self._validate_structure(config)
        errors.extend(structure_errors)
        warnings.extend(structure_warnings)
        
        # 2. 验证客户端配置
        if "clients" in config:
            client_errors, client_warnings = self._validate_clients(config["clients"])
            errors.extend(client_errors)
            warnings.extend(client_warnings)
        
        # 3. 验证模块配置
        if "module" in config:
            module_errors, module_warnings = self._validate_module(config["module"])
            errors.extend(module_errors)
            warnings.extend(module_warnings)
        
        # 4. 验证全局配置
        global_errors, global_warnings = self._validate_global_config(config)
        errors.extend(global_errors)
        warnings.extend(global_warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _build_schema_definition(self) -> Dict[str, Any]:
        """构建模式定义
        
        Returns:
            模式定义
        """
        return {
            "type": "object",
            "required": ["clients"],
            "properties": {
                "version": {
                    "type": "string",
                    "description": "配置版本"
                },
                "description": {
                    "type": "string",
                    "description": "配置描述"
                },
                "clients": {
                    "type": "object",
                    "description": "客户端配置",
                    "patternProperties": {
                        "^[a-zA-Z][a-zA-Z0-9_-]*$": {
                            "type": "object",
                            "required": ["model_type", "model_name"],
                            "properties": {
                                "model_type": {
                                    "type": "string",
                                    "enum": ["openai", "gemini", "anthropic", "mock", "human_relay"],
                                    "description": "模型类型"
                                },
                                "model_name": {
                                    "type": "string",
                                    "minLength": 1,
                                    "description": "模型名称"
                                },
                                "base_url": {
                                    "type": "string",
                                    "format": "uri",
                                    "description": "API基础URL"
                                },
                                "api_key": {
                                    "type": "string",
                                    "description": "API密钥"
                                },
                                "headers": {
                                    "type": "object",
                                    "description": "HTTP请求头"
                                },
                                "timeout": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 300,
                                    "description": "请求超时时间（秒）"
                                },
                                "max_retries": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 10,
                                    "description": "最大重试次数"
                                },
                                "temperature": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "maximum": 2.0,
                                    "description": "温度参数"
                                },
                                "max_tokens": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "description": "最大令牌数"
                                },
                                "top_p": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "maximum": 1.0,
                                    "description": "Top-p参数"
                                },
                                "stream": {
                                    "type": "boolean",
                                    "description": "是否启用流式响应"
                                },
                                "fallback_enabled": {
                                    "type": "boolean",
                                    "description": "是否启用降级"
                                },
                                "fallback_models": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "降级模型列表"
                                },
                                "max_fallback_attempts": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 5,
                                    "description": "最大降级尝试次数"
                                },
                                "connection_pool_config": {
                                    "type": "object",
                                    "properties": {
                                        "max_connections": {
                                            "type": "integer",
                                            "minimum": 1,
                                            "maximum": 100
                                        },
                                        "max_keepalive": {
                                            "type": "integer",
                                            "minimum": 1,
                                            "maximum": 100
                                        },
                                        "connection_timeout": {
                                            "type": "number",
                                            "minimum": 1.0,
                                            "maximum": 300.0
                                        }
                                    }
                                },
                                "metadata_config": {
                                    "type": "object",
                                    "description": "元数据配置"
                                }
                            }
                        }
                    }
                },
                "module": {
                    "type": "object",
                    "properties": {
                        "default_model": {
                            "type": "string",
                            "description": "默认模型"
                        },
                        "default_timeout": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 300,
                            "description": "默认超时时间"
                        },
                        "default_max_retries": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 10,
                            "description": "默认最大重试次数"
                        },
                        "cache_enabled": {
                            "type": "boolean",
                            "description": "是否启用缓存"
                        },
                        "cache_ttl": {
                            "type": "integer",
                            "minimum": 60,
                            "maximum": 86400,
                            "description": "缓存生存时间（秒）"
                        },
                        "cache_max_size": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10000,
                            "description": "最大缓存条目数"
                        },
                        "hooks_enabled": {
                            "type": "boolean",
                            "description": "是否启用钩子"
                        },
                        "log_requests": {
                            "type": "boolean",
                            "description": "是否记录请求日志"
                        },
                        "log_responses": {
                            "type": "boolean",
                            "description": "是否记录响应日志"
                        },
                        "log_errors": {
                            "type": "boolean",
                            "description": "是否记录错误日志"
                        },
                        "fallback_enabled": {
                            "type": "boolean",
                            "description": "是否启用全局降级"
                        },
                        "global_fallback_models": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "全局降级模型列表"
                        },
                        "max_concurrent_requests": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1000,
                            "description": "最大并发请求数"
                        },
                        "request_queue_size": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10000,
                            "description": "请求队列大小"
                        },
                        "metrics_enabled": {
                            "type": "boolean",
                            "description": "是否启用指标收集"
                        },
                        "performance_tracking": {
                            "type": "boolean",
                            "description": "是否启用性能跟踪"
                        },
                        "connection_pool_enabled": {
                            "type": "boolean",
                            "description": "是否启用连接池"
                        },
                        "default_max_connections": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100
                        },
                        "default_max_keepalive": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100
                        },
                        "default_connection_timeout": {
                            "type": "number",
                            "minimum": 1.0,
                            "maximum": 300.0
                        }
                    }
                }
            }
        }
    
    def _validate_structure(self, config: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """验证配置结构
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表和警告列表
        """
        errors = []
        warnings = []
        
        # 检查是否为字典
        if not isinstance(config, dict):
            errors.append("配置必须是字典类型")
            return errors, warnings
        
        # 检查必要字段
        if "clients" not in config:
            errors.append("缺少必要的clients字段")
        elif not isinstance(config["clients"], dict):
            errors.append("clients字段必须是字典类型")
        elif len(config["clients"]) == 0:
            errors.append("至少需要配置一个客户端")
        
        return errors, warnings
    
    def _validate_clients(self, clients: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """验证客户端配置
        
        Args:
            clients: 客户端配置
            
        Returns:
            错误列表和警告列表
        """
        errors = []
        warnings = []
        
        for client_name, client_config in clients.items():
            client_errors, client_warnings = self._validate_single_client(client_name, client_config)
            errors.extend(client_errors)
            warnings.extend(client_warnings)
        
        return errors, warnings
    
    def _validate_single_client(self, client_name: str, client_config: Any) -> tuple[List[str], List[str]]:
        """验证单个客户端配置
        
        Args:
            client_name: 客户端名称
            client_config: 客户端配置
            
        Returns:
            错误列表和警告列表
        """
        errors = []
        warnings = []
        
        # 检查配置类型
        if not isinstance(client_config, dict):
            errors.append(f"客户端 {client_name} 的配置必须是字典类型")
            return errors, warnings
        
        # 检查必要字段
        required_fields = ["model_type", "model_name"]
        for field in required_fields:
            if field not in client_config:
                errors.append(f"客户端 {client_name} 缺少必要字段: {field}")
            elif not client_config[field]:
                errors.append(f"客户端 {client_name} 的字段 {field} 不能为空")
        
        # 验证模型类型
        if "model_type" in client_config:
            model_type = client_config["model_type"]
            valid_types = ["openai", "gemini", "anthropic", "mock", "human_relay"]
            if model_type not in valid_types:
                errors.append(f"客户端 {client_name} 的模型类型无效: {model_type}")
        
        # 验证数值范围
        numeric_fields = {
            "timeout": (1, 300),
            "max_retries": (0, 10),
            "temperature": (0.0, 2.0),
            "top_p": (0.0, 1.0),
            "max_fallback_attempts": (1, 5)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in client_config:
                value = client_config[field]
                if not isinstance(value, (int, float)):
                    errors.append(f"客户端 {client_name} 的字段 {field} 必须是数值类型")
                elif not (min_val <= value <= max_val):
                    errors.append(f"客户端 {client_name} 的字段 {field} 值超出范围: {value}")
        
        # 验证数组字段
        array_fields = ["fallback_models"]
        for field in array_fields:
            if field in client_config:
                value = client_config[field]
                if not isinstance(value, list):
                    errors.append(f"客户端 {client_name} 的字段 {field} 必须是数组类型")
                elif not all(isinstance(item, str) for item in value):
                    errors.append(f"客户端 {client_name} 的字段 {field} 的所有元素必须是字符串")
        
        # 验证连接池配置
        if "connection_pool_config" in client_config:
            pool_config = client_config["connection_pool_config"]
            if not isinstance(pool_config, dict):
                errors.append(f"客户端 {client_name} 的连接池配置必须是字典类型")
            else:
                pool_errors, pool_warnings = self._validate_connection_pool_config(client_name, pool_config)
                errors.extend(pool_errors)
                warnings.extend(pool_warnings)
        
        return errors, warnings
    
    def _validate_connection_pool_config(self, client_name: str, pool_config: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """验证连接池配置
        
        Args:
            client_name: 客户端名称
            pool_config: 连接池配置
            
        Returns:
            错误列表和警告列表
        """
        errors = []
        warnings = []
        
        pool_fields = {
            "max_connections": (1, 100),
            "max_keepalive": (1, 100),
            "connection_timeout": (1.0, 300.0),
            "read_timeout": (1.0, 300.0),
            "write_timeout": (1.0, 300.0),
            "connect_retries": (1, 10),
            "pool_timeout": (1.0, 300.0)
        }
        
        for field, (min_val, max_val) in pool_fields.items():
            if field in pool_config:
                value = pool_config[field]
                if not isinstance(value, (int, float)):
                    errors.append(f"客户端 {client_name} 的连接池字段 {field} 必须是数值类型")
                elif not (min_val <= value <= max_val):
                    errors.append(f"客户端 {client_name} 的连接池字段 {field} 值超出范围: {value}")
        
        return errors, warnings
    
    def _validate_module(self, module: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """验证模块配置
        
        Args:
            module: 模块配置
            
        Returns:
            错误列表和警告列表
        """
        errors = []
        warnings = []
        
        # 验证数值范围
        numeric_fields = {
            "default_timeout": (1, 300),
            "default_max_retries": (0, 10),
            "cache_ttl": (60, 86400),
            "cache_max_size": (1, 10000),
            "max_concurrent_requests": (1, 1000),
            "request_queue_size": (1, 10000),
            "default_max_connections": (1, 100),
            "default_max_keepalive": (1, 100),
            "default_connection_timeout": (1.0, 300.0)
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in module:
                value = module[field]
                if not isinstance(value, (int, float)):
                    errors.append(f"模块配置的字段 {field} 必须是数值类型")
                elif not (min_val <= value <= max_val):
                    errors.append(f"模块配置的字段 {field} 值超出范围: {value}")
        
        # 验证数组字段
        array_fields = ["global_fallback_models"]
        for field in array_fields:
            if field in module:
                value = module[field]
                if not isinstance(value, list):
                    errors.append(f"模块配置的字段 {field} 必须是数组类型")
                elif not all(isinstance(item, str) for item in value):
                    errors.append(f"模块配置的字段 {field} 的所有元素必须是字符串")
        
        return errors, warnings
    
    def _validate_global_config(self, config: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """验证全局配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表和警告列表
        """
        errors = []
        warnings = []
        
        # 检查版本格式
        if "version" in config:
            version = config["version"]
            if not isinstance(version, str):
                errors.append("版本号必须是字符串类型")
            elif not self._is_valid_version(version):
                warnings.append(f"版本号格式可能不标准: {version}")
        
        # 检查默认模型是否存在
        if "module" in config and "default_model" in config["module"]:
            default_model = config["module"]["default_model"]
            if "clients" in config:
                model_exists = False
                for client_config in config["clients"].values():
                    if client_config.get("model_name") == default_model:
                        model_exists = True
                        break
                
                if not model_exists:
                    warnings.append(f"默认模型 {default_model} 在客户端配置中不存在")
        
        return errors, warnings
    
    def _is_valid_version(self, version: str) -> bool:
        """检查版本号格式是否有效
        
        Args:
            version: 版本号
            
        Returns:
            是否有效
        """
        import re
        # 简单的版本号格式检查：x.y.z
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))