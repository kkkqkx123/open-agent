"""Core层路由函数实现

提供符合IRouteFunction接口的路由函数实现。
"""

from .builtin import (
    HasToolCallsRouteFunction,
    NoToolCallsRouteFunction,
    HasToolResultsRouteFunction,
    MaxIterationsReachedRouteFunction,
    HasErrorsRouteFunction,
)

__all__ = [
    "HasToolCallsRouteFunction",
    "NoToolCallsRouteFunction",
    "HasToolResultsRouteFunction",
    "MaxIterationsReachedRouteFunction",
    "HasErrorsRouteFunction",
]