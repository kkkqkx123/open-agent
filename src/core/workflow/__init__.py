"""Core workflow module following the new architecture.

This module provides the core workflow functionality, including interfaces,
entities, implementations, and sub-modules for graph, execution, and plugins.
"""

from src.interfaces.workflow.core import (
    IWorkflow,
    ExecutionContext,
)
from src.interfaces.workflow.execution import (
    IWorkflowExecutor,
)
from src.interfaces.workflow.builders import (
    IWorkflowBuilder,
)
from src.interfaces.workflow.templates import (
    IWorkflowTemplate,
    IWorkflowTemplateRegistry,
)
from src.interfaces.state import IWorkflowState
from .entities import (
    Workflow as WorkflowEntity,
    WorkflowExecution,
    NodeExecution,
    ExecutionResult,
    WorkflowMetadata
)
# Workflow instance implementation
from .workflow_instance import WorkflowInstance

from langchain_core.messages import AIMessage as LCAIMessage
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
from ..common.exceptions.workflow import (
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
    ConditionNode,
    WaitNode,
    StartNode,
    EndNode,
    BaseEdge,
    SimpleEdge,
    ConditionalEdge,
    FlexibleConditionalEdge
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

# Execution sub-module - New Architecture
from .execution import (
    # Core execution layer
    WorkflowExecutor,
    IWorkflowExecutor,
    NodeExecutor,
    INodeExecutor,
    ExecutionContext,
    ExecutionResult,
    NodeResult,
    BatchJob,
    BatchExecutionResult,
    ExecutionStatus,
    
    # Execution strategies
    IExecutionStrategy,
    BaseStrategy,
    RetryStrategy,
    RetryConfig,
    RetryStrategy as RetryStrategyEnum,
    RetryAttempt,
    RetryConfigs,
    BatchStrategy,
    IBatchStrategy,
    BatchConfig,
    ExecutionMode,
    BatchExecutionMode,
    FailureStrategy,
    StreamingStrategy,
    IStreamingStrategy,
    StreamingConfig,
    CollaborationStrategy,
    ICollaborationStrategy,
    CollaborationConfig,
    
    # Execution modes
    IExecutionMode,
    BaseMode,
    SyncMode,
    ISyncMode,
    AsyncMode,
    IAsyncMode,
    HybridMode,
    IHybridMode,
    
    # Execution services
    ExecutionManager,
    IExecutionManager,
    ExecutionManagerConfig,
    ExecutionMonitor,
    IExecutionMonitor,
    Metric,
    MetricType,
    Alert,
    AlertLevel,
    PerformanceReport,
    ExecutionScheduler,
    IExecutionScheduler,
    ExecutionTask,
    TaskPriority,
    TaskStatus,
    SchedulerConfig,
    
    # Default implementations
    DefaultWorkflowExecutor,
    DefaultNodeExecutor,
    DefaultExecutionManager
)

# Plugin sub-module
from .plugins import (
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
    
    # Core implementations
    "WorkflowInstance",
    
    # Core entities
    "WorkflowEntity",
    "WorkflowExecution",
    "NodeExecution",
    "ExecutionResult",
    "WorkflowMetadata",
    
    # Core implementations
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
    "ConditionNode",
    "WaitNode",
    "StartNode",
    "EndNode",
    
    # Graph edge implementations
    "BaseEdge",
    "SimpleEdge",
    "ConditionalEdge",
    "FlexibleConditionalEdge",
    
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
    
    # New Architecture - Core execution layer
    "WorkflowExecutor",
    "IWorkflowExecutor",
    "NodeExecutor",
    "INodeExecutor",
    "ExecutionContext",
    "ExecutionResult",
    "NodeResult",
    "BatchJob",
    "BatchExecutionResult",
    "ExecutionStatus",
    
    # New Architecture - Execution strategies
    "IExecutionStrategy",
    "BaseStrategy",
    "RetryStrategy",
    "RetryConfig",
    "RetryStrategyEnum",
    "RetryAttempt",
    "RetryConfigs",
    "BatchStrategy",
    "IBatchStrategy",
    "BatchConfig",
    "ExecutionMode",
    "BatchExecutionMode",
    "FailureStrategy",
    "StreamingStrategy",
    "IStreamingStrategy",
    "StreamingConfig",
    "CollaborationStrategy",
    "ICollaborationStrategy",
    "CollaborationConfig",
    
    # New Architecture - Execution modes
    "IExecutionMode",
    "BaseMode",
    "SyncMode",
    "ISyncMode",
    "AsyncMode",
    "IAsyncMode",
    "HybridMode",
    "IHybridMode",
    
    # New Architecture - Execution services
    "ExecutionManager",
    "IExecutionManager",
    "ExecutionManagerConfig",
    "ExecutionMonitor",
    "IExecutionMonitor",
    "Metric",
    "MetricType",
    "Alert",
    "AlertLevel",
    "PerformanceReport",
    "ExecutionScheduler",
    "IExecutionScheduler",
    "ExecutionTask",
    "TaskPriority",
    "TaskStatus",
    "SchedulerConfig",
    
    # New Architecture - Default implementations
    "DefaultWorkflowExecutor",
    "DefaultNodeExecutor",
    "DefaultExecutionManager",
    
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