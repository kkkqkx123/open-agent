"""任务调度器实现

提供智能任务调度和并发执行功能。
"""

import asyncio
from typing import Any, Dict, List, Optional, Set

from ..types import ExecutableTask

__all__ = ("TaskScheduler",)


class TaskScheduler:
    """任务调度器，提供智能任务调度和并发执行功能。"""
    
    def __init__(self):
        """初始化任务调度器。"""
        self.task_queue: List[ExecutableTask] = []
        self.running_tasks: Set[str] = set()
        self.completed_tasks: Set[str] = set()
        self.max_concurrent_tasks = 10
        self.task_dependencies: Dict[str, List[str]] = {}
    
    def set_max_concurrent_tasks(self, max_tasks: int) -> None:
        """设置最大并发任务数。
        
        Args:
            max_tasks: 最大并发任务数
        """
        self.max_concurrent_tasks = max_tasks
    
    def add_task(self, task: ExecutableTask) -> None:
        """添加任务到调度队列。
        
        Args:
            task: 可执行任务
        """
        self.task_queue.append(task)
    
    def add_tasks(self, tasks: List[ExecutableTask]) -> None:
        """添加多个任务到调度队列。
        
        Args:
            tasks: 可执行任务列表
        """
        self.task_queue.extend(tasks)
    
    def set_task_dependencies(self, task_id: str, dependencies: List[str]) -> None:
        """设置任务依赖关系。
        
        Args:
            task_id: 任务ID
            dependencies: 依赖的任务ID列表
        """
        self.task_dependencies[task_id] = dependencies
    
    async def schedule_tasks(self) -> List[Any]:
        """调度并执行任务。
        
        Returns:
            任务执行结果列表
        """
        results = []
        
        while self.task_queue or self.running_tasks:
            # 获取可执行的任务
            ready_tasks = self._get_ready_tasks()
            
            # 执行任务
            if ready_tasks:
                # 限制并发数
                tasks_to_run = ready_tasks[:self.max_concurrent_tasks - len(self.running_tasks)]
                
                # 并发执行任务
                if tasks_to_run:
                    coroutines = [self._execute_task(task) for task in tasks_to_run]
                    task_results = await asyncio.gather(*coroutines, return_exceptions=True)
                    
                    for result in task_results:
                        if isinstance(result, Exception):
                            # 处理异常
                            results.append({"error": str(result)})
                        else:
                            results.append(result)
            
            # 短暂等待，避免忙循环
            await asyncio.sleep(0.01)
        
        return results
    
    def _get_ready_tasks(self) -> List[ExecutableTask]:
        """获取准备执行的任务。
        
        Returns:
            准备执行的任务列表
        """
        ready_tasks = []
        
        for task in self.task_queue:
            if (task.id not in self.running_tasks and 
                task.id not in self.completed_tasks and
                self._are_dependencies_completed(task.id)):
                ready_tasks.append(task)
        
        # 从队列中移除准备执行的任务
        for task in ready_tasks:
            self.task_queue.remove(task)
            self.running_tasks.add(task.id)
        
        return ready_tasks
    
    def _are_dependencies_completed(self, task_id: str) -> bool:
        """检查任务依赖是否已完成。
        
        Args:
            task_id: 任务ID
            
        Returns:
            依赖是否已完成
        """
        dependencies = self.task_dependencies.get(task_id, [])
        return all(dep_id in self.completed_tasks for dep_id in dependencies)
    
    async def _execute_task(self, task: ExecutableTask) -> Any:
        """执行单个任务。
        
        Args:
            task: 可执行任务
            
        Returns:
            任务执行结果
        """
        try:
            # 执行任务
            if asyncio.iscoroutinefunction(task.proc):
                result = await task.proc(task.input, task.config)
            else:
                result = task.proc(task.input, task.config)
            
            # 标记任务完成
            self.running_tasks.discard(task.id)
            self.completed_tasks.add(task.id)
            
            return {
                "task_id": task.id,
                "result": result,
                "status": "completed"
            }
            
        except Exception as e:
            # 标记任务失败
            self.running_tasks.discard(task.id)
            
            return {
                "task_id": task.id,
                "error": str(e),
                "status": "failed"
            }
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """获取调度器统计信息。
        
        Returns:
            统计信息字典
        """
        return {
            "queued_tasks": len(self.task_queue),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "total_dependencies": len(self.task_dependencies)
        }
    
    def reset(self) -> None:
        """重置调度器状态。"""
        self.task_queue.clear()
        self.running_tasks.clear()
        self.completed_tasks.clear()
        self.task_dependencies.clear()