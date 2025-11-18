"""
Backward compatibility module for workflow states.

This module provides backward compatibility for code that imports from the old
src.infrastructure.graph.states.workflow module.
"""

# Re-export everything from the new modules for backward compatibility
from .base import WorkflowState
from .factory import (
    create_agent_state,
    create_workflow_state,
    create_react_state,
    create_plan_execute_state,
    create_message
)
from .utils import (
    update_workflow_state_with_tool_call,
    update_workflow_state_with_tool_result,
    update_workflow_state_with_output,
    update_workflow_state_with_error,
    increment_workflow_iteration,
    is_workflow_complete,
    has_workflow_reached_max_iterations,
    add_graph_state,
    get_graph_state,
    update_graph_state,
    update_workflow_state_with_analysis,
    update_workflow_state_with_decision,
    update_workflow_state_with_context,
    update_workflow_state_with_custom_field,
    complete_workflow,
    get_workflow_duration,
    has_all_graphs_completed,
    update_state_with_message,
    update_state_with_tool_result,
    update_state_with_error,
    validate_state,
    serialize_state,
    deserialize_state
)

# Type alias for backward compatibility
from typing import Dict, Any
WorkflowStateType = Dict[str, Any]

# Additional functions for backward compatibility
def increment_global_iteration_count(state: WorkflowState) -> WorkflowState:
    """Increment global workflow iteration count (for new system).
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated workflow state
    """
    # Use custom field for global iteration count
    current_count = state.get_custom_field("workflow_iteration_count", 0)
    max_iterations = state.get_custom_field("workflow_max_iterations", state.max_iterations)
    
    new_count = current_count + 1
    state.set_custom_field("workflow_iteration_count", new_count)
    
    if new_count >= max_iterations:
        state.mark_complete()
    
    return state


def has_reached_global_max_iterations(state: WorkflowState) -> bool:
    """Check if workflow has reached global max iterations (for new system).
    
    Args:
        state: Workflow state
        
    Returns:
        Whether global max iterations reached
    """
    current_count = int(state.get_custom_field("workflow_iteration_count", 0))
    max_iterations = int(state.get_custom_field("workflow_max_iterations", state.max_iterations))
    
    return current_count >= max_iterations

# Export all symbols for backward compatibility
__all__ = [
    "WorkflowState",
    "WorkflowStateType",
    "create_agent_state",
    "create_workflow_state",
    "create_react_state",
    "create_plan_execute_state",
    "create_message",
    "update_workflow_state_with_tool_call",
    "update_workflow_state_with_tool_result",
    "update_workflow_state_with_output",
    "update_workflow_state_with_error",
    "increment_workflow_iteration",
    "increment_global_iteration_count",
    "is_workflow_complete",
    "has_workflow_reached_max_iterations",
    "has_reached_global_max_iterations",
    "add_graph_state",
    "get_graph_state",
    "update_graph_state",
    "update_workflow_state_with_analysis",
    "update_workflow_state_with_decision",
    "update_workflow_state_with_context",
    "update_workflow_state_with_custom_field",
    "complete_workflow",
    "get_workflow_duration",
    "has_all_graphs_completed",
    "update_state_with_message",
    "update_state_with_tool_result",
    "update_state_with_error",
    "validate_state",
    "serialize_state",
    "deserialize_state"
]