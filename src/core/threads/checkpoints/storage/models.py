"""Thread检查点存储领域模型

定义Thread检查点的领域模型，包含业务行为和领域规则。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
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
    MANUAL = "manual"
    AUTO = "auto"
    ERROR = "error"
    MILESTONE = "milestone"


@dataclass
class ThreadCheckpoint:
    """Thread检查点领域模型
    
    包含检查点的业务逻辑和领域规则。
    """
    
    # 基本属性
    id: str = field(default_factory=lambda: f"checkpoint_{uuid.uuid4().hex}")
    thread_id: str = ""
    state_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 状态属性
    status: CheckpointStatus = CheckpointStatus.ACTIVE
    checkpoint_type: CheckpointType = CheckpointType.AUTO
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # 统计信息
    size_bytes: int = 0
    restore_count: int = 0
    last_restored_at: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if not self.thread_id:
            raise ValueError("Thread ID cannot be empty")
        
        if not self.state_data:
            raise ValueError("State data cannot be empty")
        
        # 计算数据大小
        import json
        self.size_bytes = len(json.dumps(self.state_data))
    
    # 领域方法
    def is_valid(self) -> bool:
        """验证检查点有效性
        
        Returns:
            检查点是否有效
        """
        return (
            bool(self.id and self.thread_id and self.state_data) and
            self.status == CheckpointStatus.ACTIVE and
            not self.is_expired()
        )
    
    def can_restore(self) -> bool:
        """检查是否可以恢复
        
        Returns:
            是否可以恢复
        """
        return self.is_valid() and self.status != CheckpointStatus.CORRUPTED
    
    def is_expired(self) -> bool:
        """检查是否已过期
        
        Returns:
            是否已过期
        """
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def get_age(self) -> int:
        """获取检查点年龄（秒）
        
        Returns:
            检查点年龄（秒）
        """
        return int((datetime.now() - self.created_at).total_seconds())
    
    def get_age_hours(self) -> float:
        """获取检查点年龄（小时）
        
        Returns:
            检查点年龄（小时）
        """
        return self.get_age() / 3600.0
    
    def mark_restored(self) -> None:
        """标记为已恢复"""
        self.restore_count += 1
        self.last_restored_at = datetime.now()
        self.updated_at = datetime.now()
    
    def mark_expired(self) -> None:
        """标记为已过期"""
        self.status = CheckpointStatus.EXPIRED
        self.updated_at = datetime.now()
    
    def mark_corrupted(self) -> None:
        """标记为已损坏"""
        self.status = CheckpointStatus.CORRUPTED
        self.updated_at = datetime.now()
    
    def mark_archived(self) -> None:
        """标记为已归档"""
        self.status = CheckpointStatus.ARCHIVED
        self.updated_at = datetime.now()
    
    def update_state_data(self, new_state_data: Dict[str, Any]) -> None:
        """更新状态数据
        
        Args:
            new_state_data: 新的状态数据
        """
        if not new_state_data:
            raise ValueError("New state data cannot be empty")
        
        self.state_data = new_state_data
        self.updated_at = datetime.now()
        
        # 重新计算大小
        import json
        self.size_bytes = len(json.dumps(self.state_data))
    
    def set_expiration(self, hours: int) -> None:
        """设置过期时间
        
        Args:
            hours: 过期小时数
        """
        if hours <= 0:
            raise ValueError("Expiration hours must be positive")
        
        from datetime import timedelta
        self.expires_at = datetime.now() + timedelta(hours=hours)
        self.updated_at = datetime.now()
    
    def extend_expiration(self, hours: int) -> None:
        """延长过期时间
        
        Args:
            hours: 延长的小时数
        """
        if hours <= 0:
            raise ValueError("Extension hours must be positive")
        
        from datetime import timedelta
        
        if self.expires_at is None:
            self.expires_at = datetime.now() + timedelta(hours=hours)
        else:
            self.expires_at += timedelta(hours=hours)
        
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典表示
        """
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "state_data": self.state_data,
            "metadata": self.metadata,
            "status": self.status.value,
            "checkpoint_type": self.checkpoint_type.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "size_bytes": self.size_bytes,
            "restore_count": self.restore_count,
            "last_restored_at": self.last_restored_at.isoformat() if self.last_restored_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThreadCheckpoint':
        """从字典创建实例
        
        Args:
            data: 字典数据
            
        Returns:
            ThreadCheckpoint实例
        """
        # 处理时间字段
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        
        last_restored_at = None
        if data.get("last_restored_at"):
            last_restored_at = datetime.fromisoformat(data["last_restored_at"])
        
        return cls(
            id=data["id"],
            thread_id=data["thread_id"],
            state_data=data["state_data"],
            metadata=data.get("metadata", {}),
            status=CheckpointStatus(data.get("status", "active")),
            checkpoint_type=CheckpointType(data.get("checkpoint_type", "auto")),
            created_at=created_at,
            updated_at=updated_at,
            expires_at=expires_at,
            size_bytes=data.get("size_bytes", 0),
            restore_count=data.get("restore_count", 0),
            last_restored_at=last_restored_at,
        )
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"ThreadCheckpoint(id={self.id}, thread_id={self.thread_id}, status={self.status})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"ThreadCheckpoint(id={self.id}, thread_id={self.thread_id}, "
                f"status={self.status}, type={self.checkpoint_type}, "
                f"created_at={self.created_at.isoformat()})")


@dataclass
class CheckpointMetadata:
    """检查点元数据模型"""
    
    title: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "custom_data": self.custom_data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointMetadata':
        """从字典创建实例"""
        return cls(
            title=data.get("title"),
            description=data.get("description"),
            tags=data.get("tags", []),
            custom_data=data.get("custom_data", {}),
        )


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