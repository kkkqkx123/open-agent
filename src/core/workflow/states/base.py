"""Base workflow state and message classes."""
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from langchain_core.messages import (
    BaseMessage as LCBaseMessage,
    HumanMessage as LCHumanMessage,
    AIMessage as LCBaseAIMessage,
    SystemMessage as LCSystemMessage
)
from pydantic import BaseModel, Field


class MessageRole:
    """Message roles for the workflow."""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"


@dataclass
class BaseMessage:
    """Base message class for workflow communication."""
    content: str
    role: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_langchain(self) -> LCBaseMessage:
        """Convert to LangChain message format."""
        if self.role == MessageRole.HUMAN:
            return LCHumanMessage(content=self.content)
        elif self.role == MessageRole.AI:
            return LCBaseAIMessage(content=self.content)
        elif self.role == MessageRole.SYSTEM:
            return LCSystemMessage(content=self.content)
        else:
            return LCBaseMessage(content=self.content, type=self.role)


@dataclass
class HumanMessage(BaseMessage):
    """Human message class."""
    role: str = MessageRole.HUMAN


@dataclass
class AIMessage(BaseMessage):
    """AI message class."""
    role: str = MessageRole.AI


@dataclass
class SystemMessage(BaseMessage):
    """System message class."""
    role: str = MessageRole.SYSTEM


# LCAIMessage is an alias for LCBaseAIMessage to maintain backward compatibility
LCAIMessage = LCBaseAIMessage


class WorkflowState(BaseModel):
    """Core workflow state with enhanced capabilities."""
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

    def add_message(self, message: Union[BaseMessage, LCBaseMessage]) -> None:
        """Add a message to the workflow state."""
        self.messages.append(message)
        self.updated_at = datetime.now()

    def update_value(self, key: str, value: Any) -> None:
        """Update a value in the workflow state."""
        self.values[key] = value
        self.updated_at = datetime.now()

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the workflow state."""
        return self.values.get(key, default)

    def add_execution_record(self, record: Dict[str, Any]) -> None:
        """Add an execution record to the history."""
        self.execution_history.append(record)
        self.updated_at = datetime.now()

    def increment_iteration(self) -> None:
        """Increment the iteration count."""
        self.iteration_count += 1
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the state to a dictionary representation."""
        return {
            "messages": [
                {
                    "content": msg.content if hasattr(msg, 'content') else str(msg),
                    "role": getattr(msg, 'role', 'unknown'),
                    "type": type(msg).__name__
                }
                for msg in self.messages
            ],
            "values": self.values,
            "metadata": self.metadata,
            "thread_id": self.thread_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "iteration_count": self.iteration_count,
            "current_node": self.current_node,
            "execution_history": self.execution_history
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowState':
        """Create a WorkflowState from a dictionary."""
        # This is a simplified implementation - in practice, you'd need to properly
        # reconstruct message objects from their serialized form
        created_at_str = data.get("created_at")
        updated_at_str = data.get("updated_at")
        
        instance = cls(
            values=data.get("values", {}),
            metadata=data.get("metadata", {}),
            thread_id=data.get("thread_id"),
            session_id=data.get("session_id"),
            created_at=datetime.fromisoformat(created_at_str) if isinstance(created_at_str, str) else datetime.now(),
            updated_at=datetime.fromisoformat(updated_at_str) if isinstance(updated_at_str, str) else datetime.now(),
            iteration_count=data.get("iteration_count", 0),
            current_node=data.get("current_node"),
            execution_history=data.get("execution_history", [])
        )
        return instance