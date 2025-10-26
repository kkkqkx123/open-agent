"""触发器系统模块

提供事件驱动的节点执行功能。
"""

from .base import ITrigger, TriggerType, TriggerEvent
from .system import TriggerSystem
from .builtin_triggers import (
    TimeTrigger,
    StateTrigger,
    EventTrigger,
    CustomTrigger
)

__all__ = [
    "ITrigger",
    "TriggerType",
    "TriggerEvent",
    "TriggerSystem",
    "TimeTrigger",
    "StateTrigger",
    "EventTrigger",
    "CustomTrigger",
]