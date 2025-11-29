"""Workflow services module following the new architecture.

This module provides service implementations for workflow management,
including builders, executors, and utilities.
"""

from .building.builder_service import WorkflowBuilderService
from .building.factory import WorkflowFactory
from src.interfaces.workflow.services import (
    IWorkflowManager,
    IWorkflowFactory,
    IWorkflowExecutor,
    IWorkflowOrchestrator,
    IWorkflowRegistry,
    IWorkflowBuilderService
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

__all__ = [
    # Original services
    "WorkflowBuilderService",
    "WorkflowFactory",
    "IWorkflowFactory",
    "IWorkflowExecutor",
    "IWorkflowRegistry",
    "IWorkflowRegistryCoordinator",
    "IWorkflowBuilderService",
    
    # Newly migrated services
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
]