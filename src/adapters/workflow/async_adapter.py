"""异步工作流适配器

提供工作流的异步执行能力。
"""

from typing import Dict, Any, Optional, AsyncIterator, cast
import logging
from datetime import datetime

from src.core.workflow.interfaces import IWorkflow, IWorkflowExecutor, ExecutionContext
from src.state.interfaces import IState


logger = logging.getLogger(__name__)


class AsyncWorkflowAdapter:
    """异步工作流适配器
    
    提供工作流的异步执行能力，支持并发控制和流式处理。
    """
    
    def __init__(self, executor: Optional[IWorkflowExecutor] = None):
        """初始化异步适配器
        
        Args:
            executor: 工作流执行器
        """
        self.executor = executor

    async def execute_workflow_async(self, workflow: IWorkflow, initial_state: IState,
                                context: ExecutionContext) -> IState:
        """异步执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Returns:
            IWorkflowState: 执行结果状态
        """
        if not self.executor:
            raise ValueError("执行器未设置")
        
        start_time = datetime.now()
        
        try:
            # 异步执行工作流
            result_state = await self.executor.execute_async(workflow, initial_state, context)
            
            # 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"异步工作流执行完成: {workflow.workflow_id} ({context.execution_id})，耗时: {execution_time:.2f}s")
            
            return result_state
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"异步工作流执行失败: {workflow.workflow_id} ({context.execution_id})，耗时: {execution_time:.2f}s，错误: {e}")
            raise

    async def execute_workflow_stream(self, workflow: IWorkflow, initial_state: IState,
                                   context: ExecutionContext) -> AsyncIterator[Dict[str, Any]]:
        """异步流式执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            context: 执行上下文
            
        Yields:
            Dict[str, Any]: 执行事件
        """
        if not self.executor:
            raise ValueError("执行器未设置")
        
        start_time = datetime.now()
        
        try:
            # 发送开始事件
            yield {
                "type": "workflow_started",
                "workflow_id": workflow.workflow_id,
                "execution_id": context.execution_id,
                "timestamp": start_time.isoformat()
            }
            
            # 异步流式执行工作流
            try:
                stream = cast(AsyncIterator[Dict[str, Any]], self.executor.execute_stream_async(workflow, initial_state, context))
                async for event in stream:
                    yield event
            except (AttributeError, TypeError):
                # 回退到同步执行
                result_state = await self.executor.execute_async(workflow, initial_state, context)
                
                # 发送完成事件
                result_data = {}
                if hasattr(result_state, 'to_dict'):
                    result_data = result_state.to_dict()
                elif isinstance(result_state, dict):
                    result_data = result_state
                
                yield {
                    "type": "workflow_completed",
                    "workflow_id": workflow.workflow_id,
                    "execution_id": context.execution_id,
                    "timestamp": datetime.now().isoformat(),
                    "result": result_data
                }
            
            # 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"异步流式工作流执行完成: {workflow.workflow_id} ({context.execution_id})，耗时: {execution_time:.2f}s")
            
        except Exception as e:
            # 发送错误事件
            yield {
                "type": "workflow_error",
                "workflow_id": workflow.workflow_id,
                "execution_id": context.execution_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"异步流式工作流执行失败: {workflow.workflow_id} ({context.execution_id})，耗时: {execution_time:.2f}s，错误: {e}")

    def configure(self, config: Dict[str, Any]) -> None:
        """配置适配器
        
        Args:
            config: 配置字典
        """
        # 这里可以添加配置逻辑
        logger.info(f"配置异步工作流适配器: {config}")

    def get_adapter_stats(self) -> Dict[str, Any]:
        """获取适配器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "executor_type": type(self.executor).__name__ if self.executor else "None",
            "configured": True
        }