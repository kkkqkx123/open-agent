"""动态编译器

提供图的动态编译、热替换和运行时修改功能。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union

from ..engine.state_graph import StateGraphEngine
from ..execution.engine import CompiledGraph
from ..types import errors

StateT = TypeVar("StateT")


class GraphChanges:
    """图变更定义"""
    
    def __init__(
        self,
        added_nodes: Optional[Dict[str, Any]] = None,
        removed_nodes: Optional[Set[str]] = None,
        modified_nodes: Optional[Dict[str, Any]] = None,
        added_edges: Optional[List[Tuple[str, str]]] = None,
        removed_edges: Optional[List[Tuple[str, str]]] = None,
        modified_edges: Optional[List[Tuple[str, str, Dict[str, Any]]]] = None,
    ) -> None:
        self.added_nodes = added_nodes or {}
        self.removed_nodes = removed_nodes or set()
        self.modified_nodes = modified_nodes or {}
        self.added_edges = added_edges or []
        self.removed_edges = removed_edges or []
        self.modified_edges = modified_edges or []


class EdgeConfig:
    """边配置"""
    
    def __init__(
        self,
        start: str,
        end: str,
        condition: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.start = start
        self.end = end
        self.condition = condition
        self.metadata = metadata or {}


class OptimizedGraph:
    """优化后的图"""
    
    def __init__(
        self,
        compiled_graph: CompiledGraph,
        optimizations: List[str],
        performance_metrics: Dict[str, Any],
    ) -> None:
        self.compiled_graph = compiled_graph
        self.optimizations = optimizations
        self.performance_metrics = performance_metrics


class DynamicCompiler:
    """动态编译器
    
    支持增量编译、热替换和运行时图修改。
    """
    
    def __init__(self, cache_size: int = 100) -> None:
        """初始化动态编译器
        
        Args:
            cache_size: 编译缓存大小
        """
        self.compilation_cache: Dict[str, CompiledGraph] = {}
        self.cache_size = cache_size
        self.cache_access_order: List[str] = []
        self.optimization_rules: List[Callable] = []
    
    def _generate_graph_hash(self, graph: StateGraphEngine) -> str:
        """生成图的哈希值
        
        Args:
            graph: 状态图引擎
            
        Returns:
            图的哈希值
        """
        # 创建图的序列化表示
        graph_repr = {
            "nodes": list(graph.nodes.keys()),
            "edges": [(edge["start"], edge["end"]) if isinstance(edge, dict) else (edge.start, edge.end) for edge in graph.edges],
            "conditional_edges": [
                (edge.get("source") or getattr(edge, "source", None), str(edge.get("path") or getattr(edge, "path", ""))) for edge in graph.conditional_edges
            ],
            "entry_point": graph.entry_point,
            "finish_point": graph.finish_point,
        }
        
        # 生成哈希
        graph_str = json.dumps(graph_repr, sort_keys=True)
        return hashlib.sha256(graph_str.encode()).hexdigest()
    
    def _manage_cache(self, graph_hash: str, compiled_graph: CompiledGraph) -> None:
        """管理编译缓存
        
        Args:
            graph_hash: 图哈希值
            compiled_graph: 编译后的图
        """
        # 如果缓存已满，移除最旧的条目
        if len(self.compilation_cache) >= self.cache_size:
            oldest_hash = self.cache_access_order.pop(0)
            del self.compilation_cache[oldest_hash]
        
        # 添加新的编译结果
        self.compilation_cache[graph_hash] = compiled_graph
        self.cache_access_order.append(graph_hash)
    
    async def recompile(
        self, 
        graph: StateGraphEngine, 
        changes: GraphChanges,
        config: Optional[Dict[str, Any]] = None
    ) -> CompiledGraph:
        """增量编译图
        
        Args:
            graph: 状态图引擎
            changes: 图变更
            config: 编译配置
            
        Returns:
            编译后的图
        """
        # 应用变更到图
        self._apply_changes(graph, changes)
        
        # 生成新的图哈希
        graph_hash = self._generate_graph_hash(graph)
        
        # 检查缓存
        if graph_hash in self.compilation_cache:
            return self.compilation_cache[graph_hash]
        
        # 编译图
        compile_config = config or {}
        compiled_graph = await graph.compile(compile_config)
        
        # 缓存编译结果
        self._manage_cache(graph_hash, compiled_graph)
        
        return compiled_graph
    
    def _apply_changes(self, graph: StateGraphEngine, changes: GraphChanges) -> None:
        """应用变更到图
        
        Args:
            graph: 状态图引擎
            changes: 图变更
        """
        # 移除节点
        for node_name in changes.removed_nodes:
            if node_name in graph.nodes:
                del graph.nodes[node_name]
        
        # 添加节点
        for node_name, node_func in changes.added_nodes.items():
            graph.add_node(node_name, node_func)
        
        # 修改节点
        for node_name, node_func in changes.modified_nodes.items():
            if node_name in graph.nodes:
                graph.nodes[node_name] = node_func
        
        # 移除边
        for start, end in changes.removed_edges:
            graph.edges = [
                edge for edge in graph.edges 
                if not ((edge.get("start") if isinstance(edge, dict) else edge.start) == start and (edge.get("end") if isinstance(edge, dict) else edge.end) == end)
            ]
        
        # 添加边
        for start, end in changes.added_edges:
            graph.add_edge(start, end)
        
        # 修改边
        for start, end, edge_data in changes.modified_edges:
            # 先移除旧边
            graph.edges = [
                edge for edge in graph.edges 
                if not ((edge.get("start") if isinstance(edge, dict) else edge.start) == start and (edge.get("end") if isinstance(edge, dict) else edge.end) == end)
            ]
            # 添加新边
            if "condition" in edge_data:
                graph.add_conditional_edges(start, edge_data["condition"])
            else:
                graph.add_edge(start, end)
    
    def hot_swap_node(
        self, 
        compiled_graph: CompiledGraph, 
        node_id: str, 
        new_node: Any
    ) -> None:
        """热替换节点
        
        Args:
            compiled_graph: 编译后的图
            node_id: 节点ID
            new_node: 新节点
        """
        if not hasattr(compiled_graph, "nodes"):
            raise errors.InvalidGraphError("编译后的图不支持热替换")
        
        if node_id not in compiled_graph.nodes:
            raise errors.NodeNotFoundError(f"节点 {node_id} 不存在")
        
        # 替换节点
        compiled_graph.nodes[node_id] = new_node
    
    def add_edge_runtime(
        self, 
        compiled_graph: CompiledGraph, 
        edge: EdgeConfig
    ) -> None:
        """运行时添加边
        
        Args:
            compiled_graph: 编译后的图
            edge: 边配置
        """
        if not hasattr(compiled_graph, "edges"):
            raise errors.InvalidGraphError("编译后的图不支持运行时修改")
        
        # 添加边
        edge_data = {
            "start": edge.start,
            "end": edge.end,
        }
        if edge.condition:
            edge_data["condition"] = edge.condition
        if edge.metadata:
            edge_data.update(edge.metadata)
        
        compiled_graph.edges.append(edge_data)
    
    async def optimize_graph(self, graph: StateGraphEngine, config: Optional[Dict[str, Any]] = None) -> OptimizedGraph:
        """优化图结构
        
        Args:
            graph: 状态图引擎
            config: 编译配置
            
        Returns:
            优化后的图
        """
        optimizations = []
        performance_metrics = {}
        
        # 应用优化规则
        for rule in self.optimization_rules:
            result = rule(graph)
            if result:
                optimizations.append(result["name"])
                performance_metrics.update(result.get("metrics", {}))
        
        # 编译优化后的图
        compile_config = config or {}
        compiled_graph = await graph.compile(compile_config)
        
        return OptimizedGraph(
            compiled_graph=compiled_graph,
            optimizations=optimizations,
            performance_metrics=performance_metrics,
        )
    
    def add_optimization_rule(self, rule: Callable) -> None:
        """添加优化规则
        
        Args:
            rule: 优化规则函数，接受图并返回优化结果
        """
        self.optimization_rules.append(rule)
    
    def clear_cache(self) -> None:
        """清空编译缓存"""
        self.compilation_cache.clear()
        self.cache_access_order.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        return {
            "cache_size": len(self.compilation_cache),
            "max_cache_size": self.cache_size,
            "cache_hit_ratio": getattr(self, "_cache_hits", 0) / max(getattr(self, "_cache_requests", 1), 1),
        }
