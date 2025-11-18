"""
Core workflow state definitions.

This module provides the base state classes and message types for the workflow system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

# Import LangChain message types - core dependency
from langchain_core.messages import (
    BaseMessage as LCBaseMessage,
    HumanMessage as LCHumanMessage,
    AIMessage as LCAIMessage,
    SystemMessage as LCSystemMessage,
    ToolMessage as LCToolMessage,
)

from src.core.workflow.interfaces import IWorkflowState


class MessageRole:
    """Message role constants."""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    TOOL = "tool"
    UNKNOWN = "unknown"


@dataclass
class BaseMessage:
    """Base message class for all message types."""
    content: str
    role: str = MessageRole.UNKNOWN
    
    def to_langchain(self) -> LCBaseMessage:
        """Convert to LangChain message format."""
        if self.role == MessageRole.HUMAN:
            return LCHumanMessage(content=self.content)
        elif self.role == MessageRole.AI:
            return LCAIMessage(content=self.content)
        elif self.role == MessageRole.SYSTEM:
            return LCSystemMessage(content=self.content)
        elif self.role == MessageRole.TOOL:
            return LCToolMessage(content=self.content, tool_call_id="")
        else:
            return LCBaseMessage(content=self.content)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "content": self.content,
            "role": self.role
        }


@dataclass
class HumanMessage(BaseMessage):
    """Human message class."""
    role: str = MessageRole.HUMAN

    def to_langchain(self) -> LCHumanMessage:
        """Convert to LangChain HumanMessage format."""
        return LCHumanMessage(content=self.content)


@dataclass
class AIMessage(BaseMessage):
    """AI message class."""
    role: str = MessageRole.AI

    def to_langchain(self) -> LCAIMessage:
        """Convert to LangChain AIMessage format."""
        return LCAIMessage(content=self.content)


@dataclass
class SystemMessage(BaseMessage):
    """System message class."""
    role: str = MessageRole.SYSTEM

    def to_langchain(self) -> LCSystemMessage:
        """Convert to LangChain SystemMessage format."""
        return LCSystemMessage(content=self.content)


@dataclass
class ToolMessage(BaseMessage):
    """Tool message class."""
    role: str = MessageRole.TOOL
    tool_call_id: str = ""

    def to_langchain(self) -> LCToolMessage:
        """Convert to LangChain ToolMessage format."""
        return LCToolMessage(content=self.content, tool_call_id=self.tool_call_id)


class WorkflowState(BaseModel, IWorkflowState):
    """Core workflow state with enhanced capabilities."""
    # 基础字段
    messages: List[Union[BaseMessage, LCBaseMessage]] = Field(default_factory=list)
    values: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    thread_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    iteration_count: int = 0
    current_node: Optional[str] = None
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 从旧架构迁移的字段
    input: Optional[str] = None
    output: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    max_iterations: int = 10
    errors: List[str] = Field(default_factory=list)
    complete: bool = False
    agent_id: str = ""
    agent_config: Dict[str, Any] = Field(default_factory=dict)
    execution_result: Optional[Dict[str, Any]] = None
    workflow_id: str = ""
    workflow_name: str = ""
    workflow_config: Dict[str, Any] = Field(default_factory=dict)
    current_graph: str = ""
    analysis: Optional[str] = None
    decision: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    graph_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    # IState interface implementation
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data from the state by key."""
        return self.get_value(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """Set data in the state."""
        self.set_value(key, value)
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the state by key."""
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata in the state."""
        self.metadata[key] = value
    
    def get_id(self) -> Optional[str]:
        """Get the state ID."""
        return self.thread_id or self.session_id
    
    def set_id(self, id: str) -> None:
        """Set the state ID."""
        self.thread_id = id
        self.session_id = id
    
    def get_created_at(self) -> datetime:
        """Get the creation timestamp."""
        return self.created_at
    
    def get_updated_at(self) -> datetime:
        """Get the last update timestamp."""
        return self.updated_at
    
    def is_complete(self) -> bool:
        """Check if the workflow is complete."""
        return self.complete
    
    def mark_complete(self) -> None:
        """Mark the workflow as complete."""
        self.complete = True
        self.end_time = datetime.now()
        self.updated_at = datetime.now()
    
    # IWorkflowState interface implementation
    def get_messages(self) -> List[Union[BaseMessage, LCBaseMessage]]:
        """Get all messages in the state."""
        return self.messages
    
    def add_message(self, message: Union[BaseMessage, LCBaseMessage]) -> None:
        """Add a message to the state."""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_last_message(self) -> Optional[Union[BaseMessage, LCBaseMessage]]:
        """Get the last message in the state."""
        return self.messages[-1] if self.messages else None
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the state."""
        return self.values.get(key, default)
    
    def set_value(self, key: str, value: Any) -> None:
        """Set a value in the state."""
        self.values[key] = value
        self.updated_at = datetime.now()
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the state (backward compatibility).
        
        Args:
            key: The key to retrieve
            default: Default value to return if key is not found
            
        Returns:
            The value associated with the key, or default if not found
        """
        # First check in values, then check in common fields
        if key in self.values:
            return self.values[key]
        
        # Check common fields
        if key == "current_step" or key == "current_node":
            return self.current_node
        elif key == "iteration_count":
            return self.iteration_count
        elif key == "messages":
            return self.messages
        elif key == "thread_id":
            return self.thread_id
        elif key == "session_id":
            return self.session_id
        elif key == "input":
            return self.input
        elif key == "output":
            return self.output
        elif key == "errors":
            return self.errors
        elif key == "complete":
            return self.complete
        elif key == "workflow_id":
            return self.workflow_id
        elif key == "workflow_name":
            return self.workflow_name
        elif key == "agent_id":
            return self.agent_id
        elif key == "analysis":
            return self.analysis
        elif key == "decision":
            return self.decision
        elif key == "context":
            return self.context
        elif key == "tool_calls":
            return self.tool_calls
        elif key == "tool_results":
            return self.tool_results
        elif key == "execution_result":
            return self.execution_result
        elif key == "graph_states":
            return self.graph_states
        elif key == "custom_fields":
            return self.custom_fields
        elif key == "metadata":
            return self.metadata
        elif key == "execution_history":
            return self.execution_history
        elif key == "start_time":
            return self.start_time
        elif key == "end_time":
            return self.end_time
        elif key == "created_at":
            return self.created_at
        elif key == "updated_at":
            return self.updated_at
        elif key == "max_iterations":
            return self.max_iterations
        elif key == "agent_config":
            return self.agent_config
        elif key == "workflow_config":
            return self.workflow_config
        elif key == "current_graph":
            return self.current_graph
        
        # Check in custom fields
        if key in self.custom_fields:
            return self.custom_fields[key]
        
        return default
    
    def get_current_node(self) -> Optional[str]:
        """Get the current node in the workflow."""
        return self.current_node
    
    def set_current_node(self, node: str) -> None:
        """Set the current node in the workflow."""
        self.current_node = node
        self.updated_at = datetime.now()
    
    def get_iteration_count(self) -> int:
        """Get the current iteration count."""
        return self.iteration_count
    
    def increment_iteration(self) -> None:
        """Increment the iteration count."""
        self.iteration_count += 1
        self.updated_at = datetime.now()
    
    def get_thread_id(self) -> Optional[str]:
        """Get the thread ID."""
        return self.thread_id
    
    def set_thread_id(self, thread_id: str) -> None:
        """Set the thread ID."""
        self.thread_id = thread_id
        self.updated_at = datetime.now()
    
    def get_session_id(self) -> Optional[str]:
        """Get the session ID."""
        return self.session_id
    
    def set_session_id(self, session_id: str) -> None:
        """Set the session ID."""
        self.session_id = session_id
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the state to a dictionary."""
        # 处理消息列表，支持自定义消息和LangChain消息
        messages_data = []
        for msg in self.messages:
            if isinstance(msg, BaseMessage):
                # 自定义消息类型
                messages_data.append(msg.to_dict())
            elif hasattr(msg, 'content'):
                # LangChain消息类型
                messages_data.append({
                    "content": msg.content,
                    "role": getattr(msg, 'type', 'unknown')
                })
            else:
                # 未知消息类型
                messages_data.append({
                    "content": str(msg),
                    "role": "unknown"
                })
        
        return {
            "messages": messages_data,
            "values": self.values,
            "metadata": self.metadata,
            "thread_id": self.thread_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "iteration_count": self.iteration_count,
            "current_node": self.current_node,
            "execution_history": self.execution_history,
            "input": self.input,
            "output": self.output,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "max_iterations": self.max_iterations,
            "errors": self.errors,
            "complete": self.complete,
            "agent_id": self.agent_id,
            "agent_config": self.agent_config,
            "execution_result": self.execution_result,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "workflow_config": self.workflow_config,
            "current_graph": self.current_graph,
            "analysis": self.analysis,
            "decision": self.decision,
            "context": self.context,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "graph_states": self.graph_states,
            "custom_fields": self.custom_fields,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        """Create a state from a dictionary."""
        created_at_str = data.get("created_at")
        updated_at_str = data.get("updated_at")
        start_time_str = data.get("start_time")
        end_time_str = data.get("end_time")
        
        # 重建消息列表
        messages: List[Union[BaseMessage, LCBaseMessage]] = []
        for msg_data in data.get("messages", []):
            role = msg_data.get("role", "unknown")
            content = msg_data.get("content", "")
            
            if role == MessageRole.HUMAN:
                messages.append(HumanMessage(content=content))
            elif role == MessageRole.AI:
                messages.append(AIMessage(content=content))
            elif role == MessageRole.SYSTEM:
                messages.append(SystemMessage(content=content))
            elif role == MessageRole.TOOL:
                tool_call_id = msg_data.get("tool_call_id", "")
                messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
            else:
                messages.append(BaseMessage(content=content, role=role))
        
        instance = cls(
            messages=messages,
            values=data.get("values", {}),
            metadata=data.get("metadata", {}),
            thread_id=data.get("thread_id"),
            session_id=data.get("session_id"),
            created_at=datetime.fromisoformat(created_at_str) if isinstance(created_at_str, str) else datetime.now(),
            updated_at=datetime.fromisoformat(updated_at_str) if isinstance(updated_at_str, str) else datetime.now(),
            iteration_count=data.get("iteration_count", 0),
            current_node=data.get("current_node"),
            execution_history=data.get("execution_history", []),
            input=data.get("input"),
            output=data.get("output"),
            tool_calls=data.get("tool_calls", []),
            tool_results=data.get("tool_results", []),
            max_iterations=data.get("max_iterations", 10),
            errors=data.get("errors", []),
            complete=data.get("complete", False),
            agent_id=data.get("agent_id", ""),
            agent_config=data.get("agent_config", {}),
            execution_result=data.get("execution_result"),
            workflow_id=data.get("workflow_id", ""),
            workflow_name=data.get("workflow_name", ""),
            workflow_config=data.get("workflow_config", {}),
            current_graph=data.get("current_graph", ""),
            analysis=data.get("analysis"),
            decision=data.get("decision"),
            context=data.get("context", {}),
            start_time=datetime.fromisoformat(start_time_str) if isinstance(start_time_str, str) else datetime.now(),
            end_time=datetime.fromisoformat(end_time_str) if isinstance(end_time_str, str) else None,
            graph_states=data.get("graph_states", {}),
            custom_fields=data.get("custom_fields", {}),
        )
        return instance
    
    # 从旧架构迁移的方法
    def update_with_tool_call(self, tool_call: Dict[str, Any]) -> None:
        """Update state with a tool call."""
        self.tool_calls.append(tool_call)
        self.updated_at = datetime.now()
    
    def update_with_tool_result(self, tool_result: Dict[str, Any]) -> None:
        """Update state with a tool result."""
        self.tool_results.append(tool_result)
        self.updated_at = datetime.now()
    
    def add_error(self, error: str) -> None:
        """Add an error to the state."""
        self.errors.append(error)
        self.updated_at = datetime.now()
    
    def has_errors(self) -> bool:
        """Check if the state has any errors."""
        return len(self.errors) > 0
    
    def get_errors(self) -> List[str]:
        """Get all errors in the state."""
        return self.errors
    
    def clear_errors(self) -> None:
        """Clear all errors in the state."""
        self.errors.clear()
        self.updated_at = datetime.now()
    
    def set_input(self, input_text: str) -> None:
        """Set the input text."""
        self.input = input_text
        self.updated_at = datetime.now()
    
    def get_input(self) -> Optional[str]:
        """Get the input text."""
        return self.input
    
    def set_output(self, output_text: str) -> None:
        """Set the output text."""
        self.output = output_text
        self.updated_at = datetime.now()
    
    def get_output(self) -> Optional[str]:
        """Get the output text."""
        return self.output
    
    def set_execution_result(self, result: Dict[str, Any]) -> None:
        """Set the execution result."""
        self.execution_result = result
        self.updated_at = datetime.now()
    
    def get_execution_result(self) -> Optional[Dict[str, Any]]:
        """Get the execution result."""
        return self.execution_result
    
    def update_graph_state(self, graph_name: str, state: Dict[str, Any]) -> None:
        """Update the state of a specific graph."""
        self.graph_states[graph_name] = state
        self.updated_at = datetime.now()
    
    def get_graph_state(self, graph_name: str) -> Optional[Dict[str, Any]]:
        """Get the state of a specific graph."""
        return self.graph_states.get(graph_name)
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field."""
        self.custom_fields[key] = value
        self.updated_at = datetime.now()
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field."""
        return self.custom_fields.get(key, default)
    
    def is_max_iterations_reached(self) -> bool:
        """Check if the maximum number of iterations has been reached."""
        return self.iteration_count >= self.max_iterations
    
    def reset(self) -> None:
        """Reset the state to initial values."""
        self.messages.clear()
        self.values.clear()
        self.metadata.clear()
        self.iteration_count = 0
        self.current_node = None
        self.execution_history.clear()
        self.input = None
        self.output = None
        self.tool_calls.clear()
        self.tool_results.clear()
        self.errors.clear()
        self.complete = False
        self.execution_result = None
        self.analysis = None
        self.decision = None
        self.context.clear()
        self.end_time = None
        self.graph_states.clear()
        self.custom_fields.clear()
        self.updated_at = datetime.now()
    
    def clone(self) -> "WorkflowState":
        """Create a clone of the state."""
        return self.from_dict(self.to_dict())
    
    def merge(self, other: "WorkflowState") -> None:
        """Merge another state into this one."""
        self.messages.extend(other.messages)
        self.values.update(other.values)
        self.metadata.update(other.metadata)
        self.tool_calls.extend(other.tool_calls)
        self.tool_results.extend(other.tool_results)
        self.errors.extend(other.errors)
        self.execution_history.extend(other.execution_history)
        self.graph_states.update(other.graph_states)
        self.custom_fields.update(other.custom_fields)
        
        # Update non-mergeable fields if they are set in the other state
        if other.input is not None:
            self.input = other.input
        if other.output is not None:
            self.output = other.output
        if other.current_node is not None:
            self.current_node = other.current_node
        if other.execution_result is not None:
            self.execution_result = other.execution_result
        if other.analysis is not None:
            self.analysis = other.analysis
        if other.decision is not None:
            self.decision = other.decision
        if other.end_time is not None:
            self.end_time = other.end_time
        
        self.updated_at = datetime.now()