"""Test workflow state migration from old architecture to new architecture."""

import pytest
from datetime import datetime
from src.core.workflow.states.base import (
    WorkflowState, 
    BaseMessage, 
    HumanMessage, 
    AIMessage, 
    SystemMessage, 
    ToolMessage,
    MessageRole
)
from src.state.interfaces import IWorkflowState, IState


class TestWorkflowStateMigration:
    """Test cases for workflow state migration."""
    
    def test_workflow_state_implements_interfaces(self):
        """Test that WorkflowState implements required interfaces."""
        state = WorkflowState()
        assert isinstance(state, IWorkflowState)
        assert isinstance(state, IState)
    
    def test_basic_state_creation(self):
        """Test basic state creation and default values."""
        state = WorkflowState()
        
        # Test default values
        assert state.messages == []
        assert state.values == {}
        assert state.metadata == {}
        assert state.iteration_count == 0
        assert state.complete is False
        assert state.max_iterations == 10
        assert state.tool_calls == []
        assert state.tool_results == []
        assert state.errors == []
        assert state.workflow_id == ""
        assert state.workflow_name == ""
        assert isinstance(state.created_at, datetime)
        assert isinstance(state.updated_at, datetime)
    
    def test_message_types(self):
        """Test all message types."""
        human_msg = HumanMessage(content="Hello")
        ai_msg = AIMessage(content="Hi there")
        system_msg = SystemMessage(content="You are a helpful assistant")
        tool_msg = ToolMessage(content="Tool result", tool_call_id="123")
        
        assert human_msg.role == MessageRole.HUMAN
        assert ai_msg.role == MessageRole.AI
        assert system_msg.role == MessageRole.SYSTEM
        assert tool_msg.role == MessageRole.TOOL
        assert tool_msg.tool_call_id == "123"
    
    def test_state_interface_methods(self):
        """Test IState interface methods."""
        state = WorkflowState()
        
        # Test get_data/set_data
        state.set_data("test_key", "test_value")
        assert state.get_data("test_key") == "test_value"
        assert state.get_data("nonexistent", "default") == "default"
        
        # Test update_data
        state.update_data({"key1": "value1", "key2": "value2"})
        assert state.get_data("key1") == "value1"
        assert state.get_data("key2") == "value2"
    
    def test_workflow_state_methods(self):
        """Test workflow state specific methods."""
        state = WorkflowState()
        
        # Test add_message
        human_msg = HumanMessage(content="Hello")
        state.add_message(human_msg)
        assert len(state.messages) == 1
        assert state.messages[0] == human_msg
        
        # Test increment_iteration
        state.increment_iteration()
        assert state.iteration_count == 1
        
        # Test completion
        assert state.is_complete() is False
        state.complete = True
        assert state.is_complete() is True
    
    def test_migrated_methods(self):
        """Test methods migrated from old architecture."""
        state = WorkflowState()
        
        # Test tool call update
        tool_call = {"name": "test_tool", "args": {"arg1": "value1"}}
        state.update_with_tool_call(tool_call)
        assert len(state.tool_calls) == 1
        assert state.tool_calls[0] == tool_call
        
        # Test tool result update
        tool_result = {"tool_call": tool_call, "result": "success"}
        state.update_with_tool_result(tool_result)
        assert len(state.tool_results) == 1
        assert state.tool_results[0] == tool_result
        
        # Test output update
        state.update_with_output("Test output")
        assert state.output == "Test output"
        assert state.complete is True
        assert len(state.messages) == 2  # Human message + AI message
        
        # Test error update
        state.update_with_error("Test error")
        assert len(state.errors) == 1
        assert state.errors[0] == "Test error"
        
        # Test analysis and decision updates
        state.update_with_analysis("Test analysis")
        assert state.analysis == "Test analysis"
        
        state.update_with_decision("Test decision")
        assert state.decision == "Test decision"
        
        # Test context update
        state.update_context("context_key", "context_value")
        assert state.context["context_key"] == "context_value"
        
        # Test custom field update
        state.update_custom_field("custom_key", "custom_value")
        assert state.custom_fields["custom_key"] == "custom_value"
    
    def test_graph_state_management(self):
        """Test graph state management methods."""
        state = WorkflowState()
        
        # Test add/get graph state
        graph_state = {"node1": "value1", "node2": "value2"}
        state.add_graph_state("graph1", graph_state)
        
        retrieved_state = state.get_graph_state("graph1")
        assert retrieved_state == graph_state
        
        # Test nonexistent graph state
        assert state.get_graph_state("nonexistent") is None
    
    def test_workflow_completion(self):
        """Test workflow completion methods."""
        state = WorkflowState()
        
        # Test duration before completion
        assert state.get_duration() is None
        
        # Test completion
        state.complete_workflow()
        assert state.complete is True
        assert state.end_time is not None
        assert state.get_duration() is not None
        assert state.get_duration() >= 0
    
    def test_iteration_limits(self):
        """Test iteration limit checking."""
        state = WorkflowState(max_iterations=5)
        
        # Test initial state
        assert state.has_reached_max_iterations() is False
        
        # Increment to max
        for _ in range(5):
            state.increment_iteration()
        
        assert state.has_reached_max_iterations() is True
        assert state.complete is True  # Should auto-complete
    
    def test_serialization_deserialization(self):
        """Test state serialization and deserialization."""
        # Create a state with various data
        state = WorkflowState(
            workflow_id="test_workflow",
            workflow_name="Test Workflow",
            input="Test input",
            max_iterations=3
        )
        
        # Add some data
        state.add_message(HumanMessage(content="Hello"))
        state.update_with_tool_call({"name": "test_tool"})
        state.update_context("key", "value")
        
        # Serialize
        state_dict = state.to_dict()
        
        # Verify key fields are present
        assert "messages" in state_dict
        assert "workflow_id" in state_dict
        assert "input" in state_dict
        assert "tool_calls" in state_dict
        assert "context" in state_dict
        
        # Deserialize
        restored_state = WorkflowState.from_dict(state_dict)
        
        # Verify restored state
        assert restored_state.workflow_id == "test_workflow"
        assert restored_state.workflow_name == "Test Workflow"
        assert restored_state.input == "Test input"
        assert restored_state.max_iterations == 3
        assert len(restored_state.messages) == 1
        assert len(restored_state.tool_calls) == 1
        assert restored_state.context["key"] == "value"
    
    def test_message_langchain_conversion(self):
        """Test message conversion to LangChain format."""
        # Test all message types
        human_msg = HumanMessage(content="Hello")
        ai_msg = AIMessage(content="Hi")
        system_msg = SystemMessage(content="System message")
        tool_msg = ToolMessage(content="Tool result", tool_call_id="123")
        
        # Convert to LangChain
        lc_human = human_msg.to_langchain()
        lc_ai = ai_msg.to_langchain()
        lc_system = system_msg.to_langchain()
        lc_tool = tool_msg.to_langchain()
        
        # Verify conversions
        assert lc_human.content == "Hello"
        assert lc_ai.content == "Hi"
        assert lc_system.content == "System message"
        assert lc_tool.content == "Tool result"
        assert lc_tool.tool_call_id == "123"


if __name__ == "__main__":
    pytest.main([__file__])