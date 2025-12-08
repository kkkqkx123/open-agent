"""条件函数基础设施层实现

提供符合IFunction接口的条件函数实现。
"""

from .builtin import BuiltinConditionFunctions

__all__ = [
    "BuiltinConditionFunctions",
]