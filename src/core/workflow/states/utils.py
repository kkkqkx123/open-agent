"""
Workflow state utilities module.

This module provides utility functions for working with workflow states,
migrated from the old architecture.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .base import WorkflowState, BaseMessage, AIMessage, LCBaseMessage


def update_workflow_state_with_tool_call(
    state: WorkflowState,
    tool_call: Dict[str, Any]
) -> WorkflowState:
    """Update workflow state with a tool call.
    
    Args:
        state: Current workflow state
        tool_call: Tool call information
        
    Returns:
        Updated workflow state
    """
    state.update_with_tool_call(tool_call)
    return state


def update_workflow_state_with_tool_result(
    state: WorkflowState,
    tool_result: Dict[str, Any]
) -> WorkflowState:
    """Update workflow state with a tool result.
    
    Args:
        state: Current workflow state
        tool_result: Tool execution result
        
    Returns:
        Updated workflow state
    """
    state.update_with_tool_result(tool_result)
    return state


def update_workflow_state_with_output(
    state: WorkflowState,
    output: str
) -> WorkflowState:
    """Update workflow state with output.
    
    Args:
        state: Current workflow state
        output: Output content
        
    Returns:
        Updated workflow state
    """
    # Create new AI message
    new_ai_message = AIMessage(content=output)
    
    # Add message to state
    state.add_message(new_ai_message)
    
    # Set output and mark complete
    state.set_output(output)
    state.mark_complete()
    
    return state


def update_workflow_state_with_error(
    state: WorkflowState,
    error: str
) -> WorkflowState:
    """Update workflow state with an error.
    
    Args:
        state: Current workflow state
        error: Error information
        
    Returns:
        Updated workflow state
    """
    state.add_error(error)
    return state


def increment_workflow_iteration(state: WorkflowState) -> WorkflowState:
    """Increment workflow iteration count (backward compatibility).
    Note: New system uses IterationManager for more fine-grained iteration control.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated workflow state
    """
    state.increment_iteration()
    
    # Check if max iterations reached
    if state.is_max_iterations_reached():
        state.mark_complete()
    
    return state


def is_workflow_complete(state: WorkflowState) -> bool:
    """Check if workflow is complete.
    
    Args:
        state: Workflow state
        
    Returns:
        Whether complete
    """
    return state.is_complete()


def has_workflow_reached_max_iterations(state: WorkflowState) -> bool:
    """Check if workflow has reached max iterations (backward compatibility).
    Note: New system uses IterationManager for more fine-grained iteration control.
    
    Args:
        state: Workflow state
        
    Returns:
        Whether max iterations reached
    """
    return state.is_max_iterations_reached()


def add_graph_state(state: WorkflowState, graph_id: str, graph_state: Dict[str, Any]) -> WorkflowState:
    """Add graph state to workflow state.
    
    Args:
        state: Workflow state
        graph_id: Graph ID
        graph_state: Graph state
        
    Returns:
        Updated workflow state
    """
    state.update_graph_state(graph_id, graph_state)
    return state


def get_graph_state(state: WorkflowState, graph_id: str) -> Optional[Dict[str, Any]]:
    """Get state of specified graph.
    
    Args:
        state: Workflow state
        graph_id: Graph ID
        
    Returns:
        Graph state or None
    """
    return state.get_graph_state(graph_id)


def update_graph_state(state: WorkflowState, graph_id: str, graph_state: Dict[str, Any]) -> WorkflowState:
    """Update state of specified graph.
    
    Args:
        state: Workflow state
        graph_id: Graph ID
        graph_state: Graph state
        
    Returns:
        Updated workflow state
    """
    state.update_graph_state(graph_id, graph_state)
    return state


def update_workflow_state_with_analysis(
    state: WorkflowState,
    analysis: str
) -> WorkflowState:
    """Update workflow state with analysis result.
    
    Args:
        state: Current workflow state
        analysis: Analysis result
        
    Returns:
        Updated workflow state
    """
    state.analysis = analysis
    state.updated_at = datetime.now()
    return state


def update_workflow_state_with_decision(
    state: WorkflowState,
    decision: str
) -> WorkflowState:
    """Update workflow state with decision result.
    
    Args:
        state: Current workflow state
        decision: Decision result
        
    Returns:
        Updated workflow state
    """
    state.decision = decision
    state.updated_at = datetime.now()
    return state


def update_workflow_state_with_context(
    state: WorkflowState,
    context_key: str,
    context_value: Any
) -> WorkflowState:
    """Update workflow state with context information.
    
    Args:
        state: Current workflow state
        context_key: Context key
        context_value: Context value
        
    Returns:
        Updated workflow state
    """
    state.context[context_key] = context_value
    state.updated_at = datetime.now()
    return state


def update_workflow_state_with_custom_field(
    state: WorkflowState,
    field_key: str,
    field_value: Any
) -> WorkflowState:
    """Update workflow state with custom field.
    
    Args:
        state: Current workflow state
        field_key: Field key
        field_value: Field value
        
    Returns:
        Updated workflow state
    """
    state.set_custom_field(field_key, field_value)
    return state


def complete_workflow(state: WorkflowState) -> WorkflowState:
    """Complete workflow.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated workflow state
    """
    state.mark_complete()
    return state


def get_workflow_duration(state: WorkflowState) -> Optional[float]:
    """Get workflow execution duration.
    
    Args:
        state: Workflow state
        
    Returns:
        Execution duration (seconds) or None
    """
    if state.start_time and state.end_time:
        return (state.end_time - state.start_time).total_seconds()
    return None


def has_all_graphs_completed(state: WorkflowState, graph_ids: List[str]) -> bool:
    """Check if all graphs are complete.
    
    Args:
        state: Workflow state
        graph_ids: List of graph IDs
        
    Returns:
        Whether all graphs are complete
    """
    for graph_id in graph_ids:
        graph_state = state.get_graph_state(graph_id)
        if not graph_state or not graph_state.get("complete", False):
            return False
    
    return True


# State update functions - migrated from old state.py
def update_state_with_message(state: Dict[str, Any], message: LCBaseMessage) -> Dict[str, Any]:
    """Update state with message.
    
    Args:
        state: Current state
        message: New message
        
    Returns:
        Updated state
    """
    return {"messages": [message]}


def update_state_with_tool_result(
    state: Dict[str, Any],
    tool_call: Dict[str, Any],
    result: Any
) -> Dict[str, Any]:
    """Update state with tool result.
    
    Args:
        state: Current state
        tool_call: Tool call information
        result: Tool execution result
        
    Returns:
        Updated state
    """
    return {
        "tool_results": [{"tool_call": tool_call, "result": result}]
    }


def update_state_with_error(state: Dict[str, Any], error: str) -> Dict[str, Any]:
    """Update state with error information.
    
    Args:
        state: Current state
        error: Error information
        
    Returns:
        Updated state
    """
    return {"errors": [error]}


# State validation functions - migrated from old state.py
def validate_state(state: Dict[str, Any], state_type: type) -> List[str]:
    """Validate state.
    
    Args:
        state: State to validate
        state_type: State type
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Check required fields
    if "messages" not in state:
        errors.append("Missing messages field")
    
    if state_type == WorkflowState:
        required_fields = ["workflow_id", "input", "max_iterations"]
        for field in required_fields:
            if field not in state:
                errors.append(f"Missing required field: {field}")
    
    return errors


# State serialization functions - migrated from old state.py
def serialize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize state.
    
    Args:
        state: State to serialize
        
    Returns:
        Serialized state
    """
    serialized = state.copy()
    
    # Serialize messages
    if "messages" in serialized and serialized["messages"]:
        serialized["messages"] = [
            {
                "content": msg.content,
                "type": getattr(msg, 'type', getattr(msg, '__class__', type(msg)).__name__.lower()),
                "tool_call_id": getattr(msg, "tool_call_id", "")
            }
            for msg in serialized["messages"]
        ]
    
    return serialized


def deserialize_state(serialized_state: Dict[str, Any]) -> Dict[str, Any]:
    """Deserialize state.
    
    Args:
        serialized_state: Serialized state
        
    Returns:
        Deserialized state
    """
    from .factory import create_message
    
    state = serialized_state.copy()
    
    # Deserialize messages
    if "messages" in state:
        messages = []
        for msg_data in state["messages"]:
            message = create_message(
                content=msg_data["content"],
                role=msg_data["type"],
                tool_call_id=msg_data.get("tool_call_id", "")
            )
            messages.append(message)
        state["messages"] = messages
    
    return state