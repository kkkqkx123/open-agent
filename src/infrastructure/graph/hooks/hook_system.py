"""Hook系统核心实现

提供Hook注册、管理和执行的核心功能。
"""

from typing import Any, Dict, List, Optional

from .conditional_hooks import ConditionalHook
from .hook_chains import HookChain, HookContext, HookExecutionResult, IHookPlugin
from .hook_points import HookPoint

__all__ = ("HookSystem",)


class HookSystem:
    """Hook系统，管理所有Hook的注册和执行。"""
    
    def __init__(self):
        """初始化Hook系统。"""
        self.hooks: Dict[HookPoint, List[HookRegistration]] = {}
        self.conditional_hooks: List[ConditionalHook] = []
        self.hook_chains: Dict[str, HookChain] = {}
    
    def register_hook(
        self,
        hook_point: HookPoint,
        hook: IHookPlugin,
        priority: int = 50
    ) -> None:
        """注册Hook。
        
        Args:
            hook_point: Hook点
            hook: Hook插件
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
        hook_name: str
    ) -> bool:
        """注销Hook。
        
        Args:
            hook_point: Hook点
            hook_name: Hook名称
            
        Returns:
            是否成功注销
        """
        if hook_point not in self.hooks:
            return False
        
        for i, registration in enumerate(self.hooks[hook_point]):
            if registration.hook.name == hook_name:
                self.hooks[hook_point].pop(i)
                return True
        
        return False
    
    def register_conditional_hook(self, conditional_hook: ConditionalHook) -> None:
        """注册条件Hook。
        
        Args:
            conditional_hook: 条件Hook
        """
        self.conditional_hooks.append(conditional_hook)
    
    def create_hook_chain(
        self,
        name: str,
        hooks: List[IHookPlugin],
        mode: Any  # ExecutionMode
    ) -> HookChain:
        """创建Hook链。
        
        Args:
            name: Hook链名称
            hooks: Hook列表
            mode: 执行模式
            
        Returns:
            Hook链实例
        """
        chain = HookChain(name, hooks, mode)
        self.hook_chains[name] = chain
        return chain
    
    def get_hook_chain(self, name: str) -> Optional[HookChain]:
        """获取Hook链。
        
        Args:
            name: Hook链名称
            
        Returns:
            Hook链实例（如果存在）
        """
        return self.hook_chains.get(name)
    
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
                    result = await registration.hook.execute(context)
                    results.append(result)
                except Exception as e:
                    errors.append(e)
        
        # 执行条件Hook
        for conditional_hook in self.conditional_hooks:
            if conditional_hook.hook_point == hook_point:
                try:
                    if conditional_hook.should_execute(context):
                        result = await conditional_hook.execute(context)
                        results.append(result)
                except Exception as e:
                    errors.append(e)
        
        return HookExecutionResult(
            success=len(errors) == 0,
            results=results,
            errors=errors
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
        chain = self.hook_chains.get(chain_name)
        if not chain:
            raise ValueError(f"Hook chain not found: {chain_name}")
        
        return await chain.execute(context)
    
    def get_hooks_for_point(self, hook_point: HookPoint) -> List[IHookPlugin]:
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
    
    def __init__(self, hook: IHookPlugin, priority: int):
        self.hook = hook
        self.priority = priority