"""条件类型定义

定义所有支持的条件类型枚举。
"""

from enum import Enum


class ConditionType(Enum):
    """条件类型枚举"""
    HAS_TOOL_CALLS = "has_tool_calls"
    NO_TOOL_CALLS = "no_tool_calls"
    HAS_TOOL_RESULTS = "has_tool_results"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    HAS_ERRORS = "has_errors"
    NO_ERRORS = "no_errors"
    MESSAGE_CONTAINS = "message_contains"
    ITERATION_COUNT_EQUALS = "iteration_count_equals"
    ITERATION_COUNT_GREATER_THAN = "iteration_count_greater_than"
    CUSTOM = "custom"