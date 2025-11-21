"""异步执行模式

提供工作流的异步执行模式实现。
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, TYPE_CHECKING

from .mode_base import BaseMode, IExecutionMode

if TYPE_CHECKING:
    from ...interfaces.state import IWorkflowState
    from ...interfaces.workflow.core import INode
    from ..core.execution_context import ExecutionContext, NodeResult

logger = logging.getLogger(__name__)


class IAsyncMode(IExecutionMode):
    """异步模式接口"""
    pass


class AsyncMode(BaseMode, IAsyncMode):
    """异步执行模式
    
    提供节点的异步执行能力，支持原生异步节点和同步节点的异步包装。
    """
    
    def __init__(self):
        """初始化异步模式"""
        super().__init__("async", supports_async=True)
        logger.debug("异步执行模式初始化完成")
    
    def execute_node(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: 'ExecutionContext'
    ) -> 'NodeResult':
        """同步执行节点（异步模式的同步实现）
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Returns:
            NodeResult: 节点执行结果
        """
        # 在新的事件循环中运行异步执行
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在运行的事件循环中，使用 run_in_executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        self.execute_node_async(node, state, context)
                    )
                    return future.result()
            else:
                # 如果没有运行的事件循环，直接运行
                return asyncio.run(self.execute_node_async(node, state, context))
        except Exception as e:
            logger.error(f"异步模式同步执行失败: {e}")
            return self.handle_execution_error(e, node, state)
    
    async def execute_node_async(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: 'ExecutionContext'
    ) -> 'NodeResult':
        """异步执行节点
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Returns:
            NodeResult: 节点执行结果
        """
        start_time = time.time()
        
        try:
            # 验证输入
            self.validate_inputs(node, state, context)
            
            logger.debug(f"异步执行节点: {getattr(node, 'node_id', 'unknown')}")
            
            # 检查节点是否支持异步执行
            if hasattr(node, 'execute_async'):
                # 节点原生支持异步执行
                node_result = await node.execute_async(state, context.config)
            else:
                # 在线程池中执行同步节点
                loop = asyncio.get_event_loop()
                node_result = await loop.run_in_executor(None, node.execute, state, context.config)
            
            # 处理执行结果
            result = self._process_node_result(node_result, state, context)
            
            # 设置执行时间
            result.execution_time = time.time() - start_time
            
            logger.debug(f"节点异步执行完成: {getattr(node, 'node_id', 'unknown')}, 耗时: {result.execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"节点异步执行失败: {e}")
            
            return self.handle_execution_error(e, node, state)
    
    def supports_streaming(self) -> bool:
        """是否支持流式执行
        
        Returns:
            bool: 支持流式执行
        """
        return True
    
    async def execute_node_stream(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: 'ExecutionContext'
    ):
        """流式执行节点
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Yields:
            Dict[str, Any]: 流式事件
        """
        import time
        
        # 发送开始事件
        yield {
            "type": "node_started",
            "data": {
                "node_id": getattr(node, 'node_id', 'unknown'),
                "node_type": getattr(node, 'node_type', 'unknown'),
                "timestamp": time.time()
            }
        }
        
        try:
            # 检查节点是否支持流式执行
            if hasattr(node, 'execute_stream_async'):
                # 节点原生支持异步流式执行
                async for event in node.execute_stream_async(state, context.config):
                    yield event
            elif hasattr(node, 'execute_stream'):
                # 节点支持同步流式执行，转换为异步
                import asyncio
                loop = asyncio.get_event_loop()
                
                def sync_generator():
                    return node.execute_stream(state, context.config)
                
                gen = sync_generator()
                while True:
                    try:
                        event = await loop.run_in_executor(None, next, gen)
                        yield event
                    except StopIteration:
                        break
            else:
                # 普通节点，执行完成后发送完成事件
                result = await self.execute_node_async(node, state, context)
                
                yield {
                    "type": "node_completed",
                    "data": {
                        "node_id": getattr(node, 'node_id', 'unknown'),
                        "node_type": getattr(node, 'node_type', 'unknown'),
                        "result": result.metadata,
                        "timestamp": time.time()
                    }
                }
                
        except Exception as e:
            # 发送错误事件
            yield {
                "type": "node_error",
                "data": {
                    "node_id": getattr(node, 'node_id', 'unknown'),
                    "node_type": getattr(node, 'node_type', 'unknown'),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": time.time()
                }
            }
    
    def _process_node_result(
        self, 
        node_result: Any, 
        original_state: 'IWorkflowState', 
        context: 'ExecutionContext'
    ) -> 'NodeResult':
        """处理节点执行结果
        
        Args:
            node_result: 节点执行结果
            original_state: 原始状态
            context: 执行上下文
            
        Returns:
            NodeResult: 处理后的节点执行结果
        """
        # 提取状态
        if hasattr(node_result, 'state'):
            final_state = node_result.state
        elif isinstance(node_result, dict):
            # 如果返回的是字典，尝试更新状态
            final_state = original_state
            for key, value in node_result.items():
                if hasattr(final_state, key):
                    setattr(final_state, key, value)
                else:
                    final_state.set_data(key, value)
        else:
            # 其他情况，保持原始状态
            final_state = original_state
        
        # 提取下一个节点
        next_node = None
        if hasattr(node_result, 'next_node'):
            next_node = node_result.next_node
        elif isinstance(node_result, dict):
            next_node = node_result.get('next_node')
        
        # 提取元数据
        metadata = {}
        if hasattr(node_result, 'metadata'):
            metadata = node_result.metadata
        elif isinstance(node_result, dict):
            metadata = node_result.get('metadata', {})
        
        # 添加节点信息到元数据
        metadata.update({
            "node_id": getattr(node_result, 'node_id', getattr(original_state, 'current_node_id', 'unknown')),
            "node_type": getattr(node_result, 'node_type', 'unknown'),
            "execution_timestamp": time.time(),
            "execution_mode": "async"
        })
        
        return self.create_node_result(
            success=True,
            state=final_state,
            next_node=next_node,
            metadata=metadata
        )