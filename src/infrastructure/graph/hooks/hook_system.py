"""Hook系统核心实现

提供Hook注册、管理和执行的核心功能。
"""

from typing import Any, Dict, List, Optional

from src.interfaces.workflow.hooks import IHookSystem, HookPoint, HookContext, HookExecutionResult, IHook
from .conditional_hooks import ConditionalHook

__all__ = ("HookSystem",)


class HookSystem(IHookSystem):
    """Hook系统，管理所有Hook的注册和执行。"""
    
    def __init__(self):
        """初始化Hook系统。"""
        self.hooks: Dict[HookPoint, List[HookRegistration]] = {}
        self.conditional_hooks: List[ConditionalHook] = []
        self.hook_chains: Dict[str, Any] = {}  # 简化实现，不使用HookChain
    
    def register_hook(
        self,
        hook_point: HookPoint,
        hook: IHook,
        priority: int = 50
    ) -> None:
        """注册Hook。
        
        Args:
            hook_point: Hook点
            hook: Hook实例
            priority: 优先级，数值越小优先级越高
        """
        if hook_point not in self.hooks:
            self.hooks[hook_point] = []
        
        registration = HookRegistration(hook, priority)
        self.hooks[hook_point].append(registration)
        
        # 按优先级排序
        self.hooks[hook_point].sort(key=lambda r: r.priority)
    
    def unregister_hook(
        self,
        hook_point: HookPoint,
        hook_id: str
    ) -> bool:
        """注销Hook。
        
        Args:
            hook_point: Hook点
            hook_id: Hook ID
            
        Returns:
            是否成功注销
        """
        if hook_point not in self.hooks:
            return False
        
        for i, registration in enumerate(self.hooks[hook_point]):
            if registration.hook.hook_id == hook_id:
                self.hooks[hook_point].pop(i)
                return True
        
        return False
    
    def register_conditional_hook(self, conditional_hook: ConditionalHook) -> None:
        """注册条件Hook。
        
        Args:
            conditional_hook: 条件Hook
        """
        self.conditional_hooks.append(conditional_hook)
    
    async def execute_hooks(
        self,
        hook_point: HookPoint,
        context: HookContext
    ) -> HookExecutionResult:
        """执行Hook。
        
        Args:
            hook_point: Hook点
            context: Hook执行上下文
            
        Returns:
            Hook执行结果
        """
        results = []
        errors = []
        
        # 执行普通Hook
        if hook_point in self.hooks:
            for registration in self.hooks[hook_point]:
                try:
                    # 根据Hook点调用相应方法
                    if hook_point == HookPoint.BEFORE_EXECUTE:
                        result = registration.hook.before_execute(context)
                    elif hook_point == HookPoint.AFTER_EXECUTE:
                        result = registration.hook.after_execute(context)
                    elif hook_point == HookPoint.ON_ERROR:
                        result = registration.hook.on_error(context)
                    elif hook_point == HookPoint.BEFORE_COMPILE:
                        result = registration.hook.before_compile(context)
                    elif hook_point == HookPoint.AFTER_COMPILE:
                        result = registration.hook.after_compile(context)
                    else:
                        continue
                    results.append(result)
                except Exception as e:
                    errors.append(e)
        
        # 执行条件Hook
        for conditional_hook in self.conditional_hooks:
            if conditional_hook.hook_point == hook_point:
                try:
                    if conditional_hook.should_execute(context):
                        # 根据Hook点调用相应方法
                        if hook_point == HookPoint.BEFORE_EXECUTE:
                            result = conditional_hook.hook_plugin.before_execute(context)
                        elif hook_point == HookPoint.AFTER_EXECUTE:
                            result = conditional_hook.hook_plugin.after_execute(context)
                        elif hook_point == HookPoint.ON_ERROR:
                            result = conditional_hook.hook_plugin.on_error(context)
                        elif hook_point == HookPoint.BEFORE_COMPILE:
                            result = conditional_hook.hook_plugin.before_compile(context)
                        elif hook_point == HookPoint.AFTER_COMPILE:
                            result = conditional_hook.hook_plugin.after_compile(context)
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
    
    async def execute_hook_chain(
        self,
        chain_name: str,
        context: HookContext
    ) -> HookExecutionResult:
        """执行Hook链。
        
        Args:
            chain_name: Hook链名称
            context: Hook执行上下文
            
        Returns:
            Hook执行结果
        """
        # 简化实现，直接执行所有Hook
        return await self.execute_hooks(context.hook_point, context)
    
    def get_hooks_for_point(self, hook_point: HookPoint) -> List[IHook]:
        """获取指定Hook点的所有Hook。
        
        Args:
            hook_point: Hook点
            
        Returns:
            Hook列表
        """
        hooks = []
        
        if hook_point in self.hooks:
            hooks.extend(reg.hook for reg in self.hooks[hook_point])
        
        # 添加符合条件的条件Hook
        for conditional_hook in self.conditional_hooks:
            if conditional_hook.hook_point == hook_point:
                hooks.append(conditional_hook.hook_plugin)
        
        return hooks
    
    def clear_hooks(self, hook_point: Optional[HookPoint] = None) -> None:
        """清除Hook。
        
        Args:
            hook_point: 要清除的Hook点，如果为None则清除所有
        """
        if hook_point is None:
            self.hooks.clear()
            self.conditional_hooks.clear()
        else:
            self.hooks.pop(hook_point, None)
            self.conditional_hooks = [
                ch for ch in self.conditional_hooks
                if ch.hook_point != hook_point
            ]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息。
        
        Returns:
            统计信息字典
        """
        stats = {
            "total_hooks": sum(len(hooks) for hooks in self.hooks.values()),
            "conditional_hooks": len(self.conditional_hooks),
            "hook_chains": len(self.hook_chains),
            "hook_points": {}
        }
        
        for hook_point, hooks in self.hooks.items():
            stats["hook_points"][hook_point.value] = len(hooks)
        
        return stats


class HookRegistration:
    """Hook注册信息。"""
    
    def __init__(self, hook: IHook, priority: int):
        self.hook = hook
        self.priority = priority