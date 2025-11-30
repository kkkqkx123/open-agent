"""LangGraph工作流定义和管理"""

from typing import Any, Dict, List, Optional, Callable, AsyncGenerator
from abc import ABC, abstractmethod
import logging
from datetime import datetime
import asyncio

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.base import BaseCheckpointSaver

from .state import LangGraphState, create_initial_state, update_state_version

logger = logging.getLogger(__name__)


class ILangGraphWorkflow(ABC):
    """LangGraph工作流接口"""
    
    @property
    @abstractmethod
    def workflow_id(self) -> str:
        """工作流ID"""
        pass
    
    @property
    @abstractmethod
    def state_graph(self) -> StateGraph:
        """LangGraph StateGraph实例"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        """工作流描述"""
        pass
    
    @property
    @abstractmethod
    def state_schema(self) -> type:
        """状态schema类型"""
        pass
    
    @abstractmethod
    async def compile(self, checkpointer: Optional[BaseCheckpointSaver] = None) -> Any:
        """编译LangGraph工作流"""
        pass
    
    @abstractmethod
    async def execute(
        self,
        input_data: Dict[str, Any],
        config: Dict[str, Any],
        stream: bool = False
    ) -> Any:
        """执行工作流"""
        pass


class LangGraphWorkflow(ILangGraphWorkflow):
    """LangGraph工作流实现"""
    
    def __init__(
        self,
        workflow_id: str,
        state_schema: type = LangGraphState,
        description: Optional[str] = None
    ):
        self._workflow_id = workflow_id
        self._description = description
        self._state_schema = state_schema
        self._nodes: Dict[str, Callable] = {}
        self._edges: List[tuple] = []
        self._conditional_edges: List[tuple] = []
        self._entry_point: Optional[str] = None
        self._compiled_graph: Optional[Any] = None
        
        # 创建StateGraph
        self._state_graph = StateGraph(state_schema)
        
        # 添加默认节点
        self._add_default_nodes()
    
    @property
    def workflow_id(self) -> str:
        return self._workflow_id
    
    @property
    def state_graph(self) -> StateGraph:
        return self._state_graph
    
    @property
    def description(self) -> Optional[str]:
        return self._description
    
    @property
    def state_schema(self) -> type:
        return self._state_schema
    
    def add_node(self, name: str, func: Callable, description: Optional[str] = None):
        """添加节点"""
        self._nodes[name] = func
        self._state_graph.add_node(name, func)
        logger.debug(f"Added node '{name}' to workflow '{self._workflow_id}'")
    
    def add_edge(self, start: str, end: str):
        """添加边"""
        self._edges.append((start, end))
        self._state_graph.add_edge(start, end)
        logger.debug(f"Added edge '{start}' -> '{end}' to workflow '{self._workflow_id}'")
    
    def add_conditional_edge(
        self, 
        start: str, 
        condition: Callable, 
        mapping: Dict[str, str]
    ):
        """添加条件边"""
        self._conditional_edges.append((start, condition, mapping))
        # 转换mapping为可接受的类型（dict[Hashable, str]）
        self._state_graph.add_conditional_edges(start, condition, dict(mapping))  # type: ignore[arg-type]
        logger.debug(f"Added conditional edge from '{start}' in workflow '{self._workflow_id}'")
    
    def set_entry_point(self, node_name: str):
        """设置入口点"""
        self._entry_point = node_name
        self._state_graph.set_entry_point(node_name)
        logger.debug(f"Set entry point to '{node_name}' for workflow '{self._workflow_id}'")
    
    def set_finish_point(self, node_name: str):
        """设置结束点"""
        self._state_graph.add_edge(node_name, END)
        logger.debug(f"Set finish point to '{node_name}' for workflow '{self._workflow_id}'")
    
    async def compile(self, checkpointer: Optional[BaseCheckpointSaver] = None) -> Any:
        """编译LangGraph工作流"""
        try:
            # 验证工作流配置
            self._validate_workflow()
            
            # 编译工作流
            compile_kwargs = {}
            if checkpointer:
                compile_kwargs["checkpointer"] = checkpointer
            
            self._compiled_graph = self._state_graph.compile(**compile_kwargs)
            
            logger.info(f"Successfully compiled workflow '{self._workflow_id}'")
            return self._compiled_graph
            
        except Exception as e:
            logger.error(f"Failed to compile workflow '{self._workflow_id}': {str(e)}")
            raise
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        config: Dict[str, Any],
        stream: bool = False
    ) -> Any:
        """执行工作流"""
        if not self._compiled_graph:
            raise RuntimeError(f"Workflow '{self._workflow_id}' must be compiled before execution")
        
        try:
            # 准备输入数据
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                raise ValueError("thread_id is required in config")
            
            # 创建初始状态
            initial_state_obj = create_initial_state(thread_id, self._workflow_id)
            initial_state = dict(initial_state_obj) | input_data  # type: ignore[assignment]
            
            # 执行工作流
            if stream:
                return self._stream_execute(initial_state, config)
            else:
                return await self._invoke_execute(initial_state, config)
                
        except Exception as e:
            logger.error(f"Error executing workflow '{self._workflow_id}': {str(e)}")
            raise
    
    async def _invoke_execute(self, initial_state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """同步执行工作流"""
        logger.info(f"Invoking workflow '{self._workflow_id}' with thread {config['configurable']['thread_id']}")
        
        if self._compiled_graph is None:
            raise RuntimeError(f"Compiled graph is None for workflow '{self._workflow_id}'")
        
        result = await self._compiled_graph.ainvoke(initial_state, config)
        
        logger.info(f"Workflow '{self._workflow_id}' completed successfully")
        return result
    
    async def _stream_execute(
        self, 
        initial_state: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行工作流"""
        logger.info(f"Streaming workflow '{self._workflow_id}' with thread {config['configurable']['thread_id']}")
        
        if self._compiled_graph is None:
            raise RuntimeError(f"Compiled graph is None for workflow '{self._workflow_id}'")
        
        async for chunk in self._compiled_graph.astream(initial_state, config):
            yield chunk
        
        logger.info(f"Workflow '{self._workflow_id}' streaming completed")
    
    def _add_default_nodes(self):
        """添加默认节点"""
        # 开始节点
        def start_node(state: LangGraphState) -> LangGraphState:
            logger.debug(f"Starting workflow '{self._workflow_id}' for thread {state['thread_id']}")
            state["current_step"] = "started"
            return update_state_version(state)
        
        # 结束节点
        def end_node(state: LangGraphState) -> LangGraphState:
            logger.debug(f"Ending workflow '{self._workflow_id}' for thread {state['thread_id']}")
            state["current_step"] = "completed"
            return update_state_version(state)
        
        # 错误处理节点
        def error_node(state: LangGraphState) -> LangGraphState:
            logger.error(f"Error in workflow '{self._workflow_id}' for thread {state['thread_id']}")
            state["current_step"] = "error"
            return update_state_version(state)
        
        self.add_node("start", start_node, "工作流开始")
        self.add_node("end", end_node, "工作流结束")
        self.add_node("error", error_node, "错误处理")
        
        # 设置默认入口点
        if not self._entry_point:
            self.set_entry_point("start")
    
    def _validate_workflow(self):
        """验证工作流配置"""
        if not self._nodes:
            raise ValueError("Workflow must have at least one node")
        
        if not self._entry_point:
            raise ValueError("Workflow must have an entry point")
        
        # 验证节点引用
        all_nodes = set(self._nodes.keys())
        
        # 验证边
        for start, end in self._edges:
            if start not in all_nodes:
                raise ValueError(f"Edge references unknown node: {start}")
            if end not in all_nodes:
                raise ValueError(f"Edge references unknown node: {end}")
        
        # 验证条件边
        for start, condition, mapping in self._conditional_edges:
            if start not in all_nodes:
                raise ValueError(f"Conditional edge references unknown node: {start}")
            for target in mapping.values():
                if target not in all_nodes and target != END:
                    raise ValueError(f"Conditional edge mapping references unknown node: {target}")


