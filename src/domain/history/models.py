from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class MessageRecord:
    record_id: str
    session_id: str
    timestamp: datetime
    record_type: str = "message"
    message_type: MessageType = MessageType.USER
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolCallRecord:
    record_id: str
    session_id: str
    timestamp: datetime
    record_type: str = "tool_call"
    tool_name: str = ""
    tool_input: Dict[str, Any] = field(default_factory=dict)
    tool_output: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HistoryQuery:
    session_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    record_types: Optional[list] = None
    limit: Optional[int] = None
    offset: Optional[int] = None

@dataclass
class HistoryResult:
    records: list
    total: int = 0