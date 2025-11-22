"""会话核心实体定义"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4


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