"""Compatibility module for state imports following the new architecture.

This module provides backward compatibility by re-exporting the new state classes
from the core module, allowing existing code to continue working during the migration.
"""
from src.core.workflow.states import WorkflowState, BaseMessage, SystemMessage, HumanMessage, AIMessage, LCAIMessage

# Re-export all the state-related classes to maintain backward compatibility
__all__ = [
    "WorkflowState",
    "BaseMessage", 
    "SystemMessage",
    "HumanMessage",
    "AIMessage",
    "LCAIMessage"
]