"""Hook链实现

支持Hook的链式执行和条件执行。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .hook_points import HookPoint

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


class IHookPlugin(ABC):
    """Hook插件接口。"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Hook插件名称。"""
        pass
    
    @abstractmethod
    async def execute(self, context: HookContext) -> Any:
        """执行Hook逻辑。
        
        Args:
            context: Hook执行上下文
            
        Returns:
            Hook执行结果
        """
        pass
    
    @property
    def priority(self) -> int:
        """Hook优先级，数值越小优先级越高。"""
        return 50


@dataclass
class HookContext:
    """Hook执行上下文。"""
    hook_point: HookPoint
    """Hook点"""
    graph_id: str
    """图ID"""
    node_id: Optional[str] = None
    """节点ID（如果适用）"""
    step: Optional[int] = None
    """步骤号（如果适用）"""
    state: Optional[Dict[str, Any]] = None
    """当前状态（如果适用）"""
    config: Optional[Dict[str, Any]] = None
    """配置信息"""
    metadata: Dict[str, Any] = field(default_factory=dict)
    """额外元数据"""
    error: Optional[Exception] = None
    """错误信息（如果适用）"""
    
    def with_node(self, node_id: str) -> HookContext:
        """创建带有节点ID的上下文副本。"""
        return HookContext(
            hook_point=self.hook_point,
            graph_id=self.graph_id,
            node_id=node_id,
            step=self.step,
            state=self.state,
            config=self.config,
            metadata=self.metadata.copy(),
            error=self.error,
        )
    
    def with_step(self, step: int) -> HookContext:
        """创建带有步骤号的上下文副本。"""
        return HookContext(
            hook_point=self.hook_point,
            graph_id=self.graph_id,
            node_id=self.node_id,
            step=step,
            state=self.state,
            config=self.config,
            metadata=self.metadata.copy(),
            error=self.error,
        )
    
    def with_error(self, error: Exception) -> HookContext:
        """创建带有错误信息的上下文副本。"""
        return HookContext(
            hook_point=self.hook_point,
            graph_id=self.graph_id,
            node_id=self.node_id,
            step=self.step,
            state=self.state,
            config=self.config,
            metadata=self.metadata.copy(),
            error=error,
        )


@dataclass
class HookExecutionResult:
    """Hook执行结果。"""
    success: bool
    """是否成功"""
    results: List[Any] = field(default_factory=list)
    """Hook执行结果列表"""
    errors: List[Exception] = field(default_factory=list)
    """错误列表"""
    metadata: Dict[str, Any] = field(default_factory=dict)
    """额外元数据"""
    
    @classmethod
    def success_result(cls, results: Optional[List[Any]] = None) -> HookExecutionResult:
        """创建成功结果。"""
        return cls(success=True, results=results or [])
    
    @classmethod
    def failure_result(cls, errors: Optional[List[Exception]] = None) -> HookExecutionResult:
        """创建失败结果。"""
        return cls(success=False, errors=errors or [])


class HookChain:
    """Hook链，支持多个Hook的有序执行。"""
    
    def __init__(
        self,
        name: str,
        hooks: List[IHookPlugin],
        mode: ExecutionMode = ExecutionMode.SEQUENCE
    ):
        self.name = name
        self.hooks = sorted(hooks, key=lambda h: h.priority)
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
                result = await hook.execute(context)
                results.append(result)
            except Exception as e:
                errors.append(e)
                # 在顺序模式下，遇到错误就停止执行
                break
        
        return HookExecutionResult(
            success=len(errors) == 0,
            results=results,
            errors=errors
        )
    
    async def _execute_parallel(self, context: HookContext) -> HookExecutionResult:
        """并行执行Hook。"""
        import asyncio
        
        tasks = [hook.execute(context) for hook in self.hooks]
        results = []
        errors = []
        
        # 使用gather并设置return_exceptions=True来收集所有结果
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for task_result in completed_tasks:
            if isinstance(task_result, Exception):
                errors.append(task_result)
            else:
                results.append(task_result)
        
        return HookExecutionResult(
            success=len(errors) == 0,
            results=results,
            errors=errors
        )
    
    async def _execute_conditional(self, context: HookContext) -> HookExecutionResult:
        """条件执行Hook。"""
        results = []
        errors = []
        
        for hook in self.hooks:
            try:
                # 检查是否应该执行此Hook
                if await self._should_execute_hook(hook, context):
                    result = await hook.execute(context)
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        return HookExecutionResult(
            success=len(errors) == 0,
            results=results,
            errors=errors
        )
    
    async def _should_execute_hook(self, hook: IHookPlugin, context: HookContext) -> bool:
        """判断是否应该执行Hook。
        
        默认实现总是返回True，子类可以覆盖此方法来实现条件逻辑。
        """
        return True
    
    def add_hook(self, hook: IHookPlugin) -> None:
        """添加Hook到链中。"""
        self.hooks.append(hook)
        self.hooks.sort(key=lambda h: h.priority)
    
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