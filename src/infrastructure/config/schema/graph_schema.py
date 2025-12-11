"""Graph配置模式

定义Graph模块的配置验证模式。
"""

from typing import Dict, Any, List
import logging

from .base_schema import BaseSchema
from src.interfaces.common_domain import ValidationResult

logger = logging.getLogger(__name__)


class GraphSchema(BaseSchema):
    """Graph配置模式
    
    定义Graph模块的配置验证规则和模式。
    """
    
    def __init__(self):
        """初始化Graph配置模式"""
        super().__init__(self._get_schema_definition())
        logger.debug("Graph配置模式初始化完成")
    
    def _get_schema_definition(self) -> Dict[str, Any]:
        """获取模式定义
        
        Returns:
            模式定义字典
        """
        return {
            "type": "object",
            "required": ["name", "nodes"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "图名称"
                },
                "id": {
                    "type": "string",
                    "description": "图ID"
                },
                "description": {
                    "type": "string",
                    "description": "图描述"
                },
                "version": {
                    "type": "string",
                    "pattern": r"^\d+\.\d+(\.\d+)?$",
                    "description": "版本号"
                },
                "enable_tracing": {
                    "type": "boolean",
                    "description": "是否启用跟踪"
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
                            "properties": {
                                "ref": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "description": "节点引用"
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
                    "description": "边引用"
                },
                "entry_point": {
                    "type": "string",
                    "description": "入口点"
                },
                "additional_config": {
                    "type": "object",
                    "properties": {
                        "retry_attempts": {"type": "integer", "minimum": 0},
                        "retry_delay": {"type": "number", "minimum": 0},
                        "logging_level": {
                            "type": "string",
                            "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                        },
                        "enable_tracing": {"type": "boolean"},
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
        
        # Graph特定验证
        errors.extend(self._validate_graph_structure(config))
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
    
    def _validate_graph_structure(self, config: Dict[str, Any]) -> List[str]:
        """验证图结构
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        
        # 验证图名称
        name = config.get("name")
        if not name:
            errors.append("图名称不能为空")
        elif not isinstance(name, str):
            errors.append("图名称必须是字符串")
        
        # 验证图ID
        graph_id = config.get("id")
        if graph_id and not isinstance(graph_id, str):
            errors.append("图ID必须是字符串")
        
        # 验证版本号
        version = config.get("version")
        if version and not isinstance(version, str):
            errors.append("版本号必须是字符串")
        
        # 验证数值字段
        retry_attempts = config.get("retry_attempts")
        if retry_attempts is not None:
            if not isinstance(retry_attempts, int) or retry_attempts < 0:
                errors.append("retry_attempts必须是非负整数")
        
        retry_delay = config.get("retry_delay")
        if retry_delay is not None:
            if not isinstance(retry_delay, (int, float)) or retry_delay < 0:
                errors.append("retry_delay必须是非负数")
        
        return errors
    
    def _validate_nodes(self, config: Dict[str, Any]) -> List[str]:
        """验证节点引用
        
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
        
        for node_name, node_ref in nodes.items():
            if not isinstance(node_ref, dict):
                errors.append(f"节点 {node_name} 引用必须是字典")
                continue
            
            # 验证引用字段
            if "ref" not in node_ref:
                errors.append(f"节点 {node_name} 缺少ref配置")
        
        return errors
    
    def _validate_edges(self, config: Dict[str, Any]) -> List[str]:
        """验证边引用
        
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
                errors.append(f"边 {i} 引用必须是字典")
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
            warnings.append("建议添加图描述")
        
        # 检查是否缺少入口点
        if not config.get("entry_point"):
            warnings.append("建议指定入口点")
        
        # 检查是否缺少版本号
        if not config.get("version"):
            warnings.append("建议指定版本号")
        
        # 检查重试配置
        retry_attempts = config.get("retry_attempts", 0)
        if retry_attempts > 5:
            warnings.append("重试次数过多可能影响性能")
        
        # 检查节点数量
        nodes = config.get("nodes", {})
        if len(nodes) > 50:
            warnings.append("节点数量过多可能影响性能")
        
        # 检查边数量
        edges = config.get("edges", [])
        if len(edges) > 100:
            warnings.append("边数量过多可能影响性能")
        
        return warnings