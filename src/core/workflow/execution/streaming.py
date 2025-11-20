"""流式执行器

提供工作流的流式执行能力。
"""

import asyncio
from typing import Dict, Any, List, AsyncIterator, Optional, AsyncGenerator
from .interfaces import IStreamingExecutor
from ..interfaces import IWorkflow, IWorkflowState, ExecutionContext


class StreamingExecutor(IStreamingExecutor):
    """流式执行器
    
    提供工作流的流式执行能力，实时返回执行事件。
    """
    
    def __init__(self):
        """初始化流式执行器"""
        self._execution_context: Optional[ExecutionContext] = None

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
        self._execution_context = context
        
        # 获取入口点
        if not workflow._entry_point:
            raise ValueError("工作流未设置入口点")
        
        events = []
        current_node_id = workflow._entry_point
        current_state = initial_state
        
        # 添加开始事件
        events.append({
            "type": "workflow_started",
            "workflow_id": context.workflow_id,
            "execution_id": context.execution_id,
            "timestamp": self._get_timestamp()
        })
        
        while current_node_id:
            # 获取当前节点
            current_node = workflow.get_node(current_node_id)
            if not current_node:
                raise ValueError(f"节点不存在: {current_node_id}")
            
            # 添加节点开始事件
            events.append({
                "type": "node_started",
                "node_id": current_node_id,
                "node_type": current_node.node_type,
                "timestamp": self._get_timestamp()
            })
            
            # 执行节点
            try:
                result = current_node.execute(current_state, context.config)
                current_state = result.state
                
                # 添加节点完成事件
                events.append({
                    "type": "node_completed",
                    "node_id": current_node_id,
                    "node_type": current_node.node_type,
                    "result": result.metadata,
                    "timestamp": self._get_timestamp()
                })
                
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
                events.append({
                    "type": "node_error",
                    "node_id": current_node_id,
                    "node_type": current_node.node_type,
                    "error": str(e),
                    "timestamp": self._get_timestamp()
                })
                
                # 处理执行错误
                current_state.set_data("error", str(e))
                current_node_id = None  # 终止工作流
        
        # 添加工作流结束事件
        events.append({
            "type": "workflow_completed",
            "workflow_id": context.workflow_id,
            "execution_id": context.execution_id,
            "final_state": current_state.get_data("error") is None,
            "timestamp": self._get_timestamp()
        })
        
        return events

    async def execute_stream_async(self, workflow: IWorkflow, initial_state: IWorkflowState,
                              context: ExecutionContext) -> AsyncIterator[Dict[str, Any]]:
        """异步流式执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Yields:
            Dict[str, Any]: 执行事件
        """
        self._execution_context = context
        
        # 获取入口点
        if not workflow._entry_point:
            raise ValueError("工作流未设置入口点")
        
        # 发送开始事件
        yield {
            "type": "workflow_started",
            "workflow_id": context.workflow_id,
            "execution_id": context.execution_id,
            "timestamp": self._get_timestamp()
        }
        
        current_node_id = workflow._entry_point
        current_state = initial_state
        
        while current_node_id:
            # 获取当前节点
            current_node = workflow.get_node(current_node_id)
            if not current_node:
                raise ValueError(f"节点不存在: {current_node_id}")
            
            # 发送节点开始事件
            yield {
                "type": "node_started",
                "node_id": current_node_id,
                "node_type": current_node.node_type,
                "timestamp": self._get_timestamp()
            }
            
            # 异步执行节点
            try:
                result = await current_node.execute_async(current_state, context.config)
                current_state = result.state
                
                # 发送节点完成事件
                yield {
                    "type": "node_completed",
                    "node_id": current_node_id,
                    "node_type": current_node.node_type,
                    "result": result.metadata,
                    "timestamp": self._get_timestamp()
                }
                
                # 确定下一个节点
                if result.next_node:
                    current_node_id = result.next_node
                else:
                    # 查找出边
                    next_nodes = await self._get_next_nodes_async(workflow, current_node_id, current_state, context.config)
                    if next_nodes:
                        current_node_id = next_nodes[0]  # 简单选择第一个
                    else:
                        current_node_id = None  # 工作流结束
            except Exception as e:
                # 发送节点错误事件
                yield {
                    "type": "node_error",
                    "node_id": current_node_id,
                    "node_type": current_node.node_type,
                    "error": str(e),
                    "timestamp": self._get_timestamp()
                }
                
                # 处理执行错误
                current_state.set_data("error", str(e))
                current_node_id = None  # 终止工作流
        
        # 发送工作流结束事件
        yield {
            "type": "workflow_completed",
            "workflow_id": context.workflow_id,
            "execution_id": context.execution_id,
            "final_state": current_state.get_data("error") is None,
            "timestamp": self._get_timestamp()
        }

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
        next_nodes = []
        
        # 获取所有出边
        for edge in workflow._edges.values():
            if edge.from_node == node_id:
                # 检查是否可以遍历
                if edge.can_traverse(state, config):
                    next_node_ids = edge.get_next_nodes(state, config)
                    next_nodes.extend(next_node_ids)
        
        return next_nodes

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
        next_nodes = []
        
        # 获取所有出边
        for edge in workflow._edges.values():
            if edge.from_node == node_id:
                # 检查是否可以遍历
                if hasattr(edge, 'can_traverse_async'):
                    can_traverse = await edge.can_traverse_async(state, config)
                else:
                    can_traverse = edge.can_traverse(state, config)
                
                if can_traverse:
                    if hasattr(edge, 'get_next_nodes_async'):
                        next_node_ids = await edge.get_next_nodes_async(state, config)
                    else:
                        next_node_ids = edge.get_next_nodes(state, config)
                    next_nodes.extend(next_node_ids)
        
        return next_nodes

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()