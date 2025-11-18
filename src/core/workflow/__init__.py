"""Core workflow module following the new architecture.

This module provides the core workflow functionality, including interfaces,
entities, implementations, and sub-modules for graph, execution, and plugins.
"""

from .interfaces import (
    IWorkflow,
    IWorkflowState,
    IWorkflowExecutor,
    IWorkflowBuilder
)
from .entities import (
    Workflow as WorkflowEntity,
    WorkflowExecution,
    NodeExecution,
    ExecutionResult,
    WorkflowMetadata
)
from .workflow import Workflow
from .states import (
    WorkflowState,
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    LCAIMessage
)
from .value_objects import (
    WorkflowStep,
    WorkflowTransition,
    WorkflowRule,
    WorkflowTemplate,
    StepType,
    TransitionType,
    RuleType,
    RuleOperator
)
from .exceptions import (
    WorkflowError,
    WorkflowValidationError,
    WorkflowExecutionError,
    WorkflowStepError,
    WorkflowTransitionError,
    WorkflowRuleError,
    WorkflowTimeoutError,
    WorkflowStateError,
    WorkflowConfigError,
    WorkflowDependencyError,
    WorkflowPermissionError,
    WorkflowConcurrencyError,
    WorkflowResourceError,
    WorkflowIntegrationError,
    WorkflowTemplateError,
    WorkflowVersionError,
    create_workflow_exception,
    handle_workflow_exception
)

# Graph sub-module
from .graph import (
    IGraph,
    INode,
    IEdge,
    IGraphBuilder,
    INodeRegistry,
    IRoutingFunction,
    IRoutingRegistry,
    node,
    NodeRegistry,
    register_node,
    get_global_registry,
    get_node_class,
    get_node_instance,
    list_node_types,
    BaseNode,
    LLMNode,
    ToolNode,
    AnalysisNode,
    ConditionNode,
    WaitNode,
    StartNode,
    EndNode,
    BaseEdge,
    SimpleEdge,
    ConditionalEdge,
    FlexibleConditionalEdge,
    GraphBuilder
)

# Configuration sub-module
from .config import (
    GraphConfig,
    NodeConfig,
    EdgeConfig,
    EdgeType,
    StateFieldConfig,
    GraphStateConfig,
    WorkflowConfig
)

# Registry sub-module
from .registry import (
    BaseNode as RegistryBaseNode,
    NodeRegistry as RegistryNodeRegistry,
    NodeExecutionResult,
    get_global_registry as get_global_node_registry,
    register_node as register_node_type,
    register_node_instance,
    get_node,
    node as node_decorator
)

# Management sub-module
from .management import (
    IterationManager,
    WorkflowValidator,
    ValidationSeverity,
    ValidationIssue,
    validate_workflow_config
)

# Nodes and Edges sub-modules are exported through graph module
# No need to import them separately

# Execution sub-module
from .execution import (
    IAsyncExecutor,
    IStreamingExecutor,
    IExecutionContext,
    WorkflowExecutor
)

# Plugin sub-module
from .plugins import (
    IPlugin,
    IStartPlugin,
    IEndPlugin,
    IHookPlugin,
    PluginMetadata,
    PluginType,
    PluginContext,
    HookPoint,
    HookContext,
    HookExecutionResult,
    BasePlugin,
    PluginRegistry,
    PluginManager,
    ContextSummaryPlugin,
    EnvironmentCheckPlugin,
    MetadataCollectorPlugin,
    CleanupManagerPlugin,
    ExecutionStatsPlugin,
    FileTrackerPlugin,
    ResultSummaryPlugin,
    DeadLoopDetectionPlugin,
    ErrorRecoveryPlugin,
    LoggingPlugin,
    MetricsCollectionPlugin,
    PerformanceMonitoringPlugin
)

