"""Workflow states module following the new architecture."""
from .base import (
    WorkflowState,
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
    MessageRole,
)
from .factory import (
    WorkflowStateFactory,
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

__all__ = [
    # Core classes
    "WorkflowState",
    "BaseMessage",
    "SystemMessage",
    "HumanMessage",
    "AIMessage",
    "ToolMessage",
    "MessageRole",
    
    # Factory
    "WorkflowStateFactory",
    "create_agent_state",
    "create_workflow_state",
    "create_react_state",
    "create_plan_execute_state",
    "create_message",
    
    # Utilities
    "update_workflow_state_with_tool_call",
    "update_workflow_state_with_tool_result",
    "update_workflow_state_with_output",
    "update_workflow_state_with_error",
    "increment_workflow_iteration",
    "is_workflow_complete",
    "has_workflow_reached_max_iterations",
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