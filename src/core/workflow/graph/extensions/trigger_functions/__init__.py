"""触发器函数模块

提供灵活的触发器函数管理功能，支持配置驱动的触发器函数管理。
"""

from .registry import TriggerFunctionRegistry, TriggerFunctionConfig
from .manager import TriggerFunctionManager, get_trigger_function_manager
from .loader import TriggerFunctionLoader
from .builtin import BuiltinTriggerFunctions
from .config import TriggerCompositionConfig, TriggerFunctionConfigLoader
from .impl import (
    TimeTriggerImplementation,
    StateTriggerImplementation,
    EventTriggerImplementation,
    ToolErrorTriggerImplementation,
    IterationLimitTriggerImplementation,
)

__all__ = [
    "TriggerFunctionRegistry",
    "TriggerFunctionConfig",
    "TriggerFunctionManager",
    "TriggerFunctionLoader",
    "BuiltinTriggerFunctions",
    "TriggerCompositionConfig",
    "TriggerFunctionConfigLoader",
    "get_trigger_function_manager",
    # 实现类
    "TimeTriggerImplementation",
    "StateTriggerImplementation",
    "EventTriggerImplementation",
    "ToolErrorTriggerImplementation",
    "IterationLimitTriggerImplementation",
]