"""
检查点核心数据模型

定义检查点相关的核心数据模型，包括检查点、元数据和元组等。
统一Thread特定的checkpoint和通用checkpoint模型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid


class CheckpointStatus(str, Enum):
    """检查点状态枚举"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CORRUPTED = "corrupted"
    ARCHIVED = "archived"


class CheckpointType(str, Enum):
    """检查点类型枚举"""
    AUTO = "auto"
    MANUAL = "manual"
    ERROR = "error"
    MILESTONE = "milestone"


@dataclass
class CheckpointMetadata:
    """统一的检查点元数据模型"""
    
    # 基础元数据
    source: Optional[str] = None
    step: Optional[int] = None
    parents: Optional[Dict[str, str]] = None
    
    # Thread特定元数据
    thread_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # 统计信息
    size_bytes: int = 0
    restore_count: int = 0
    last_restored_at: Optional[datetime] = None
    
    # 自定义数据
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "source": self.source,
            "step": self.step,
            "parents": self.parents,
            "thread_id": self.thread_id,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "size_bytes": self.size_bytes,
            "restore_count": self.restore_count,
            "last_restored_at": self.last_restored_at.isoformat() if self.last_restored_at else None,
            "custom_data": self.custom_data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointMetadata':
        """从字典创建实例"""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])
        
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        
        last_restored_at = None
        if data.get("last_restored_at"):
            last_restored_at = datetime.fromisoformat(data["last_restored_at"])
        
        return cls(
            source=data.get("source"),
            step=data.get("step"),
            parents=data.get("parents"),
            thread_id=data.get("thread_id"),
            title=data.get("title"),
            description=data.get("description"),
            tags=data.get("tags", []),
            created_at=created_at,
            updated_at=updated_at,
            expires_at=expires_at,
            size_bytes=data.get("size_bytes", 0),
            restore_count=data.get("restore_count", 0),
            last_restored_at=last_restored_at,
            custom_data=data.get("custom_data", {}),
        )


@dataclass
class Checkpoint:
    """统一的检查点数据模型"""
    
    # 基础属性
    id: str = field(default_factory=lambda: f"checkpoint_{uuid.uuid4().hex}")
    channel_values: Dict[str, Any] = field(default_factory=dict)
    channel_versions: Dict[str, Any] = field(default_factory=dict)
    versions_seen: Dict[str, Any] = field(default_factory=dict)
    
    # 状态属性
    status: CheckpointStatus = CheckpointStatus.ACTIVE
    checkpoint_type: CheckpointType = CheckpointType.AUTO
    
    # 时间戳
    ts: datetime = field(default_factory=datetime.now)
    
    # 元数据
    metadata: CheckpointMetadata = field(default_factory=CheckpointMetadata)
    
    # Thread特定属性
    thread_id: Optional[str] = None
    state_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        # 设置元数据时间戳
        if not self.metadata.created_at:
            self.metadata.created_at = self.ts
        self.metadata.updated_at = self.ts
        
        # 设置Thread ID
        if self.thread_id:
            self.metadata.thread_id = self.thread_id
        
        # 计算数据大小
        import json
        self.metadata.size_bytes = len(json.dumps(self.to_dict()))
    
    # 领域方法
    def is_valid(self) -> bool:
        """验证检查点有效性"""
        return (
            bool(self.id) and
            self.status == CheckpointStatus.ACTIVE and
            not self.is_expired()
        )
    
    def can_restore(self) -> bool:
        """检查是否可以恢复"""
        return self.is_valid() and self.status != CheckpointStatus.CORRUPTED
    
    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.metadata.expires_at is None:
            return False
        return datetime.now() > self.metadata.expires_at
    
    def get_age_hours(self) -> float:
        """获取检查点年龄（小时）"""
        return (datetime.now() - self.ts).total_seconds() / 3600.0
    
    def mark_restored(self) -> None:
        """标记为已恢复"""
        self.metadata.restore_count += 1
        self.metadata.last_restored_at = datetime.now()
        self.metadata.updated_at = datetime.now()
    
    def mark_expired(self) -> None:
        """标记为已过期"""
        self.status = CheckpointStatus.EXPIRED
        self.metadata.updated_at = datetime.now()
    
    def mark_corrupted(self) -> None:
        """标记为已损坏"""
        self.status = CheckpointStatus.CORRUPTED
        self.metadata.updated_at = datetime.now()
    
    def mark_archived(self) -> None:
        """标记为已归档"""
        self.status = CheckpointStatus.ARCHIVED
        self.metadata.updated_at = datetime.now()
    
    def set_expiration(self, hours: int) -> None:
        """设置过期时间"""
        if hours <= 0:
            raise ValueError("Expiration hours must be positive")
        
        from datetime import timedelta
        self.metadata.expires_at = datetime.now() + timedelta(hours)
        self.metadata.updated_at = datetime.now()
    
    def extend_expiration(self, hours: int) -> None:
        """延长过期时间"""
        if hours <= 0:
            raise ValueError("Extension hours must be positive")
        
        from datetime import timedelta
        
        if self.metadata.expires_at is None:
            self.metadata.expires_at = datetime.now() + timedelta(hours)
        else:
            self.metadata.expires_at += timedelta(hours)
        
        self.metadata.updated_at = datetime.now()
    
    def get_channel_value(self, channel: str, default: Any = None) -> Any:
        """获取通道值"""
        return self.channel_values.get(channel, default)
    
    def set_channel_value(self, channel: str, value: Any) -> None:
        """设置通道值"""
        self.channel_values[channel] = value
        self.metadata.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "channel_values": self.channel_values,
            "channel_versions": self.channel_versions,
            "versions_seen": self.versions_seen,
            "status": self.status.value,
            "checkpoint_type": self.checkpoint_type.value,
            "ts": self.ts.isoformat(),
            "metadata": self.metadata.to_dict(),
            "thread_id": self.thread_id,
            "state_data": self.state_data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoint':
        """从字典创建实例"""
        # 处理时间字段
        ts = datetime.fromisoformat(data["ts"])
        
        # 处理元数据
        metadata_data = data.get("metadata", {})
        metadata = CheckpointMetadata.from_dict(metadata_data)
        
        return cls(
            id=data["id"],
            channel_values=data.get("channel_values", {}),
            channel_versions=data.get("channel_versions", {}),
            versions_seen=data.get("versions_seen", {}),
            status=CheckpointStatus(data.get("status", "active")),
            checkpoint_type=CheckpointType(data.get("checkpoint_type", "auto")),
            ts=ts,
            metadata=metadata,
            thread_id=data.get("thread_id"),
            state_data=data.get("state_data", {}),
        )


