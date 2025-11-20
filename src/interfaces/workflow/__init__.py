"""Workflow interfaces module.

This module contains all workflow-related interfaces for the application.
These interfaces define the contract for workflow implementations.
"""

from .core import (
    IWorkflow,
    ExecutionContext
)

from .execution import (
    IWorkflowExecutor
)

from .graph import (
    IGraph,
    INode,
    IEdge,
    IGraphBuilder,
    INodeRegistry,
    IRoutingFunction,
    IRoutingRegistry
)

from .templates import (
    IWorkflowTemplate,
    IWorkflowTemplateRegistry
)

from .builders import (
    IWorkflowBuilder
)

from .visualization import (
    IWorkflowVisualizer
)

__all__ = [
    # Core interfaces
    "IWorkflow",
    "ExecutionContext",
    
    # Execution interfaces
    "IWorkflowExecutor",
    
    # Graph interfaces
    "IGraph",
    "INode",
    "IEdge",
    "IGraphBuilder",
    "INodeRegistry",
    "IRoutingFunction",
    "IRoutingRegistry",
    
    # Template interfaces
    "IWorkflowTemplate",
    "IWorkflowTemplateRegistry",
    
    # Builder interfaces
    "IWorkflowBuilder",
    
    # Visualization interfaces
    "IWorkflowVisualizer"
]