"""Graph sub-module for workflow core.

This module provides graph-related functionality for workflows,
including nodes, edges, builders, and routing systems.
"""

from src.interfaces.workflow.graph import (
    IGraph,
    INode,
    IEdge,
    IGraphBuilder,
    INodeRegistry,
    IRoutingFunction,
    IRoutingRegistry,
    NodeExecutionResult
)
from .decorators import node
from .registry import (
    NodeRegistry,
    register_node,
    get_global_registry,
    get_node_class,
    get_node_instance,
    list_node_types
)
from .nodes import (
    LLMNode,
    ToolNode,
    ConditionNode,
    WaitNode,
    StartNode,
    EndNode
)
from .edges import (
    BaseEdge,
    SimpleEdge,
    ConditionalEdge,
    FlexibleConditionalEdge
)
# GraphBuilder 已移除，因为接口已移至 src/interfaces
# from .builder import GraphBuilder

__all__ = [
    # Interfaces
    "IGraph",
    "INode",
    "IEdge",
    "IGraphBuilder",
    "INodeRegistry",
    "IRoutingFunction",
    "IRoutingRegistry",
    
    # Decorators
    "node",
    
    # Registry
    "NodeRegistry",
    "register_node",
    "get_global_registry",
    "get_node_class",
    "get_node_instance",
    "list_node_types",
    
    # Nodes
    "LLMNode",
    "ToolNode",
    "ConditionNode",
    "WaitNode",
    "StartNode",
    "EndNode",
    
    # Edges
    "BaseEdge",
    "SimpleEdge",
    "ConditionalEdge",
    "FlexibleConditionalEdge",
]