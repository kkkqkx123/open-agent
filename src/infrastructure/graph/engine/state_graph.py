"""状态图引擎实现

替代LangGraph的StateGraph，支持节点和边的定义、条件边和编译过程。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from ..hooks import HookPoint, HookSystem, HookContext
from ..types import START, END
from .compiler import GraphCompiler
from .node_builder import NodeBuilder
from .edge_builder import EdgeBuilder

StateT = TypeVar("StateT")

__all__ = ("StateGraphEngine",)


class StateGraphEngine:
    """状态图引擎，替代LangGraph的StateGraph。
    
    支持节点和边的定义、条件边和编译过程，集成Hook系统。
    """
    
    def __init__(self, state_schema: Type[StateT]) -> None:
        """初始化状态图引擎。
        
        Args:
            state_schema: 状态模式类型
        """
        self.state_schema = state_schema
        self.nodes: Dict[str, Callable] = {}
        self.edges: List[Dict[str, Any]] = []
        self.conditional_edges: List[Dict[str, Any]] = []
        self.entry_point: Optional[str] = None
        self.finish_point: Optional[str] = None
        self.hook_system: Optional[HookSystem] = None
        self.compiled_graph: Optional[Any] = None
        
        # 初始化构建器
        self.node_builder = NodeBuilder()
        self.edge_builder = EdgeBuilder()
        self.compiler = GraphCompiler()
    
    def add_node(self, name: str, func: Callable, **kwargs) -> StateGraphEngine:
        """添加节点。
        
        Args:
            name: 节点名称
            func: 节点函数
            **kwargs: 额外参数
            
        Returns:
            自身实例，支持链式调用
        """
        self.nodes[name] = func
        return self
    
    def add_edge(self, start: str, end: str) -> StateGraphEngine:
        """添加边。
        
        Args:
            start: 起始节点
            end: 目标节点
            
        Returns:
            自身实例，支持链式调用
        """
        self.edges.append({
            "start": start,
            "end": end,
            "type": "simple"
        })
        return self
    
    def add_conditional_edges(
        self,
        source: str,
        path: Callable,
        path_map: Optional[Dict] = None
    ) -> StateGraphEngine:
        """添加条件边。
        
        Args:
            source: 源节点
            path: 路径函数
            path_map: 路径映射
            
        Returns:
            自身实例，支持链式调用
        """
        self.conditional_edges.append({
            "source": source,
            "path": path,
            "path_map": path_map
        })
        return self
    
    def set_entry_point(self, node_name: str) -> StateGraphEngine:
        """设置入口点。
        
        Args:
            node_name: 入口节点名称
            
        Returns:
            自身实例，支持链式调用
        """
        self.entry_point = node_name
        return self
    
    def set_finish_point(self, node_name: str) -> StateGraphEngine:
        """设置结束点。
        
        Args:
            node_name: 结束节点名称
            
        Returns:
            自身实例，支持链式调用
        """
        self.finish_point = node_name
        return self
    
    def set_hook_system(self, hook_system: HookSystem) -> None:
        """设置Hook系统。
        
        Args:
            hook_system: Hook系统实例
        """
        self.hook_system = hook_system
    
    async def compile(self, checkpointer: Optional[Any] = None) -> Any:
        """编译图。
        
        Args:
            checkpointer: 检查点保存器
            
        Returns:
            编译后的图
        """
        # 执行编译前Hook
        if self.hook_system:
            context = HookContext(
                hook_point=HookPoint.BEFORE_COMPILE,
                graph_id=str(id(self)),
                config={"checkpointer": checkpointer}
            )
            await self.hook_system.execute_hooks(HookPoint.BEFORE_COMPILE, context)
        
        try:
            # 验证图结构
            self._validate_graph()
            
            # 使用编译器编译图
            self.compiled_graph = await self.compiler.compile(
                self,
                checkpointer=checkpointer
            )
            
            # 执行编译后Hook
            if self.hook_system:
                context = HookContext(
                    hook_point=HookPoint.AFTER_COMPILE,
                    graph_id=str(id(self)),
                    config={"checkpointer": checkpointer}
                )
                await self.hook_system.execute_hooks(HookPoint.AFTER_COMPILE, context)
            
            return self.compiled_graph
            
        except Exception as e:
            # 错误处理
            if self.hook_system:
                context = HookContext(
                    hook_point=HookPoint.BEFORE_COMPILE,
                    graph_id=str(id(self)),
                    config={"checkpointer": checkpointer},
                    error=e
                )
                await self.hook_system.execute_hooks(HookPoint.BEFORE_COMPILE, context)
            raise
    
    def _validate_graph(self) -> None:
        """验证图结构。
        
        Raises:
            ValueError: 图结构无效
        """
        if not self.entry_point:
            raise ValueError("图必须设置入口点")
        
        if self.entry_point not in self.nodes:
            raise ValueError(f"入口节点 '{self.entry_point}' 不存在")
        
        # 验证边
        for edge in self.edges:
            if edge["start"] not in self.nodes and edge["start"] != START:
                raise ValueError(f"边起始节点 '{edge['start']}' 不存在")
            if edge["end"] not in self.nodes and edge["end"] != END:
                raise ValueError(f"边目标节点 '{edge['end']}' 不存在")
        
        # 验证条件边
        for cond_edge in self.conditional_edges:
            if cond_edge["source"] not in self.nodes:
                raise ValueError(f"条件边源节点 '{cond_edge['source']}' 不存在")
    
    def get_node(self, name: str) -> Optional[Callable]:
        """获取节点。
        
        Args:
            name: 节点名称
            
        Returns:
            节点函数（如果存在）
        """
        return self.nodes.get(name)
    
    def get_nodes(self) -> Dict[str, Callable]:
        """获取所有节点。
        
        Returns:
            节点字典
        """
        return self.nodes.copy()
    
    def get_edges(self) -> List[Dict[str, Any]]:
        """获取所有边。
        
        Returns:
            边列表
        """
        return self.edges.copy()
    
    def get_conditional_edges(self) -> List[Dict[str, Any]]:
        """获取所有条件边。
        
        Returns:
            条件边列表
        """
        return self.conditional_edges.copy()
    
    def get_graph_info(self) -> Dict[str, Any]:
        """获取图信息。
        
        Returns:
            图信息字典
        """
        return {
            "state_schema": self.state_schema.__name__ if self.state_schema else None,
            "nodes": list(self.nodes.keys()),
            "edges": len(self.edges),
            "conditional_edges": len(self.conditional_edges),
            "entry_point": self.entry_point,
            "finish_point": self.finish_point,
            "compiled": self.compiled_graph is not None,
            "hook_system": self.hook_system is not None
        }
    
    async def destroy(self) -> None:
        """销毁图，释放资源。"""
        # 执行销毁前Hook
        if self.hook_system:
            context = HookContext(
                hook_point=HookPoint.BEFORE_DESTROY,
                graph_id=str(id(self))
            )
            await self.hook_system.execute_hooks(HookPoint.BEFORE_DESTROY, context)
        
        # 清理资源
        self.nodes.clear()
        self.edges.clear()
        self.conditional_edges.clear()
        self.compiled_graph = None
        self.hook_system = None