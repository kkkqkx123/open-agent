"""配置验证器

验证工作流配置的完整性，检查函数存在性，提供错误修复建议。
"""

from typing import Dict, Any, List, Optional, Union, Set
from dataclasses import dataclass
from pathlib import Path
import logging

from src.core.workflow.config.config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
from src.services.workflow.function_registry import FunctionRegistry, FunctionType, get_global_function_registry

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0
    
    def get_summary(self) -> str:
        """获取验证摘要"""
        if self.is_valid:
            return "配置验证通过"
        else:
            return f"配置验证失败: {len(self.errors)} 个错误, {len(self.warnings)} 个警告"


class ConfigValidationError(Exception):
    """配置验证异常"""
    pass


class WorkflowConfigValidator:
    """工作流配置验证器
    
    验证工作流配置的完整性，检查函数存在性，提供错误修复建议。
    """
    
    def __init__(self, function_registry: Optional[FunctionRegistry] = None):
        """初始化配置验证器
        
        Args:
            function_registry: 函数注册表
        """
        self.function_registry = function_registry or get_global_function_registry()
    
    def validate_config(self, config: Union[str, Dict[str, Any], GraphConfig]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置路径、配置字典或配置对象
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # 解析配置
            if isinstance(config, str):
                graph_config = self._load_config_from_file(config)
            elif isinstance(config, dict):
                graph_config = GraphConfig.from_dict(config)
            elif isinstance(config, GraphConfig):
                graph_config = config
            else:
                errors.append("配置类型无效，必须是文件路径、字典或 GraphConfig 对象")
                return ValidationResult(False, errors, warnings, suggestions)
            
            # 执行各项验证
            self._validate_basic_structure(graph_config, errors, warnings, suggestions)
            self._validate_nodes(graph_config, errors, warnings, suggestions)
            self._validate_edges(graph_config, errors, warnings, suggestions)
            self._validate_functions(graph_config, errors, warnings, suggestions)
            self._validate_state_schema(graph_config, errors, warnings, suggestions)
            self._validate_entry_point(graph_config, errors, warnings, suggestions)
            
            # 检查是否有错误
            is_valid = len(errors) == 0
            
            return ValidationResult(is_valid, errors, warnings, suggestions)
            
        except Exception as e:
            errors.append(f"配置验证过程中发生异常: {e}")
            return ValidationResult(False, errors, warnings, suggestions)
    
    def validate_config_file(self, config_path: str) -> ValidationResult:
        """验证配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            ValidationResult: 验证结果
        """
        if not Path(config_path).exists():
            return ValidationResult(
                False,
                [f"配置文件不存在: {config_path}"],
                [],
                ["请检查文件路径是否正确"]
            )
        
        return self.validate_config(config_path)
    
    def _load_config_from_file(self, config_path: str) -> GraphConfig:
        """从文件加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            GraphConfig: 图配置
            
        Raises:
            ConfigValidationError: 配置加载失败
        """
        try:
            # 使用统一配置管理器加载
            from src.core.config.config_manager import get_default_manager
            config_manager = get_default_manager()
            config_data = config_manager.load_config_for_module(config_path, "workflow")
            
            return GraphConfig.from_dict(config_data)
            
        except Exception as e:
            raise ConfigValidationError(f"加载配置文件失败: {e}")
    
    def _validate_basic_structure(self, config: GraphConfig, errors: List[str], warnings: List[str], suggestions: List[str]) -> None:
        """验证基本结构
        
        Args:
            config: 图配置
            errors: 错误列表
            warnings: 警告列表
            suggestions: 建议列表
        """
        # 检查必需字段
        if not config.name or not config.name.strip():
            errors.append("工作流名称不能为空")
            suggestions.append("请在配置中添加 'name' 字段")
        
        if not config.description or not config.description.strip():
            warnings.append("工作流描述为空")
            suggestions.append("建议添加 'description' 字段以提高可读性")
        
        # 检查版本格式
        if config.version:
            if not isinstance(config.version, str) or not config.version.replace('.', '').isdigit():
                warnings.append("版本格式可能不规范")
                suggestions.append("建议使用语义化版本号，如 '1.0.0'")
        
        # 检查节点和边
        if not config.nodes:
            warnings.append("工作流没有定义节点")
            suggestions.append("请在 'nodes' 部分添加至少一个节点")
        
        if not config.edges:
            warnings.append("工作流没有定义边")
            suggestions.append("建议在 'edges' 部分定义节点之间的连接关系")
    
    def _validate_nodes(self, config: GraphConfig, errors: List[str], warnings: List[str], suggestions: List[str]) -> None:
        """验证节点配置
        
        Args:
            config: 图配置
            errors: 错误列表
            warnings: 警告列表
            suggestions: 建议列表
        """
        node_names = set(config.nodes.keys())
        
        for node_name, node_config in config.nodes.items():
            # 检查节点名称
            if not node_name or not node_name.strip():
                errors.append("节点名称不能为空")
                continue
            
            # 检查函数名称
            if not node_config.function_name or not node_config.function_name.strip():
                errors.append(f"节点 '{node_name}' 的函数名称不能为空")
                suggestions.append(f"请为节点 '{node_name}' 指定 'function' 或 'type' 字段")
            
            # 检查节点配置
            if node_config.config and not isinstance(node_config.config, dict):
                errors.append(f"节点 '{node_name}' 的配置必须是字典类型")
            
            # 检查节点描述
            if not node_config.description:
                warnings.append(f"节点 '{node_name}' 缺少描述")
                suggestions.append(f"建议为节点 '{node_name}' 添加 'description' 字段")
    
    def _validate_edges(self, config: GraphConfig, errors: List[str], warnings: List[str], suggestions: List[str]) -> None:
        """验证边配置
        
        Args:
            config: 图配置
            errors: 错误列表
            warnings: 警告列表
            suggestions: 建议列表
        """
        node_names = set(config.nodes.keys())
        special_nodes = {"__start__", "__end__"}
        
        for i, edge in enumerate(config.edges):
            # 检查边的起始节点
            if edge.from_node not in node_names and edge.from_node not in special_nodes:
                errors.append(f"边 {i+1} 的起始节点 '{edge.from_node}' 不存在")
                suggestions.append(f"请确保节点 '{edge.from_node}' 已在 'nodes' 部分定义")
            
            # 检查边的目标节点
            if edge.to_node not in node_names and edge.to_node not in special_nodes:
                errors.append(f"边 {i+1} 的目标节点 '{edge.to_node}' 不存在")
                suggestions.append(f"请确保节点 '{edge.to_node}' 已在 'nodes' 部分定义")
            
            # 检查条件边
            if edge.type == EdgeType.CONDITIONAL:
                if not edge.condition:
                    errors.append(f"条件边 {i+1} 缺少条件表达式")
                    suggestions.append(f"请为条件边添加 'condition' 字段")
                
                if not edge.path_map:
                    warnings.append(f"条件边 {i+1} 缺少路径映射")
                    suggestions.append(f"建议为条件边添加 'path_map' 字段以明确路由规则")
            
            # 检查边描述
            if not edge.description:
                warnings.append(f"边 {i+1} 缺少描述")
                suggestions.append(f"建议为边添加 'description' 字段以提高可读性")
    
    def _validate_functions(self, config: GraphConfig, errors: List[str], warnings: List[str], suggestions: List[str]) -> None:
        """验证函数存在性
        
        Args:
            config: 图配置
            errors: 错误列表
            warnings: 警告列表
            suggestions: 建议列表
        """
        if not self.function_registry:
            warnings.append("函数注册表未初始化，无法验证函数存在性")
            suggestions.append("请确保函数注册表已正确初始化")
            return
        
        # 验证节点函数
        missing_node_functions = []
        for node_name, node_config in config.nodes.items():
            function_name = node_config.function_name
            if not self.function_registry.validate_function_exists(function_name, FunctionType.NODE_FUNCTION):
                missing_node_functions.append((node_name, function_name))
        
        if missing_node_functions:
            for node_name, function_name in missing_node_functions:
                errors.append(f"节点 '{node_name}' 引用的函数 '{function_name}' 不存在")
            
            suggestions.extend([
                "请确保所有引用的函数已注册到函数注册表",
                "可以通过以下方式注册函数:",
                "  1. 使用 loader.register_function() 方法",
                "  2. 在配置中添加 function_registrations 部分",
                "  3. 启用自动发现功能"
            ])
        
        # 验证条件函数
        missing_condition_functions = []
        for edge in config.edges:
            if edge.condition and not self.function_registry.validate_function_exists(edge.condition, FunctionType.CONDITION_FUNCTION):
                missing_condition_functions.append((edge.from_node, edge.to_node, edge.condition))
        
        if missing_condition_functions:
            for from_node, to_node, condition in missing_condition_functions:
                errors.append(f"边 '{from_node}' -> '{to_node}' 引用的条件函数 '{condition}' 不存在")
    
    def _validate_state_schema(self, config: GraphConfig, errors: List[str], warnings: List[str], suggestions: List[str]) -> None:
        """验证状态模式
        
        Args:
            config: 图配置
            errors: 错误列表
            warnings: 警告列表
            suggestions: 建议列表
        """
        if not config.state_schema:
            errors.append("工作流必须定义状态模式")
            suggestions.append("请在配置中添加 'state_schema' 部分")
            return
        
        # 检查状态模式名称
        if not config.state_schema.name or not config.state_schema.name.strip():
            errors.append("状态模式名称不能为空")
            suggestions.append("请在状态模式中添加 'name' 字段")
        
        # 检查状态字段
        if not config.state_schema.fields:
            warnings.append("状态模式没有定义字段")
            suggestions.append("建议在状态模式中定义至少一个字段")
        
        # 检查字段类型
        for field_name, field_config in config.state_schema.fields.items():
            if not field_config.type or not field_config.type.strip():
                errors.append(f"状态字段 '{field_name}' 的类型不能为空")
                suggestions.append(f"请为字段 '{field_name}' 指定 'type' 字段")
            
            # 检查类型格式
            valid_types = {
                "str", "int", "float", "bool", "list", "dict",
                "List[str]", "List[int]", "List[dict]", "Dict[str, Any]"
            }
            if field_config.type not in valid_types and not field_config.type.startswith("List[") and not field_config.type.startswith("Dict["):
                warnings.append(f"状态字段 '{field_name}' 的类型 '{field_config.type}' 可能不规范")
                suggestions.append(f"建议使用标准类型，如 'str', 'List[str]', 'Dict[str, Any]' 等")
    
    def _validate_entry_point(self, config: GraphConfig, errors: List[str], warnings: List[str], suggestions: List[str]) -> None:
        """验证入口点
        
        Args:
            config: 图配置
            errors: 错误列表
            warnings: 警告列表
            suggestions: 建议列表
        """
        if not config.entry_point:
            warnings.append("工作流没有定义入口点")
            suggestions.append("建议在配置中添加 'entry_point' 字段")
            return
        
        # 检查入口点是否存在
        if config.entry_point not in config.nodes:
            errors.append(f"入口节点 '{config.entry_point}' 不存在")
            suggestions.append(f"请确保入口节点 '{config.entry_point}' 已在 'nodes' 部分定义")
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """获取验证规则
        
        Returns:
            Dict[str, Any]: 验证规则
        """
        return {
            "required_fields": {
                "name": "工作流名称（必需）",
                "description": "工作流描述（必需）",
                "nodes": "节点定义（必需）",
                "state_schema": "状态模式（必需）"
            },
            "optional_fields": {
                "version": "版本号",
                "edges": "边定义",
                "entry_point": "入口点",
                "checkpointer": "检查点配置",
                "additional_config": "附加配置"
            },
            "node_requirements": {
                "function": "函数名称（必需）",
                "config": "节点配置（可选）",
                "description": "节点描述（可选）"
            },
            "edge_requirements": {
                "from": "起始节点（必需）",
                "to": "目标节点（必需）",
                "type": "边类型（必需）",
                "condition": "条件表达式（条件边必需）",
                "path_map": "路径映射（条件边可选）"
            },
            "state_schema_requirements": {
                "name": "状态模式名称（必需）",
                "fields": "状态字段定义（必需）"
            }
        }
    
    def suggest_fixes(self, config: Union[str, Dict[str, Any], GraphConfig]) -> List[str]:
        """建议修复方案
        
        Args:
            config: 配置
            
        Returns:
            List[str]: 修复建议
        """
        validation_result = self.validate_config(config)
        return validation_result.suggestions


# 便捷函数
def validate_workflow_config(config: Union[str, Dict[str, Any], GraphConfig]) -> ValidationResult:
    """验证工作流配置
    
    Args:
        config: 配置
        
    Returns:
        ValidationResult: 验证结果
    """
    validator = WorkflowConfigValidator()
    return validator.validate_config(config)


def validate_workflow_config_file(config_path: str) -> ValidationResult:
    """验证工作流配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        ValidationResult: 验证结果
    """
    validator = WorkflowConfigValidator()
    return validator.validate_config_file(config_path)