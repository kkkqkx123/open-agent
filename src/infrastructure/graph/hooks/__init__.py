"""基础设施层Hook系统

提供图级别的Hook机制，支持在执行过程中插入自定义逻辑。
"""

from .hook_system import HookSystem
from .hook_points import HookPoint
from .conditional_hooks import ConditionalHook
from .hook_chains import HookChain, HookContext, HookExecutionResult, ExecutionMode, IHookPlugin

__all__ = [
    "HookSystem",
    "HookPoint",
    "ConditionalHook",
    "HookChain",
    "HookContext",
    "HookExecutionResult",
    "ExecutionMode",
    "IHookPlugin",
]