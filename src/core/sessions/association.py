"""Session-Thread关联实体定义"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
from uuid import uuid4

from src.infrastructure.error_management.impl.sessions import SessionOperationHandler
from src.infrastructure.error_management import create_error_context, handle_error
from src.interfaces.sessions.exceptions import AssociationNotFoundError

if TYPE_CHECKING:
    from src.interfaces.sessions.association import ISessionThreadAssociation


@dataclass
class SessionThreadAssociation:
    """Session-Thread关联实体"""
    
    # 基本标识
    association_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = ""
    thread_id: str = ""
    thread_name: str = ""
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 关联状态
    is_active: bool = True
    association_type: str = "session_thread"  # 关联类型
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        context = create_error_context(
            "sessions",
            "association_post_init",
            session_id=self.session_id,
            thread_id=self.thread_id,
            thread_name=self.thread_name
        )
        
        def _validate():
            if not self.session_id:
                raise ValueError("session_id cannot be empty")
            if not self.thread_id:
                raise ValueError("thread_id cannot be empty")
            if not self.thread_name:
                raise ValueError("thread_name cannot be empty")
        
        try:
            from src.infrastructure.error_management import safe_execution
            safe_execution(_validate, context=context)
        except Exception as e:
            handle_error(e, context)
            raise AssociationNotFoundError(
                self.session_id,
                self.thread_id,
                cause=e
            ) from e
    
    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """停用关联"""
        self.is_active = False
        self.update_timestamp()
    
    def activate(self) -> None:
        """激活关联"""
        self.is_active = True
        self.update_timestamp()
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """更新元数据"""
        self.metadata.update(metadata)
        self.update_timestamp()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "association_id": self.association_id,
            "session_id": self.session_id,
            "thread_id": self.thread_id,
            "thread_name": self.thread_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "association_type": self.association_type,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionThreadAssociation':
        """从字典创建实例"""
        context = create_error_context(
            "sessions",
            "association_from_dict",
            session_id=data.get("session_id"),
            thread_id=data.get("thread_id"),
            thread_name=data.get("thread_name")
        )
        
        def _create_from_dict():
            return cls(
                association_id=data.get("association_id", str(uuid4())),
                session_id=data["session_id"],
                thread_id=data["thread_id"],
                thread_name=data["thread_name"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                is_active=data.get("is_active", True),
                association_type=data.get("association_type", "session_thread"),
                metadata=data.get("metadata", {})
            )
        
        try:
            return SessionOperationHandler.safe_association_creation(
                lambda: _create_from_dict(),
                data["session_id"],
                data["thread_id"],
                data["thread_name"],
                context=context
            )
        except Exception as e:
            handle_error(e, context)
            raise AssociationNotFoundError(
                data["session_id"],
                data["thread_id"],
                cause=e
            ) from e
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"SessionThreadAssociation(session_id={self.session_id}, thread_id={self.thread_id}, thread_name={self.thread_name})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"SessionThreadAssociation(association_id={self.association_id}, "
                f"session_id={self.session_id}, thread_id={self.thread_id}, "
                f"thread_name={self.thread_name}, is_active={self.is_active})")
