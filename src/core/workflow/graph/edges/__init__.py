"""边实现

提供各种类型的边实现。

边类型：
├─ SimpleEdge: 简单边（无条件判断的节点连接）
├─ ConditionalEdge: 条件边（基于条件判断的节点连接）
└─ FlexibleConditionalEdge: 灵活条件边（基于路由函数的节点连接）

使用方式：
1. 通过EdgeRegistry注册边类型（位于 src.core.workflow.registry）
2. 创建边实例并添加到工作流图
3. 配置边参数和条件
"""

from .base import BaseEdge
from .simple_edge import SimpleEdge
from .conditional_edge import ConditionalEdge
from .flexible_conditional_edge import FlexibleConditionalEdge

__all__ = [
    "BaseEdge",
    "SimpleEdge",
    "ConditionalEdge",
    "FlexibleConditionalEdge",
]

