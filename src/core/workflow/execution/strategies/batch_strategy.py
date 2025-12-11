"""批量策略

提供工作流的批量执行策略实现。
"""

from src.interfaces.dependency_injection import get_logger
import asyncio
import concurrent.futures
from typing import TYPE_CHECKING, Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.core.workflow.execution.core.execution_context import BatchExecutionResult, ExecutionResult, NodeResult

from .strategy_base import BaseStrategy, IExecutionStrategy

if TYPE_CHECKING:
    from src.interfaces.workflow.execution import IWorkflowExecutor
    from ..core.execution_context import ExecutionContext, BatchJob
    from src.interfaces.workflow.core import IWorkflow
    from src.interfaces.state import IWorkflowState

logger = get_logger(__name__)

# 添加状态工厂导入
from src.core.state.factories.state_factory import create_workflow_state


class ExecutionMode(Enum):
    """执行模式枚举"""
    SEQUENTIAL = "sequential"      # 顺序执行
    THREAD_POOL = "thread_pool"    # 线程池执行
    PROCESS_POOL = "process_pool"  # 进程池执行
    ASYNCIO = "asyncio"           # 异步执行


class FailureStrategy(Enum):
    """失败策略枚举"""
    STOP_ON_FAILURE = "stop_on_failure"    # 遇到失败立即停止
    CONTINUE_ON_FAILURE = "continue_on_failure"  # 遇到失败继续执行
    RETRY_ON_FAILURE = "retry_on_failure"  # 遇到失败重试


@dataclass
class BatchConfig:
    """批量执行配置"""
    mode: ExecutionMode = ExecutionMode.THREAD_POOL
    max_workers: int = 3
    failure_strategy: FailureStrategy = FailureStrategy.CONTINUE_ON_FAILURE
    timeout: Optional[float] = None
    chunk_size: int = 1  # 分块大小，用于大数据集处理
    progress_callback: Optional[Callable[[int, int, Dict[str, Any]], None]] = None
    result_callback: Optional[Callable[[str, ExecutionResult], None]] = None


class IBatchStrategy(IExecutionStrategy):
    """批量策略接口"""
    pass


