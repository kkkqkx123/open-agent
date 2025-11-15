"""边定义系统

定义工作流中节点之间的连接关系和条件路由。
"""

from .simple_edge import SimpleEdge
from .conditional_edge import ConditionalEdge
from .flexible_conditional_edge import FlexibleConditionalEdge, FlexibleConditionalEdgeFactory

__all__ = [
    "SimpleEdge",
    "ConditionalEdge",
    "FlexibleConditionalEdge",
    "FlexibleConditionalEdgeFactory",
]