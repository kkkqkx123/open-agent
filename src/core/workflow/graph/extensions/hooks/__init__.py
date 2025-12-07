"""Hook系统模块

包含所有Hook相关的组件，包括基础类、注册表、管理器和内置Hook。
"""

from .base import BaseHook, ConfigurableHook
from .manager import HookManager
from src.core.workflow.registry import HookRegistry

# 内置Hook
from .metrics_collection import MetricsCollectionHook
from .logging import LoggingHook
from .performance_monitoring import PerformanceMonitoringHook
from .dead_loop_detection import DeadLoopDetectionHook
from .error_recovery import ErrorRecoveryHook

__all__ = [
    # 基础类
    "BaseHook",
    "ConfigurableHook",
    
    # 核心组件
    "HookRegistry",
    "HookManager",
    
    # 内置Hook
    "MetricsCollectionHook",
    "LoggingHook",
    "PerformanceMonitoringHook",
    "DeadLoopDetectionHook",
    "ErrorRecoveryHook"
]