"""批量执行器 - 新架构实现

实现批量执行工作流的功能，支持多线程/多进程执行、动态 worker 管理、部分失败处理和执行进度跟踪。
"""

from typing import Dict, Any, Optional, List, Union, Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import asyncio
import concurrent.futures
import threading
import time
from pathlib import Path

from ..loading.loader_service import UniversalLoaderService
from ..workflow_instance import WorkflowInstance
from .runner import WorkflowExecutionResult
from .retry_executor import RetryExecutor, RetryConfig
from src.core.workflow.exceptions import WorkflowExecutionError

logger = logging.getLogger(__name__)


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
class BatchExecutionConfig:
    """批量执行配置"""
    mode: ExecutionMode = ExecutionMode.THREAD_POOL
    max_workers: int = 3
    failure_strategy: FailureStrategy = FailureStrategy.CONTINUE_ON_FAILURE
    retry_config: Optional[RetryConfig] = None
    progress_callback: Optional[Callable[[int, int, Dict[str, Any]], None]] = None
    result_callback: Optional[Callable[[str, WorkflowExecutionResult], None]] = None
    timeout: Optional[float] = None
    chunk_size: int = 1  # 分块大小，用于大数据集处理
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.retry_config is None:
            self.retry_config = RetryConfig(max_retries=1)  # 默认只尝试一次


@dataclass
class BatchJob:
    """批量作业"""
    job_id: str
    config_path: Optional[str] = None
    workflow_instance: Optional[WorkflowInstance] = None
    initial_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if not self.config_path and not self.workflow_instance:
            raise ValueError("必须提供 config_path 或 workflow_instance")


@dataclass
class BatchExecutionResult:
    """批量执行结果"""
    success: bool
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    total_time: float
    results: List[WorkflowExecutionResult] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_jobs == 0:
            return 0.0
        return self.successful_jobs / self.total_jobs
    
    @property
    def average_execution_time(self) -> float:
        """平均执行时间"""
        if self.successful_jobs == 0:
            return 0.0
        total_time = sum(r.execution_time or 0.0 for r in self.results if r.success)
        return total_time / self.successful_jobs
    
    def get_successful_results(self) -> List[WorkflowExecutionResult]:
        """获取成功的结果"""
        return [r for r in self.results if r.success]
    
    def get_failed_results(self) -> List[WorkflowExecutionResult]:
        """获取失败的结果"""
        return [r for r in self.results if not r.success]


