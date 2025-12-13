"""Workflow interfaces module.

This module contains all workflow-related interfaces for the application.
These interfaces define the contract for workflow implementations.
"""

from .core import (
    IWorkflow
)

from ...core.common import WorkflowExecutionContext as ExecutionContext

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
    IStartPlugin,
    IEndPlugin,
    PluginType,
    PluginStatus,
    PluginMetadata,
    PluginContext,
    PluginExecutionResult
)

from .hooks import (
    IHook,
    IHookRegistry,
    IHookExecutor,
    IHookSystem,
    HookPoint,
    HookContext,
    HookExecutionResult
)

from .functions import (
    FunctionType,
    FunctionMetadata,
    IFunction,
    INodeFunction,
    IConditionFunction,
    IRouteFunction,
    ITriggerFunction,
    IFunctionRegistry
)

from .graph_engine import (
    IGraphEngine,
    IGraphBuilder
)

from .config import (
    INodeConfig,
    IEdgeConfig,
    IStateFieldConfig,
    IGraphStateConfig,
    IGraphConfig,
    EdgeType
)

from .services import (
    IWorkflowService
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
    "IStartPlugin",
    "IEndPlugin",
    "PluginType",
    "PluginStatus",
    "PluginMetadata",
    "PluginContext",
    "PluginExecutionResult",
    
    # Hook interfaces
    "IHook",
    "IHookRegistry",
    "IHookExecutor",
    "IHookSystem",
    "HookPoint",
    "HookContext",
    "HookExecutionResult",
    
    # Function interfaces
    "FunctionType",
    "FunctionMetadata",
    "IFunction",
    "INodeFunction",
    "IConditionFunction",
    "IRouteFunction",
    "ITriggerFunction",
    "IFunctionRegistry",
    
    # Graph engine interfaces
    "IGraphEngine",
    "IGraphBuilder",
    
    # Config interfaces
    "INodeConfig",
    "IEdgeConfig",
    "IStateFieldConfig",
    "IGraphStateConfig",
    "IGraphConfig",
    "EdgeType",
    
    # Service interfaces
    "IWorkflowService",
]