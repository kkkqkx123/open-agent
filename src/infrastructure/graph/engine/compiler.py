"""图编译器实现

负责将状态图编译为可执行的图结构。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, TYPE_CHECKING

from ..types import START, END

if TYPE_CHECKING:
    from .state_graph import StateGraphEngine

__all__ = ("GraphCompiler", "CompiledGraph")


class CompiledGraph:
    """编译后的图结构。"""
    
    def __init__(
        self,
        graph_id: str,
        nodes: Dict[str, Any],
        edges: List[Dict[str, Any]],
        entry_point: str,
        state_schema: Type,
        checkpointer: Optional[Any] = None
    ):
        self.graph_id = graph_id
        self.nodes = nodes
        self.edges = edges
        self.entry_point = entry_point
        self.state_schema = state_schema
        self.checkpointer = checkpointer
        self.compiled_at = None  # 可以添加编译时间戳
    
    def get_node(self, name: str) -> Optional[Any]:
        """获取节点。"""
        return self.nodes.get(name)
    
    def get_next_nodes(self, current_node: str, state: Any) -> List[str]:
        """获取下一个节点列表。"""
        next_nodes = []
        
        # 查找简单边
        for edge in self.edges:
            if edge["start"] == current_node and edge["type"] == "simple":
                next_nodes.append(edge["end"])
        
        # 查找条件边（简化实现）
        for edge in self.edges:
            if edge["start"] == current_node and edge["type"] == "conditional":
                # 这里应该根据状态和条件函数确定下一个节点
                # 简化实现，直接返回映射中的第一个节点
                if edge.get("path_map"):
                    next_nodes.extend(edge["path_map"].values())
        
        return next_nodes


class GraphCompiler:
    """图编译器，将状态图编译为可执行的图结构。"""
    
    async def compile(
        self,
        graph: "StateGraphEngine",
        checkpointer: Optional[Any] = None
    ) -> CompiledGraph:
        """编译状态图。
        
        Args:
            graph: 状态图引擎
            checkpointer: 检查点保存器
            
        Returns:
            编译后的图
        """
        # 创建编译后的节点
        compiled_nodes = {}
        for name, func in graph.get_nodes().items():
            compiled_nodes[name] = {
                "name": name,
                "func": func,
                "type": "node"
            }
        
        # 编译边
        compiled_edges = []
        
        # 处理简单边
        for edge in graph.get_edges():
            compiled_edges.append({
                "start": edge["start"],
                "end": edge["end"],
                "type": "simple"
            })
        
        # 处理条件边
        for cond_edge in graph.get_conditional_edges():
            compiled_edges.append({
                "start": cond_edge["source"],
                "path": cond_edge["path"],
                "path_map": cond_edge["path_map"],
                "type": "conditional"
            })
        
        # 创建编译后的图
        compiled_graph = CompiledGraph(
            graph_id=str(id(graph)),
            nodes=compiled_nodes,
            edges=compiled_edges,
            entry_point=graph.entry_point or START,
            state_schema=graph.state_schema,
            checkpointer=checkpointer
        )
        
        return compiled_graph