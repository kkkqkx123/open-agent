"""条件判断模块

提供统一的条件判断功能，供条件节点和条件边使用。
"""

from .condition_types import ConditionType
from .condition_evaluator import ConditionEvaluator

__all__ = [
    "ConditionType",
    "ConditionEvaluator"
]