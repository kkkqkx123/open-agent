"""全局检查节点管理器

提供全局检查节点的注册、注入和管理功能。
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from ..engine.state_graph import StateGraphEngine
from ..types import errors


class InjectionPoint(Enum):
    """注入点"""
    BEFORE_ALL_NODES = "before_all"      # 在所有节点之前
    AFTER_ALL_NODES = "after_all"        # 在所有节点之后
    BEFORE_SPECIFIC_NODES = "before_specific"  # 在特定节点之前
    AFTER_SPECIFIC_NODES = "after_specific"    # 在特定节点之后


class GlobalCheckNode:
    """全局检查节点"""
    
    def __init__(
        self,
        name: str,
        check_function: Callable,
        injection_points: List[InjectionPoint],
        priority: int = 50,
        conditions: Optional[List[str]] = None,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化全局检查节点
        
        Args:
            name: 节点名称
            check_function: 检查函数
            injection_points: 注入点列表
            priority: 优先级
            conditions: 注入条件列表
            enabled: 是否启用
            metadata: 元数据
        """
        self.name = name
        self.check_function = check_function
        self.injection_points = injection_points
        self.priority = priority
        self.conditions = conditions or []
        self.enabled = enabled
        self.metadata = metadata or {}
    
    def should_inject(self, graph: StateGraphEngine, context: Optional[Dict[str, Any]] = None) -> bool:
        """判断是否应该注入
        
        Args:
            graph: 状态图
            context: 注入上下文
            
        Returns:
            是否应该注入
        """
        if not self.enabled:
            return False
        
        # 检查条件
        if self.conditions:
            safe_dict = {
                "graph": graph,
                "context": context or {},
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "re": re,
            }
            
            for condition in self.conditions:
                try:
                    if not eval(condition, {"__builtins__": {}}, safe_dict):
                        return False
                except Exception:
                    return False
        
        return True
    
    def create_node_config(self) -> Dict[str, Any]:
        """创建节点配置
        
        Returns:
            节点配置
        """
        return {
            "name": self.name,
            "func": self.check_function,
            "priority": self.priority,
            "metadata": self.metadata,
        }


class InjectionRule:
    """注入规则"""
    
    def __init__(
        self,
        pattern: str,
        injection_point: InjectionPoint,
        priority: int = 50,
    ) -> None:
        """初始化注入规则
        
        Args:
            pattern: 图名称模式（支持正则表达式）
            injection_point: 注入点
            priority: 优先级
        """
        self.pattern = pattern
        self.injection_point = injection_point
        self.priority = priority
        self.compiled_pattern = re.compile(pattern)
    
    def matches(self, graph_name: str) -> bool:
        """检查图名称是否匹配规则
        
        Args:
            graph_name: 图名称
            
        Returns:
            是否匹配
        """
        return bool(self.compiled_pattern.match(graph_name))


class ConditionalInjection:
    """条件注入"""
    
    def __init__(
        self,
        condition: str,
        check_node: GlobalCheckNode,
        injection_point: InjectionPoint,
        priority: int = 50,
    ) -> None:
        """初始化条件注入
        
        Args:
            condition: 注入条件
            check_node: 检查节点
            injection_point: 注入点
            priority: 优先级
        """
        self.condition = condition
        self.check_node = check_node
        self.injection_point = injection_point
        self.priority = priority
    
    def should_inject(self, graph: StateGraphEngine, context: Optional[Dict[str, Any]] = None) -> bool:
        """判断是否应该注入
        
        Args:
            graph: 状态图
            context: 注入上下文
            
        Returns:
            是否应该注入
        """
        safe_dict = {
            "graph": graph,
            "context": context or {},
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "re": re,
        }
        
        try:
            return eval(self.condition, {"__builtins__": {}}, safe_dict)
        except Exception:
            return False