@dataclass
class CheckpointTuple:
    """检查点元组"""
    
    config: Dict[str, Any]
    checkpoint: Checkpoint
    parent_config: Optional[Dict[str, Any]] = None
    pending_writes: Optional[List[Any]] = None
    metadata: Optional[CheckpointMetadata] = None
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = self.checkpoint.metadata
    
    def get_thread_id(self) -> str:
        """获取线程ID"""
        return self.config.get("configurable", {}).get("thread_id", "") or self.checkpoint.thread_id or ""
    
    def get_checkpoint_ns(self) -> str:
        """获取检查点命名空间"""
        return self.config.get("configurable", {}).get("checkpoint_ns", "")
    
    def get_checkpoint_id(self) -> str:
        """获取检查点ID"""
        config_id = self.config.get("configurable", {}).get("checkpoint_id", "")
        return config_id or self.checkpoint.id
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "config": self.config,
            "checkpoint": self.checkpoint.to_dict(),
            "parent_config": self.parent_config,
            "pending_writes": self.pending_writes,
        }


@dataclass
class CheckpointStatistics:
    """检查点统计模型"""
    
    total_checkpoints: int = 0
    active_checkpoints: int = 0
    expired_checkpoints: int = 0
    corrupted_checkpoints: int = 0
    archived_checkpoints: int = 0
    
    total_size_bytes: int = 0
    average_size_bytes: float = 0.0
    largest_checkpoint_bytes: int = 0
    smallest_checkpoint_bytes: int = 0
    
    total_restores: int = 0
    average_restores: float = 0.0
    
    oldest_checkpoint_age_hours: float = 0.0
    newest_checkpoint_age_hours: float = 0.0
    average_age_hours: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_checkpoints": self.total_checkpoints,
            "active_checkpoints": self.active_checkpoints,
            "expired_checkpoints": self.expired_checkpoints,
            "corrupted_checkpoints": self.corrupted_checkpoints,
            "archived_checkpoints": self.archived_checkpoints,
            "total_size_bytes": self.total_size_bytes,
            "average_size_bytes": self.average_size_bytes,
            "largest_checkpoint_bytes": self.largest_checkpoint_bytes,
            "smallest_checkpoint_bytes": self.smallest_checkpoint_bytes,
            "total_restores": self.total_restores,
            "average_restores": self.average_restores,
            "oldest_checkpoint_age_hours": self.oldest_checkpoint_age_hours,
            "newest_checkpoint_age_hours": self.newest_checkpoint_age_hours,
            "average_age_hours": self.average_age_hours,
        }