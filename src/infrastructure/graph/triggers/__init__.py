"""触发器系统模块

提供事件驱动的节点执行功能，支持基于函数组合的灵活触发器架构。
"""

from .base import ITrigger, TriggerType, TriggerEvent
from .system import TriggerSystem, WorkflowTriggerSystem
from .builtin_triggers import (
    TimeTrigger,
    StateTrigger,
    EventTrigger,
    CustomTrigger,
    ToolErrorTrigger,
    IterationLimitTrigger
)
from .factory import TriggerFactory
from ..trigger_functions import get_trigger_function_manager

__all__ = [
    "ITrigger",
    "TriggerType",
    "TriggerEvent",
    "TriggerSystem",
    "WorkflowTriggerSystem",
    "TimeTrigger",
    "StateTrigger",
    "EventTrigger",
    "CustomTrigger",
    "ToolErrorTrigger",
    "IterationLimitTrigger",
    "TriggerFactory",
    "get_trigger_function_manager",
]