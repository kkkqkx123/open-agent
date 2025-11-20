"""Workflow services module following the new architecture.

This module provides service implementations for workflow management,
including builders, executors, and utilities.
"""

from .builder_service import WorkflowBuilderService
from .execution.executor import WorkflowExecutorService
from .factory import WorkflowFactory
from .interfaces import (
    IWorkflowManager,
    IWorkflowFactory,
    IWorkflowExecutor,
    IWorkflowOrchestrator,
    IWorkflowRegistry,
    IWorkflowBuilderService
)
from .registry import WorkflowRegistry
from .di_config import register_workflow_services, configure_workflow_services

from .config_manager import (
    IWorkflowConfigManager,
    WorkflowConfigManager
)
from .registry_service import (
    IWorkflowRegistryService,
    WorkflowRegistryService,
    WorkflowDefinition
)
# Newly migrated services
from .builder import UnifiedGraphBuilder
from .execution.async_executor import (
    IAsyncNodeExecutor
)
from .function_registry import (
    FunctionRegistry,
    FunctionType,
    FunctionRegistrationError,
    FunctionDiscoveryError,
    get_global_function_registry,
    register_node_function,
    register_condition_function,
    get_node_function,
    get_condition_function
)
from .graph_cache import (
    GraphCache,
    CacheEntry,
    CacheEvictionPolicy,
    create_graph_cache,
    calculate_config_hash
)
from .node_config_loader import (
    NodeConfigLoader,
    get_node_config_loader
)

# === 新架构服务 ===
from .loader_service import UniversalLoaderService
from .workflow_instance import WorkflowInstance
from .runner import WorkflowRunner, WorkflowExecutionResult, run_workflow, run_workflow_async
from .retry_executor import (
    RetryExecutor, 
    RetryConfig, 
    RetryStrategy, 
    RetryResult, 
    RetryAttempt,
    RetryConfigs,
    execute_with_retry,
    execute_with_retry_async
)
from .batch_executor import (
    BatchExecutor,
    BatchJob,
    BatchExecutionResult,
    BatchExecutionConfig,
    ExecutionMode,
    FailureStrategy,
    batch_run_workflows,
    batch_run_workflows_async
)

__all__ = [
    # Original services
    "WorkflowBuilderService",
    "WorkflowExecutorService",
    "WorkflowFactory",
    "IWorkflowManager",
    "IWorkflowFactory",
    "IWorkflowExecutor",
    "IWorkflowOrchestrator",
    "IWorkflowRegistry",
    "IWorkflowBuilderService",
    "WorkflowRegistry",
    "register_workflow_services",
    "configure_workflow_services",
    
    # Newly migrated services
    "IWorkflowConfigManager",
    "WorkflowConfigManager",
    "IWorkflowRegistryService",
    "WorkflowRegistryService",
    "WorkflowDefinition",
    "UnifiedGraphBuilder",
    "IAsyncNodeExecutor",
    "FunctionRegistry",
    "FunctionType",
    "FunctionRegistrationError",
    "FunctionDiscoveryError",
    "get_global_function_registry",
    "register_node_function",
    "register_condition_function",
    "get_node_function",
    "get_condition_function",
    "GraphCache",
    "CacheEntry",
    "CacheEvictionPolicy",
    "create_graph_cache",
    "calculate_config_hash",
    "NodeConfigLoader",
    "get_node_config_loader",
    
    # === 新架构服务 ===
    "UniversalLoaderService",
    "WorkflowInstance",
    "WorkflowRunner",
    "WorkflowExecutionResult",
    "run_workflow",
    "run_workflow_async",
    "RetryExecutor",
    "RetryConfig",
    "RetryStrategy",
    "RetryResult",
    "RetryAttempt",
    "RetryConfigs",
    "execute_with_retry",
    "execute_with_retry_async",
    "BatchExecutor",
    "BatchJob",
    "BatchExecutionResult",
    "BatchExecutionConfig",
    "ExecutionMode",
    "FailureStrategy",
    "batch_run_workflows",
    "batch_run_workflows_async"
]