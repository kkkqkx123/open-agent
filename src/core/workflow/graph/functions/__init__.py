"""Core层函数实现

提供符合IFunction接口的函数实现，包括节点函数、条件函数、路由函数和触发器函数。
这些实现直接在Core层提供，避免了与基础设施层的重复实现。
"""

from .nodes import BuiltinNodeFunctions
from .conditions import BuiltinConditionFunctions
from .routing import BuiltinRouteFunctions
from .triggers import BuiltinTriggerFunctions

__all__ = [
    "BuiltinNodeFunctions",
    "BuiltinConditionFunctions", 
    "BuiltinRouteFunctions",
    "BuiltinTriggerFunctions",
]