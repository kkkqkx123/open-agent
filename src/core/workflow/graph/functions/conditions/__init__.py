"""Core层条件函数实现

提供符合IConditionFunction接口的条件函数实现。
"""

from .builtin import (
    HasToolCallsCondition,
    NoToolCallsCondition,
    HasToolResultsCondition,
    HasErrorsCondition,
    MaxIterationsReachedCondition,
)

__all__ = [
    "HasToolCallsCondition",
    "NoToolCallsCondition",
    "HasToolResultsCondition",
    "HasErrorsCondition",
    "MaxIterationsReachedCondition",
]