"""执行调度器

提供工作流执行的调度和资源管理服务。
"""

from src.interfaces.dependency_injection import get_logger
import time
import threading
import queue
import uuid
from typing import Dict, Any, Optional, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future, as_completed

if TYPE_CHECKING:
    from ..core.execution_context import ExecutionContext, ExecutionResult
    from ...workflow import Workflow

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class ExecutionTask:
    """执行任务"""
    task_id: str
    workflow: 'Workflow'
    context: 'ExecutionContext'
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional['ExecutionResult'] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other: 'ExecutionTask') -> bool:
        """优先级比较，用于优先队列"""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value  # 高优先级在前
        return self.created_at < other.created_at  # 早创建的在前


@dataclass
class SchedulerConfig:
    """调度器配置"""
    max_workers: int = 4
    max_queue_size: int = 100
    enable_priority_queue: bool = True
    enable_retry: bool = True
    default_retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    retry_backoff_factor: float = 2.0
    task_timeout: Optional[float] = None
    cleanup_interval: float = 300.0  # 5分钟


class IExecutionScheduler:
    """执行调度器接口"""
    pass


class ExecutionScheduler(IExecutionScheduler):
    """执行调度器
    
    提供工作流任务的调度、排队和资源管理功能。
    """
    
    def __init__(
        self, 
        config: Optional[SchedulerConfig] = None,
        execution_callback: Optional[Callable[[ExecutionTask], 'ExecutionResult']] = None
    ):
        """初始化执行调度器
        
        Args:
            config: 调度器配置
            execution_callback: 执行回调函数
        """
        self.config = config or SchedulerConfig()
        self.execution_callback = execution_callback
        
        # 任务队列
        if self.config.enable_priority_queue:
            self._task_queue = queue.PriorityQueue(maxsize=self.config.max_queue_size)
        else:
            self._task_queue = queue.Queue(maxsize=self.config.max_queue_size)
        
        # 线程池
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
        # 任务跟踪
        self._tasks: Dict[str, ExecutionTask] = {}
        self._running_tasks: Dict[str, Future] = {}
        
        # 调度器状态
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        
        # 统计信息
        self._statistics = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
            "average_wait_time": 0.0,
            "average_execution_time": 0.0,
            "queue_size": 0
        }
        
        # 锁
        self._lock = threading.RLock()
        
        logger.debug("执行调度器初始化完成")
    
    def start(self) -> None:
        """启动调度器"""
        with self._lock:
            if self._running:
                logger.warning("调度器已经在运行")
                return
            
            self._running = True
            self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self._scheduler_thread.start()
            
            logger.info("执行调度器已启动")
    
    def stop(self, timeout: Optional[float] = None) -> None:
        """停止调度器
        
        Args:
            timeout: 停止超时时间
        """
        with self._lock:
            if not self._running:
                logger.warning("调度器未在运行")
                return
            
            self._running = False
            
            # 等待调度器线程结束
            if self._scheduler_thread:
                self._scheduler_thread.join(timeout=timeout)
            
            # 关闭线程池
            self._executor.shutdown(wait=True)
            
            logger.info("执行调度器已停止")
    
    def submit_task(
        self, 
        workflow: 'Workflow',
        context: 'ExecutionContext',
        priority: TaskPriority = TaskPriority.NORMAL,
        scheduled_at: Optional[datetime] = None
    ) -> str:
        """提交执行任务
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            priority: 任务优先级
            scheduled_at: 计划执行时间
            
        Returns:
            str: 任务ID
        """
        import uuid
        
        task_id = str(uuid.uuid4())
        
        task = ExecutionTask(
            task_id=task_id,
            workflow=workflow,
            context=context,
            priority=priority,
            scheduled_at=scheduled_at
        )
        
        with self._lock:
            # 检查队列是否已满
            if self._task_queue.full():
                raise queue.Full("任务队列已满")
            
            # 添加任务到队列
            if self.config.enable_priority_queue:
                # 优先队列需要使用优先级作为排序键
                priority_value = 5 - task.priority.value  # 反转优先级值
                self._task_queue.put((priority_value, task))
            else:
                self._task_queue.put(task)
            
            # 跟踪任务
            self._tasks[task_id] = task
            
            # 更新统计
            self._statistics["total_tasks"] += 1
            self._statistics["queue_size"] = self._task_queue.qsize()
            
            logger.debug(f"任务已提交: {task_id}, 优先级: {priority.name}")
        
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        with self._lock:
            if task_id not in self._tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False
            
            task = self._tasks[task_id]
            
            if task.status == TaskStatus.RUNNING:
                # 尝试取消正在运行的任务
                if task_id in self._running_tasks:
                    future = self._running_tasks[task_id]
                    cancelled = future.cancel()
                    if cancelled:
                        task.status = TaskStatus.CANCELLED
                        task.completed_at = datetime.now()
                        self._statistics["cancelled_tasks"] += 1
                        logger.info(f"任务已取消: {task_id}")
                        return True
                    else:
                        logger.warning(f"无法取消正在运行的任务: {task_id}")
                        return False
                else:
                    logger.warning(f"无法取消正在运行的任务: {task_id}")
                    return False
            elif task.status == TaskStatus.PENDING:
                # 从队列中移除任务（简化实现，实际可能需要更复杂的逻辑）
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now()
                self._statistics["cancelled_tasks"] += 1
                logger.info(f"任务已取消: {task_id}")
                return True
            else:
                logger.warning(f"任务无法取消，当前状态: {task.status.value}")
                return False
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskStatus]: 任务状态
        """
        with self._lock:
            task = self._tasks.get(task_id)
            return task.status if task else None
    
    def get_task_result(self, task_id: str) -> Optional['ExecutionResult']:
        """获取任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[ExecutionResult]: 执行结果
        """
        with self._lock:
            task = self._tasks.get(task_id)
            return task.result if task else None
    
    def get_queue_size(self) -> int:
        """获取队列大小
        
        Returns:
            int: 队列大小
        """
        return self._task_queue.qsize()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            stats = self._statistics.copy()
            stats["queue_size"] = self._task_queue.qsize()
            stats["running_tasks"] = len(self._running_tasks)
            stats["active_workers"] = self._executor._threads.__len__() if hasattr(self._executor, '_threads') else 0
            
            # 计算平均等待时间和执行时间
            if stats["completed_tasks"] > 0:
                total_wait_time = 0.0
                total_execution_time = 0.0
                
                for task in self._tasks.values():
                    if task.status == TaskStatus.COMPLETED and task.started_at and task.completed_at:
                        wait_time = (task.started_at - task.created_at).total_seconds()
                        execution_time = (task.completed_at - task.started_at).total_seconds()
                        total_wait_time += wait_time
                        total_execution_time += execution_time
                
                stats["average_wait_time"] = total_wait_time / stats["completed_tasks"]
                stats["average_execution_time"] = total_execution_time / stats["completed_tasks"]
            
            return stats
    
    def _scheduler_loop(self) -> None:
        """调度器主循环"""
        logger.info("调度器主循环已启动")
        
        while self._running:
            try:
                # 获取任务
                if self.config.enable_priority_queue:
                    priority_value, task = self._task_queue.get(timeout=1.0)
                else:
                    task = self._task_queue.get(timeout=1.0)
                    priority_value = None
                
                # 检查是否到了计划执行时间
                if task.scheduled_at and task.scheduled_at > datetime.now():
                    # 重新放回队列
                    if self.config.enable_priority_queue:
                        self._task_queue.put((priority_value, task))
                    else:
                        self._task_queue.put(task)
                    time.sleep(0.1)  # 短暂等待
                    continue
                
                # 提交任务到线程池
                future = self._executor.submit(self._execute_task, task)
                
                with self._lock:
                    self._running_tasks[task.task_id] = future
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.now()
                
                # 添加完成回调
                future.add_done_callback(lambda f, t=task: self._task_completed(f, t))
                
            except queue.Empty:
                # 队列为空，继续循环
                continue
            except Exception as e:
                logger.error(f"调度器循环出错: {e}")
                time.sleep(1.0)
        
        logger.info("调度器主循环已退出")
    
    def _execute_task(self, task: ExecutionTask) -> 'ExecutionResult':
        """执行任务
        
        Args:
            task: 执行任务
            
        Returns:
            ExecutionResult: 执行结果
        """
        try:
            logger.debug(f"开始执行任务: {task.task_id}")
            
            # 使用执行回调执行任务
            if self.execution_callback:
                result = self.execution_callback(task)
            else:
                # 使用协调器执行工作流
                from ..executor import WorkflowExecutor
                executor = WorkflowExecutor()
                from src.core.state.implementations.workflow_state import WorkflowState
                initial_state = WorkflowState(
                    workflow_id=task.workflow.workflow_id,
                    execution_id=str(uuid.uuid4()),
                    data=task.context.get_config("initial_data") or {}
                )
                result_state = executor.execute(task.workflow, initial_state, task.context.config)
                # 使用 getattr 安全访问 data 属性，因为 IWorkflowState 接口可能没有定义 data
                final_data = getattr(result_state, 'data', result_state)
                
                # 创建执行结果
                from ..core.execution_context import ExecutionResult
                result = ExecutionResult(
                    success=True,
                    result=final_data if isinstance(final_data, dict) else {"result": final_data},
                    metadata={
                        "task_id": task.task_id,
                        "workflow_name": task.workflow.config.name,
                        "execution_time": (datetime.now() - task.started_at).total_seconds() if task.started_at else 0.0
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"任务执行失败: {task.task_id}, 错误: {e}")
            
            # 创建错误结果
            from ..core.execution_context import ExecutionResult
            return ExecutionResult(
                success=False,
                error=str(e),
                metadata={
                    "task_id": task.task_id,
                    "workflow_name": task.workflow.config.name,
                    "error_type": type(e).__name__
                }
            )
    
    def _task_completed(self, future: Future, task: ExecutionTask) -> None:
        """任务完成回调
        
        Args:
            future: Future对象
            task: 执行任务
        """
        with self._lock:
            # 从运行任务中移除
            if task.task_id in self._running_tasks:
                del self._running_tasks[task.task_id]
            
            try:
                # 获取执行结果
                result = future.result()
                task.result = result
                
                if result.success:
                    task.status = TaskStatus.COMPLETED
                    self._statistics["completed_tasks"] += 1
                    logger.debug(f"任务执行成功: {task.task_id}")
                else:
                    task.status = TaskStatus.FAILED
                    task.error = result.error
                    self._statistics["failed_tasks"] += 1
                    logger.debug(f"任务执行失败: {task.task_id}")
                    
                    # 检查是否需要重试
                    if (self.config.enable_retry and 
                        task.retry_count < task.max_retries and 
                        task.status == TaskStatus.FAILED):
                        self._schedule_retry(task)
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                self._statistics["failed_tasks"] += 1
                logger.error(f"任务执行异常: {task.task_id}, 错误: {e}")
                
                # 检查是否需要重试
                if (self.config.enable_retry and 
                    task.retry_count < task.max_retries):
                    self._schedule_retry(task)
            
            finally:
                task.completed_at = datetime.now()
                self._statistics["queue_size"] = self._task_queue.qsize()
    
    def _schedule_retry(self, task: ExecutionTask) -> None:
        """调度重试
        
        Args:
            task: 执行任务
        """
        task.retry_count += 1
        task.status = TaskStatus.PENDING
        
        # 计算重试延迟
        retry_delay = min(
            self.config.default_retry_delay * (self.config.retry_backoff_factor ** (task.retry_count - 1)),
            self.config.max_retry_delay
        )
        
        # 计划重试时间
        retry_time = datetime.now() + timedelta(seconds=retry_delay)
        task.scheduled_at = retry_time
        
        # 重新提交任务
        if self.config.enable_priority_queue:
            priority_value = 5 - task.priority.value
            self._task_queue.put((priority_value, task))
        else:
            self._task_queue.put(task)
        
        logger.info(f"任务已安排重试: {task.task_id}, 第{task.retry_count}次重试, 延迟: {retry_delay:.2f}秒")
    
    def cleanup_completed_tasks(self, max_age: timedelta = timedelta(hours=1)) -> int:
        """清理已完成的任务
        
        Args:
            max_age: 最大保留时间
            
        Returns:
            int: 清理的任务数量
        """
        with self._lock:
            cutoff_time = datetime.now() - max_age
            tasks_to_remove = []
            
            for task_id, task in self._tasks.items():
                if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                    task.completed_at and task.completed_at < cutoff_time):
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self._tasks[task_id]
            
            logger.info(f"已清理 {len(tasks_to_remove)} 个已完成任务")
            return len(tasks_to_remove)