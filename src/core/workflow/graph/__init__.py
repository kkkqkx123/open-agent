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
    FunctionRegistry
)
# 从基础设施层导入基础组件
from src.infrastructure.graph.registry import (
    NodeRegistry,
    EdgeRegistry
)
from src.infrastructure.graph.nodes import (
    BaseNode,
    SimpleNode,
    AsyncNode,
    StartNode as InfraStartNode,
    EndNode as InfraEndNode
)
from src.infrastructure.graph.edges import (
    BaseEdge,
    SimpleEdge
)
from src.infrastructure.graph.core import Graph as InfraGraph

# 核心层特有的业务节点
from .nodes import (
    LLMNode,
    ToolNode,
    ConditionNode,
    WaitNode,
    # StartNode 和 EndNode 保留在核心层，但继承自基础设施层
    StartNode,
    EndNode
)
from .edges import (
    ConditionalEdge,
    FlexibleConditionalEdge
)
from .service import GraphService, create_graph_service, IGraphService

__all__ = [
    # Service
    "IGraphService",
    "GraphService",
    "create_graph_service",
    # Graph
    "InfraGraph",
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
    
    # Infrastructure Nodes (re-exported)
    "BaseNode",
    "SimpleNode",
    "AsyncNode",
    "InfraStartNode",
    "InfraEndNode",
    
    # Infrastructure Edges (re-exported)
    "BaseEdge",
    "SimpleEdge",
    
    # Core Business Nodes
    "LLMNode",
    "ToolNode",
    "ConditionNode",
    "WaitNode",
    "StartNode",
    "EndNode",
    
    # Core Business Edges
    "ConditionalEdge",
    "FlexibleConditionalEdge",
]