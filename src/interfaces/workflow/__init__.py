"""Workflow interfaces module.

This module contains all workflow-related interfaces for the application.
These interfaces define the contract for workflow implementations.
"""

from .core import (
    IWorkflow
)

from ..common_domain import WorkflowExecutionContext as ExecutionContext

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

from .entities import (
    IWorkflowState,
    IExecutionResult,
    IWorkflow as IWorkflowEntity,
    IWorkflowExecution,
    INodeExecution,
    IWorkflowMetadata
)

from .hooks import (
    IHookExecutor,
    IHookSystem
)

from .plugins import (
    IPlugin,
    IHookPlugin,
    IStartPlugin,
    IEndPlugin,
    PluginType,
    PluginStatus,
    HookPoint,
    PluginMetadata,
    PluginContext,
    PluginExecutionResult,
    HookContext,
    HookExecutionResult
)

from .graph_engine import (
    IGraphEngine,
    IGraphBuilder
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
    "IWorkflowVisualizer",
    
    # Entity interfaces
    "IWorkflowState",
    "IExecutionResult",
    "IWorkflowEntity",
    "IWorkflowExecution",
    "INodeExecution",
    "IWorkflowMetadata",
    
    # Hook interfaces
    "IHookExecutor",
    "IHookSystem",
    
    # Plugin interfaces
    "IPlugin",
    "IHookPlugin",
    "IStartPlugin",
    "IEndPlugin",
    "PluginType",
    "PluginStatus",
    "HookPoint",
    "PluginMetadata",
    "PluginContext",
    "PluginExecutionResult",
    "HookContext",
    "HookExecutionResult",
    
    # Graph engine interfaces
    "IGraphEngine",
    "IGraphBuilder",
]