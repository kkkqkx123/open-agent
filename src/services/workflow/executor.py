"""工作流执行器服务

提供工作流的执行服务。
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ..core.workflow.interfaces import IWorkflow, IWorkflowExecutor, IWorkflowState, ExecutionContext
from ..core.workflow.entities import Workflow, WorkflowExecution, ExecutionResult


logger = logging.getLogger(__name__)


class WorkflowExecutorService(IWorkflowExecutor):
    """工作流执行器服务
    
    提供工作流的执行能力，包括同步、异步和流式执行。
    """
    
    def __init__(self, executor: Optional[IWorkflowExecutor] = None):
        """初始化执行器服务
        
        Args:
            executor: 工作流执行器实例
        """
        self._executor = executor
        self._execution_history: Dict[str, WorkflowExecution] = {}

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
        if not self._executor:
            raise ValueError("执行器未设置")
        
        start_time = datetime.now()
        
        try:
            # 执行工作流
            result_state = self._executor.execute(workflow, initial_state, context)
            
            # 记录执行历史
            execution = WorkflowExecution(
                execution_id=context.execution_id,
                workflow_id=workflow.workflow_id,
                status="completed",
                started_at=start_time,
                completed_at=datetime.now()
            )
            
            self._execution_history[context.execution_id] = execution
            
            logger.info(f"工作流执行完成: {workflow.workflow_id} ({context.execution_id})")
            return result_state
            
        except Exception as e:
            # 记录错误
            execution = WorkflowExecution(
                execution_id=context.execution_id,
                workflow_id=workflow.workflow_id,
                status="failed",
                started_at=start_time,
                completed_at=datetime.now(),
                error=str(e)
            )
            
            self._execution_history[context.execution_id] = execution
            
            logger.error(f"工作流执行失败: {workflow.workflow_id} ({context.execution_id}): {e}")
            raise

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
        if not self._executor:
            raise ValueError("执行器未设置")
        
        start_time = datetime.now()
        
        try:
            # 异步执行工作流
            result_state = await self._executor.execute_async(workflow, initial_state, context)
            
            # 记录执行历史
            execution = WorkflowExecution(
                execution_id=context.execution_id,
                workflow_id=workflow.workflow_id,
                status="completed",
                started_at=start_time,
                completed_at=datetime.now()
            )
            
            self._execution_history[context.execution_id] = execution
            
            logger.info(f"工作流异步执行完成: {workflow.workflow_id} ({context.execution_id})")
            return result_state
            
        except Exception as e:
            # 记录错误
            execution = WorkflowExecution(
                execution_id=context.execution_id,
                workflow_id=workflow.workflow_id,
                status="failed",
                started_at=start_time,
                completed_at=datetime.now(),
                error=str(e)
            )
            
            self._execution_history[context.execution_id] = execution
            
            logger.error(f"工作流异步执行失败: {workflow.workflow_id} ({context.execution_id}): {e}")
            raise

    def get_execution_history(self, execution_id: Optional[str] = None) -> Optional[WorkflowExecution]:
        """获取执行历史
        
        Args:
            execution_id: 执行ID，如果为None则返回所有历史
            
        Returns:
            Optional[WorkflowExecution]: 执行历史，如果不存在则返回None
        """
        if execution_id:
            return self._execution_history.get(execution_id)
        return list(self._execution_history.values())

    def clear_execution_history(self) -> None:
        """清除执行历史"""
        self._execution_history.clear()
        logger.info("执行历史已清除")

    def get_executor_stats(self) -> Dict[str, Any]:
        """获取执行器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        completed_executions = [e for e in self._execution_history.values() if e.status == "completed"]
        failed_executions = [e for e in self._execution_history.values() if e.status == "failed"]
        
        return {
            "total_executions": len(self._execution_history),
            "completed_executions": len(completed_executions),
            "failed_executions": len(failed_executions),
            "success_rate": len(completed_executions) / len(self._execution_history) if self._execution_history else 0,
            "execution_history_size": len(self._execution_history)
        }