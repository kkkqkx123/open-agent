"""流式策略

提供工作流的流式执行策略实现。
"""

from src.interfaces.dependency_injection import get_logger
import asyncio
from typing import Dict, Any, Optional, List, AsyncIterator, Iterator, TYPE_CHECKING, cast
from dataclasses import dataclass, field

from .strategy_base import BaseStrategy, IExecutionStrategy

if TYPE_CHECKING:
    from src.interfaces.workflow.execution import IWorkflowExecutor
    from ..core.execution_context import ExecutionContext, ExecutionResult
    from src.interfaces.workflow.core import IWorkflow
    from src.interfaces.state.workflow import IWorkflowState

logger = get_logger(__name__)


@dataclass
class StreamingConfig:
    """流式执行配置"""
    buffer_size: int = 10  # 缓冲区大小
    include_metadata: bool = True  # 是否包含元数据
    include_timestamps: bool = True  # 是否包含时间戳
    event_types: List[str] = field(default_factory=lambda: [
        "workflow_started",
        "node_started", 
        "node_completed",
        "node_error",
        "workflow_completed"
    ])  # 要包含的事件类型


class IStreamingStrategy(IExecutionStrategy):
    """流式策略接口"""
    pass


class StreamingStrategy(BaseStrategy, IStreamingStrategy):
    """流式策略实现
    
    提供工作流的流式执行能力，实时返回执行事件。
    """
    
    def __init__(self, config: Optional[StreamingConfig] = None):
        """初始化流式策略
        
        Args:
            config: 流式执行配置
        """
        super().__init__("streaming", priority=15)
        self.config = config or StreamingConfig()
        logger.debug("流式策略初始化完成")
    
    def execute(
        self,
        executor: 'IWorkflowExecutor',
        workflow: 'IWorkflow',
        context: 'ExecutionContext'
    ) -> 'ExecutionResult':
        """使用流式策略执行工作流
        
        Args:
            executor: 工作流执行器
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        logger.debug(f"开始流式执行工作流: {workflow.config.name}")
        
        # 创建流式执行上下文
        streaming_context = self._create_streaming_context(context)
        
        # 执行流式工作流
        events = [e for e in list(self._execute_stream(executor, workflow, streaming_context)) if e is not None]
        
        # 处理最终结果
        final_result = self._process_streaming_result(events, workflow, streaming_context)
        
        logger.debug(f"流式执行完成: {workflow.config.name}, 事件数: {len(events)}")
        
        return final_result
    
    async def execute_async(
        self,
        executor: 'IWorkflowExecutor',
        workflow: 'IWorkflow',
        context: 'ExecutionContext'
    ) -> 'ExecutionResult':
        """异步使用流式策略执行工作流
        
        Args:
            executor: 工作流执行器
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        logger.debug(f"开始异步流式执行工作流: {workflow.config.name}")
        
        # 创建流式执行上下文
        streaming_context = self._create_streaming_context(context)
        
        # 异步执行流式工作流
        events = []
        async for event in self._execute_stream_async(executor, workflow, streaming_context):
            if event is not None:
                events.append(event)
        
        # 处理最终结果
        final_result = self._process_streaming_result(events, workflow, streaming_context)
        
        logger.debug(f"异步流式执行完成: {workflow.config.name}, 事件数: {len(events)}")
        
        return final_result
    
    def can_handle(self, workflow: 'IWorkflow', context: 'ExecutionContext') -> bool:
        """判断是否适用流式策略
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            bool: 是否适用流式策略
        """
        return context.get_config("streaming_enabled", False)
    
    def execute_stream(
        self,
        executor: 'IWorkflowExecutor',
        workflow: 'IWorkflow',
        context: 'ExecutionContext'
    ) -> Iterator[Dict[str, Any]]:
        """流式执行工作流（同步生成器）
        
        Args:
            executor: 工作流执行器
            workflow: 工作流实例
            context: 执行上下文
            
        Yields:
            Dict[str, Any]: 流式事件
        """
        logger.debug(f"开始流式生成器执行工作流: {workflow.config.name}")
        
        # 创建流式执行上下文
        streaming_context = self._create_streaming_context(context)
        
        # 执行流式工作流并生成事件
        yield from self._execute_stream(executor, workflow, streaming_context)
    
    async def execute_stream_async(
        self,
        executor: 'IWorkflowExecutor',
        workflow: 'IWorkflow',
        context: 'ExecutionContext'
    ) -> AsyncIterator[Dict[str, Any]]:
        """异步流式执行工作流（异步生成器）
        
        Args:
            executor: 工作流执行器
            workflow: 工作流实例
            context: 执行上下文
            
        Yields:
            Dict[str, Any]: 流式事件
        """
        logger.debug(f"开始异步流式生成器执行工作流: {workflow.config.name}")
        
        # 创建流式执行上下文
        streaming_context = self._create_streaming_context(context)
        
        # 异步执行流式工作流并生成事件
        async for event in self._execute_stream_async(executor, workflow, streaming_context):
            yield event
    
    def _create_streaming_context(self, context: 'ExecutionContext') -> 'ExecutionContext':
        """创建流式执行上下文
        
        Args:
            context: 原始执行上下文
            
        Returns:
            ExecutionContext: 流式执行上下文
        """
        # 复�贝原始上下文并添加流式配置
        # 注意：实际的ExecutionContext构造函数参数可能不同，这里进行兼容处理
        streaming_context = context.__class__(
            **{**context.__dict__, 
               "config": {**context.config, "streaming": True},
               "metadata": {**context.metadata, "streaming_enabled": True}}
        )
        
        return streaming_context
    
    def _execute_stream(
        self,
        executor: 'IWorkflowExecutor',
        workflow: 'IWorkflow',
        context: 'ExecutionContext'
    ) -> Iterator[Dict[str, Any]]:
        """执行流式工作流（同步）
        
        Args:
            executor: 工作流执行器
            workflow: 工作流实例
            context: 执行上下文
            
        Yields:
            Dict[str, Any]: 流式事件
        """
        import time
        
        # 发送开始事件
        event = self._create_event("workflow_started", {
            "workflow_name": workflow.config.name,
            "workflow_id": workflow.config.id
        })
        if event:
            yield event
        
        # 获取初始状态
        initial_data = context.get_config("initial_data") if hasattr(context, 'get_config') else None
        # 使用 WorkflowState 创建初始状态，因为新的 WorkflowInstance 没有 create_initial_state 方法
        from src.core.state.implementations.workflow_state import WorkflowState
        import uuid
        initial_state = WorkflowState(
            workflow_id=workflow.workflow_id,
            execution_id=str(uuid.uuid4()),
            data=initial_data or {}
        )
        current_state = initial_state
        current_node_id = workflow.config.entry_point
        
        # 执行工作流节点
        while current_node_id:
            current_node = None
            try:
                # 获取当前节点
                current_node = workflow.get_node(current_node_id)
                if not current_node:
                    raise ValueError(f"节点不存在: {current_node_id}")
                
                # 发送节点开始事件
                event = self._create_event("node_started", {
                    "node_id": current_node_id,
                    "node_type": getattr(current_node, 'node_type', 'unknown')
                })
                if event:
                    yield event
                
                # 执行节点
                start_time = time.time()
                node_result = current_node.execute(cast('IWorkflowState', current_state), context.config)
                execution_time = time.time() - start_time
                
                # 更新状态
                if hasattr(node_result, 'state'):
                    current_state = node_result.state
                
                # 发送节点完成事件
                event = self._create_event("node_completed", {
                    "node_id": current_node_id,
                    "node_type": getattr(current_node, 'node_type', 'unknown'),
                    "execution_time": execution_time,
                    "result": getattr(node_result, 'result', None)
                })
                if event:
                    yield event
                
                # 确定下一个节点
                if hasattr(node_result, 'next_node') and node_result.next_node:
                    current_node_id = node_result.next_node
                else:
                    # 查找出边
                    next_nodes = self._get_next_nodes(workflow, current_node_id, current_state, context.config)
                    current_node_id = next_nodes[0] if next_nodes else None
                    
            except Exception as e:
                # 发送节点错误事件
                event = self._create_event("node_error", {
                    "node_id": current_node_id,
                    "node_type": getattr(current_node, 'node_type', 'unknown') if current_node else 'unknown',
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                if event:
                    yield event
                
                # 根据配置决定是否继续
                if context.get_config("stop_on_error", True):
                    break
                else:
                    # 继续执行下一个节点
                    next_nodes = self._get_next_nodes(workflow, current_node_id, current_state, context.config)
                    current_node_id = next_nodes[0] if next_nodes else None
        
        # 发送工作流完成事件
        final_state = current_state if isinstance(current_state, dict) else (getattr(current_state, 'data', {}) if hasattr(current_state, 'data') else {})
        event = self._create_event("workflow_completed", {
            "workflow_name": workflow.config.name,
            "workflow_id": workflow.config.id,
            "final_state": final_state
        })
        if event:
            yield event
    
    async def _execute_stream_async(
        self,
        executor: 'IWorkflowExecutor',
        workflow: 'IWorkflow',
        context: 'ExecutionContext'
    ) -> AsyncIterator[Dict[str, Any]]:
        """异步执行流式工作流
        
        Args:
            executor: 工作流执行器
            workflow: 工作流实例
            context: 执行上下文
            
        Yields:
            Dict[str, Any]: 流式事件
        """
        import time
        
        # 发送开始事件
        event = self._create_event("workflow_started", {
            "workflow_name": workflow.config.name,
            "workflow_id": workflow.config.id
        })
        if event:
            yield event
        
        # 获取初始状态
        initial_data = context.get_config("initial_data") if hasattr(context, 'get_config') else None
        # 使用 WorkflowState 创建初始状态，因为新的 WorkflowInstance 没有 create_initial_state 方法
        from src.core.state.implementations.workflow_state import WorkflowState
        import uuid
        initial_state = WorkflowState(
            workflow_id=workflow.workflow_id,
            execution_id=str(uuid.uuid4()),
            data=initial_data or {}
        )
        current_state = initial_state
        current_node_id = workflow.config.entry_point
        
        # 异步执行工作流节点
        while current_node_id:
            current_node = None
            try:
                # 获取当前节点
                current_node = workflow.get_node(current_node_id)
                if not current_node:
                    raise ValueError(f"节点不存在: {current_node_id}")
                
                # 发送节点开始事件
                event = self._create_event("node_started", {
                    "node_id": current_node_id,
                    "node_type": getattr(current_node, 'node_type', 'unknown')
                })
                if event:
                    yield event
                
                # 异步执行节点
                start_time = time.time()
                if hasattr(current_node, 'execute_async'):
                    node_result = await current_node.execute_async(cast('IWorkflowState', current_state), context.config)
                else:
                    # 在线程池中执行同步节点
                    import asyncio
                    loop = asyncio.get_event_loop()
                    node_result = await loop.run_in_executor(None, current_node.execute, cast('IWorkflowState', current_state), context.config)
                
                execution_time = time.time() - start_time
                
                # 更新状态
                if hasattr(node_result, 'state'):
                    current_state = node_result.state
                
                # 发送节点完成事件
                event = self._create_event("node_completed", {
                    "node_id": current_node_id,
                    "node_type": getattr(current_node, 'node_type', 'unknown'),
                    "execution_time": execution_time,
                    "result": getattr(node_result, 'result', None)
                })
                if event:
                    yield event
                
                # 确定下一个节点
                if hasattr(node_result, 'next_node') and node_result.next_node:
                    current_node_id = node_result.next_node
                else:
                    # 查找出边
                    next_nodes = await self._get_next_nodes_async(workflow, current_node_id, current_state, context.config)
                    current_node_id = next_nodes[0] if next_nodes else None
                    
            except Exception as e:
                # 发送节点错误事件
                event = self._create_event("node_error", {
                    "node_id": current_node_id,
                    "node_type": getattr(current_node, 'node_type', 'unknown') if current_node else 'unknown',
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                if event:
                    yield event
                
                # 根据配置决定是否继续
                if context.get_config("stop_on_error", True):
                    break
                else:
                    # 继续执行下一个节点
                    next_nodes = await self._get_next_nodes_async(workflow, current_node_id, current_state, context.config)
                    current_node_id = next_nodes[0] if next_nodes else None
        
        # 发送工作流完成事件
        final_state = current_state if isinstance(current_state, dict) else (getattr(current_state, 'data', {}) if hasattr(current_state, 'data') else {})
        event = self._create_event("workflow_completed", {
            "workflow_name": workflow.config.name,
            "workflow_id": workflow.config.id,
            "final_state": final_state
        })
        if event:
            yield event
    
    def _create_event(self, event_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建流式事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            Optional[Dict[str, Any]]: 流式事件，如果事件类型被过滤则返回None
        """
        import time
        
        event = {
            "type": event_type,
            "data": data
        }
        
        # 添加时间戳
        if self.config.include_timestamps:
            event["timestamp"] = time.time()
        
        # 添加元数据
        if self.config.include_metadata:
            event["metadata"] = {
                "streaming_config": {
                    "buffer_size": self.config.buffer_size,
                    "include_metadata": self.config.include_metadata,
                    "include_timestamps": self.config.include_timestamps
                }
            }
        
        # 过滤事件类型
        if event_type not in self.config.event_types:
            return None
        
        return event
    
    def _process_streaming_result(
        self,
        events: List[Dict[str, Any]],
        workflow: 'IWorkflow',
        context: 'ExecutionContext'
    ) -> 'ExecutionResult':
        """处理流式执行结果
        
        Args:
            events: 流式事件列表（仅包含非None事件）
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 事件列表已经被过滤，只包含非None值
        valid_events = events
        
        # 检查是否有错误
        error_events = [e for e in valid_events if e["type"] == "node_error"]
        success = len(error_events) == 0
        
        # 获取最终状态
        final_state = {}
        completed_event = next((e for e in valid_events if e["type"] == "workflow_completed"), None)
        if completed_event:
            final_state = completed_event["data"].get("final_state", {})
        
        # 统计信息
        node_started_events = [e for e in valid_events if e["type"] == "node_started"]
        node_completed_events = [e for e in valid_events if e["type"] == "node_completed"]
        
        return self.create_execution_result(
            success=success,
            result=final_state,
            error=error_events[0]["data"]["error"] if error_events else None,
            metadata={
                "streaming": True,
                "total_events": len(valid_events),
                "total_nodes": len(node_started_events),
                "completed_nodes": len(node_completed_events),
                "error_nodes": len(error_events),
                "event_types": list(set(e["type"] for e in valid_events))
            }
        )
    
    def _get_next_nodes(
        self,
        workflow: 'IWorkflow',
        node_id: str,
        state: Any,
        config: Dict[str, Any]
    ) -> List[str]:
        """获取下一个节点列表（同步）
        
        Args:
            workflow: 工作流实例
            node_id: 当前节点ID
            state: 当前状态
            config: 配置
            
        Returns:
            List[str]: 下一个节点ID列表
        """
        # 简化实现，实际应该根据工作流的边定义来查找
        # 使用 WorkflowInstanceCoordinator 来获取下一个节点
        from ..executor import WorkflowExecutor
        executor = WorkflowExecutor()
        # 简化实现，返回空列表，实际应该根据工作流的边定义来查找
        return []
        return []
    
    async def _get_next_nodes_async(
        self,
        workflow: 'IWorkflow',
        node_id: str,
        state: Any,
        config: Dict[str, Any]
    ) -> List[str]:
        """获取下一个节点列表（异步）
        
        Args:
            workflow: 工作流实例
            node_id: 当前节点ID
            state: 当前状态
            config: 配置
            
        Returns:
            List[str]: 下一个节点ID列表
        """
        # 简化实现，实际应该根据工作流的边定义来查找
        # 使用 WorkflowInstanceCoordinator 来获取下一个节点
        from ..executor import WorkflowExecutor
        executor = WorkflowExecutor()
        # 简化实现，返回空列表，实际应该根据工作流的边定义来查找
        return []
