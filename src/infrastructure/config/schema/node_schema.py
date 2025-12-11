"""Node配置模式

定义Node模块的配置验证模式。
"""

from typing import Dict, Any, List
import logging

from .base_schema import BaseSchema
from src.interfaces.common_domain import ValidationResult

logger = logging.getLogger(__name__)


class NodeSchema(BaseSchema):
    """Node配置模式
    
    定义Node模块的配置验证规则和模式。
    """
    
    def __init__(self):
        """初始化Node配置模式"""
        super().__init__(self._get_schema_definition())
        logger.debug("Node配置模式初始化完成")
    
    def _get_schema_definition(self) -> Dict[str, Any]:
        """获取模式定义
        
        Returns:
            模式定义字典
        """
        return {
            "type": "object",
            "required": ["name", "function_name"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "节点名称"
                },
                "id": {
                    "type": "string",
                    "description": "节点ID"
                },
                "description": {
                    "type": "string",
                    "description": "节点描述"
                },
                "type": {
                    "type": "string",
                    "enum": ["llm", "tool", "condition", "start", "end", "custom", "input", "output"],
                    "description": "节点类型"
                },
                "function_name": {
                    "type": "string",
                    "description": "函数名称"
                },
                "timeout": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "超时时间（秒）"
                },
                "retry_attempts": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "重试次数"
                },
                "retry_delay": {
                    "type": "number",
                    "minimum": 0,
                    "description": "重试延迟（秒）"
                },
                "enable_tracing": {
                    "type": "boolean",
                    "description": "是否启用跟踪"
                },
                "log_inputs": {
                    "type": "boolean",
                    "description": "是否记录输入"
                },
                "log_outputs": {
                    "type": "boolean",
                    "description": "是否记录输出"
                },
                "function_config": {
                    "type": "object",
                    "properties": {
                        "model": {"type": "string"},
                        "temperature": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 2
                        },
                        "max_tokens": {
                            "type": "integer",
                            "minimum": 1
                        },
                        "tool_name": {"type": "string"},
                        "timeout": {"type": "integer", "minimum": 1},
                        "error_handling": {
                            "type": "string",
                            "enum": ["raise", "ignore", "log"]
                        },
                        "default_path": {"type": "string"}
                    },
                    "description": "函数配置"
                },
                "input_parameters": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "required": {"type": "boolean"},
                                "default": {},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "description": "输入参数"
                },
                "output_parameters": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "description": "输出参数"
                },
                "environment": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {"type": "string"}
                    },
                    "description": "环境变量"
                },
                "input_mapping": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {"type": "string"}
                    },
                    "description": "输入映射"
                },
                "output_mapping": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {"type": "string"}
                    },
                    "description": "输出映射"
                },
                "state_updates": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {"type": "string"}
                    },
                    "description": "状态更新"
                },
                "additional_config": {
                    "type": "object",
                    "properties": {
                        "enable_caching": {"type": "boolean"},
                        "cache_ttl": {"type": "integer", "minimum": 0},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "normal", "high"]
                        }
                    },
                    "description": "额外配置"
                }
            }
        }
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 基础验证
        base_result = super().validate(config)
        errors.extend(base_result.errors)
        warnings.extend(base_result.warnings)
        
        # Node特定验证
        errors.extend(self._validate_node_structure(config))
        errors.extend(self._validate_function_config(config))
        errors.extend(self._validate_parameters(config))
        
        # 生成警告
        warnings.extend(self._generate_warnings(config))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_node_structure(self, config: Dict[str, Any]) -> List[str]:
        """验证节点结构
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        
        # 验证节点名称
        name = config.get("name")
        if not name:
            errors.append("节点名称不能为空")
        elif not isinstance(name, str):
            errors.append("节点名称必须是字符串")
        
        # 验证节点ID
        node_id = config.get("id")
        if node_id and not isinstance(node_id, str):
            errors.append("节点ID必须是字符串")
        
        # 验证函数名称
        function_name = config.get("function_name")
        if not function_name:
            errors.append("函数名称不能为空")
        elif not isinstance(function_name, str):
            errors.append("函数名称必须是字符串")
        
        # 验证节点类型
        node_type = config.get("type")
        if node_type and node_type not in ["llm", "tool", "condition", "start", "end", "custom", "input", "output"]:
            errors.append(f"不支持的节点类型: {node_type}")
        
        # 验证数值字段
        timeout = config.get("timeout")
        if timeout is not None:
            if not isinstance(timeout, int) or timeout <= 0:
                errors.append("timeout必须是大于0的整数")
        
        retry_attempts = config.get("retry_attempts")
        if retry_attempts is not None:
            if not isinstance(retry_attempts, int) or retry_attempts < 0:
                errors.append("retry_attempts必须是非负整数")
        
        retry_delay = config.get("retry_delay")
        if retry_delay is not None:
            if not isinstance(retry_delay, (int, float)) or retry_delay < 0:
                errors.append("retry_delay必须是非负数")
        
        return errors
    
    def _validate_function_config(self, config: Dict[str, Any]) -> List[str]:
        """验证函数配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        node_type = config.get("type")
        function_config = config.get("function_config", {})
        
        if not isinstance(function_config, dict):
            errors.append("function_config必须是字典")
            return errors
        
        # 根据节点类型验证特定配置
        if node_type == "llm":
            if "model" not in function_config:
                errors.append("LLM节点必须指定模型")
            
            temperature = function_config.get("temperature")
            if temperature is not None:
                if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
                    errors.append("temperature必须在0-2之间")
            
            max_tokens = function_config.get("max_tokens")
            if max_tokens is not None:
                if not isinstance(max_tokens, int) or max_tokens <= 0:
                    errors.append("max_tokens必须是大于0的整数")
        
        elif node_type == "tool":
            if "tool_name" not in function_config and "timeout" not in function_config:
                errors.append("Tool节点必须指定tool_name或timeout")
            
            timeout = function_config.get("timeout")
            if timeout is not None:
                if not isinstance(timeout, int) or timeout <= 0:
                    errors.append("timeout必须是大于0的整数")
        
        elif node_type == "condition":
            error_handling = function_config.get("error_handling")
            if error_handling and error_handling not in ["raise", "ignore", "log"]:
                errors.append("error_handling必须是raise、ignore或log")
        
        return errors
    
    def _validate_parameters(self, config: Dict[str, Any]) -> List[str]:
        """验证参数配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        
        # 验证输入参数
        input_params = config.get("input_parameters", {})
        if not isinstance(input_params, dict):
            errors.append("input_parameters必须是字典")
        else:
            for param_name, param_config in input_params.items():
                if not isinstance(param_config, dict):
                    errors.append(f"输入参数 {param_name} 配置必须是字典")
                    continue
                
                if "type" not in param_config:
                    errors.append(f"输入参数 {param_name} 必须指定type")
        
        # 验证输出参数
        output_params = config.get("output_parameters", {})
        if not isinstance(output_params, dict):
            errors.append("output_parameters必须是字典")
        else:
            for param_name, param_config in output_params.items():
                if not isinstance(param_config, dict):
                    errors.append(f"输出参数 {param_name} 配置必须是字典")
                    continue
                
                if "type" not in param_config:
                    errors.append(f"输出参数 {param_name} 必须指定type")
        
        # 验证环境变量
        environment = config.get("environment", {})
        if not isinstance(environment, dict):
            errors.append("environment必须是字典")
        
        # 验证映射配置
        for mapping_name in ["input_mapping", "output_mapping", "state_updates"]:
            mapping = config.get(mapping_name, {})
            if not isinstance(mapping, dict):
                errors.append(f"{mapping_name}必须是字典")
        
        return errors
    
    def _generate_warnings(self, config: Dict[str, Any]) -> List[str]:
        """生成警告
        
        Args:
            config: 配置数据
            
        Returns:
            警告列表
        """
        warnings = []
        
        # 检查是否缺少描述
        if not config.get("description"):
            warnings.append("建议添加节点描述")
        
        # 检查重试配置
        retry_attempts = config.get("retry_attempts", 0)
        if retry_attempts > 5:
            warnings.append("重试次数过多可能影响性能")
        
        # 检查超时配置
        timeout = config.get("timeout", 30)
        if timeout > 300:
            warnings.append("超时时间过长可能影响性能")
        
        # 检查日志配置
        if not config.get("log_inputs", True):
            warnings.append("禁用输入日志可能影响调试")
        
        if not config.get("log_outputs", True):
            warnings.append("禁用输出日志可能影响调试")
        
        # 检查参数数量
        input_params = config.get("input_parameters", {})
        output_params = config.get("output_parameters", {})
        
        if len(input_params) > 20:
            warnings.append("输入参数过多可能影响性能")
        
        if len(output_params) > 20:
            warnings.append("输出参数过多可能影响性能")
        
        return warnings