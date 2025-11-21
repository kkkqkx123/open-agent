"""工作流配置验证器

验证工作流配置的结构和一致性。
"""

from typing import Dict, List, Any, Optional, Set
import os
import re
import logging

logger = logging.getLogger(__name__)


class ValidationSeverity:
    """验证严重程度枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationResult:
    """验证结果数据结构"""
    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def add_error(self, message: str) -> None:
        """添加错误信息"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """添加警告信息"""
        self.warnings.append(message)
    
    def add_info(self, message: str) -> None:
        """添加信息"""
        self.info.append(message)
    
    def merge(self, other: 'ValidationResult') -> None:
        """合并另一个验证结果"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)
        if not other.is_valid:
            self.is_valid = False
    
    def has_messages(self, severity: ValidationSeverity) -> bool:
        """检查是否有指定严重程度的消息"""
        if severity == ValidationSeverity.ERROR:
            return len(self.errors) > 0
        elif severity == ValidationSeverity.WARNING:
            return len(self.warnings) > 0
        elif severity == ValidationSeverity.INFO:
            return len(self.info) > 0
        return False
    
    def get_messages(self, severity: ValidationSeverity) -> List[str]:
        """获取指定严重程度的消息"""
        if severity == ValidationSeverity.ERROR:
            return self.errors
        elif severity == ValidationSeverity.WARNING:
            return self.warnings
        elif severity == ValidationSeverity.INFO:
            return self.info
        return []


