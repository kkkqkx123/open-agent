"""Hook链实现

支持Hook的链式执行和条件执行。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# 从接口层导入，保持一致性
from src.interfaces.workflow.hooks import HookPoint, HookContext, HookExecutionResult, IHook as IHookPlugin

__all__ = (
    "ExecutionMode",
    "IHookPlugin",
    "HookContext",
    "HookExecutionResult",
    "HookChain",
)


class ExecutionMode(Enum):
    """Hook链执行模式。"""
    SEQUENCE = "sequence"
    """顺序执行"""
    PARALLEL = "parallel"
    """并行执行"""
    CONDITIONAL = "conditional"
    """条件执行"""


# 重新导出接口层的类型，确保一致性
# 这样可以避免类型冲突


class HookChain:
    """Hook链，支持多个Hook的有序执行。"""
    
    def __init__(
        self,
        name: str,
        hooks: List[IHookPlugin],
        mode: ExecutionMode = ExecutionMode.SEQUENCE
    ):
        self.name = name
        self.hooks = sorted(hooks, key=lambda h: h.name)
        self.mode = mode
    
    async def execute(self, context: HookContext) -> HookExecutionResult:
        """执行Hook链。
        
        Args:
            context: Hook执行上下文
            
        Returns:
            Hook执行结果
        """
        if self.mode == ExecutionMode.SEQUENCE:
            return await self._execute_sequence(context)
        elif self.mode == ExecutionMode.PARALLEL:
            return await self._execute_parallel(context)
        elif self.mode == ExecutionMode.CONDITIONAL:
            return await self._execute_conditional(context)
        else:
            raise ValueError(f"Unsupported execution mode: {self.mode}")
    
    async def _execute_sequence(self, context: HookContext) -> HookExecutionResult:
        """顺序执行Hook。"""
        results = []
        errors = []
        
        for hook in self.hooks:
            try:
                # 根据Hook点调用相应方法
                if context.hook_point == HookPoint.BEFORE_EXECUTE:
                    result = hook.before_execute(context)
                elif context.hook_point == HookPoint.AFTER_EXECUTE:
                    result = hook.after_execute(context)
                elif context.hook_point == HookPoint.ON_ERROR:
                    result = hook.on_error(context)
                else:
                    continue
                results.append(result)
            except Exception as e:
                errors.append(e)
                # 在顺序模式下，遇到错误就停止执行
                break
        
        # 合并结果
        should_continue = True
        modified_state = context.state
        modified_result = context.execution_result
        force_next_node = None
        metadata = {"executed_hooks": []}
        
        for result in results:
            if not result.should_continue:
                should_continue = False
            
            if result.modified_state:
                modified_state = result.modified_state
            
            if result.modified_result:
                modified_result = result.modified_result
            
            if result.force_next_node:
                force_next_node = result.force_next_node
            
            if result.metadata:
                metadata.update(result.metadata)
        
        return HookExecutionResult(
            should_continue=should_continue,
            modified_state=modified_state,
            modified_result=modified_result,
            force_next_node=force_next_node,
            metadata=metadata
        )
    
    async def _execute_parallel(self, context: HookContext) -> HookExecutionResult:
        """并行执行Hook。"""
        import asyncio
        
        tasks = []
        for hook in self.hooks:
            # 根据Hook点创建相应的任务
            if context.hook_point == HookPoint.BEFORE_EXECUTE:
                task = asyncio.create_task(self._execute_hook_safe(hook.before_execute, context))
            elif context.hook_point == HookPoint.AFTER_EXECUTE:
                task = asyncio.create_task(self._execute_hook_safe(hook.after_execute, context))
            elif context.hook_point == HookPoint.ON_ERROR:
                task = asyncio.create_task(self._execute_hook_safe(hook.on_error, context))
            else:
                continue
            tasks.append(task)
        
        results = []
        errors = []
        
        # 使用gather并设置return_exceptions=True来收集所有结果
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for task_result in completed_tasks:
            if isinstance(task_result, Exception):
                errors.append(task_result)
            else:
                results.append(task_result)
        
        # 合并结果
        should_continue = True
        modified_state = context.state
        modified_result = context.execution_result
        force_next_node = None
        metadata = {"executed_hooks": []}
        
        for result in results:
            if not result.should_continue:
                should_continue = False
            
            if result.modified_state:
                modified_state = result.modified_state
            
            if result.modified_result:
                modified_result = result.modified_result
            
            if result.force_next_node:
                force_next_node = result.force_next_node
            
            if result.metadata:
                metadata.update(result.metadata)
        
        return HookExecutionResult(
            should_continue=should_continue,
            modified_state=modified_state,
            modified_result=modified_result,
            force_next_node=force_next_node,
            metadata=metadata
        )
    
    async def _execute_conditional(self, context: HookContext) -> HookExecutionResult:
        """条件执行Hook。"""
        results = []
        errors = []
        
        for hook in self.hooks:
            try:
                # 检查是否应该执行此Hook
                if await self._should_execute_hook(hook, context):
                    # 根据Hook点调用相应方法
                    if context.hook_point == HookPoint.BEFORE_EXECUTE:
                        result = hook.before_execute(context)
                    elif context.hook_point == HookPoint.AFTER_EXECUTE:
                        result = hook.after_execute(context)
                    elif context.hook_point == HookPoint.ON_ERROR:
                        result = hook.on_error(context)
                    else:
                        continue
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        # 合并结果
        should_continue = True
        modified_state = context.state
        modified_result = context.execution_result
        force_next_node = None
        metadata = {"executed_hooks": []}
        
        for result in results:
            if not result.should_continue:
                should_continue = False
            
            if result.modified_state:
                modified_state = result.modified_state
            
            if result.modified_result:
                modified_result = result.modified_result
            
            if result.force_next_node:
                force_next_node = result.force_next_node
            
            if result.metadata:
                metadata.update(result.metadata)
        
        return HookExecutionResult(
            should_continue=should_continue,
            modified_state=modified_state,
            modified_result=modified_result,
            force_next_node=force_next_node,
            metadata=metadata
        )
    
    async def _execute_hook_safe(self, hook_func, context: HookContext) -> HookExecutionResult:
        """安全执行Hook函数"""
        try:
            return hook_func(context)
        except Exception as e:
            # 返回一个错误结果
            return HookExecutionResult(
                should_continue=True,
                metadata={"error": str(e)}
            )
    
    async def _should_execute_hook(self, hook: IHookPlugin, context: HookContext) -> bool:
        """判断是否应该执行Hook。
        
        默认实现总是返回True，子类可以覆盖此方法来实现条件逻辑。
        """
        return True
    
    def add_hook(self, hook: IHookPlugin) -> None:
        """添加Hook到链中。"""
        self.hooks.append(hook)
        self.hooks.sort(key=lambda h: h.name)
    
    def remove_hook(self, hook_name: str) -> bool:
        """从链中移除Hook。
         
        Args:
             hook_name: Hook名称
             
        Returns:
             是否成功移除
        """
        for i, hook in enumerate(self.hooks):
            if hook.name == hook_name:
                self.hooks.pop(i)
                return True
        return False