"""Plugin sub-module for workflow core.

This module provides plugin system functionality for workflows,
including plugin interfaces, registry, and built-in plugins.
"""

from src.interfaces.workflow.plugins import (
    IPlugin,
    IStartPlugin,
    IEndPlugin,
    IHookPlugin,
    PluginMetadata,
    PluginType,
    PluginContext,
    HookPoint,
    HookContext,
    HookExecutionResult
)
from .base import BasePlugin
from .manager import PluginManager
from src.core.workflow.registry import PluginRegistry

# Built-in plugins
from .builtin.start import (
    ContextSummaryPlugin,
    EnvironmentCheckPlugin,
    MetadataCollectorPlugin
)
from .builtin.end import (
    CleanupManagerPlugin,
    ExecutionStatsPlugin,
    FileTrackerPlugin,
    ResultSummaryPlugin
)
from .builtin.hooks import (
    DeadLoopDetectionPlugin,
    ErrorRecoveryPlugin,
    LoggingPlugin,
    MetricsCollectionPlugin,
    PerformanceMonitoringPlugin
)

__all__ = [
    # Interfaces
    "IPlugin",
    "IStartPlugin",
    "IEndPlugin",
    "IHookPlugin",
    "PluginMetadata",
    "PluginType",
    "PluginContext",
    "HookPoint",
    "HookContext",
    "HookExecutionResult",
    
    # Base classes
    "BasePlugin",
    
    # Core implementations
    "PluginRegistry",
    "PluginManager",
    
    # Built-in start plugins
    "ContextSummaryPlugin",
    "EnvironmentCheckPlugin",
    "MetadataCollectorPlugin",
    
    # Built-in end plugins
    "CleanupManagerPlugin",
    "ExecutionStatsPlugin",
    "FileTrackerPlugin",
    "ResultSummaryPlugin",
    
    # Built-in hook plugins
    "DeadLoopDetectionPlugin",
    "ErrorRecoveryPlugin",
    "LoggingPlugin",
    "MetricsCollectionPlugin",
    "PerformanceMonitoringPlugin"
]