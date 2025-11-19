"""统一图构建器

集成所有功能的统一图构建器，包含基础构建、函数注册表集成和迭代管理功能。
"""

from typing import Dict, Any, Optional, List, Callable, Union, TYPE_CHECKING, cast
from pathlib import Path
import yaml
import logging
import asyncio
import concurrent.futures
import time
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from langchain_core.runnables import RunnableConfig

from src.core.workflow.config.config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
from src.core.workflow.states import WorkflowState
from langchain_core.messages import BaseMessage as LCBaseMessage
from src.core.workflow.graph.nodes.registry import NodeRegistry, get_global_registry, BaseNode
from src.services.workflow.state_converter import get_state_converter, WorkflowStateAdapter as GraphAgentState
from src.state.interfaces import IStateLifecycleManager
from .function_registry import (
    FunctionRegistry,
    FunctionType,
    get_global_function_registry,
)
from src.core.workflow.management.iteration_manager import IterationManager
from src.core.workflow.graph.route_functions import get_route_function_manager
from src.core.workflow.graph.node_functions import get_node_function_manager

logger = logging.getLogger(__name__)

# 导入LangGraph核心组件
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver


class INodeExecutor(ABC):
    """节点执行器接口"""
    
    @abstractmethod
    def execute_node(self, node: BaseNode, state: WorkflowState, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点
        
        Args:
            node: 节点实例
            state: 工作流状态
            config: 配置
            
        Returns:
            更新后的状态
        """
        pass


class DefaultNodeExecutor(INodeExecutor):
    """默认节点执行器"""
    
    def execute_node(self, node: BaseNode, state: WorkflowState, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点
        
        Args:
            node: 节点实例
            state: 工作流状态
            config: 配置
            
        Returns:
            更新后的状态
        """
        result = node.execute(state, config)
        if hasattr(result.state, 'to_dict'):
            return result.state.to_dict()
        elif isinstance(result.state, dict):
            return result.state
        else:
            return {}


class UnifiedGraphBuilder:
    """统一图构建器"""
    
    def __init__(
        self,
        node_registry: Optional[NodeRegistry] = None,
        function_registry: Optional[FunctionRegistry] = None,
        enable_function_fallback: bool = True,
        enable_iteration_management: bool = True,
        graph_config: Optional[GraphConfig] = None
    ):
        """初始化统一图构建器
        
        Args:
            node_registry: 节点注册表
            function_registry: 函数注册表
            enable_function_fallback: 是否启用函数回退
            enable_iteration_management: 是否启用迭代管理
            graph_config: 图配置，用于迭代管理器
        """
        self.node_registry = node_registry or get_global_registry()
        self.function_registry = function_registry or get_global_function_registry()
        self.enable_function_fallback = enable_function_fallback
        self.enable_iteration_management = enable_iteration_management
        self.iteration_manager: Optional[IterationManager] = None
        self.graph_config = graph_config
        self.node_executor = DefaultNodeExecutor()
    
    def build_graph(self, config: GraphConfig) -> StateGraph:
        """构建图
        
        Args:
            config: 图配置
            
        Returns:
            构建好的图
        """
        graph = StateGraph(WorkflowState)
        
        # 保存配置用于迭代管理
        self.graph_config = config
        
        # 初始化迭代管理器（如果启用）
        if self.enable_iteration_management:
            self.iteration_manager = IterationManager(config)
        
        # 添加节点
        for node_config in config.nodes.values():
            self._add_node(graph, node_config)
        
        # 添加边
        for edge_config in config.edges:
            self._add_edge(graph, edge_config)
        
        # 设置入口点
        if config.entry_point:
            graph.set_entry_point(config.entry_point)
        
        return graph
    
    def _add_node(self, graph: StateGraph, node_config: NodeConfig) -> None:
        """添加节点到图
        
        Args:
            graph: 图实例
            node_config: 节点配置
        """
        # 使用 function_name 获取节点实例
        node = self.node_registry.get_node_instance(node_config.function_name)
        
        def node_function(state: WorkflowState) -> Dict[str, Any]:
            """节点函数包装器"""
            # 执行节点
            result = self.node_executor.execute_node(node, state, node_config.config)
            
            return result
        
        graph.add_node(node_config.name, node_function)
    
    def _add_edge(self, graph: StateGraph, edge_config: EdgeConfig) -> None:
        """添加边到图
        
        Args:
            graph: 图实例
            edge_config: 边配置
        """
        if edge_config.type == EdgeType.CONDITIONAL:
            # 条件边
            if edge_config.route_function is None:
                raise ValueError(f"条件边必须指定路由函数")
            route_function = self._get_route_function(edge_config.route_function)
            
            # 创建路径映射或使用默认的路径
            # LangGraph 的 add_conditional_edges 需要 dict[Hashable, str] 类型
            if edge_config.path_map:
                # 确保所有值都是字符串
                path_map_converted = {k: str(v) for k, v in edge_config.path_map.items()}  # type: ignore
                graph.add_conditional_edges(
                    edge_config.from_node,
                    route_function,
                    path_map_converted  # type: ignore
                )
            else:
                # 无路径映射，使用 None
                graph.add_conditional_edges(
                    edge_config.from_node,
                    route_function
                )
        else:
            # 普通边
            graph.add_edge(edge_config.from_node, edge_config.to_node)
    
    def _get_route_function(self, function_name: str) -> Callable:
        """获取路由函数
        
        Args:
            function_name: 函数名称
            
        Returns:
            路由函数
        """
        # 首先尝试从函数注册表获取条件函数
        function = self.function_registry.get_condition_function(function_name)
        if function:
            return function
        
        # 如果启用函数回退，尝试从路由函数管理器获取
        if self.enable_function_fallback:
            route_manager = get_route_function_manager()
            function = route_manager.get_route_function(function_name)
            if function:
                return function
        
        raise ValueError(f"未知的路由函数: {function_name}")
    
    def compile(
        self,
        graph: StateGraph,
        checkpointer: Optional[Union[InMemorySaver, SqliteSaver]] = None,
        interrupt_before: Optional[List[str]] = None,
        interrupt_after: Optional[List[str]] = None
    ) -> Any:
        """编译图
        
        Args:
            graph: 图实例
            checkpointer: 检查点保存器
            interrupt_before: 在指定节点前中断
            interrupt_after: 在指定节点后中断
            
        Returns:
            编译后的图
        """
        compile_kwargs = {}
        
        if checkpointer:
            compile_kwargs["checkpointer"] = checkpointer
        
        if interrupt_before:
            compile_kwargs["interrupt_before"] = interrupt_before
        
        if interrupt_after:
            compile_kwargs["interrupt_after"] = interrupt_after
        
        return graph.compile(**compile_kwargs)