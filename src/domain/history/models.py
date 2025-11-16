from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from ...infrastructure.common.interfaces import ISerializable

class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class MessageRecord(ISerializable):
    record_id: str
    session_id: str
    timestamp: datetime
    record_type: str = "message"
    message_type: MessageType = MessageType.USER
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理枚举类型
        if isinstance(self.message_type, MessageType):
            data['message_type'] = self.message_type.value
        # 处理datetime类型
        if isinstance(self.timestamp, datetime):
            data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageRecord':
        """从字典创建实例"""
        # 处理枚举类型
        if 'message_type' in data and isinstance(data['message_type'], str):
            try:
                data['message_type'] = MessageType(data['message_type'])
            except ValueError:
                data['message_type'] = MessageType.USER
        # 处理datetime类型
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class ToolCallRecord(ISerializable):
    record_id: str
    session_id: str
    timestamp: datetime
    record_type: str = "tool_call"
    tool_name: str = ""
    tool_input: Dict[str, Any] = field(default_factory=dict)
    tool_output: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理datetime类型
        if isinstance(self.timestamp, datetime):
            data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolCallRecord':
        """从字典创建实例"""
        # 处理datetime类型
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

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