class InjectionContext:
    """注入上下文"""
    
    def __init__(
        self,
        graph: StateGraphEngine,
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化注入上下文
        
        Args:
            graph: 状态图
            execution_context: 执行上下文
        """
        self.graph = graph
        self.execution_context = execution_context or {}
        self.injection_history: List[str] = []


class GlobalCheckNodeManager:
    """全局检查节点管理器
    
    管理全局检查节点的注册、注入和管理。
    """
    
    def __init__(self) -> None:
        """初始化全局检查节点管理器"""
        self.check_nodes: Dict[str, GlobalCheckNode] = {}
        self.injection_rules: List[InjectionRule] = []
        self.conditional_injections: Dict[str, ConditionalInjection] = {}
        self.injection_history: Dict[int, List[str]] = {}
    
    def register_check_node(self, check_node: GlobalCheckNode) -> None:
        """注册检查节点
        
        Args:
            check_node: 检查节点
        """
        self.check_nodes[check_node.name] = check_node
    
    def unregister_check_node(self, name: str) -> bool:
        """注销检查节点
        
        Args:
            name: 节点名称
            
        Returns:
            是否成功注销
        """
        if name in self.check_nodes:
            del self.check_nodes[name]
            return True
        return False
    
    def add_injection_rule(self, rule: InjectionRule) -> None:
        """添加注入规则
        
        Args:
            rule: 注入规则
        """
        self.injection_rules.append(rule)
        # 按优先级排序
        self.injection_rules.sort(key=lambda r: r.priority, reverse=True)
    
    def add_conditional_injection(self, injection: ConditionalInjection) -> None:
        """添加条件注入
        
        Args:
            injection: 条件注入
        """
        key = f"{injection.check_node.name}_{injection.injection_point.value}"
        self.conditional_injections[key] = injection
    
    def inject_into_graph(
        self,
        graph: StateGraphEngine,
        context: Optional[Dict[str, Any]] = None,
    ) -> StateGraphEngine:
        """注入检查节点到图
        
        Args:
            graph: 状态图
            context: 注入上下文
            
        Returns:
            注入后的状态图
        """
        injection_context = InjectionContext(graph, context)
        
        # 记录注入历史
        graph_id = id(graph)
        if graph_id not in self.injection_history:
            self.injection_history[graph_id] = []
        
        # 注入全局检查节点
        for check_node in self.check_nodes.values():
            if check_node.should_inject(graph, context):
                self._inject_check_node(graph, check_node, injection_context)
        
        # 应用注入规则
        for rule in self.injection_rules:
            if rule.matches(graph.__class__.__name__):
                self._apply_injection_rule(graph, rule, injection_context)
        
        # 应用条件注入
        for injection in self.conditional_injections.values():
            if injection.should_inject(graph, context):
                self._inject_check_node_at_point(
                    graph,
                    injection.check_node,
                    injection.injection_point,
                    injection_context,
                )
        
        return graph
    
    def _inject_check_node(
        self,
        graph: StateGraphEngine,
        check_node: GlobalCheckNode,
        context: InjectionContext,
    ) -> None:
        """注入检查节点
        
        Args:
            graph: 状态图
            check_node: 检查节点
            context: 注入上下文
        """
        for injection_point in check_node.injection_points:
            self._inject_check_node_at_point(graph, check_node, injection_point, context)
    
    def _inject_check_node_at_point(
        self,
        graph: StateGraphEngine,
        check_node: GlobalCheckNode,
        injection_point: InjectionPoint,
        context: InjectionContext,
    ) -> None:
        """在指定点注入检查节点
        
        Args:
            graph: 状态图
            check_node: 检查节点
            injection_point: 注入点
            context: 注入上下文
        """
        node_name = f"check_{check_node.name}_{injection_point.value}"
        
        # 避免重复注入
        if node_name in graph.nodes:
            return
        
        # 添加检查节点
        graph.add_node(node_name, check_node.check_function)
        
        # 根据注入点添加边
        if injection_point == InjectionPoint.BEFORE_ALL_NODES:
            if graph.entry_point:
                # 在入口点之后添加
                temp_entry = f"temp_entry_{node_name}"
                graph.add_node(temp_entry, lambda x: x)
                graph.add_edge(graph.entry_point, temp_entry)
                graph.add_edge(temp_entry, node_name)
                graph.entry_point = temp_entry
            else:
                graph.entry_point = node_name
        
        elif injection_point == InjectionPoint.AFTER_ALL_NODES:
            if graph.finish_point:
                # 在结束点之前添加
                temp_finish = f"temp_finish_{node_name}"
                graph.add_node(temp_finish, lambda x: x)
                graph.add_edge(node_name, temp_finish)
                graph.add_edge(temp_finish, graph.finish_point)
                graph.finish_point = temp_finish
            else:
                graph.finish_point = node_name
        
        elif injection_point == InjectionPoint.BEFORE_SPECIFIC_NODES:
            # 在特定节点之前注入
            for node in graph.nodes:
                if node != node_name:
                    # 创建临时节点
                    temp_before = f"temp_before_{node_name}_{node}"
                    graph.add_node(temp_before, lambda x: x)
                    graph.add_edge(temp_before, node)
                    
                    # 更新所有指向原节点的边
                    for edge in graph.edges:
                        edge_end = edge.get("end") if isinstance(edge, dict) else getattr(edge, "end", None)
                        if edge_end == node:
                            if isinstance(edge, dict):
                                edge["end"] = temp_before
                            else:
                                edge.end = temp_before
        
        elif injection_point == InjectionPoint.AFTER_SPECIFIC_NODES:
            # 在特定节点之后注入
            for node in graph.nodes:
                if node != node_name:
                    # 创建临时节点
                    temp_after = f"temp_after_{node_name}_{node}"
                    graph.add_node(temp_after, lambda x: x)
                    graph.add_edge(node, temp_after)
                    
                    # 更新所有从原节点出发的边
                    for edge in graph.edges:
                        edge_start = edge.get("start") if isinstance(edge, dict) else getattr(edge, "start", None)
                        if edge_start == node:
                            if isinstance(edge, dict):
                                edge["start"] = temp_after
                            else:
                                edge.start = temp_after
        
        # 记录注入历史
        graph_id = id(graph)
        self.injection_history[graph_id].append(node_name)
        context.injection_history.append(node_name)
    
    def _apply_injection_rule(
        self,
        graph: StateGraphEngine,
        rule: InjectionRule,
        context: InjectionContext,
    ) -> None:
        """应用注入规则
        
        Args:
            graph: 状态图
            rule: 注入规则
            context: 注入上下文
        """
        # 查找匹配规则的检查节点
        matching_nodes = [
            node for node in self.check_nodes.values()
            if rule.injection_point in node.injection_points
        ]
        
        # 注入匹配的节点
        for check_node in matching_nodes:
            self._inject_check_node_at_point(
                graph,
                check_node,
                rule.injection_point,
                context,
            )
    
    def update_check_node(self, name: str, updates: Dict[str, Any]) -> bool:
        """更新检查节点
        
        Args:
            name: 节点名称
            updates: 更新内容
            
        Returns:
            是否成功更新
        """
        if name not in self.check_nodes:
            return False
        
        check_node = self.check_nodes[name]
        
        for key, value in updates.items():
            if hasattr(check_node, key):
                setattr(check_node, key, value)
        
        return True
    
    def enable_check_node(self, name: str) -> bool:
        """启用检查节点
        
        Args:
            name: 节点名称
            
        Returns:
            是否成功启用
        """
        if name in self.check_nodes:
            self.check_nodes[name].enabled = True
            return True
        return False
    
    def disable_check_node(self, name: str) -> bool:
        """禁用检查节点
        
        Args:
            name: 节点名称
            
        Returns:
            是否成功禁用
        """
        if name in self.check_nodes:
            self.check_nodes[name].enabled = False
            return True
        return False
    
    def get_check_node(self, name: str) -> Optional[GlobalCheckNode]:
        """获取检查节点
        
        Args:
            name: 节点名称
            
        Returns:
            检查节点
        """
        return self.check_nodes.get(name)
    
    def list_check_nodes(self) -> List[str]:
        """列出所有检查节点名称
        
        Returns:
            检查节点名称列表
        """
        return list(self.check_nodes.keys())
    
    def get_injection_history(self, graph: StateGraphEngine) -> List[str]:
        """获取图的注入历史
        
        Args:
            graph: 状态图
            
        Returns:
            注入历史
        """
        graph_id: int = id(graph)
        return self.injection_history.get(graph_id, []).copy()
    
    def clear_injection_history(self, graph: StateGraphEngine) -> None:
        """清空图的注入历史
        
        Args:
            graph: 状态图
        """
        graph_id = id(graph)
        if graph_id in self.injection_history:
            del self.injection_history[graph_id]
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息
        
        Returns:
            统计信息
        """
        return {
            "total_check_nodes": len(self.check_nodes),
            "enabled_check_nodes": sum(1 for node in self.check_nodes.values() if node.enabled),
            "total_injection_rules": len(self.injection_rules),
            "total_conditional_injections": len(self.conditional_injections),
            "injection_history_count": len(self.injection_history),
        }