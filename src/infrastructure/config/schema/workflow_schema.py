"""Workflow配置模式

定义Workflow模块的配置验证模式。
"""

from typing import Dict, Any, List
import logging

from ..impl.base_impl import ConfigSchema
from src.interfaces.common_domain import ValidationResult

logger = logging.getLogger(__name__)


class WorkflowSchema(ConfigSchema):
    """Workflow配置模式
    
    定义Workflow模块的配置验证规则和模式。
    """
    
    def __init__(self):
        """初始化Workflow配置模式"""
        super().__init__(self._get_schema_definition())
        logger.debug("Workflow配置模式初始化完成")
    
    def _get_schema_definition(self) -> Dict[str, Any]:
        """获取模式定义
        
        Returns:
            模式定义字典
        """
        return {
            "type": "object",
            "required": ["workflow_name", "nodes"],
            "properties": {
                "workflow_name": {
                    "type": "string",
                    "description": "工作流名称"
                },
                "description": {
                    "type": "string",
                    "description": "工作流描述"
                },
                "workflow_type": {
                    "type": "string",
                    "enum": ["sequential", "parallel", "conditional", "loop", "react", "state_machine"],
                    "description": "工作流类型"
                },
                "max_iterations": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1000,
                    "description": "最大迭代次数"
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
                "logging_level": {
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    "description": "日志级别"
                },
                "enable_tracing": {
                    "type": "boolean",
                    "description": "是否启用跟踪"
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "description": {"type": "string"},
                        "author": {"type": "string"},
                        "workflow_type": {"type": "string"}
                    },
                    "description": "元数据"
                },
                "state_schema": {
                    "type": "object",
                    "required": ["name", "fields"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "状态名称"
                        },
                        "fields": {
                            "type": "object",
                            "patternProperties": {
                                ".*": {
                                    "type": "object",
                                    "required": ["type"],
                                    "properties": {
                                        "type": {"type": "string"},
                                        "default": {},
                                        "reducer": {"type": "string"},
                                        "description": {"type": "string"}
                                    }
                                }
                            },
                            "description": "状态字段"
                        }
                    },
                    "description": "状态模式"
                },
                "nodes": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {
                            "type": "object",
                            "required": ["function"],
                            "properties": {
                                "function": {"type": "string"},
                                "config": {
                                    "type": "object",
                                    "properties": {
                                        "description": {"type": "string"},
                                        "timeout": {"type": "integer", "minimum": 1},
                                        "retry_attempts": {"type": "integer", "minimum": 0},
                                        "retry_delay": {"type": "number", "minimum": 0}
                                    }
                                },
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "description": "节点配置"
                },
                "edges": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["from", "type"],
                        "properties": {
                            "from": {"type": "string"},
                            "to": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": ["simple", "conditional", "parallel", "merge", "always"]
                            },
                            "condition": {"type": "string"},
                            "path_map": {
                                "oneOf": [
                                    {"type": "object"},
                                    {"type": "array"}
                                ]
                            },
                            "description": {"type": "string"}
                        }
                    },
                    "description": "边配置"
                },
                "entry_point": {
                    "type": "string",
                    "description": "入口点"
                },
                "validation_rules": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["field", "rule_type"],
                        "properties": {
                            "field": {"type": "string"},
                            "rule_type": {
                                "type": "string",
                                "enum": ["required", "range", "pattern", "custom"]
                            },
                            "value": {},
                            "message": {"type": "string"}
                        }
                    },
                    "description": "验证规则"
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
        
        # Workflow特定验证
        errors.extend(self._validate_workflow_structure(config))
        errors.extend(self._validate_nodes(config))
        errors.extend(self._validate_edges(config))
        errors.extend(self._validate_state_schema(config))
        
        # 生成警告
        warnings.extend(self._generate_warnings(config))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_workflow_structure(self, config: Dict[str, Any]) -> List[str]:
        """验证工作流结构
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        
        # 验证工作流名称
        workflow_name = config.get("workflow_name")
        if not workflow_name:
            errors.append("工作流名称不能为空")
        elif not isinstance(workflow_name, str):
            errors.append("工作流名称必须是字符串")
        
        # 验证工作流类型
        workflow_type = config.get("workflow_type")
        if workflow_type and workflow_type not in ["sequential", "parallel", "conditional", "loop", "react", "state_machine"]:
            errors.append(f"不支持的工作流类型: {workflow_type}")
        
        # 验证数值字段
        max_iterations = config.get("max_iterations")
        if max_iterations is not None:
            if not isinstance(max_iterations, int) or max_iterations < 1:
                errors.append("max_iterations必须是大于0的整数")
        
        timeout = config.get("timeout")
        if timeout is not None:
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                errors.append("timeout必须是大于0的数字")
        
        return errors
    
    def _validate_nodes(self, config: Dict[str, Any]) -> List[str]:
        """验证节点配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        nodes = config.get("nodes", {})
        
        if not nodes:
            errors.append("至少需要配置一个节点")
            return errors
        
        for node_name, node_config in nodes.items():
            if not isinstance(node_config, dict):
                errors.append(f"节点 {node_name} 配置必须是字典")
                continue
            
            # 验证函数配置
            if "function" not in node_config:
                errors.append(f"节点 {node_name} 缺少function配置")
            
            # 验证节点配置
            node_config_dict = node_config.get("config", {})
            if not isinstance(node_config_dict, dict):
                errors.append(f"节点 {node_name} 的config配置必须是字典")
        
        return errors
    
    def _validate_edges(self, config: Dict[str, Any]) -> List[str]:
        """验证边配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        edges = config.get("edges", [])
        nodes = set(config.get("nodes", {}).keys())
        
        for i, edge in enumerate(edges):
            if not isinstance(edge, dict):
                errors.append(f"边 {i} 配置必须是字典")
                continue
            
            # 验证起始节点
            from_node = edge.get("from")
            if not from_node:
                errors.append(f"边 {i} 缺少from配置")
            elif from_node not in nodes and from_node != "__start__":
                errors.append(f"边 {i} 引用了不存在的起始节点: {from_node}")
            
            # 验证目标节点
            to_node = edge.get("to")
            edge_type = edge.get("type", "simple")
            if edge_type == "simple" and not to_node:
                errors.append(f"简单边 {i} 必须指定to配置")
            elif to_node and to_node not in nodes and to_node != "__end__":
                errors.append(f"边 {i} 引用了不存在的目标节点: {to_node}")
            
            # 验证边类型
            if edge_type not in ["simple", "conditional", "parallel", "merge", "always"]:
                errors.append(f"边 {i} 类型不支持: {edge_type}")
            
            # 验证条件边
            if edge_type == "conditional":
                if "condition" not in edge and "path_map" not in edge:
                    errors.append(f"条件边 {i} 必须指定condition或path_map")
        
        return errors
    
    def _validate_state_schema(self, config: Dict[str, Any]) -> List[str]:
        """验证状态模式
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        state_schema = config.get("state_schema", {})
        
        if not state_schema:
            return errors
        
        # 验证状态名称
        if "name" not in state_schema:
            errors.append("状态模式必须指定name")
        
        # 验证字段配置
        fields = state_schema.get("fields", {})
        if not fields:
            errors.append("状态模式必须包含字段定义")
            return errors
        
        for field_name, field_config in fields.items():
            if not isinstance(field_config, dict):
                errors.append(f"状态字段 {field_name} 配置必须是字典")
                continue
            
            if "type" not in field_config:
                errors.append(f"状态字段 {field_name} 必须指定type")
        
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
            warnings.append("建议添加工作流描述")
        
        # 检查是否缺少入口点
        if not config.get("entry_point"):
            warnings.append("建议指定入口点")
        
        # 检查是否缺少元数据
        metadata = config.get("metadata", {})
        if not metadata.get("version"):
            warnings.append("建议在元数据中指定版本")
        
        # 检查重试配置
        retry_attempts = config.get("retry_attempts", 0)
        if retry_attempts > 5:
            warnings.append("重试次数过多可能影响性能")
        
        return warnings