class WorkflowConfigValidator:
    """工作流配置验证器
    
    验证工作流配置的结构和一致性。
    """
    
    def __init__(self):
        """初始化工作流配置验证器"""
        self.name = "WorkflowConfigValidator"
        self.logger = logging.getLogger(f"{__name__}.WorkflowConfigValidator")
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult()
        
        # 基础验证
        self._validate_basic_structure(config, result)
        
        # 自定义验证
        self._validate_custom(config, result)
        
        # 记录验证结果
        self._log_validation_result(result)
        
        return result
    
    def _validate_basic_structure(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """验证基础结构
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        if not isinstance(config, dict):
            result.add_error("配置必须是字典类型")
            return
        
        if not config:
            result.add_error("配置不能为空")
    
    def _validate_custom(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """自定义验证逻辑
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        # 验证基础结构
        self._validate_workflow_structure(config, result)
        
        # 验证状态模式
        if "state_schema" in config:
            self._validate_state_schema(config["state_schema"], result)
        
        # 验证节点配置
        if "nodes" in config:
            self._validate_nodes(config["nodes"], result)
        
        # 验证边配置
        if "edges" in config:
            self._validate_edges(config["edges"], config.get("nodes", {}), result)
        
        # 验证入口点
        if "entry_point" in config:
            self._validate_entry_point(config["entry_point"], config.get("nodes", {}), result)
        
        # 验证验证规则
        if "validation_rules" in config:
            self._validate_workflow_validation_rules(config["validation_rules"], result)
        
        # 验证继承关系
        if "inherits_from" in config:
            self._validate_inheritance(config, result)
    
    def _validate_workflow_structure(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """验证工作流基础结构
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        # 验证元数据
        if "metadata" in config:
            metadata = config["metadata"]
            if not isinstance(metadata, dict):
                result.add_error("metadata 必须是字典类型")
            else:
                # 验证必需的元数据字段
                required_fields = ["name", "version", "description"]
                self._validate_required_fields(metadata, required_fields, result)
                
                # 验证字段类型
                type_rules = {
                    "name": str,
                    "version": str,
                    "description": str,
                    "author": str
                }
                self._validate_field_types(config, type_rules, result)
        
        # 验证基础字段
        type_rules = {
            "config_type": str,
            "workflow_name": str,
            "description": str,
            "max_iterations": int,
            "timeout": int,
            "entry_point": str
        }
        self._validate_field_types(config, type_rules, result)
        
        # 验证值范围
        value_rules = {
            "max_iterations": {"range": [1, 1000]},
            "timeout": {"range": [1, 3600]}
        }
        self._validate_field_values(config, value_rules, result)
    
    def _validate_state_schema(self, state_schema: Any, result: ValidationResult) -> None:
        """验证状态模式
        
        Args:
            state_schema: 状态模式配置
            result: 验证结果
        """
        if not isinstance(state_schema, dict):
            result.add_error("state_schema 必须是字典类型")
            return
        
        # 验证必需字段
        required_fields = ["name", "fields"]
        self._validate_required_fields(state_schema, required_fields, result)
        
        # 验证字段类型
        type_rules = {
            "name": str
        }
        self._validate_field_types(state_schema, type_rules, result)
        
        # 验证字段定义
        if "fields" in state_schema:
            fields = state_schema["fields"]
            if not isinstance(fields, dict):
                result.add_error("state_schema.fields 必须是字典类型")
            else:
                for field_name, field_config in fields.items():
                    self._validate_state_field(field_name, field_config, result)
    
    def _validate_state_field(self, name: str, config: Any, result: ValidationResult) -> None:
        """验证状态字段
        
        Args:
            name: 字段名称
            config: 字段配置
            result: 验证结果
        """
        if not isinstance(config, dict):
            result.add_error(f"状态字段 '{name}' 的配置必须是字典类型")
            return
        
        # 验证必需字段
        if "type" not in config:
            result.add_error(f"状态字段 '{name}' 缺少类型定义")
        
        # 验证字段类型
        type_rules = {
            "type": str,
            "default": (str, int, float, bool, list, dict),
            "description": str,
            "reducer": str
        }
        self._validate_field_types(config, type_rules, result)
        
        # 验证类型格式
        if "type" in config:
            field_type = config["type"]
            # 支持的类型：str, int, float, bool, List[dict], List[str] 等
            type_pattern = r'^(str|int|float|bool|list|dict|List\[.*\]|Dict\[.*\])$'
            if not re.match(type_pattern, field_type):
                result.add_warning(f"状态字段 '{name}' 的类型 '{field_type}' 可能不被支持")
    
    def _validate_nodes(self, nodes: Any, result: ValidationResult) -> None:
        """验证节点配置
        
        Args:
            nodes: 节点配置
            result: 验证结果
        """
        if not isinstance(nodes, dict):
            result.add_error("nodes 必须是字典类型")
            return
        
        if not nodes:
            result.add_error("nodes 不能为空")
            return
        
        # 验证每个节点
        for node_name, node_config in nodes.items():
            self._validate_node(node_name, node_config, result)
    
    def _validate_node(self, name: str, config: Any, result: ValidationResult) -> None:
        """验证单个节点
        
        Args:
            name: 节点名称
            config: 节点配置
            result: 验证结果
        """
        if not isinstance(config, dict):
            result.add_error(f"节点 '{name}' 的配置必须是字典类型")
            return
        
        # 验证必需字段
        required_fields = ["function", "description"]
        self._validate_required_fields(config, required_fields, result)
        
        # 验证字段类型
        type_rules = {
            "function": str,
            "description": str,
            "type": str
        }
        self._validate_field_types(config, type_rules, result)
        
        # 验证节点类型
        if "type" in config:
            node_type = config["type"]
            valid_types = [
                "start", "end", "process", "decision", "parallel", "conditional",
                "llm_node", "analysis_node", "tool_node", "condition_node",
                "deep_thinking_node", "agent_configuration_node", "parallel_node",
                "solution_integration_node", "collaborative_validation_node"
            ]
            if node_type not in valid_types:
                result.add_warning(f"节点 '{name}' 的类型 '{node_type}' 可能不被支持")
        
        # 验证配置
        if "config" in config:
            node_config = config["config"]
            if not isinstance(node_config, dict):
                result.add_error(f"节点 '{name}' 的 config 必须是字典类型")
    
    def _validate_edges(self, edges: Any, nodes: Dict[str, Any], result: ValidationResult) -> None:
        """验证边配置
        
        Args:
            edges: 边配置
            nodes: 节点配置
            result: 验证结果
        """
        if not isinstance(edges, list):
            result.add_error("edges 必须是列表类型")
            return
        
        if not edges:
            result.add_warning("edges 列表为空，工作流可能无法正常执行")
            return
        
        # 获取所有节点名称
        node_names = set(nodes.keys())
        
        # 验证每条边
        for i, edge in enumerate(edges):
            self._validate_edge(i, edge, node_names, result)
    
    def _validate_edge(self, index: int, edge: Any, node_names: Set[str], result: ValidationResult) -> None:
        """验证单条边
        
        Args:
            index: 边的索引
            edge: 边配置
            node_names: 节点名称集合
            result: 验证结果
        """
        if not isinstance(edge, dict):
            result.add_error(f"边 {index} 的配置必须是字典类型")
            return
        
        # 验证必需字段
        required_fields = ["from", "to", "type"]
        self._validate_required_fields(edge, required_fields, result)
        
        # 验证字段类型
        type_rules = {
            "from": str,
            "to": str,
            "type": str,
            "description": str,
            "condition": str
        }
        self._validate_field_types(edge, type_rules, result)
        
        # 验证节点引用
        if "from" in edge:
            from_node = edge["from"]
            if from_node not in node_names:
                result.add_error(f"边 {index} 的源节点 '{from_node}' 不存在")
        
        if "to" in edge:
            to_node = edge["to"]
            if to_node not in node_names:
                result.add_error(f"边 {index} 的目标节点 '{to_node}' 不存在")
        
        # 验证边类型
        if "type" in edge:
            edge_type = edge["type"]
            valid_types = ["simple", "conditional", "parallel"]
            if edge_type not in valid_types:
                result.add_warning(f"边 {index} 的类型 '{edge_type}' 可能不被支持")
        
        # 验证条件边
        if edge.get("type") == "conditional" and "condition" not in edge:
            result.add_error(f"条件边 {index} 必须指定 condition 字段")
    
    def _validate_entry_point(self, entry_point: str, nodes: Dict[str, Any], result: ValidationResult) -> None:
        """验证入口点
        
        Args:
            entry_point: 入口点名称
            nodes: 节点配置
            result: 验证结果
        """
        if not isinstance(entry_point, str):
            result.add_error("entry_point 必须是字符串类型")
            return
        
        if not entry_point:
            result.add_error("entry_point 不能为空")
            return
        
        # 检查入口点节点是否存在
        if entry_point not in nodes:
            result.add_error(f"入口点节点 '{entry_point}' 不存在")
    
    def _validate_workflow_validation_rules(self, validation_rules: Any, result: ValidationResult) -> None:
        """验证工作流验证规则
        
        Args:
            validation_rules: 验证规则配置
            result: 验证结果
        """
        if not isinstance(validation_rules, list):
            result.add_error("validation_rules 必须是列表类型")
            return
        
        # 验证每个规则
        for i, rule in enumerate(validation_rules):
            if not isinstance(rule, dict):
                result.add_error(f"验证规则 {i} 必须是字典类型")
                continue
            
            # 验证必需字段
            required_fields = ["field", "rule_type", "message"]
            self._validate_required_fields(rule, required_fields, result)
            
            # 验证字段类型
            type_rules = {
                "field": str,
                "rule_type": str,
                "message": str
            }
            self._validate_field_types(rule, type_rules, result)
            
            # 验证规则类型
            if "rule_type" in rule:
                rule_type = rule["rule_type"]
                valid_types = ["required", "range", "pattern", "enum"]
                if rule_type not in valid_types:
                    result.add_warning(f"未知的规则类型: {rule_type}")
                
                # 验证规则参数
                if rule_type == "range" and "value" not in rule:
                    result.add_error(f"范围规则 {i} 必须指定 value 字段")
                elif rule_type == "enum" and "value" not in rule:
                    result.add_error(f"枚举规则 {i} 必须指定 value 字段")
                elif rule_type == "pattern" and "value" not in rule:
                    result.add_error(f"模式规则 {i} 必须指定 value 字段")
    
    def _validate_inheritance(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """验证继承关系
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        inherits_from = config.get("inherits_from")
        
        if not inherits_from:
            return  # 没有继承关系，跳过验证
        
        if not isinstance(inherits_from, str):
            result.add_error("inherits_from 必须是字符串类型")
            return
        
        if not inherits_from:
            result.add_error("inherits_from 不能为空")
            return
        
        # 检查继承的文件是否存在
        # 这里只做基本验证，实际文件检查在配置加载时进行
        if not inherits_from.endswith(('.yaml', '.yml')):
            result.add_warning(f"继承文件 '{inherits_from}' 可能不是YAML文件")
        
        # 检查循环继承（简单检查）
        if "name" in config and inherits_from == config.get("name", "") + ".yaml":
            result.add_error("检测到可能的循环继承")
    
    def _validate_required_fields(self, config: Dict[str, Any], required_fields: List[str], result: ValidationResult) -> None:
        """验证必需字段
        
        Args:
            config: 配置字典
            required_fields: 必需字段列表
            result: 验证结果
        """
        for field in required_fields:
            if field not in config:
                result.add_error(f"缺少必需字段: {field}")
            elif config[field] is None:
                result.add_error(f"必需字段不能为空: {field}")
    
    def _validate_field_types(self, config: Dict[str, Any], type_rules: Dict[str, type], result: ValidationResult) -> None:
        """验证字段类型
        
        Args:
            config: 配置字典
            type_rules: 类型规则字典 {字段名: 期望类型}
            result: 验证结果
        """
        for field, expected_type in type_rules.items():
            if field in config and config[field] is not None:
                if not isinstance(config[field], expected_type):
                    result.add_error(f"字段 '{field}' 类型错误，期望 {expected_type.__name__}，实际 {type(config[field]).__name__}")
    
    def _validate_field_values(self, config: Dict[str, Any], value_rules: Dict[str, Dict[str, Any]], result: ValidationResult) -> None:
        """验证字段值
        
        Args:
            config: 配置字典
            value_rules: 值规则字典 {字段名: 规则字典}
            result: 验证结果
        """
        for field, rules in value_rules.items():
            if field not in config or config[field] is None:
                continue
            
            value = config[field]
            
            # 验证枚举值
            if "enum" in rules and value not in rules["enum"]:
                result.add_error(f"字段 '{field}' 值无效，必须是 {rules['enum']} 中的一个")
            
            # 验证范围
            if "range" in rules:
                min_val, max_val = rules["range"]
                if not (min_val <= value <= max_val):
                    result.add_error(f"字段 '{field}' 值超出范围，必须在 {min_val} 到 {max_val} 之间")
            
            # 验证正则表达式
            if "pattern" in rules:
                pattern = rules["pattern"]
                if not re.match(pattern, str(value)):
                    result.add_error(f"字段 '{field}' 值格式不正确，必须匹配模式: {pattern}")
            
            # 验证最小长度
            if "min_length" in rules:
                min_len = rules["min_length"]
                if len(str(value)) < min_len:
                    result.add_error(f"字段 '{field}' 长度不足，最小长度为 {min_len}")
            
            # 验证最大长度
            if "max_length" in rules:
                max_len = rules["max_length"]
                if len(str(value)) > max_len:
                    result.add_error(f"字段 '{field}' 长度超限，最大长度为 {max_len}")
    
    def _log_validation_result(self, result: ValidationResult) -> None:
        """记录验证结果
        
        Args:
            result: 验证结果
        """
        if result.is_valid:
            self.logger.debug(f"配置验证通过: {self.name}")
        else:
            self.logger.error(f"配置验证失败: {self.name}")
            for error in result.errors:
                self.logger.error(f"  错误: {error}")
        
        for warning in result.warnings:
            self.logger.warning(f"  警告: {warning}")
        
        for info in result.info:
            self.logger.info(f"  信息: {info}")