"""执行器实现

提供工作流执行器的基础实现。
"""

import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from src.interfaces.workflow.core import IWorkflow, ExecutionContext
from src.interfaces.state import IWorkflowState, IState
from .base import BaseExecutor
from .utils import NextNodesResolver


class WorkflowExecutor(BaseExecutor):
    """工作流执行器
    
    提供同步、异步和流式执行能力。
    """
    
    def __init__(self):
        """初始化执行器"""
        super().__init__()

    def execute(self, workflow: IWorkflow, initial_state: IWorkflowState,
                context: ExecutionContext) -> IWorkflowState:
        """执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        self._set_execution_context(context)
        self._validate_workflow(workflow)
        
        current_node_id = workflow.entry_point
        current_state: IWorkflowState = initial_state
        
        while current_node_id:
            # 获取当前节点
            current_node = workflow.get_node(current_node_id)
            if not current_node:
                raise ValueError(f"节点不存在: {current_node_id}")
            
            # 执行节点
            try:
                result = current_node.execute(current_state, context.config)
                current_state = result.state  # type: ignore
                
                # 确定下一个节点
                if result.next_node:
                    current_node_id = result.next_node
                else:
                    # 查找出边
                    next_nodes = self._get_next_nodes(workflow, current_node_id, current_state, context.config)
                    if next_nodes:
                        current_node_id = next_nodes[0]  # 简单选择第一个
                    else:
                        current_node_id = None  # 工作流结束
            except Exception as e:
                # 处理执行错误
                current_state.set_data("error", str(e))
                current_node_id = None  # 终止工作流
        
        return current_state

    async def execute_async(self, workflow: IWorkflow, initial_state: IWorkflowState,
                           context: ExecutionContext) -> IWorkflowState:
        """异步执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        self._set_execution_context(context)
        self._validate_workflow(workflow)
        
        current_node_id = workflow.entry_point
        current_state: IWorkflowState = initial_state
        
        while current_node_id:
            # 获取当前节点
            current_node = workflow.get_node(current_node_id)
            if not current_node:
                raise ValueError(f"节点不存在: {current_node_id}")
            
            # 异步执行节点
            try:
                result = await current_node.execute_async(current_state, context.config)
                current_state = result.state  # type: ignore
                
                # 确定下一个节点
                if result.next_node:
                    current_node_id = result.next_node
                else:
                    # 异步查找出边
                    next_nodes = await self._get_next_nodes_async(workflow, current_node_id, current_state, context.config)
                    if next_nodes:
                        current_node_id = next_nodes[0]  # 简单选择第一个
                    else:
                        current_node_id = None  # 工作流结束
            except Exception as e:
                # 处理执行错误
                current_state.set_data("error", str(e))
                current_node_id = None  # 终止工作流
        
        return current_state

    def execute_stream(self, workflow: IWorkflow, initial_state: IWorkflowState,
                       context: ExecutionContext) -> List[Dict[str, Any]]:
        """流式执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            List[Dict[str, Any]]: 执行事件列表
        """
        events = []
        
        self._set_execution_context(context)
        self._validate_workflow(workflow)
        
        current_node_id = workflow.entry_point
        current_state = initial_state
        
        # 添加开始事件
        events.append(self._create_workflow_started_event())
        
        while current_node_id:
            # 获取当前节点
            current_node = self._get_node(workflow, current_node_id)
            
            # 添加节点开始事件
            events.append(self._create_node_started_event(
                current_node_id, current_node.node_type
            ))
            
            # 执行节点
            try:
                result = current_node.execute(current_state, context.config)
                current_state = result.state
                
                # 添加节点完成事件
                events.append(self._create_node_completed_event(
                    current_node_id, current_node.node_type, result.metadata
                ))
                
                # 确定下一个节点
                if result.next_node:
                    current_node_id = result.next_node
                else:
                    # 查找出边
                    next_nodes = self._get_next_nodes(workflow, current_node_id, current_state, context.config)
                    if next_nodes:
                        current_node_id = next_nodes[0]  # 简单选择第一个
                    else:
                        current_node_id = None  # 工作流结束
            except Exception as e:
                # 添加节点错误事件
                events.append(self._create_node_error_event(
                    current_node_id, current_node.node_type, e
                ))
                
                # 处理执行错误
                current_state.set_data("error", str(e))
                current_node_id = None  # 终止工作流
        
        # 添加工作流结束事件
        events.append(self._create_workflow_completed_event(current_state))
        
        return events

    def _get_next_nodes(self, workflow: IWorkflow, node_id: str,
                        state: IWorkflowState, config: Dict[str, Any]) -> List[str]:
        """获取下一个节点列表
        
        Args:
            workflow: 工作流实例
            node_id: 当前节点ID
            state: 当前状态
            config: 配置
            
        Returns:
            List[str]: 下一个节点ID列表
        """
        return NextNodesResolver.get_next_nodes(workflow, node_id, state, config)

    async def _get_next_nodes_async(self, workflow: IWorkflow, node_id: str,
                                state: IWorkflowState, config: Dict[str, Any]) -> List[str]:
        """异步获取下一个节点列表
        
        Args:
            workflow: 工作流实例
            node_id: 当前节点ID
            state: 当前状态
            config: 配置
            
        Returns:
            List[str]: 下一个节点ID列表
        """
        return await NextNodesResolver.get_next_nodes_async(workflow, node_id, state, config)

    async def execute_stream_async(  # type: ignore[override]
        self, workflow: IWorkflow, initial_state: IWorkflowState,
        context: ExecutionContext
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """异步流式执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Yields:
            Dict[str, Any]: 执行事件
        """
        self._set_execution_context(context)
        self._validate_workflow(workflow)
        
        # 添加开始事件
        yield self._create_workflow_started_event()
        
        current_node_id = workflow.entry_point
        current_state = initial_state
        
        while current_node_id:
            # 获取当前节点
            current_node = self._get_node(workflow, current_node_id)
            
            # 添加节点开始事件
            yield self._create_node_started_event(
                current_node_id, current_node.node_type
            )
            
            # 异步执行节点
            try:
                result = await current_node.execute_async(current_state, context.config)
                current_state = result.state
                
                # 添加节点完成事件
                yield self._create_node_completed_event(
                    current_node_id, current_node.node_type, result.metadata
                )
                
                # 确定下一个节点
                if result.next_node:
                    current_node_id = result.next_node
                else:
                    # 异步查找出边
                    next_nodes = await self._get_next_nodes_async(workflow, current_node_id, current_state, context.config)
                    if next_nodes:
                        current_node_id = next_nodes[0]  # 简单选择第一个
                    else:
                        current_node_id = None  # 工作流结束
            except Exception as e:
                # 添加节点错误事件
                yield self._create_node_error_event(
                    current_node_id, current_node.node_type, e
                )
                
                # 处理执行错误
                current_state.set_data("error", str(e))
                current_node_id = None # 终止工作流
        
        # 添加工作流结束事件
        yield self._create_workflow_completed_event(current_state)