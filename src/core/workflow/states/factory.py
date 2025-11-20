"""
Workflow state factory module.

This module provides factory functions for creating different types of workflow states.
"""

from typing import Any, Dict, List, Optional, Type, Union, Sequence
from datetime import datetime

from .base import (
    WorkflowState, 
    BaseMessage, 
    HumanMessage, 
    AIMessage, 
    SystemMessage, 
    ToolMessage,
    LCBaseMessage,
    LCHumanMessage
)


class WorkflowStateFactory:
    """Factory for creating workflow states."""
    
    @staticmethod
    def create_state_class_from_config(state_schema: Any) -> Type[Dict[str, Any]]:
        """Create a state class from configuration
        
        Args:
            state_schema: State schema configuration
            
        Returns:
            Type[Dict[str, Any]]: State class type
        """
        # Create a dynamic state class based on configuration
        fields: Dict[str, Any] = {}
        
        if hasattr(state_schema, 'fields'):
            for field_name, field_config in state_schema.fields.items():
                fields[field_name] = field_config
        
        # Return a dynamic class that can be used as a state
        class DynamicState(dict):
            """Dynamic state class created from configuration"""
            pass
        
        return DynamicState
    
    @staticmethod
    def create_agent_state(
        input_text: str,
        max_iterations: int = 10,
        messages: Optional[Sequence[LCBaseMessage]] = None
    ) -> WorkflowState:
        """Create an agent state.
        
        Args:
            input_text: Input text
            max_iterations: Maximum number of iterations
            messages: Initial message list
            
        Returns:
            WorkflowState instance
        """
        if messages is None:
            messages = [LCHumanMessage(content=input_text)]
        
        # Convert to list and cast to Union type
        message_list: List[Union[BaseMessage, LCBaseMessage]] = list(messages)
        
        return WorkflowState(
            messages=message_list,
            input=input_text,
            max_iterations=max_iterations,
            start_time=datetime.now()
        )
    
    @staticmethod
    def create_workflow_state(
        workflow_id: str,
        workflow_name: str,
        input_text: str,
        workflow_config: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10,
        messages: Optional[Sequence[Union[BaseMessage, LCBaseMessage]]] = None
    ) -> WorkflowState:
        """Create a workflow state.
        
        Args:
            workflow_id: Workflow ID
            workflow_name: Workflow name
            input_text: Input text
            workflow_config: Workflow configuration
            max_iterations: Maximum number of iterations
            messages: Initial message list
            
        Returns:
            WorkflowState instance
        """
        if messages is None:
            messages = [HumanMessage(content=input_text)]
        
        # Convert to list
        message_list: List[Union[BaseMessage, LCBaseMessage]] = list(messages)
        
        return WorkflowState(
            messages=message_list,
            input=input_text,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            workflow_config=workflow_config or {},
            max_iterations=max_iterations,
            agent_id=workflow_id,
            agent_config=workflow_config or {},
            start_time=datetime.now()
        )
    
    @staticmethod
    def create_react_state(
        workflow_id: str,
        input_text: str,
        max_iterations: int = 10
    ) -> WorkflowState:
        """Create a ReAct state.
        
        Args:
            workflow_id: Workflow ID
            input_text: Input text
            max_iterations: Maximum number of iterations
            
        Returns:
            WorkflowState instance with ReAct-specific fields
        """
        base_state = WorkflowStateFactory.create_workflow_state(
            workflow_id=workflow_id,
            workflow_name=f"react_{workflow_id}",
            input_text=input_text,
            max_iterations=max_iterations
        )
        
        # Add ReAct-specific custom fields
        base_state.set_custom_field("thought", None)
        base_state.set_custom_field("action", None)
        base_state.set_custom_field("observation", None)
        base_state.set_custom_field("steps", [])
        
        return base_state
    
    @staticmethod
    def create_plan_execute_state(
        workflow_id: str,
        input_text: str,
        max_iterations: int = 10
    ) -> WorkflowState:
        """Create a plan execute state.
        
        Args:
            workflow_id: Workflow ID
            input_text: Input text
            max_iterations: Maximum number of iterations
            
        Returns:
            WorkflowState instance with plan-execute-specific fields
        """
        base_state = WorkflowStateFactory.create_workflow_state(
            workflow_id=workflow_id,
            workflow_name=f"plan_execute_{workflow_id}",
            input_text=input_text,
            max_iterations=max_iterations
        )
        
        # Add plan-execute-specific custom fields
        base_state.set_custom_field("plan", None)
        base_state.set_custom_field("steps", [])
        base_state.set_custom_field("current_step", None)
        base_state.set_custom_field("step_results", [])
        
        return base_state
    
    @staticmethod
    def create_message(content: str, role: str, **kwargs: Any) -> LCBaseMessage:
        """Create a message.
        
        Args:
            content: Message content
            role: Message role
            **kwargs: Additional parameters
            
        Returns:
            LangChain BaseMessage instance
        """
        from .base import MessageRole
        
        if role == MessageRole.HUMAN:
            return LCHumanMessage(content=content)
        elif role == MessageRole.AI:
            return AIMessage(content=content).to_langchain()
        elif role == MessageRole.SYSTEM:
            return SystemMessage(content=content).to_langchain()
        elif role == MessageRole.TOOL:
            return ToolMessage(
                content=content, 
                tool_call_id=kwargs.get("tool_call_id", "")
            ).to_langchain()
        else:
            # Create a generic message
            from langchain_core.messages import BaseMessage as LCBaseMessage
            return LCBaseMessage(content=content, type=role)


# Convenience functions for backward compatibility
def create_agent_state(
    input_text: str,
    max_iterations: int = 10,
    messages: Optional[Sequence[LCBaseMessage]] = None
) -> WorkflowState:
    """Create an agent state (backward compatibility function)."""
    return WorkflowStateFactory.create_agent_state(
        input_text=input_text,
        max_iterations=max_iterations,
        messages=messages
    )


def create_workflow_state(
    workflow_id: str,
    workflow_name: str,
    input_text: str,
    workflow_config: Optional[Dict[str, Any]] = None,
    max_iterations: int = 10,
    messages: Optional[Sequence[Union[BaseMessage, LCBaseMessage]]] = None
) -> WorkflowState:
    """Create a workflow state (backward compatibility function)."""
    return WorkflowStateFactory.create_workflow_state(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        input_text=input_text,
        workflow_config=workflow_config,
        max_iterations=max_iterations,
        messages=messages
    )


def create_react_state(
    workflow_id: str,
    input_text: str,
    max_iterations: int = 10
) -> WorkflowState:
    """Create a ReAct state (backward compatibility function)."""
    return WorkflowStateFactory.create_react_state(
        workflow_id=workflow_id,
        input_text=input_text,
        max_iterations=max_iterations
    )


def create_plan_execute_state(
    workflow_id: str,
    input_text: str,
    max_iterations: int = 10
) -> WorkflowState:
    """Create a plan execute state (backward compatibility function)."""
    return WorkflowStateFactory.create_plan_execute_state(
        workflow_id=workflow_id,
        input_text=input_text,
        max_iterations=max_iterations
    )


def create_message(content: str, role: str, **kwargs: Any) -> LCBaseMessage:
    """Create a message (backward compatibility function)."""
    return WorkflowStateFactory.create_message(content=content, role=role, **kwargs)