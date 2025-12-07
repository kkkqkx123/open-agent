"""边实现

提供各种类型的边实现。
"""

# 从基础设施层导入基础边
from src.infrastructure.graph.edges import (
    BaseEdge,
    SimpleEdge,
)

# 从基础设施层导入条件边
from src.infrastructure.graph.edges import (
    ConditionalEdge,
    FlexibleConditionalEdge,
)

__all__ = [
    # 基础设施层基础边（重新导出）
    "BaseEdge",
    "SimpleEdge",
    # 基础设施层条件边（重新导出）
    "ConditionalEdge",
    "FlexibleConditionalEdge"
]