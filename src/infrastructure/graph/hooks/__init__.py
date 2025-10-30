"""Graph节点Hook系统

提供灵活的节点Hook机制，支持死循环检测、性能监控、错误恢复等功能。
"""

from .interfaces import INodeHook, IHookManager
from .manager import NodeHookManager
from .config import HookConfig, NodeHookConfig, GlobalHookConfig
from .decorators import with_hooks, hook_node
from .builtin import (
    DeadLoopDetectionHook,
    PerformanceMonitoringHook,
    ErrorRecoveryHook,
    LoggingHook,
    MetricsCollectionHook,
    create_builtin_hook
)
# Moved to nodes module to avoid circular import
from ..hook_aware_builder import HookAwareGraphBuilder, create_hook_aware_builder
from .trigger_coordinator import HookTriggerCoordinator

__all__ = [
    "INodeHook",
    "IHookManager",
    "NodeHookManager",
    "HookConfig",
    "NodeHookConfig",
    "GlobalHookConfig",
    "with_hooks",
    "hook_node",
    "DeadLoopDetectionHook",
    "PerformanceMonitoringHook",
    "ErrorRecoveryHook",
    "LoggingHook",
    "MetricsCollectionHook",
    "create_builtin_hook",
    "HookAwareGraphBuilder",
    "create_hook_aware_builder",
    "HookTriggerCoordinator",
]