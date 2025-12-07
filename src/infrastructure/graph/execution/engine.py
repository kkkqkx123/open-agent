"""执行引擎实现

替代LangGraph的Pregel，提供图工作流执行引擎，集成优化调度和消息传递。
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional, TypeVar, Union

from ..engine.compiler import CompiledGraph
from ..hooks import HookPoint, HookSystem, HookContext
from ..types import END, START
from .scheduler import TaskScheduler
from .state_manager import StateManager
from .stream_processor import StreamProcessor

StateT = TypeVar("StateT")

__all__ = ("ExecutionEngine",)


class ExecutionEngine:
    """执行引擎，替代LangGraph的Pregel。
    
    提供图工作流执行引擎，集成优化调度和消息传递。
    """
    
    def __init__(self, graph: 'CompiledGraph') -> None:
        """初始化执行引擎。
        
        Args:
            graph: 编译后的图
        """
        self.graph = graph
        self.hook_system: Optional[HookSystem] = None
        
        # 初始化组件
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """初始化组件。"""
        self.task_scheduler: TaskScheduler = TaskScheduler()
        self.state_manager: StateManager = StateManager(self.graph.state_schema)
        self.stream_processor: StreamProcessor = StreamProcessor()
    
    def set_hook_system(self, hook_system: HookSystem) -> None:
        """设置Hook系统。
        
        Args:
            hook_system: Hook系统实例
        """
        self.hook_system = hook_system
    
    def set_task_scheduler(self, scheduler: TaskScheduler) -> None:
        """设置任务调度器。
        
        Args:
            scheduler: 任务调度器实例
        """
        self.task_scheduler = scheduler
    
    async def invoke(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """同步执行图。
        
        Args:
            input_data: 输入数据
            config: 配置信息
            
        Returns:
            执行结果
        """
        return await self._execute_graph(input_data, config, stream_mode=False)
    
    async def ainvoke(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """异步执行图。
        
        Args:
            input_data: 输入数据
            config: 配置信息
            
        Returns:
            执行结果
        """
        return await self._execute_graph(input_data, config, stream_mode=False)
    
    async def stream(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """流式执行图。
        
        Args:
            input_data: 输入数据
            config: 配置信息
            
        Yields:
            流式输出结果
        """
        async for result in self._execute_graph_stream(input_data, config):
            yield result
    
    async def _execute_graph(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]],
        stream_mode: bool = False
    ) -> Dict[str, Any]:
        """执行图的核心逻辑。
        
        Args:
            input_data: 输入数据
            config: 配置信息
            stream_mode: 是否为流式模式
            
        Returns:
            执行结果
        """
        # 执行前Hook
        if self.hook_system:
            context = HookContext(
                hook_point=HookPoint.BEFORE_EXECUTE,
                config=config or {},
                graph_id=self.graph.graph_id
            )
            await self.hook_system.execute_hooks(HookPoint.BEFORE_EXECUTE, context)
        
        try:
            # 初始化状态
            current_state = await self.state_manager.initialize_state(input_data)
            current_node = self.graph.entry_point
            
            # 执行图
            step = 0
            while current_node and current_node != END:
                # 执行节点
                try:
                    # 执行节点前Hook
                    if self.hook_system:
                        context = HookContext(
                            hook_point=HookPoint.BEFORE_EXECUTE,
                            graph_id=self.graph.graph_id,
                            state=current_state,
                            config=config or {},
                            metadata={"node": current_node, "step": step}
                        )
                        await self.hook_system.execute_hooks(HookPoint.BEFORE_EXECUTE, context)
                    
                    # 获取节点函数
                    node_config = self.graph.get_node(current_node)
                    if not node_config:
                        raise ValueError(f"节点 '{current_node}' 不存在")
                    
                    node_func = node_config["func"]
                    
                    # 执行节点
                    node_result = await self._execute_node(node_func, current_state, config)
                    
                    # 更新状态
                    current_state = await self.state_manager.update_state(current_state, node_result)
                    
                    # 执行节点后Hook
                    if self.hook_system:
                        context = HookContext(
                            hook_point=HookPoint.AFTER_EXECUTE,
                            graph_id=self.graph.graph_id,
                            state=current_state,
                            config=config or {},
                            metadata={"node": current_node, "step": step}
                        )
                        await self.hook_system.execute_hooks(HookPoint.AFTER_EXECUTE, context)
                    
                    # 获取下一个节点
                    next_nodes = self.graph.get_next_nodes(current_node, current_state)
                    if not next_nodes:
                        current_node = END
                    else:
                        # 简化实现：选择第一个下一个节点
                        current_node = next_nodes[0]
                    
                    step += 1
                    
                except Exception as e:
                    # 执行节点错误Hook
                    if self.hook_system:
                        context = HookContext(
                            hook_point=HookPoint.ON_ERROR,
                            graph_id=self.graph.graph_id,
                            state=current_state,
                            config=config or {},
                            error=e,
                            metadata={"node": current_node, "step": step}
                        )
                        await self.hook_system.execute_hooks(HookPoint.ON_ERROR, context)
                    raise
            
            # 执行后Hook
            if self.hook_system:
                context = HookContext(
                    hook_point=HookPoint.AFTER_EXECUTE,
                    graph_id=self.graph.graph_id,
                    state=current_state,
                    config=config or {}
                )
                await self.hook_system.execute_hooks(HookPoint.AFTER_EXECUTE, context)
            
            return current_state
            
        except Exception as e:
            # 错误处理
            if self.hook_system:
                context = HookContext(
                    hook_point=HookPoint.ON_ERROR,
                    graph_id=self.graph.graph_id,
                    config=config or {},
                    error=e
                )
                await self.hook_system.execute_hooks(HookPoint.ON_ERROR, context)
            raise
    
    async def _execute_graph_stream(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]]
    ) -> AsyncIterator[Dict[str, Any]]:
        """流式执行图。
        
        Args:
            input_data: 输入数据
            config: 配置信息
            
        Yields:
            流式输出结果
        """
        # 执行前Hook
        if self.hook_system:
            context = HookContext(
                hook_point=HookPoint.BEFORE_EXECUTE,
                config=config or {},
                graph_id=self.graph.graph_id
            )
            await self.hook_system.execute_hooks(HookPoint.BEFORE_EXECUTE, context)
        
        try:
            # 初始化状态
            current_state = await self.state_manager.initialize_state(input_data)
            current_node = self.graph.entry_point
            
            # 执行图并流式输出
            step = 0
            while current_node and current_node != END:
                # 执行节点
                node_config = self.graph.get_node(current_node)
                if not node_config:
                    raise ValueError(f"节点 '{current_node}' 不存在")
                
                node_func = node_config["func"]
                
                # 流式执行节点
                async for node_result in self._execute_node_stream(node_func, current_state, config):
                    # 更新状态
                    current_state = await self.state_manager.update_state(current_state, node_result)
                    
                    # 流式输出
                    yield {
                        "node": current_node,
                        "step": step,
                        "state": current_state,
                        "result": node_result
                    }
                
                # 获取下一个节点
                next_nodes = self.graph.get_next_nodes(current_node, current_state)
                if not next_nodes:
                    current_node = END
                else:
                    current_node = next_nodes[0]
                
                step += 1
            
            # 执行后Hook
            if self.hook_system:
                context = HookContext(
                    hook_point=HookPoint.AFTER_EXECUTE,
                    graph_id=self.graph.graph_id,
                    state=current_state,
                    config=config or {}
                )
                await self.hook_system.execute_hooks(HookPoint.AFTER_EXECUTE, context)
        
        except Exception as e:
            # 错误处理
            if self.hook_system:
                context = HookContext(
                    hook_point=HookPoint.ON_ERROR,
                    graph_id=self.graph.graph_id,
                    config=config or {},
                    error=e
                )
                await self.hook_system.execute_hooks(HookPoint.ON_ERROR, context)
            raise
    
    async def _execute_node(
        self,
        node_func: Any,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]]
    ) -> Any:
        """执行节点。
        
        Args:
            node_func: 节点函数
            state: 当前状态
            config: 配置信息
            
        Returns:
            节点执行结果
        """
        # 简化实现
        if asyncio.iscoroutinefunction(node_func):
            return await node_func(state, config or {})
        else:
            return node_func(state, config or {})
    
    async def _execute_node_stream(
        self,
        node_func: Any,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]]
    ) -> AsyncIterator[Any]:
        """流式执行节点。
        
        Args:
            node_func: 节点函数
            state: 当前状态
            config: 配置信息
            
        Yields:
            节点执行结果
        """
        # 简化实现：直接执行并yield结果
        result = await self._execute_node(node_func, state, config)
        yield result