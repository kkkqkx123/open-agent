"""基础设施层Hook系统

提供图级别的Hook机制，支持在执行过程中插入自定义逻辑。
"""

from .hook_system import HookSystem
from .hook_points import HookPoint
from .conditional_hooks import ConditionalHook
from .hook_chains import HookChain, ExecutionMode
from .workflow_hook_executor import WorkflowHookExecutor

# 从接口层导入，保持一致性
from src.interfaces.workflow.hooks import HookContext, HookExecutionResult, IHook

__all__ = [
    "HookSystem",
    "HookPoint",
    "ConditionalHook",
    "HookChain",
    "HookContext",
    "HookExecutionResult",
    "ExecutionMode",
    "IHook",
    "WorkflowHookExecutor",
]