"""Core workflow module following the new architecture.

This module provides the core workflow functionality, including interfaces,
entities, implementations, and sub-modules for graph, execution, and plugins.
"""

from .interfaces import (
    IWorkflow,
    IWorkflowState,
    IWorkflowExecutor,
    IWorkflowBuilder,
    IWorkflowTemplate,
    IWorkflowTemplateRegistry
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
    INodeExecutor,
    IWorkflowExecutor,
    IExecutionStrategy,
    IExecutionObserver,
    IStreamingExecutor,
    IAsyncNodeExecutor,
    AsyncNodeExecutor,
    NodeExecutionContext,
    NodeExecutionResult,
    execute_node_async,
    execute_nodes_batch,
    IRetryExecutor,
    RetryExecutor,
    RetryConfig,
    RetryStrategy,
    RetryAttempt,
    RetryResult,
    RetryConfigs,
    execute_with_retry,
    execute_with_retry_async,
    IBatchExecutor,
    BatchExecutor,
    BatchExecutionConfig,
    BatchJob,
    BatchExecutionResult,
    ExecutionMode,
    FailureStrategy,
    batch_run_workflows,
    batch_run_workflows_async,
    IWorkflowRunner,
    WorkflowRunner,
    WorkflowExecutionResult,
    run_workflow,
    run_workflow_async,
    ICollaborationExecutor,
    CollaborationExecutor,
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
    "IWorkflowTemplate",
    "IWorkflowTemplateRegistry",
    
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
    
    # Management
    "IterationManager",
    "WorkflowValidator",
    "ValidationSeverity",
    "ValidationIssue",
    "validate_workflow_config",
    
    # Execution interfaces
    "INodeExecutor",
    "IWorkflowExecutor",
    "IExecutionStrategy",
    "IExecutionObserver",
    "IStreamingExecutor",
    "IAsyncNodeExecutor",
    "IRetryExecutor",
    "IBatchExecutor",
    "IWorkflowRunner",
    "ICollaborationExecutor",
    
    # Execution implementations
    "AsyncNodeExecutor",
    "NodeExecutionContext",
    "NodeExecutionResult",
    "execute_node_async",
    "execute_nodes_batch",
    "RetryExecutor",
    "RetryConfig",
    "RetryStrategy",
    "RetryAttempt",
    "RetryResult",
    "RetryConfigs",
    "execute_with_retry",
    "execute_with_retry_async",
    "BatchExecutor",
    "BatchExecutionConfig",
    "BatchJob",
    "BatchExecutionResult",
    "ExecutionMode",
    "FailureStrategy",
    "batch_run_workflows",
    "batch_run_workflows_async",
    "WorkflowRunner",
    "WorkflowExecutionResult",
    "run_workflow",
    "run_workflow_async",
    "CollaborationExecutor",
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