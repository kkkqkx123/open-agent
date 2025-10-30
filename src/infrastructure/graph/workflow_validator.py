"""工作流静态验证器

提供工作流配置的静态检测功能，帮助及早发现配置问题。
"""

import os
import yaml
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging

from .config import GraphConfig, EdgeConfig, EdgeType

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """验证问题严重程度"""
    ERROR = "error"      # 严重错误，必须修复
    WARNING = "warning"  # 警告，建议修复
    INFO = "info"        # 信息提示


@dataclass
class ValidationIssue:
    """验证问题"""
    severity: ValidationSeverity
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


class WorkflowValidator:
    """工作流验证器"""
    
    # LangGraph 内置字段名
    LANGGRAPH_BUILTIN_FIELDS = {
        "messages", "iteration_count", "max_iterations", 
        "tool_calls", "tool_results", "errors"
    }
    
    # 特殊节点名
    SPECIAL_NODES = {"__start__", "__end__"}
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
    
    def validate_config_file(self, config_path: str) -> List[ValidationIssue]:
        """验证配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            验证问题列表
        """
        self.issues = []
        
        if not os.path.exists(config_path):
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"配置文件不存在: {config_path}",
                suggestion="检查文件路径是否正确"
            ))
            return self.issues
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            self._validate_config_data(config_data, config_path)
            
        except yaml.YAMLError as e:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"YAML解析错误: {e}",
                location=config_path,
                suggestion="检查YAML语法是否正确"
            ))
        except Exception as e:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"配置文件读取错误: {e}",
                location=config_path,
                suggestion="检查文件权限和格式"
            ))
        
        return self.issues
    
    def validate_config_object(self, config: GraphConfig) -> List[ValidationIssue]:
        """验证配置对象
        
        Args:
            config: 图配置对象
            
        Returns:
            验证问题列表
        """
        self.issues = []
        self._validate_graph_config(config)
        return self.issues
    
    def _validate_config_data(self, config_data: Dict[str, Any], config_path: str) -> None:
        """验证配置数据"""
        # 基本字段检查
        if "name" not in config_data:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="缺少必需字段: name",
                location=config_path,
                suggestion="添加工作流名称"
            ))
        
        if "nodes" not in config_data:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="缺少必需字段: nodes",
                location=config_path,
                suggestion="添加节点定义"
            ))
        
        if "edges" not in config_data:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="缺少必需字段: edges",
                location=config_path,
                suggestion="添加边定义"
            ))
        
        # 验证状态模式
        if "state_schema" in config_data:
            self._validate_state_schema(config_data["state_schema"], config_path)
        
        # 验证节点
        if "nodes" in config_data:
            self._validate_nodes(config_data["nodes"], config_path)
        
        # 验证边
        if "edges" in config_data:
            self._validate_edges(config_data["edges"], config_data.get("nodes", {}), config_path)
        
        # 验证入口点
        if "entry_point" in config_data and "nodes" in config_data:
            entry_point = config_data["entry_point"]
            nodes = config_data["nodes"]
            if entry_point not in nodes and entry_point not in self.SPECIAL_NODES:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"入口节点不存在: {entry_point}",
                    location=config_path,
                    suggestion=f"确保入口节点 '{entry_point}' 在节点列表中定义"
                ))
    
    def _validate_state_schema(self, state_schema: Dict[str, Any], config_path: str) -> None:
        """验证状态模式"""
        if "fields" not in state_schema:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="状态模式缺少字段定义",
                location=f"{config_path}:state_schema",
                suggestion="添加 fields 定义"
            ))
            return
        
        fields = state_schema["fields"]
        for field_name, field_config in fields.items():
            # 检查字段名冲突
            if field_name in self.LANGGRAPH_BUILTIN_FIELDS:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"状态字段名与LangGraph内置字段冲突: {field_name}",
                    location=f"{config_path}:state_schema.fields.{field_name}",
                    suggestion=f"使用自定义前缀，如 'workflow_{field_name}'"
                ))
            
            # 检查字段类型
            if not isinstance(field_config, dict) or "type" not in field_config:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"状态字段缺少类型定义: {field_name}",
                    location=f"{config_path}:state_schema.fields.{field_name}",
                    suggestion="添加 type 字段定义"
                ))
    
    def _validate_nodes(self, nodes: Dict[str, Any], config_path: str) -> None:
        """验证节点定义"""
        for node_name, node_config in nodes.items():
            if not isinstance(node_config, dict):
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"节点配置格式错误: {node_name}",
                    location=f"{config_path}:nodes.{node_name}",
                    suggestion="确保节点配置是字典格式"
                ))
                continue
            
            # 检查必需字段
            if "type" not in node_config and "function" not in node_config:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"节点缺少类型定义: {node_name}",
                    location=f"{config_path}:nodes.{node_name}",
                    suggestion="添加 type 或 function 字段"
                ))
    
    def _validate_edges(self, edges: List[Dict[str, Any]], nodes: Dict[str, Any], config_path: str) -> None:
        """验证边定义"""
        node_names = set(nodes.keys())
        conditional_edges = {}
        
        for i, edge in enumerate(edges):
            if not isinstance(edge, dict):
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"边配置格式错误: edges[{i}]",
                    location=f"{config_path}:edges[{i}]",
                    suggestion="确保边配置是字典格式"
                ))
                continue
            
            # 检查必需字段
            if "from" not in edge:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"边缺少起始节点: edges[{i}]",
                    location=f"{config_path}:edges[{i}]",
                    suggestion="添加 from 字段"
                ))
            
            if "type" not in edge:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"边缺少类型定义: edges[{i}]",
                    location=f"{config_path}:edges[{i}]",
                    suggestion="添加 type 字段"
                ))
                continue
            
            edge_type = edge["type"]
            from_node = edge.get("from")
            
            # 检查条件边配置
            if edge_type == "conditional":
                self._validate_conditional_edge(edge, i, node_names, conditional_edges, config_path)
            elif edge_type == "simple":
                self._validate_simple_edge(edge, i, node_names, config_path)
            else:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"未知的边类型: {edge_type}",
                    location=f"{config_path}:edges[{i}]",
                    suggestion="使用 'simple' 或 'conditional'"
                ))
        
        # 检查条件边冲突
        self._check_conditional_edge_conflicts(conditional_edges, config_path)
    
    def _validate_conditional_edge(self, edge: Dict[str, Any], index: int, 
                                 node_names: Set[str], conditional_edges: Dict[str, List[Dict[str, Any]]], 
                                 config_path: str) -> None:
        """验证条件边"""
        from_node = edge.get("from")
        
        if from_node not in node_names and from_node not in self.SPECIAL_NODES:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"条件边的起始节点不存在: {from_node}",
                location=f"{config_path}:edges[{index}]",
                suggestion=f"确保节点 '{from_node}' 已定义"
            ))
        
        if "condition" not in edge:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"条件边缺少条件函数: edges[{index}]",
                location=f"{config_path}:edges[{index}]",
                suggestion="添加 condition 字段"
            ))
        
        if "path_map" not in edge:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"条件边缺少路径映射: edges[{index}]",
                location=f"{config_path}:edges[{index}]",
                suggestion="添加 path_map 字段以定义条件路由"
            ))
        else:
            # 验证路径映射
            path_map = edge["path_map"]
            if not isinstance(path_map, dict):
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"路径映射格式错误: edges[{index}].path_map",
                    location=f"{config_path}:edges[{index}]",
                    suggestion="确保 path_map 是字典格式"
                ))
            else:
                for condition_result, target_node in path_map.items():
                    if target_node not in node_names and target_node not in self.SPECIAL_NODES:
                        self.issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"路径映射的目标节点不存在: {target_node}",
                            location=f"{config_path}:edges[{index}].path_map",
                            suggestion=f"确保节点 '{target_node}' 已定义"
                        ))
        
        # 记录条件边用于冲突检查
        if from_node:
            if from_node not in conditional_edges:
                conditional_edges[from_node] = []
            conditional_edges[from_node].append(edge)
    
    def _validate_simple_edge(self, edge: Dict[str, Any], index: int, 
                            node_names: Set[str], config_path: str) -> None:
        """验证简单边"""
        from_node = edge.get("from")
        to_node = edge.get("to")
        
        if from_node not in node_names and from_node not in self.SPECIAL_NODES:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"简单边的起始节点不存在: {from_node}",
                location=f"{config_path}:edges[{index}]",
                suggestion=f"确保节点 '{from_node}' 已定义"
            ))
        
        if to_node not in node_names and to_node not in self.SPECIAL_NODES:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"简单边的目标节点不存在: {to_node}",
                location=f"{config_path}:edges[{index}]",
                suggestion=f"确保节点 '{to_node}' 已定义"
            ))
    
    def _check_conditional_edge_conflicts(self, conditional_edges: Dict[str, List[Dict[str, Any]]], 
                                       config_path: str) -> None:
        """检查条件边冲突"""
        for from_node, edges in conditional_edges.items():
            if len(edges) > 1:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"节点 '{from_node}' 有多个条件边，这可能导致冲突",
                    location=f"{config_path}:edges",
                    suggestion="合并多个条件边为单个条件边，使用 path_map 定义路由"
                ))
    
    def _validate_graph_config(self, config: GraphConfig) -> None:
        """验证图配置对象"""
        # 验证基本配置
        if not config.name:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="图名称不能为空",
                suggestion="设置图名称"
            ))
        
        if not config.nodes:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="图必须至少包含一个节点",
                suggestion="添加节点定义"
            ))
        
        # 验证状态模式
        if config.state_schema and config.state_schema.fields:
            for field_name in config.state_schema.fields:
                if field_name in self.LANGGRAPH_BUILTIN_FIELDS:
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"状态字段名与LangGraph内置字段冲突: {field_name}",
                        suggestion=f"使用自定义前缀，如 'workflow_{field_name}'"
                    ))
        
        # 验证边
        node_names = set(config.nodes.keys())
        conditional_edges = {}
        
        for edge in config.edges:
            if edge.from_node not in node_names and edge.from_node not in self.SPECIAL_NODES:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"边的起始节点不存在: {edge.from_node}",
                    suggestion=f"确保节点 '{edge.from_node}' 已定义"
                ))
            
            if edge.to_node not in node_names and edge.to_node not in self.SPECIAL_NODES:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"边的目标节点不存在: {edge.to_node}",
                    suggestion=f"确保节点 '{edge.to_node}' 已定义"
                ))
            
            if edge.type == EdgeType.CONDITIONAL:
                if edge.from_node not in conditional_edges:
                    conditional_edges[edge.from_node] = []
                conditional_edges[edge.from_node].append(edge)
        
        # 检查条件边冲突
        for from_node, edges in conditional_edges.items():
            if len(edges) > 1:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"节点 '{from_node}' 有多个条件边，这可能导致冲突",
                    suggestion="合并多个条件边为单个条件边，使用 path_map 定义路由"
                ))
        
        # 验证图连通性
        self._validate_graph_connectivity(config)
    
    def print_issues(self, issues: List[ValidationIssue]) -> None:
        """打印验证问题"""
        if not issues:
            print("✅ 验证通过，未发现问题")
            return
        
        error_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.WARNING)
        info_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.INFO)
        
        print(f"🔍 验证完成，发现 {len(issues)} 个问题:")
        print(f"   ❌ 错误: {error_count}")
        print(f"   ⚠️  警告: {warning_count}")
        print(f"   ℹ️  信息: {info_count}")
        print()
        
        for issue in issues:
            icon = "❌" if issue.severity == ValidationSeverity.ERROR else \
                   "⚠️" if issue.severity == ValidationSeverity.WARNING else "ℹ️"
            
            print(f"{icon} {issue.message}")
            if issue.location:
                print(f"   位置: {issue.location}")
            if issue.suggestion:
                print(f"   建议: {issue.suggestion}")
            print()


def validate_workflow_config(config_path: str) -> List[ValidationIssue]:
    """验证工作流配置文件的便捷函数
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        验证问题列表
    """
    validator = WorkflowValidator()
    return validator.validate_config_file(config_path)


def main():
    """命令行验证工具"""
    import sys
    
    if len(sys.argv) != 2:
        print("用法: python -m src.infrastructure.graph.workflow_validator <config_file>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    validator = WorkflowValidator()
    issues = validator.validate_config_file(config_path)
    validator.print_issues(issues)
    
    # 如果有错误，返回非零退出码
    error_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.ERROR)
    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()