"""触发器函数基础设施层实现

提供符合IFunction接口的触发器函数实现。
"""

from .builtin import BuiltinTriggerFunctions

__all__ = [
    "BuiltinTriggerFunctions",
]