"""会话核心实体定义"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4
from enum import Enum
from typing import TYPE_CHECKING

from src.interfaces.sessions.entities import ISession, IUserRequest, IUserInteraction, ISessionContext
from src.interfaces.common_domain import AbstractSessionData, AbstractSessionStatus

# 使用通用领域接口中的会话状态枚举，避免重复定义
SessionStatus = AbstractSessionStatus


class Session(ISession, AbstractSessionData):
    """会话实体"""
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        status: str = "active",
        message_count: int = 0,
        checkpoint_count: int = 0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        thread_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ):
        """初始化会话实体"""
        self._session_id = session_id or str(uuid4())
        self._status = SessionStatus(status)
        self.message_count = message_count
        self.checkpoint_count = checkpoint_count
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()
        self.metadata = metadata or {}
        # 如果提供了user_id，将其存储在metadata中
        if user_id:
            self.metadata['user_id'] = user_id
        self.tags = tags or []
        self._thread_ids = thread_ids or []

    @property
    def id(self) -> str:
        """获取会话ID - 实现AbstractSessionData接口"""
        return self._session_id

    @property
    def session_id(self) -> str:
        """会话ID"""
        return self._session_id

    @property
    def status(self) -> AbstractSessionStatus:
        """会话状态 - 实现AbstractSessionData接口"""
        return self._status

    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """更新时间"""
        return self._updated_at

    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        return self._metadata

    @metadata.setter
    def metadata(self, value: Dict[str, Any]) -> None:
        self._metadata = value

    @property
    def thread_ids(self) -> List[str]:
        """关联的线程ID列表"""
        return self._thread_ids

    @thread_ids.setter
    def thread_ids(self, value: List[str]) -> None:
        self._thread_ids = value
    
    @property
    def user_id(self) -> Optional[str]:
        """用户ID（从metadata中获取）"""
        return self.metadata.get('user_id')

    def is_active(self) -> bool:
        """检查会话是否活跃"""
        return self._status == SessionStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 - 实现AbstractSessionData接口"""
        return {
            'id': self._session_id,
            'session_id': self._session_id,
            'status': self._status.value,
            'message_count': self.message_count,
            'checkpoint_count': self.checkpoint_count,
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat(),
            'metadata': self._metadata,
            'tags': self.tags,
            'thread_ids': self._thread_ids
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """从字典创建实例"""
        return cls(
            session_id=data.get("session_id"),
            status=data.get("status", "active"),
            message_count=data.get("message_count", 0),
            checkpoint_count=data.get("checkpoint_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else None,
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            thread_ids=data.get("thread_ids", [])
        )
    
    def update_timestamp(self) -> None:
        """更新时间戳"""
        self._updated_at = datetime.now()
    
    def add_thread(self, thread_id: str) -> None:
        """添加线程ID"""
        if thread_id not in self._thread_ids:
            self._thread_ids.append(thread_id)
            self.update_timestamp()

    def remove_thread(self, thread_id: str) -> None:
        """移除线程ID"""
        if thread_id in self._thread_ids:
            self._thread_ids.remove(thread_id)
            self.update_timestamp()

    def update_status(self, status: str) -> None:
        """更新状态"""
        self._status = SessionStatus(status)
        self.update_timestamp()

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """更新元数据"""
        self.metadata.update(metadata)
        self.update_timestamp()


# SessionEntity 类已被删除，功能合并到 Session 类中
# 如果需要 user_id 功能，请使用 Session 类的 metadata 字段


class UserInteractionEntity(IUserInteraction):
    """用户交互实体"""
    
    def __init__(
        self,
        interaction_id: Optional[str] = None,
        session_id: str = "",
        thread_id: Optional[str] = None,
        interaction_type: str = "user_input",
        content: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        """初始化用户交互实体"""
        self._interaction_id = interaction_id or str(uuid4())
        self._session_id = session_id
        self._thread_id = thread_id
        self._interaction_type = interaction_type
        self._content = content
        self._metadata = metadata or {}
        self._timestamp = timestamp or datetime.now()

    @property
    def interaction_id(self) -> str:
        """交互ID"""
        return self._interaction_id

    @property
    def session_id(self) -> str:
        """会话ID"""
        return self._session_id

    @property
    def thread_id(self) -> Optional[str]:
        """线程ID"""
        return self._thread_id

    @property
    def interaction_type(self) -> str:
        """交互类型"""
        return self._interaction_type

    @property
    def content(self) -> str:
        """交互内容"""
        return self._content

    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        return self._metadata

    @property
    def timestamp(self) -> datetime:
        """时间戳"""
        return self._timestamp

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "interaction_id": self._interaction_id,
            "session_id": self._session_id,
            "thread_id": self._thread_id,
            "interaction_type": self._interaction_type,
            "content": self._content,
            "metadata": self._metadata,
            "timestamp": self._timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInteractionEntity':
        """从字典创建实体"""
        return cls(
            interaction_id=data.get("interaction_id"),
            session_id=data.get("session_id", ""),
            thread_id=data.get("thread_id"),
            interaction_type=data.get("interaction_type", "user_input"),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None
        )


class UserRequestEntity(IUserRequest):
    """用户请求实体"""
    
    def __init__(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        content: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        """初始化用户请求实体"""
        self._request_id = request_id or str(uuid4())
        self._user_id = user_id
        self._content = content
        self._metadata = metadata or {}
        self._timestamp = timestamp or datetime.now()

    @property
    def request_id(self) -> str:
        """请求ID"""
        return self._request_id

    @property
    def user_id(self) -> Optional[str]:
        """用户ID"""
        return self._user_id

    @property
    def content(self) -> str:
        """请求内容"""
        return self._content

    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        return self._metadata

    @property
    def timestamp(self) -> datetime:
        """时间戳"""
        return self._timestamp

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self._request_id,
            "user_id": self._user_id,
            "content": self._content,
            "metadata": self._metadata,
            "timestamp": self._timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserRequestEntity':
        """从字典创建实体"""
        return cls(
            request_id=data.get("request_id"),
            user_id=data.get("user_id"),
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None
        )


class SessionContext(ISessionContext):
    """会话上下文"""
    
    def __init__(
        self,
        session_id: str,
        user_id: Optional[str],
        thread_ids: List[str],
        status: str,
        created_at: datetime,
        updated_at: datetime,
        metadata: Dict[str, Any]
    ):
        """初始化会话上下文"""
        self._session_id = session_id
        self._user_id = user_id
        self._thread_ids = thread_ids
        self._status = status
        self._created_at = created_at
        self._updated_at = updated_at
        self._metadata = metadata

    @property
    def session_id(self) -> str:
        """会话ID"""
        return self._session_id

    @property
    def user_id(self) -> Optional[str]:
        """用户ID"""
        return self._user_id

    @property
    def thread_ids(self) -> List[str]:
        """线程ID列表"""
        return self._thread_ids

    @property
    def status(self) -> str:
        """状态"""
        return self._status

    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """更新时间"""
        return self._updated_at

    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        return self._metadata

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self._session_id,
            "user_id": self._user_id,
            "thread_ids": self._thread_ids,
            "status": self._status,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "metadata": self._metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionContext':
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