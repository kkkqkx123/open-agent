"""扩展模块

提供图系统的扩展功能，包括触发器和插件。
"""

from .triggers import *
from .plugins import *
from .trigger_functions import *

__all__ = [
    # 触发器相关
    "ITrigger",
    "BaseTrigger",
    "TriggerType",
    "TriggerEvent",
    "TriggerHandler",
    "MonitoringTrigger",
    "TimingInfo",
    "StateChangeInfo",
    "MemoryInfo",
    "TimeTrigger",
    "StateTrigger",
    "EventTrigger",
    "CustomTrigger",
    "ToolErrorTrigger",
    "IterationLimitTrigger",
    "ToolExecutionTimingTrigger",
    "LLMResponseTimingTrigger",
    "WorkflowStateTimingTrigger",
    "WorkflowStateCaptureTrigger",
    "WorkflowStateChangeTrigger",
    "WorkflowErrorStateTrigger",
    "UserInputPatternTrigger",
    "LLMOutputPatternTrigger",
    "ToolOutputPatternTrigger",
    "StatePatternTrigger",
    "TriggerFactory",
    "get_trigger_factory",
    "reset_trigger_factory",
    "TriggerSystem",
    "WorkflowTriggerSystem",
    
    # 插件相关
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
    "BasePlugin",
    "PluginRegistry",
    "PluginManager",
    "ContextSummaryPlugin",
    "EnvironmentCheckPlugin",
    "MetadataCollectorPlugin",
    "CleanupManagerPlugin",
    "ExecutionStatsPlugin",
    "FileTrackerPlugin",
    "ResultSummaryPlugin",
    "DeadLoopDetectionPlugin",
    "ErrorRecoveryPlugin",
    "LoggingPlugin",
    "MetricsCollectionPlugin",
    "PerformanceMonitoringPlugin"
]