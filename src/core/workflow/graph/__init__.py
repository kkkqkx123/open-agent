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
    EdgeRegistry,
    FunctionRegistry,
    GlobalRegistry,
    get_global_registry
)
from .registry.global_registry import (
    register_node,
    register_edge,
    register_node_function,
    register_route_function,
    get_node_class,
    get_edge_class,
    get_node_function,
    get_route_function
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
from .service import GraphService, get_graph_service, IGraphService
from .graph import Graph

__all__ = [
    # Service
    "IGraphService",
    "GraphService",
    "get_graph_service",
    # Graph
    "Graph",
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
    "EdgeRegistry",
    "FunctionRegistry",
    "GlobalRegistry",
    "get_global_registry",
    "register_node",
    "register_edge",
    "register_node_function",
    "register_route_function",
    "get_node_class",
    "get_edge_class",
    "get_node_function",
    "get_route_function",
    
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