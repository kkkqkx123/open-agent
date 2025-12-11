"""Edge配置模式

定义Edge模块的配置验证模式。
"""

from typing import Dict, Any, List
import logging

from .base_schema import BaseSchema
from src.interfaces.common_domain import ValidationResult

logger = logging.getLogger(__name__)


class EdgeSchema(BaseSchema):
    """Edge配置模式
    
    定义Edge模块的配置验证规则和模式。
    """
    
    def __init__(self):
        """初始化Edge配置模式"""
        super().__init__(self._get_schema_definition())
        logger.debug("Edge配置模式初始化完成")
    
    def _get_schema_definition(self) -> Dict[str, Any]:
        """获取模式定义
        
        Returns:
            模式定义字典
        """
        return {
            "type": "object",
            "required": ["name", "from", "type"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "边名称"
                },
                "id": {
                    "type": "string",
                    "description": "边ID"
                },
                "description": {
                    "type": "string",
                    "description": "边描述"
                },
                "from": {
                    "type": "string",
                    "description": "起始节点"
                },
                "to": {
                    "type": "string",
                    "description": "目标节点"
                },
                "type": {
                    "type": "string",
                    "enum": ["simple", "conditional", "parallel", "merge", "always", "map", "reduce"],
                    "description": "边类型"
                },
                "condition": {
                    "type": "string",
                    "description": "条件表达式"
                },
                "condition_function": {
                    "type": "string",
                    "description": "条件函数名称"
                },
                "condition_parameters": {
                    "type": "object",
                    "description": "条件函数参数"
                },
                "path_map": {
                    "oneOf": [
                        {"type": "object"},
                        {"type": "array"}
                    ],
                    "description": "路径映射"
                },
                "data_transformation": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "transform_function": {"type": "string"},
                        "transform_parameters": {"type": "object"}
                    },
                    "description": "数据转换配置"
                },
                "filter": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "filter_function": {"type": "string"},
                        "filter_parameters": {"type": "object"}
                    },
                    "description": "过滤配置"
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
                "log_execution": {
                    "type": "boolean",
                    "description": "是否记录执行日志"
                },
                "additional_config": {
                    "type": "object",
                    "properties": {
                        "priority": {"type": "string"},
                        "weight": {
                            "type": "number",
                            "minimum": 0
                        },
                        "enabled": {"type": "boolean"}
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
        
        # Edge特定验证
        errors.extend(self._validate_edge_structure(config))
        errors.extend(self._validate_condition_config(config))
        errors.extend(self._validate_transformation_config(config))
        
        # 生成警告
        warnings.extend(self._generate_warnings(config))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_edge_structure(self, config: Dict[str, Any]) -> List[str]:
        """验证边结构
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        
        # 验证边名称
        name = config.get("name")
        if not name:
            errors.append("边名称不能为空")
        elif not isinstance(name, str):
            errors.append("边名称必须是字符串")
        
        # 验证边ID
        edge_id = config.get("id")
        if edge_id and not isinstance(edge_id, str):
            errors.append("边ID必须是字符串")
        
        # 验证起始节点
        from_node = config.get("from")
        if not from_node:
            errors.append("起始节点不能为空")
        elif not isinstance(from_node, str):
            errors.append("起始节点必须是字符串")
        
        # 验证目标节点
        to_node = config.get("to")
        edge_type = config.get("type", "simple")
        if edge_type == "simple" and not to_node:
            errors.append("简单边必须指定目标节点")
        elif to_node and not isinstance(to_node, str):
            errors.append("目标节点必须是字符串")
        
        # 验证边类型
        if edge_type not in ["simple", "conditional", "parallel", "merge", "always", "map", "reduce"]:
            errors.append(f"不支持的边类型: {edge_type}")
        
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
    
    def _validate_condition_config(self, config: Dict[str, Any]) -> List[str]:
        """验证条件配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        edge_type = config.get("type")
        
        if edge_type == "conditional":
            # 验证条件配置
            condition = config.get("condition")
            condition_function = config.get("condition_function")
            path_map = config.get("path_map")
            
            if not condition and not condition_function and not path_map:
                errors.append("条件边必须指定condition、condition_function或path_map")
            
            # 验证条件函数参数
            condition_parameters = config.get("condition_parameters", {})
            if condition_parameters and not isinstance(condition_parameters, dict):
                errors.append("condition_parameters必须是字典")
            
            # 验证路径映射
            if path_map:
                if isinstance(path_map, dict):
                    if not path_map:
                        errors.append("路径映射不能为空")
                elif isinstance(path_map, list):
                    if not path_map:
                        errors.append("路径映射不能为空")
                else:
                    errors.append("路径映射必须是字典或数组")
        
        return errors
    
    def _validate_transformation_config(self, config: Dict[str, Any]) -> List[str]:
        """验证转换配置
        
        Args:
            config: 配置数据
            
        Returns:
            错误列表
        """
        errors = []
        
        # 验证数据转换配置
        data_transformation = config.get("data_transformation", {})
        if data_transformation and not isinstance(data_transformation, dict):
            errors.append("data_transformation必须是字典")
        else:
            if data_transformation:
                transform_function = data_transformation.get("transform_function")
                if data_transformation.get("enabled") and not transform_function:
                    errors.append("启用的数据转换必须指定transform_function")
                
                transform_parameters = data_transformation.get("transform_parameters", {})
                if transform_parameters and not isinstance(transform_parameters, dict):
                    errors.append("transform_parameters必须是字典")
        
        # 验证过滤配置
        filter_config = config.get("filter", {})
        if filter_config and not isinstance(filter_config, dict):
            errors.append("filter必须是字典")
        else:
            if filter_config:
                filter_function = filter_config.get("filter_function")
                if filter_config.get("enabled") and not filter_function:
                    errors.append("启用的过滤必须指定filter_function")
                
                filter_parameters = filter_config.get("filter_parameters", {})
                if filter_parameters and not isinstance(filter_parameters, dict):
                    errors.append("filter_parameters必须是字典")
        
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
            warnings.append("建议添加边描述")
        
        # 检查重试配置
        retry_attempts = config.get("retry_attempts", 0)
        if retry_attempts > 5:
            warnings.append("重试次数过多可能影响性能")
        
        # 检查超时配置
        timeout = config.get("timeout", 30)
        if timeout > 300:
            warnings.append("超时时间过长可能影响性能")
        
        # 检查条件边配置
        edge_type = config.get("type")
        if edge_type == "conditional":
            condition = config.get("condition")
            path_map = config.get("path_map")
            
            if condition and path_map:
                warnings.append("同时指定condition和path_map可能导致混淆")
        
        # 检查转换配置
        data_transformation = config.get("data_transformation", {})
        if data_transformation.get("enabled"):
            warnings.append("数据转换可能影响性能")
        
        # 检查过滤配置
        filter_config = config.get("filter", {})
        if filter_config.get("enabled"):
            warnings.append("过滤可能影响性能")
        
        # 检查额外配置
        additional_config = config.get("additional_config", {})
        weight = additional_config.get("weight", 1.0)
        if weight > 10:
            warnings.append("权重过高可能影响性能")
        
        return warnings