class WorkflowBuilder:
    """工作流构建器 - 简化工作流创建"""
    
    def __init__(self, workflow_id: str):
        self.workflow = LangGraphWorkflow(workflow_id)
    
    def start_with(self, node_name: str, func: Callable) -> 'WorkflowBuilder':
        """设置起始节点"""
        self.workflow.add_node(node_name, func)
        self.workflow.set_entry_point(node_name)
        return self
    
    def then(self, node_name: str, func: Callable) -> 'WorkflowBuilder':
        """添加下一个节点"""
        self.workflow.add_node(node_name, func)
        # 自动连接到上一个节点
        if self.workflow._entry_point:
            last_node = node_name
            # 这里需要跟踪上一个节点，简化实现
        return self
    
    def connect(self, from_node: str, to_node: str) -> 'WorkflowBuilder':
        """连接两个节点"""
        self.workflow.add_edge(from_node, to_node)
        return self
    
    def branch_when(
        self, 
        node_name: str, 
        condition: Callable, 
        mapping: Dict[str, str]
    ) -> 'WorkflowBuilder':
        """添加条件分支"""
        self.workflow.add_conditional_edge(node_name, condition, mapping)
        return self
    
    def end_with(self, node_name: str, func: Callable) -> 'WorkflowBuilder':
        """设置结束节点"""
        self.workflow.add_node(node_name, func)
        self.workflow.set_finish_point(node_name)
        return self
    
    def build(self) -> LangGraphWorkflow:
        """构建工作流"""
        return self.workflow


# 便捷函数
def create_simple_workflow(
    workflow_id: str,
    nodes: Dict[str, Callable],
    edges: List[tuple],
    entry_point: Optional[str] = None
) -> LangGraphWorkflow:
    """创建简单工作流"""
    workflow = LangGraphWorkflow(workflow_id)
    
    # 添加节点
    for name, func in nodes.items():
        workflow.add_node(name, func)
    
    # 添加边
    for start, end in edges:
        workflow.add_edge(start, end)
    
    # 设置入口点
    if entry_point:
        workflow.set_entry_point(entry_point)
    
    return workflow