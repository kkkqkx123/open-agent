"""工作流验证器 - 统一验证逻辑

集中所有工作流验证功能，避免验证逻辑分散。
"""

from abc import ABC, abstractmethod
import os
import yaml
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
from src.interfaces.dependency_injection import get_logger

from src.core.workflow.graph_entities import GraphConfig, EdgeConfig, EdgeType

logger = get_logger(__name__)


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


class IWorkflowValidator(ABC):
    """工作流验证器接口"""
    
    @abstractmethod
    def validate_config_file(self, config_path: str) -> List[ValidationIssue]:
        """验证配置文件"""
        pass
    
    @abstractmethod
    def validate_config_object(self, config: GraphConfig) -> List[ValidationIssue]:
        """验证配置对象"""
        pass


class WorkflowValidator(IWorkflowValidator):
    """工作流验证器实现
    
    集中所有验证逻辑，提供统一的验证服务。
    """
    
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
            # 使用配置管理器加载
            from src.core.config.config_manager import get_default_manager
            config_manager = get_default_manager()
            config_data = config_manager.load_config_for_module(config_path, "workflow")
            
            self._validate_config_data(config_data, config_path)
            
        except Exception as e:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"配置文件读取错误: {e}",
                location=config_path,
                suggestion="检查文件路径是否正确，或配置管理器是否正确初始化"
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
        
        # 验证图连通性
        if "nodes" in config_data and "edges" in config_data:
            self._validate_connectivity_from_dict(config_data, config_path)
    
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
    
    def _validate_connectivity_from_dict(self, config_data: Dict[str, Any], config_path: str) -> None:
        """从字典配置验证图连通性"""
        if not config_data.get("nodes") or not config_data.get("edges"):
            return
        
        # 构建图结构
        graph = self._build_graph_structure_from_dict(config_data)
        
        # 检测可达性
        self._check_reachability_from_dict(graph, config_data, config_path)
        
        # 检测环路
        self._detect_cycles_from_dict(graph, config_data, config_path)
        
        # 检测死节点
        self._detect_dead_nodes_from_dict(graph, config_data, config_path)
        
        # 检测终止路径
        self._check_termination_paths_from_dict(graph, config_data, config_path)
    
    def _build_graph_structure_from_dict(self, config_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """从字典配置构建图结构"""
        graph = {}
        
        # 检查nodes是否存在且是字典
        if "nodes" not in config_data:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="配置中缺少nodes字段",
                suggestion="添加nodes定义"
            ))
            return graph
        
        if not isinstance(config_data["nodes"], dict):
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="nodes字段必须是字典格式",
                suggestion="检查nodes配置格式"
            ))
            return graph
        
        # 初始化所有节点
        for node_name in config_data["nodes"]:
            graph[node_name] = {
                "outgoing": set(),
                "incoming": set(),
                "is_conditional": False,
                "targets": set()
            }
        
        # 添加边关系
        for edge in config_data["edges"]:
            from_node = edge.get("from")
            to_node = edge.get("to")
            edge_type = edge.get("type")
            
            if from_node in graph:
                if edge_type == "conditional":
                    graph[from_node]["is_conditional"] = True
                    # 对于条件边，添加所有可能的路径
                    path_map = edge.get("path_map", {})
                    for target in path_map.values():
                        if target in graph or target in self.SPECIAL_NODES:
                            graph[from_node]["targets"].add(target)
                else:
                    # 简单边
                    if to_node in graph or to_node in self.SPECIAL_NODES:
                        graph[from_node]["targets"].add(to_node)
                
                if to_node:
                    graph[from_node]["outgoing"].add(to_node)
            
            if to_node and to_node in graph:
                graph[to_node]["incoming"].add(from_node)
        
        return graph
    
    def _check_reachability_from_dict(self, graph: Dict[str, Dict[str, Any]], 
                                    config_data: Dict[str, Any], config_path: str) -> None:
        """检查从入口点开始的可达性"""
        entry_point = config_data.get("entry_point")
        if not entry_point or entry_point not in graph:
            return
        
        # 使用DFS查找所有可达节点
        visited = set()
        stack = [entry_point]
        
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            
            visited.add(node)
            
            if node in graph:
                stack.extend(graph[node]["targets"] - visited)
        
        # 检查是否有不可达的节点
        unreachable = set(graph.keys()) - visited
        for node in unreachable:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"节点 '{node}' 从入口点不可达",
                location=config_path,
                suggestion="检查边的连接，确保所有节点都能从入口点到达"
            ))
    
    def _detect_cycles_from_dict(self, graph: Dict[str, Dict[str, Any]], config_data: Dict[str, Any], config_path: str) -> None:
        """检测图中的环路"""
        visited = set()
        rec_stack = set()

        def dfs_cycle_detection(node: str, path: List[str]) -> List[str]:
            """DFS检测环路，返回环路路径"""
            if node in rec_stack:
                # 找到环路
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]

            if node in visited:
                return []

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            if node in graph:
                for target in graph[node]["targets"]:
                    if target not in self.SPECIAL_NODES:  # 忽略特殊节点
                        cycle = dfs_cycle_detection(target, path.copy())
                        if cycle:
                            return cycle

            rec_stack.remove(node)
            return []

        # 查找所有环路
        all_cycles = []
        for node in graph:
            if node not in visited:
                cycle = dfs_cycle_detection(node, [])
                if cycle:
                    all_cycles.append(cycle)

        # 分析每个环路
        for cycle in all_cycles:
            self._analyze_cycle(cycle, config_data, config_path)
    
    def _analyze_cycle(self, cycle: List[str], config_data: Dict[str, Any], config_path: str) -> None:
        """分析环路是否有退出条件"""
        cycle_str = " -> ".join(cycle)
        
        # 检查环路中的节点是否有条件边
        has_conditional_edges = False
        has_termination_potential = False
        
        edges = config_data.get("edges", [])
        
        for edge in edges:
            if edge.get("from") in cycle and edge.get("type") == "conditional":
                has_conditional_edges = True
                
                # 检查条件函数是否有退出条件
                condition_name = edge.get("condition", "")
                if self._has_termination_condition(condition_name, cycle):
                    has_termination_potential = True
        
        # 检查环路中是否有终端节点
        has_terminal_node = any(
            self._is_terminal_node_from_dict(node, config_data) 
            for node in cycle
        )
        
        # 检查环路中是否有指向 __end__ 的边
        has_end_edge = any(
            edge.get("from") in cycle and edge.get("to") == "__end__"
            for edge in edges
        )
        
        # 根据分析结果确定问题严重程度
        if has_termination_potential or has_terminal_node or has_end_edge:
            # 这是一个受控环路，可能是有意设计的
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message=f"检测到受控环路: {cycle_str}",
                location=config_path,
                suggestion="这是一个有退出条件的环路，请确保条件函数能正确触发退出"
            ))
        elif has_conditional_edges:
            # 有条件边但不确定是否有退出条件
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"检测到潜在问题环路: {cycle_str}",
                location=config_path,
                suggestion="检查条件函数是否包含退出条件，避免无限循环"
            ))
        else:
            # 没有条件边的环路，很可能是无限循环
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"检测到无限环路: {cycle_str}",
                location=config_path,
                suggestion="重新设计工作流逻辑，添加退出条件或打破环路"
            ))
    
    def _has_termination_condition(self, condition_name: str, cycle: List[str]) -> bool:
        """检查条件函数是否有终止条件"""
        # 这是一个简化的检查，实际应用中可能需要更复杂的分析
        # 这里我们基于函数名和常见的终止模式进行判断
        
        termination_keywords = [
            "end", "finish", "complete", "final", "terminate", 
            "exit", "stop", "break", "done", "success", "failure"
        ]
        
        condition_lower = condition_name.lower()
        for keyword in termination_keywords:
            if keyword in condition_lower:
                return True
        
        # 检查是否包含返回特殊节点的逻辑
        special_node_keywords = ["__end__", "end_node", "final_node", "terminal"]
        for keyword in special_node_keywords:
            if keyword in condition_lower:
                return True
        
        return False
    
    def _detect_dead_nodes_from_dict(self, graph: Dict[str, Dict[str, Any]], 
                                   config_data: Dict[str, Any], config_path: str) -> None:
        """检测死节点（没有出边的节点）"""
        for node_name, node_info in graph.items():
            if not node_info["targets"]:
                # 检查是否是终端节点（有意设计为结束点）
                is_terminal = self._is_terminal_node_from_dict(node_name, config_data)
                
                if not is_terminal:
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"节点 '{node_name}' 没有出边，可能是死节点",
                        location=config_path,
                        suggestion="添加出边或确认这是有意设计的终端节点"
                    ))
    
    def _is_terminal_node_from_dict(self, node_name: str, config_data: Dict[str, Any]) -> bool:
        """判断是否是终端节点"""
        # 检查节点名称是否包含结束相关关键词
        terminal_keywords = ["end", "finish", "complete", "final", "terminal", "exit"]
        node_lower = node_name.lower()
        
        for keyword in terminal_keywords:
            if keyword in node_lower:
                return True
        
        # 检查节点配置
        nodes = config_data.get("nodes", {})
        if node_name in nodes:
            node_config = nodes[node_name]
            description = node_config.get("description", "").lower()
            for keyword in terminal_keywords:
                if keyword in description:
                    return True
        
        return False
    
    def _check_termination_paths_from_dict(self, graph: Dict[str, Dict[str, Any]], 
                                          config_data: Dict[str, Any], config_path: str) -> None:
        """检查是否有到终止节点的路径"""
        entry_point = config_data.get("entry_point")
        if not entry_point or entry_point not in graph:
            return
        
        # 查找所有可能的终止节点
        termination_nodes = set()
        for node_name in graph:
            if self._is_terminal_node_from_dict(node_name, config_data):
                termination_nodes.add(node_name)
        
        # 如果没有明确的终止节点，检查是否有到 __end__ 的路径
        has_end_edges = any(
            edge.get("to") == "__end__" 
            for edge in config_data.get("edges", [])
        )
        
        if not termination_nodes and not has_end_edges:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="工作流缺少明确的终止路径",
                location=config_path,
                suggestion="添加指向 __end__ 的边或创建终端节点"
            ))
            return
        
        # 检查从入口点是否能到达终止节点
        if termination_nodes:
            visited = set()
            stack = [entry_point]
            
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                
                visited.add(node)
                
                if node in termination_nodes:
                    return  # 找到终止路径
                
                if node in graph:
                    stack.extend(graph[node]["targets"] - visited)
            
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="从入口点无法到达任何终止节点",
                location=config_path,
                suggestion="检查边的连接，确保有路径可以到达终止节点"
            ))
    
    def _validate_graph_connectivity(self, config: GraphConfig) -> None:
        """验证图连通性，检测成环、无法结束等问题"""
        if not config.nodes or not config.edges:
            return
        
        # 构建图结构
        graph = self._build_graph_structure(config)
        
        # 检测可达性
        self._check_reachability(graph, config)
        
        # 检测环路
        self._detect_cycles(graph)
        
        # 检测死节点
        self._detect_dead_nodes(graph, config)
        
        # 检测终止路径
        self._check_termination_paths(graph, config)
    
    def _build_graph_structure(self, config: GraphConfig) -> Dict[str, Dict[str, Any]]:
        """构建图结构"""
        graph = {}
        
        # 初始化所有节点
        for node_name in config.nodes:
            graph[node_name] = {
                "outgoing": set(),
                "incoming": set(),
                "is_conditional": False,
                "targets": set()
            }
        
        # 添加边关系
        for edge in config.edges:
            from_node = edge.from_node
            to_node = edge.to_node
            
            if from_node in graph:
                if edge.type == EdgeType.CONDITIONAL:
                    graph[from_node]["is_conditional"] = True
                    # 对于条件边，添加所有可能的路径
                    if edge.path_map:
                        for target in edge.path_map.values():
                            if target in graph or target in self.SPECIAL_NODES:
                                graph[from_node]["targets"].add(target)
                else:
                    # 简单边
                    if to_node in graph or to_node in self.SPECIAL_NODES:
                        graph[from_node]["targets"].add(to_node)
                
                graph[from_node]["outgoing"].add(to_node)
            
            if to_node in graph:
                graph[to_node]["incoming"].add(from_node)
        
        return graph
    
    def _check_reachability(self, graph: Dict[str, Dict[str, Any]], config: GraphConfig) -> None:
        """检查从入口点开始的可达性"""
        if not config.entry_point or config.entry_point not in graph:
            return
        
        # 使用DFS查找所有可达节点
        visited = set()
        stack = [config.entry_point]
        
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            
            visited.add(node)
            
            if node in graph:
                stack.extend(graph[node]["targets"] - visited)
        
        # 检查是否有不可达的节点
        unreachable = set(graph.keys()) - visited
        for node in unreachable:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"节点 '{node}' 从入口点不可达",
                suggestion="检查边的连接，确保所有节点都能从入口点到达"
            ))
    
    def _detect_cycles(self, graph: Dict[str, Dict[str, Any]]) -> None:
        """检测图中的环路"""
        visited = set()
        rec_stack = set()
        
        def dfs_cycle_detection(node: str, path: List[str]) -> bool:
            """DFS检测环路"""
            if node in rec_stack:
                # 找到环路
                cycle_start = path.index(node)
                cycle_path = path[cycle_start:] + [node]
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"检测到环路: {' -> '.join(cycle_path)}",
                    suggestion="重新设计工作流逻辑，避免无限循环"
                ))
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            if node in graph:
                for target in graph[node]["targets"]:
                    if target not in self.SPECIAL_NODES:  # 忽略特殊节点
                        if dfs_cycle_detection(target, path.copy()):
                            return True
            
            rec_stack.remove(node)
            return False
        
        # 对每个节点进行环路检测
        for node in graph:
            if node not in visited:
                dfs_cycle_detection(node, [])
    
    def _detect_dead_nodes(self, graph: Dict[str, Dict[str, Any]], config: GraphConfig) -> None:
        """检测死节点（没有出边的节点）"""
        for node_name, node_info in graph.items():
            if not node_info["targets"]:
                # 检查是否是终端节点（有意设计为结束点）
                is_terminal = self._is_terminal_node(node_name, config)
                
                if not is_terminal:
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"节点 '{node_name}' 没有出边，可能是死节点",
                        suggestion="添加出边或确认这是有意设计的终端节点"
                    ))
    
    def _is_terminal_node(self, node_name: str, config: GraphConfig) -> bool:
        """判断是否是终端节点"""
        # 检查节点名称是否包含结束相关关键词
        terminal_keywords = ["end", "finish", "complete", "final", "terminal", "exit"]
        node_lower = node_name.lower()
        
        for keyword in terminal_keywords:
            if keyword in node_lower:
                return True
        
        # 检查节点配置
        if node_name in config.nodes:
            node_config = config.nodes[node_name]
            description = getattr(node_config, 'description', '').lower()
            for keyword in terminal_keywords:
                if keyword in description:
                    return True
        
        return False
    
    def _check_termination_paths(self, graph: Dict[str, Dict[str, Any]], config: GraphConfig) -> None:
        """检查是否有到终止节点的路径"""
        if not config.entry_point or config.entry_point not in graph:
            return
        
        # 查找所有可能的终止节点
        termination_nodes = set()
        for node_name in graph:
            if self._is_terminal_node(node_name, config):
                termination_nodes.add(node_name)
        
        # 如果没有明确的终止节点，检查是否有到 __end__ 的路径
        has_end_edges = any(
            edge.to_node == "__end__" 
            for edge in config.edges
        )
        
        if not termination_nodes and not has_end_edges:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="工作流缺少明确的终止路径",
                suggestion="添加指向 __end__ 的边或创建终端节点"
            ))
            return
        
        # 检查从入口点是否能到达终止节点
        if termination_nodes:
            visited = set()
            stack = [config.entry_point]
            
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                
                visited.add(node)
                
                if node in termination_nodes:
                    return  # 找到终止路径
                
                if node in graph:
                    stack.extend(graph[node]["targets"] - visited)
            
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="从入口点无法到达任何终止节点",
                suggestion="检查边的连接，确保有路径可以到达终止节点"
            ))
    
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