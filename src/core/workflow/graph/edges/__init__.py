"""边实现

提供各种类型的边实现。
"""

from .base import BaseEdge
from .simple_edge import SimpleEdge
from .conditional_edge import ConditionalEdge
from .flexible_edge import FlexibleConditionalEdge

__all__ = [
    "BaseEdge",
    "SimpleEdge",
    "ConditionalEdge",
    "FlexibleConditionalEdge"
]