"""触发器函数模块

提供灵活的触发器函数管理功能，支持配置驱动的触发器函数管理。
"""

from .registry import TriggerFunctionRegistry, TriggerFunctionConfig
from .manager import TriggerFunctionManager, get_trigger_function_manager
from .loader import TriggerFunctionLoader
# from .rest import BuiltinTriggerFunctions  # 模块不存在，已注释
from .config import TriggerCompositionConfig, TriggerFunctionConfigLoader

__all__ = [
    "TriggerFunctionRegistry",
    "TriggerFunctionConfig", 
    "TriggerFunctionManager",
    "TriggerFunctionLoader",
    # "BuiltinTriggerFunctions",  # 模块不存在，已移除
    "TriggerCompositionConfig",
    "TriggerFunctionConfigLoader",
    "get_trigger_function_manager",
]