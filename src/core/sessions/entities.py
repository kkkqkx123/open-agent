"""会话核心实体定义"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4
from enum import Enum
from src.interfaces.common import AbstractSessionData, AbstractSessionStatus


# 直接使用接口层定义的会话状态枚举
SessionStatus = AbstractSessionStatus


@dataclass
class Session(AbstractSessionData):
    """会话实体"""
    session_id: str
    _status: SessionStatus = SessionStatus.ACTIVE  # 使用私有属性避免属性冲突
    message_count: int = 0
    checkpoint_count: int = 0
    _created_at: datetime = field(default_factory=datetime.now)
    _updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    thread_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化后处理"""
        if not self.session_id:
            self.session_id = str(uuid4())
        if isinstance(self._status, str):
            self._status = SessionStatus(self._status)

    @property
    def id(self) -> str:
        """会话ID"""
        return self.session_id

    @property
    def status(self) -> AbstractSessionStatus:
        """会话状态"""
        return self._status

    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """更新时间"""
        return self._updated_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'session_id': self.session_id,
            'status': self._status.value if hasattr(self._status, 'value') else self._status,
            'message_count': self.message_count,
            'checkpoint_count': self.checkpoint_count,
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat(),
            'metadata': self.metadata,
            'tags': self.tags,
            'thread_ids': self.thread_ids
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """从字典创建实例"""
        return cls(
            session_id=data["session_id"],
            _status=SessionStatus(data["status"]) if isinstance(data["status"], str) else data["status"],
            message_count=data.get("message_count", 0),
            checkpoint_count=data.get("checkpoint_count", 0),
            _created_at=datetime.fromisoformat(data["created_at"]),
            _updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            thread_ids=data.get("thread_ids", [])
        )
    
    def update_timestamp(self) -> None:
        """更新时间戳"""
        self._updated_at = datetime.now()


@dataclass
class SessionEntity:
    """会话实体"""
    session_id: str
    user_id: Optional[str] = None
    thread_ids: List[str] = field(default_factory=list)
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if not self.session_id:
            self.session_id = str(uuid4())

    def add_thread(self, thread_id: str) -> None:
        """添加线程ID"""
        if thread_id not in self.thread_ids:
            self.thread_ids.append(thread_id)
            self.updated_at = datetime.now()

    def remove_thread(self, thread_id: str) -> None:
        """移除线程ID"""
        if thread_id in self.thread_ids:
            self.thread_ids.remove(thread_id)
            self.updated_at = datetime.now()

    def update_status(self, status: str) -> None:
        """更新状态"""
        self.status = status
        self.updated_at = datetime.now()

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """更新元数据"""
        self.metadata.update(metadata)
        self.updated_at = datetime.now()

    def is_active(self) -> bool:
        """检查会话是否活跃"""
        return self.status == "active"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "thread_ids": self.thread_ids,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionEntity':
        """从字典创建实体"""
        return cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            thread_ids=data.get("thread_ids", []),
            status=data.get("status", "active"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class UserInteractionEntity:
    """用户交互实体"""
    interaction_id: str
    session_id: str
    thread_id: Optional[str] = None
    interaction_type: str = "user_input"
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后处理"""
        if not self.interaction_id:
            self.interaction_id = str(uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "interaction_id": self.interaction_id,
            "session_id": self.session_id,
            "thread_id": self.thread_id,
            "interaction_type": self.interaction_type,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInteractionEntity':
        """从字典创建实体"""
        return cls(
            interaction_id=data["interaction_id"],
            session_id=data["session_id"],
            thread_id=data.get("thread_id"),
            interaction_type=data.get("interaction_type", "user_input"),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


@dataclass
class UserRequestEntity:
    """用户请求实体"""
    request_id: str
    user_id: Optional[str] = None
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后处理"""
        if not self.request_id:
            self.request_id = str(uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserRequestEntity':
        """从字典创建实体"""
        return cls(
            request_id=data["request_id"],
            user_id=data.get("user_id"),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


@dataclass
class SessionContext:
    """会话上下文"""
    session_id: str
    user_id: Optional[str]
    thread_ids: List[str]
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]