__all__ = [
    # Core interfaces
    "IWorkflow",
    "IWorkflowState",
    "IWorkflowExecutor",
    "IWorkflowBuilder",
    
    # Core entities
    "WorkflowEntity",
    "WorkflowExecution",
    "NodeExecution",
    "ExecutionResult",
    "WorkflowMetadata",
    
    # Core implementations
    "Workflow",
    
    # States
    "WorkflowState",
    "BaseMessage",
    "SystemMessage",
    "HumanMessage",
    "AIMessage",
    "LCAIMessage",
    # Value objects
    "WorkflowStep",
    "WorkflowTransition",
    "WorkflowRule",
    "WorkflowTemplate",
    "StepType",
    "TransitionType",
    "RuleType",
    "RuleOperator",
    
    # Exceptions
    "WorkflowError",
    "WorkflowValidationError",
    "WorkflowExecutionError",
    "WorkflowStepError",
    "WorkflowTransitionError",
    "WorkflowRuleError",
    "WorkflowTimeoutError",
    "WorkflowStateError",
    "WorkflowConfigError",
    "WorkflowDependencyError",
    "WorkflowPermissionError",
    "WorkflowConcurrencyError",
    "WorkflowResourceError",
    "WorkflowIntegrationError",
    "WorkflowTemplateError",
    "WorkflowVersionError",
    "create_workflow_exception",
    "handle_workflow_exception",
    
    # Graph interfaces
    "IGraph",
    "INode",
    "IEdge",
    "IGraphBuilder",
    "INodeRegistry",
    "IRoutingFunction",
    "IRoutingRegistry",
    
    # Graph decorators
    "node",
    
    # Graph registry
    "NodeRegistry",
    "register_node",
    "get_global_registry",
    "get_node_class",
    "get_node_instance",
    "list_node_types",
    
    # Graph node implementations
    "BaseNode",
    "LLMNode",
    "ToolNode",
    "AnalysisNode",
    "ConditionNode",
    "WaitNode",
    "StartNode",
    "EndNode",
    
    # Graph edge implementations
    "BaseEdge",
    "SimpleEdge",
    "ConditionalEdge",
    "FlexibleConditionalEdge",
    
    # Graph builder
    "GraphBuilder",
    
    # Configuration
    "GraphConfig",
    "NodeConfig",
    "EdgeConfig",
    "EdgeType",
    "StateFieldConfig",
    "GraphStateConfig",
    "WorkflowConfig",
    
    # Registry
    "RegistryBaseNode",
    "RegistryNodeRegistry",
    "NodeExecutionResult",
    "get_global_node_registry",
    "register_node_type",
    "register_node_instance",
    "get_node",
    "node_decorator",
    
    # Management
    "IterationManager",
    "WorkflowValidator",
    "ValidationSeverity",
    "ValidationIssue",
    "validate_workflow_config",
    
    # Execution interfaces
    "IAsyncExecutor",
    "IStreamingExecutor",
    "IExecutionContext",
    
    # Execution implementations
    "WorkflowExecutor",
    
    # Plugin interfaces
    "IPlugin",
    "IStartPlugin",
    "IEndPlugin",
    "IHookPlugin",
    "PluginMetadata",
    "PluginType",
    "PluginContext",
    "HookPoint",
    "HookContext",
    "HookExecutionResult",
    
    # Plugin base classes
    "BasePlugin",
    
    # Plugin implementations
    "PluginRegistry",
    "PluginManager",
    
    # Built-in start plugins
    "ContextSummaryPlugin",
    "EnvironmentCheckPlugin",
    "MetadataCollectorPlugin",
    
    # Built-in end plugins
    "CleanupManagerPlugin",
    "ExecutionStatsPlugin",
    "FileTrackerPlugin",
    "ResultSummaryPlugin",
    
    # Built-in hook plugins
    "DeadLoopDetectionPlugin",
    "ErrorRecoveryPlugin",
    "LoggingPlugin",
    "MetricsCollectionPlugin",
    "PerformanceMonitoringPlugin"
]