class BatchExecutor:
    """批量执行器
    
    实现批量执行工作流的功能，支持多种执行模式和失败策略。
    """
    
    def __init__(
        self,
        loader_service: Optional[UniversalLoaderService] = None,
        retry_executor: Optional[RetryExecutor] = None
    ):
        """初始化批量执行器
        
        Args:
            loader_service: 统一加载器服务
            retry_executor: 重试执行器
        """
        self.loader_service = loader_service or UniversalLoaderService()
        self.retry_executor = retry_executor or RetryExecutor()
        self._execution_id_counter = 0
        self._lock = threading.Lock()
        
        logger.debug("批量执行器初始化完成")
    
    def execute(
        self,
        jobs: List[BatchJob],
        config: Optional[BatchExecutionConfig] = None
    ) -> BatchExecutionResult:
        """执行批量作业
        
        Args:
            jobs: 批量作业列表
            config: 批量执行配置
            
        Returns:
            BatchExecutionResult: 批量执行结果
        """
        config = config or BatchExecutionConfig()
        start_time = datetime.now()
        
        logger.info(f"开始批量执行 {len(jobs)} 个作业，模式: {config.mode.value}")
        
        try:
            if config.mode == ExecutionMode.SEQUENTIAL:
                result = self._execute_sequential(jobs, config)
            elif config.mode == ExecutionMode.THREAD_POOL:
                result = self._execute_thread_pool(jobs, config)
            elif config.mode == ExecutionMode.PROCESS_POOL:
                result = self._execute_process_pool(jobs, config)
            else:
                raise ValueError(f"不支持的执行模式: {config.mode}")
            
            # 设置时间信息
            result.start_time = start_time
            result.end_time = datetime.now()
            result.total_time = (result.end_time - start_time).total_seconds()
            
            logger.info(f"批量执行完成: 成功 {result.successful_jobs}/{result.total_jobs}, 耗时: {result.total_time:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"批量执行失败: {e}")
            
            # 返回失败结果
            end_time = datetime.now()
            return BatchExecutionResult(
                success=False,
                total_jobs=len(jobs),
                successful_jobs=0,
                failed_jobs=len(jobs),
                total_time=(end_time - start_time).total_seconds(),
                errors=[{"error": str(e), "type": type(e).__name__}],
                start_time=start_time,
                end_time=end_time
            )
    
    async def execute_async(
        self,
        jobs: List[BatchJob],
        config: Optional[BatchExecutionConfig] = None
    ) -> BatchExecutionResult:
        """异步执行批量作业
        
        Args:
            jobs: 批量作业列表
            config: 批量执行配置
            
        Returns:
            BatchExecutionResult: 批量执行结果
        """
        config = config or BatchExecutionConfig()
        config.mode = ExecutionMode.ASYNCIO  # 强制使用异步模式
        
        start_time = datetime.now()
        
        logger.info(f"开始异步批量执行 {len(jobs)} 个作业")
        
        try:
            result = await self._execute_asyncio(jobs, config)
            
            # 设置时间信息
            result.start_time = start_time
            result.end_time = datetime.now()
            result.total_time = (result.end_time - start_time).total_seconds()
            
            logger.info(f"异步批量执行完成: 成功 {result.successful_jobs}/{result.total_jobs}, 耗时: {result.total_time:.2f}秒")
            return result
            
        except Exception as e:
            logger.error(f"异步批量执行失败: {e}")
            
            # 返回失败结果
            end_time = datetime.now()
            return BatchExecutionResult(
                success=False,
                total_jobs=len(jobs),
                successful_jobs=0,
                failed_jobs=len(jobs),
                total_time=(end_time - start_time).total_seconds(),
                errors=[{"error": str(e), "type": type(e).__name__}],
                start_time=start_time,
                end_time=end_time
            )
    
    def _execute_sequential(
        self,
        jobs: List[BatchJob],
        config: BatchExecutionConfig
    ) -> BatchExecutionResult:
        """顺序执行作业
        
        Args:
            jobs: 批量作业列表
            config: 批量执行配置
            
        Returns:
            BatchExecutionResult: 批量执行结果
        """
        results = []
        errors = []
        successful_count = 0
        
        for i, job in enumerate(jobs):
            try:
                # 执行单个作业
                result = self._execute_single_job(job, config)
                results.append(result)
                
                if result.success:
                    successful_count += 1
                else:
                    errors.append({
                        "job_id": job.job_id,
                        "error": result.error,
                        "type": "execution_failure"
                    })
                    
                    # 根据失败策略决定是否继续
                    if config.failure_strategy == FailureStrategy.STOP_ON_FAILURE:
                        logger.error(f"作业 {job.job_id} 失败，停止执行")
                        break
                
                # 调用进度回调
                if config.progress_callback:
                    config.progress_callback(i + 1, len(jobs), {
                        "successful": successful_count,
                        "failed": i + 1 - successful_count
                    })
                
                # 调用结果回调
                if config.result_callback:
                    config.result_callback(job.job_id, result)
                    
            except Exception as e:
                logger.error(f"执行作业 {job.job_id} 时发生异常: {e}")
                errors.append({
                    "job_id": job.job_id,
                    "error": str(e),
                    "type": type(e).__name__
                })
                
                if config.failure_strategy == FailureStrategy.STOP_ON_FAILURE:
                    break
        
        return BatchExecutionResult(
            success=successful_count == len(jobs),
            total_jobs=len(jobs),
            successful_jobs=successful_count,
            failed_jobs=len(jobs) - successful_count,
            total_time=0.0,  # 将在外部设置
            results=results,
            errors=errors
        )
    
    def _execute_thread_pool(
        self,
        jobs: List[BatchJob],
        config: BatchExecutionConfig
    ) -> BatchExecutionResult:
        """使用线程池执行作业
        
        Args:
            jobs: 批量作业列表
            config: 批量执行配置
            
        Returns:
            BatchExecutionResult: 批量执行结果
        """
        results = []
        errors = []
        successful_count = 0
        completed_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            # 提交所有作业
            future_to_job = {
                executor.submit(self._execute_single_job, job, config): job
                for job in jobs
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_job, timeout=config.timeout):
                job = future_to_job[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.success:
                        successful_count += 1
                    else:
                        errors.append({
                            "job_id": job.job_id,
                            "error": result.error,
                            "type": "execution_failure"
                        })
                    
                    # 调用进度回调
                    if config.progress_callback:
                        config.progress_callback(completed_count, len(jobs), {
                            "successful": successful_count,
                            "failed": completed_count - successful_count
                        })
                    
                    # 调用结果回调
                    if config.result_callback:
                        config.result_callback(job.job_id, result)
                        
                except Exception as e:
                    logger.error(f"执行作业 {job.job_id} 时发生异常: {e}")
                    errors.append({
                        "job_id": job.job_id,
                        "error": str(e),
                        "type": type(e).__name__
                    })
        
        return BatchExecutionResult(
            success=successful_count == len(jobs),
            total_jobs=len(jobs),
            successful_jobs=successful_count,
            failed_jobs=len(jobs) - successful_count,
            total_time=0.0,  # 将在外部设置
            results=results,
            errors=errors
        )
    
    def _execute_process_pool(
        self,
        jobs: List[BatchJob],
        config: BatchExecutionConfig
    ) -> BatchExecutionResult:
        """使用进程池执行作业
        
        Args:
            jobs: 批量作业列表
            config: 批量执行配置
            
        Returns:
            BatchExecutionResult: 批量执行结果
        """
        # 注意：进程池执行需要序列化工作流实例，这里简化实现
        # 实际使用中可能需要更复杂的序列化机制
        logger.warning("进程池执行模式需要工作流实例可序列化，当前使用线程池模式")
        return self._execute_thread_pool(jobs, config)
    
    async def _execute_asyncio(
        self,
        jobs: List[BatchJob],
        config: BatchExecutionConfig
    ) -> BatchExecutionResult:
        """使用异步执行作业
        
        Args:
            jobs: 批量作业列表
            config: 批量执行配置
            
        Returns:
            BatchExecutionResult: 批量执行结果
        """
        results: List[WorkflowExecutionResult] = []
        errors = []
        successful_count = 0
        completed_count = 0
        
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(config.max_workers)
        
        async def execute_job_with_semaphore(job: BatchJob) -> Union[WorkflowExecutionResult, Exception]:
            async with semaphore:
                try:
                    return await self._execute_single_job_async(job, config)
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
                    errors.append({
                        "job_id": job.job_id,
                        "error": str(result),
                        "type": type(result).__name__
                    })
                elif isinstance(result, WorkflowExecutionResult):
                    results.append(result)
                    
                    if result.success:
                        successful_count += 1
                    else:
                        errors.append({
                            "job_id": job.job_id,
                            "error": result.error or "Unknown error",
                            "type": "execution_failure"
                        })
                else:
                    # 处理其他可能的返回值类型
                    logger.warning(f"作业 {job.job_id} 返回未知类型: {type(result)}")
                    errors.append({
                        "job_id": job.job_id,
                        "error": f"Unknown result type: {type(result)}",
                        "type": "unknown_result"
                    })
                
                # 调用进度回调
                if config.progress_callback:
                    config.progress_callback(completed_count, len(jobs), {
                        "successful": successful_count,
                        "failed": completed_count - successful_count
                    })
                
                # 调用结果回调
                if config.result_callback and isinstance(result, WorkflowExecutionResult):
                    config.result_callback(job.job_id, result)
                    
        except Exception as e:
            logger.error(f"异步批量执行过程中发生异常: {e}")
            errors.append({
                "error": str(e),
                "type": type(e).__name__
            })
        
        return BatchExecutionResult(
            success=successful_count == len(jobs),
            total_jobs=len(jobs),
            successful_jobs=successful_count,
            failed_jobs=len(jobs) - successful_count,
            total_time=0.0,  # 将在外部设置
            results=results,
            errors=errors
        )
    
    def _execute_single_job(
        self,
        job: BatchJob,
        config: BatchExecutionConfig
    ) -> WorkflowExecutionResult:
        """执行单个作业
        
        Args:
            job: 批量作业
            config: 批量执行配置
            
        Returns:
            WorkflowExecutionResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 获取工作流实例
            if job.workflow_instance:
                workflow = job.workflow_instance
            elif job.config_path:
                workflow = self.loader_service.load_from_file(job.config_path)
            else:
                raise ValueError("必须提供 workflow_instance 或 config_path")
            
            # 根据重试配置执行
            if config.retry_config and config.retry_config.max_retries > 0:
                retry_result = self.retry_executor.execute(
                    workflow, 
                    job.initial_data, 
                    **job.metadata
                )
                
                if retry_result.success:
                    return WorkflowExecutionResult(
                        workflow_name=workflow.config.name,
                        success=True,
                        result=retry_result.result,
                        execution_time=retry_result.total_time,
                        start_time=start_time,
                        end_time=datetime.now(),
                        metadata={
                            "job_id": job.job_id,
                            "retry_attempts": retry_result.total_attempts - 1
                        }
                    )
                else:
                    return WorkflowExecutionResult(
                        workflow_name=workflow.config.name,
                        success=False,
                        error=str(retry_result.exception),
                        execution_time=retry_result.total_time,
                        start_time=start_time,
                        end_time=datetime.now(),
                        metadata={
                            "job_id": job.job_id,
                            "retry_attempts": retry_result.total_attempts - 1
                        }
                    )
            else:
                # 直接执行
                result = workflow.run(job.initial_data, **job.metadata)
                
                return WorkflowExecutionResult(
                    workflow_name=workflow.config.name,
                    success=True,
                    result=result,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    start_time=start_time,
                    end_time=datetime.now(),
                    metadata={"job_id": job.job_id}
                )
                
        except Exception as e:
            return WorkflowExecutionResult(
                workflow_name="unknown",
                success=False,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                metadata={
                    "job_id": job.job_id,
                    "error_type": type(e).__name__
                }
            )
    
    async def _execute_single_job_async(
        self,
        job: BatchJob,
        config: BatchExecutionConfig
    ) -> WorkflowExecutionResult:
        """异步执行单个作业
        
        Args:
            job: 批量作业
            config: 批量执行配置
            
        Returns:
            WorkflowExecutionResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 获取工作流实例
            if job.workflow_instance:
                workflow = job.workflow_instance
            elif job.config_path:
                workflow = self.loader_service.load_from_file(job.config_path)
            else:
                raise ValueError("必须提供 workflow_instance 或 config_path")
            
            # 根据重试配置执行
            if config.retry_config and config.retry_config.max_retries > 0:
                retry_result = await self.retry_executor.execute_async(
                    workflow, 
                    job.initial_data, 
                    **job.metadata
                )
                
                if retry_result.success:
                    return WorkflowExecutionResult(
                        workflow_name=workflow.config.name,
                        success=True,
                        result=retry_result.result,
                        execution_time=retry_result.total_time,
                        start_time=start_time,
                        end_time=datetime.now(),
                        metadata={
                            "job_id": job.job_id,
                            "retry_attempts": retry_result.total_attempts - 1,
                            "execution_mode": "async"
                        }
                    )
                else:
                    return WorkflowExecutionResult(
                        workflow_name=workflow.config.name,
                        success=False,
                        error=str(retry_result.exception),
                        execution_time=retry_result.total_time,
                        start_time=start_time,
                        end_time=datetime.now(),
                        metadata={
                            "job_id": job.job_id,
                            "retry_attempts": retry_result.total_attempts - 1,
                            "execution_mode": "async"
                        }
                    )
            else:
                # 直接异步执行
                result = await workflow.run_async(job.initial_data, **job.metadata)
                
                return WorkflowExecutionResult(
                    workflow_name=workflow.config.name,
                    success=True,
                    result=result,
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    start_time=start_time,
                    end_time=datetime.now(),
                    metadata={
                        "job_id": job.job_id,
                        "execution_mode": "async"
                    }
                )
                
        except Exception as e:
            return WorkflowExecutionResult(
                workflow_name="unknown",
                success=False,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                metadata={
                    "job_id": job.job_id,
                    "error_type": type(e).__name__,
                    "execution_mode": "async"
                }
            )
    
    def _generate_execution_id(self) -> str:
        """生成执行ID
        
        Returns:
            str: 执行ID
        """
        with self._lock:
            self._execution_id_counter += 1
            return f"batch_exec_{self._execution_id_counter}_{int(time.time())}"


# 便捷函数
def batch_run_workflows(
    config_paths: List[str],
    initial_data_list: Optional[List[Optional[Dict[str, Any]]]] = None,
    max_workers: int = 3
) -> BatchExecutionResult:
    """批量运行工作流（便捷函数）
    
    Args:
        config_paths: 配置文件路径列表
        initial_data_list: 初始数据列表
        max_workers: 最大并发数
        
    Returns:
        BatchExecutionResult: 批量执行结果
    """
    # 创建批量作业
    jobs = []
    for i, config_path in enumerate(config_paths):
        initial_data = None
        if initial_data_list and i < len(initial_data_list):
            initial_data = initial_data_list[i]
        
        job = BatchJob(
            job_id=f"job_{i}",
            config_path=config_path,
            initial_data=initial_data
        )
        jobs.append(job)
    
    # 创建批量执行器并执行
    executor = BatchExecutor()
    config = BatchExecutionConfig(
        mode=ExecutionMode.THREAD_POOL,
        max_workers=max_workers
    )
    
    return executor.execute(jobs, config)


async def batch_run_workflows_async(
    config_paths: List[str],
    initial_data_list: Optional[List[Optional[Dict[str, Any]]]] = None,
    max_workers: int = 3
) -> BatchExecutionResult:
    """异步批量运行工作流（便捷函数）
    
    Args:
        config_paths: 配置文件路径列表
        initial_data_list: 初始数据列表
        max_workers: 最大并发数
        
    Returns:
        BatchExecutionResult: 批量执行结果
    """
    # 创建批量作业
    jobs = []
    for i, config_path in enumerate(config_paths):
        initial_data = None
        if initial_data_list and i < len(initial_data_list):
            initial_data = initial_data_list[i]
        
        job = BatchJob(
            job_id=f"job_{i}",
            config_path=config_path,
            initial_data=initial_data
        )
        jobs.append(job)
    
    # 创建批量执行器并执行
    executor = BatchExecutor()
    config = BatchExecutionConfig(
        mode=ExecutionMode.ASYNCIO,
        max_workers=max_workers
    )
    
    return await executor.execute_async(jobs, config)