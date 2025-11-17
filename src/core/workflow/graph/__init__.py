"""图子模块

提供工作流图的基础设施，包括节点、边和构建器。
"""

from .interfaces import (
    IGraph, INode, IEdge, IGraphBuilder, INodeRegistry, 
    IRoutingFunction, IRoutingRegistry, NodeExecutionResult
)

__all__ = [
    "IGraph", "INode", "IEdge", "IGraphBuilder", "INodeRegistry",
    "IRoutingFunction", "IRoutingRegistry", "NodeExecutionResult"
]