class BatchStrategy(BaseStrategy, IBatchStrategy):
    """批量策略实现
    
    提供批量执行工作流的功能，支持多种执行模式和失败策略。
    """
    
    def __init__(self, config: Optional[BatchConfig] = None):
        """初始化批量策略
        
        Args:
            config: 批量执行配置
        """
        super().__init__("batch", priority=20)
        self.config = config or BatchConfig()
        logger.debug(f"批量策略初始化完成，模式: {self.config.mode.value}")
    
    def execute(
        self,
        executor: 'IWorkflowExecutor',
        workflow: 'IWorkflow',
        context: 'ExecutionContext'
    ) -> 'ExecutionResult':
        """使用批量策略执行工作流
        
        Args:
            executor: 工作流执行器
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 获取批量作业列表
        jobs = self._get_batch_jobs(context, workflow)
        
        if not jobs:
            return self.create_execution_result(
                success=False,
                error="没有找到批量作业"
            )
        
        start_time = datetime.now()
        
        logger.info(f"开始批量执行 {len(jobs)} 个作业，模式: {self.config.mode.value}")
        
        try:
            if self.config.mode == ExecutionMode.SEQUENTIAL:
                results = self._execute_sequential(executor, jobs, context)
            elif self.config.mode == ExecutionMode.THREAD_POOL:
                results = self._execute_thread_pool(executor, jobs, context)
            elif self.config.mode == ExecutionMode.PROCESS_POOL:
                results = self._execute_process_pool(executor, jobs, context)
            else:
                raise ValueError(f"不支持的执行模式: {self.config.mode}")
            
            # 统计结果
            successful_count = sum(1 for r in results if r.success)
            failed_count = len(results) - successful_count
            total_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"批量执行完成: 成功 {successful_count}/{len(jobs)}, 耗时: {total_time:.2f}秒")
            
            # 创建批量执行结果
            batch_result = self._create_batch_result(
                success=failed_count == 0,
                total_jobs=len(jobs),
                successful_jobs=successful_count,
                failed_jobs=failed_count,
                total_time=total_time,
                results=results,
                start_time=start_time,
                end_time=datetime.now()
            )
            
            return self.create_execution_result(
                success=batch_result.success,
                result={"batch_result": batch_result.__dict__},
                metadata={
                    "batch_strategy": self.config.mode.value,
                    "total_jobs": len(jobs),
                    "successful_jobs": successful_count,
                    "failed_jobs": failed_count,
                    "total_time": total_time
                }
            )
            
        except Exception as e:
            logger.error(f"批量执行失败: {e}")
            
            return self.create_execution_result(
                success=False,
                error=str(e),
                metadata={
                    "batch_strategy": self.config.mode.value,
                    "total_jobs": len(jobs),
                    "error_type": type(e).__name__
                }
            )
    
    async def execute_async(
        self,
        executor: 'IWorkflowExecutor',
        workflow: 'IWorkflow',
        context: 'ExecutionContext'
    ) -> 'ExecutionResult':
        """异步使用批量策略执行工作流
        
        Args:
            executor: 工作流执行器
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 获取批量作业列表
        jobs = self._get_batch_jobs(context, workflow)
        
        if not jobs:
            return self.create_execution_result(
                success=False,
                error="没有找到批量作业"
            )
        
        start_time = datetime.now()
        
        logger.info(f"开始异步批量执行 {len(jobs)} 个作业")
        
        try:
            results = await self._execute_asyncio(executor, jobs, context)
            
            # 统计结果
            successful_count = sum(1 for r in results if r.success)
            failed_count = len(results) - successful_count
            total_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"异步批量执行完成: 成功 {successful_count}/{len(jobs)}, 耗时: {total_time:.2f}秒")
            
            # 创建批量执行结果
            batch_result = self._create_batch_result(
                success=failed_count == 0,
                total_jobs=len(jobs),
                successful_jobs=successful_count,
                failed_jobs=failed_count,
                total_time=total_time,
                results=results,
                start_time=start_time,
                end_time=datetime.now()
            )
            
            return self.create_execution_result(
                success=batch_result.success,
                result={"batch_result": batch_result.__dict__},
                metadata={
                    "batch_strategy": "asyncio",
                    "total_jobs": len(jobs),
                    "successful_jobs": successful_count,
                    "failed_jobs": failed_count,
                    "total_time": total_time,
                    "execution_mode": "async"
                }
            )
            
        except Exception as e:
            logger.error(f"异步批量执行失败: {e}")
            
            return self.create_execution_result(
                success=False,
                error=str(e),
                metadata={
                    "batch_strategy": "asyncio",
                    "total_jobs": len(jobs),
                    "error_type": type(e).__name__,
                    "execution_mode": "async"
                }
            )
    
    def can_handle(self, workflow: 'IWorkflow', context: 'ExecutionContext') -> bool:
        """判断是否适用批量策略
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            bool: 是否适用批量策略
        """
        return context.get_config("batch_enabled", False) or "batch_jobs" in context.config
    
    def _get_batch_jobs(self, context: 'ExecutionContext', workflow: 'IWorkflow') -> List['BatchJob']:
        """获取批量作业列表
        
        Args:
            context: 执行上下文
            workflow: 工作流实例
            
        Returns:
            List[BatchJob]: 批量作业列表
        """
        jobs = context.get_config("batch_jobs", [])
        
        # 如果没有提供作业列表，尝试从上下文中创建单个作业
        if not jobs and context.get_config("create_single_job", False):
            from ..core.execution_context import BatchJob
            
            # 由于 BatchJob 期望的是 Workflow 类型而不是 IWorkflow，
            # 我们需要检查 workflow 是否是具体的 Workflow 实例
            workflow_instance = None
            if hasattr(workflow, '_config'):  # 检查是否是 Workflow 实例
                from src.core.workflow.workflow import Workflow
                if isinstance(workflow, Workflow):
                    workflow_instance = workflow
            
            job = BatchJob(
                job_id="single_job",
                workflow_id=context.workflow_id,
                initial_data=context.get_config("initial_data"),
                metadata=context.metadata,
                workflow_instance=workflow_instance
            )
            jobs = [job]
        
        return jobs
    
    def _create_workflow_state_from_context(self, context: 'ExecutionContext') -> 'IWorkflowState':
        """从执行上下文创建工作流状态
        
        Args:
            context: 执行上下文
            
        Returns:
            IWorkflowState: 工作流状态
        """
        # 创建初始状态数据
        state_data = {
            "workflow_id": context.workflow_id,
            "execution_id": context.execution_id,
            "config": context.config,
            "metadata": context.metadata,
        }
        
        # 使用状态工厂创建工作流状态
        return create_workflow_state(**state_data)
    
    def _convert_workflow_state_to_execution_result(self, state: 'IWorkflowState') -> 'ExecutionResult':
        """将工作流状态转换为执行结果
        
        Args:
            state: 工作流状态
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 获取状态值
        state_values = {}
        if hasattr(state, 'values'):
            state_values = state.values
        elif hasattr(state, 'get'):
            # 尝试获取一些常见的字段
            try:
                state_values = {
                    "messages": state.get("messages", []),
                    "current_node": state.get("current_node"),
                    "iteration_count": state.get("iteration_count", 0)
                }
            except:
                state_values = {}
        
        # 获取元数据（通过 get 方法）
        metadata = {}
        if hasattr(state, 'get'):
            # 尝试获取元数据字段
            metadata = state.get('metadata', {})
        
        # 创建节点结果
        node_result = NodeResult(
            success=True,  # 假设成功，除非有错误信息
            state=state,
            metadata=metadata
        )
        
        # 创建执行结果
        execution_result = ExecutionResult(
            success=True,  # 假设成功，除非有错误信息
            result=state_values,
            metadata=metadata,
            node_results=[node_result],
            execution_time=0.0
        )
        
        return execution_result
    
    def _execute_sequential(
        self, 
        executor: 'IWorkflowExecutor', 
        jobs: List['BatchJob'], 
        context: 'ExecutionContext'
    ) -> List['ExecutionResult']:
        """顺序执行作业
        
        Args:
            executor: 工作流执行器
            jobs: 批量作业列表
            context: 执行上下文
            
        Returns:
            List[ExecutionResult]: 执行结果列表
        """
        results = []
        
        for i, job in enumerate(jobs):
            try:
                # 创建作业上下文
                job_context = self._create_job_context(job, context)
                
                # 执行作业
                result = self._execute_single_job(executor, job, context)
                results.append(result)
                
                # 调用进度回调
                if self.config.progress_callback:
                    self.config.progress_callback(i + 1, len(jobs), {
                        "successful": sum(1 for r in results if r.success),
                        "failed": i + 1 - sum(1 for r in results if r.success)
                    })
                
                # 调用结果回调
                if self.config.result_callback:
                    self.config.result_callback(job.job_id, result)
                
                # 根据失败策略决定是否继续
                if not result.success and self.config.failure_strategy == FailureStrategy.STOP_ON_FAILURE:
                    logger.error(f"作业 {job.job_id} 失败，停止执行")
                    break
                    
            except Exception as e:
                logger.error(f"执行作业 {job.job_id} 时发生异常: {e}")
                
                # 创建错误结果
                error_result = self.create_execution_result(
                    success=False,
                    error=str(e),
                    metadata={"job_id": job.job_id, "error_type": type(e).__name__}
                )
                results.append(error_result)
                
                if self.config.failure_strategy == FailureStrategy.STOP_ON_FAILURE:
                    break
        
        return results
    
    def _execute_thread_pool(
        self, 
        executor: 'IWorkflowExecutor', 
        jobs: List['BatchJob'], 
        context: 'ExecutionContext'
    ) -> List['ExecutionResult']:
        """使用线程池执行作业
        
        Args:
            executor: 工作流执行器
            jobs: 批量作业列表
            context: 执行上下文
            
        Returns:
            List[ExecutionResult]: 执行结果列表
        """
        results = []
        completed_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as pool:
            # 提交所有作业
            future_to_job = {
                pool.submit(self._execute_single_job, executor, job, context): job
                for job in jobs
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_job, timeout=self.config.timeout):
                job = future_to_job[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # 调用进度回调
                    if self.config.progress_callback:
                        self.config.progress_callback(completed_count, len(jobs), {
                            "successful": sum(1 for r in results if r.success),
                            "failed": completed_count - sum(1 for r in results if r.success)
                        })
                    
                    # 调用结果回调
                    if self.config.result_callback:
                        self.config.result_callback(job.job_id, result)
                        
                except Exception as e:
                    logger.error(f"执行作业 {job.job_id} 时发生异常: {e}")
                    
                    # 创建错误结果
                    error_result = self.create_execution_result(
                        success=False,
                        error=str(e),
                        metadata={"job_id": job.job_id, "error_type": type(e).__name__}
                    )
                    results.append(error_result)
        
        return results
    
    def _execute_process_pool(
        self, 
        executor: 'IWorkflowExecutor', 
        jobs: List['BatchJob'], 
        context: 'ExecutionContext'
    ) -> List['ExecutionResult']:
        """使用进程池执行作业
        
        Args:
            executor: 工作流执行器
            jobs: 批量作业列表
            context: 执行上下文
            
        Returns:
            List[ExecutionResult]: 执行结果列表
        """
        # 注意：进程池执行需要序列化工作流实例，这里简化实现
        # 实际使用中可能需要更复杂的序列化机制
        logger.warning("进程池执行模式需要工作流实例可序列化，当前使用线程池模式")
        return self._execute_thread_pool(executor, jobs, context)
    
    async def _execute_asyncio(
        self, 
        executor: 'IWorkflowExecutor', 
        jobs: List['BatchJob'], 
        context: 'ExecutionContext'
    ) -> List['ExecutionResult']:
        """使用异步执行作业
        
        Args:
            executor: 工作流执行器
            jobs: 批量作业列表
            context: 执行上下文
            
        Returns:
            List[ExecutionResult]: 执行结果列表
        """
        results = []
        completed_count = 0
        
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(self.config.max_workers)
        
        async def execute_job_with_semaphore(job: 'BatchJob') -> Union['ExecutionResult', Exception]:
            async with semaphore:
                try:
                    return await self._execute_single_job_async(executor, job, context)
                except Exception as e:
                    return e
        
        # 创建所有任务
        tasks = [execute_job_with_semaphore(job) for job in jobs]
        
        # 等待所有任务完成
        try:
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(completed_results):
                job = jobs[i]
                completed_count += 1
                
                if isinstance(result, Exception):
                    logger.error(f"执行作业 {job.job_id} 时发生异常: {result}")
                    
                    # 创建错误结果
                    final_result = self.create_execution_result(
                        success=False,
                        error=str(result),
                        metadata={"job_id": job.job_id, "error_type": type(result).__name__}
                    )
                else:
                    # 类型收缩：此时 result 一定是 ExecutionResult
                    final_result = result
                
                results.append(final_result)
                
                # 调用进度回调
                if self.config.progress_callback:
                    self.config.progress_callback(completed_count, len(jobs), {
                        "successful": sum(1 for r in results if r.success),
                        "failed": completed_count - sum(1 for r in results if r.success)
                    })
                
                # 调用结果回调
                if self.config.result_callback:
                    if isinstance(final_result, ExecutionResult):
                        self.config.result_callback(job.job_id, final_result)
                    
        except Exception as e:
            logger.error(f"异步批量执行过程中发生异常: {e}")
        
        return results
    
    def _execute_single_job(
        self, 
        executor: 'IWorkflowExecutor', 
        job: 'BatchJob', 
        context: 'ExecutionContext'
    ) -> 'ExecutionResult':
        """执行单个作业
        
        Args:
            executor: 工作流执行器
            job: 批量作业
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 创建作业上下文
        job_context = self._create_job_context(job, context)
        
        # 执行作业
        workflow_to_execute = job.workflow_instance
        if workflow_to_execute is None:
            # 如果作业中没有工作流实例，则创建错误结果
            return self.create_execution_result(
                success=False,
                error="作业中没有工作流实例"
            )
        
        # 将 ExecutionContext 转换为 IWorkflowState
        initial_state = self._create_workflow_state_from_context(job_context)
        
        # 执行工作流
        workflow_state_result = executor.execute(workflow_to_execute, initial_state)
        
        # 将 IWorkflowState 结果转换为 ExecutionResult
        return self._convert_workflow_state_to_execution_result(workflow_state_result)
    
    async def _execute_single_job_async(
        self, 
        executor: 'IWorkflowExecutor', 
        job: 'BatchJob', 
        context: 'ExecutionContext'
    ) -> 'ExecutionResult':
        """异步执行单个作业
        
        Args:
            executor: 工作流执行器
            job: 批量作业
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 创建作业上下文
        job_context = self._create_job_context(job, context)
        
        # 异步执行作业
        workflow_to_execute = job.workflow_instance
        if workflow_to_execute is None:
            # 如果作业中没有工作流实例，则创建错误结果
            return self.create_execution_result(
                success=False,
                error="作业中没有工作流实例"
            )
        # 将 ExecutionContext 转换为 IWorkflowState
        initial_state = self._create_workflow_state_from_context(job_context)
        
        # 异步执行工作流
        workflow_state_result = await executor.execute_async(workflow_to_execute, initial_state)
        
        # 将 IWorkflowState 结果转换为 ExecutionResult
        return self._convert_workflow_state_to_execution_result(workflow_state_result)
    
    def _create_job_context(
        self, 
        job: 'BatchJob', 
        parent_context: 'ExecutionContext'
    ) -> 'ExecutionContext':
        """创建作业上下文
        
        Args:
            job: 批量作业
            parent_context: 父执行上下文
            
        Returns:
            ExecutionContext: 作业执行上下文
        """
        from ..core.execution_context import ExecutionContext
        
        return ExecutionContext(
            workflow_id=job.workflow_id,
            execution_id=f"{parent_context.execution_id}_{job.job_id}",
            config=job.initial_data or {},
            metadata={**parent_context.metadata, **job.metadata, "job_id": job.job_id}
        )
    
    def _create_batch_result(
        self,
        success: bool,
        total_jobs: int,
        successful_jobs: int,
        failed_jobs: int,
        total_time: float,
        results: List['ExecutionResult'],
        start_time: datetime,
        end_time: datetime
    ) -> 'BatchExecutionResult':
        """创建批量执行结果
        
        Args:
            success: 是否成功
            total_jobs: 总作业数
            successful_jobs: 成功作业数
            failed_jobs: 失败作业数
            total_time: 总时间
            results: 执行结果列表
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            BatchExecutionResult: 批量执行结果
        """
        from ..core.execution_context import BatchExecutionResult
        
        errors = []
        for result in results:
            if not result.success and result.error:
                errors.append({
                    "error": result.error,
                    "metadata": result.metadata
                })
        
        return BatchExecutionResult(
            success=success,
            total_jobs=total_jobs,
            successful_jobs=successful_jobs,
            failed_jobs=failed_jobs,
            total_time=total_time,
            results=results,
            errors=errors,
            start_time=start_time,
            end_time=end_time
        )