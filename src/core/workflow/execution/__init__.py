"""Execution sub-module for workflow core.

This module provides execution engine functionality for workflows,
including synchronous, asynchronous, and streaming execution.
"""

from .interfaces import (
    IAsyncExecutor,
    IStreamingExecutor,
    IExecutionContext
)
from .executor import WorkflowExecutor

__all__ = [
    # Interfaces
    "IAsyncExecutor",
    "IStreamingExecutor",
    "IExecutionContext",
    
    # Implementations
    "WorkflowExecutor"
]