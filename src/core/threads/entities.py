"""Thread实体定义"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field

from src.interfaces.threads.entities import IThread, IThreadBranch, IThreadSnapshot


class ThreadStatus(str, Enum):
    """线程状态枚举"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"
    BRANCHED = "branched"  # 已分支状态


class ThreadType(str, Enum):
    """线程类型枚举"""
    MAIN = "main"          # 主线线程
    BRANCH = "branch"      # 分支线程
    SNAPSHOT = "snapshot"  # 快照线程
    FORK = "fork"         # 派生线程


@dataclass
class ThreadMetadata:
    """线程元数据模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_data: Dict[str, Any] = field(default_factory=dict)


class Thread(IThread):
    """线程实体模型"""
    
    def __init__(
        self,
        id: str,
        status: str = "active",
        type: str = "main",
        graph_id: Optional[str] = None,
        parent_thread_id: Optional[str] = None,
        source_checkpoint_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[ThreadMetadata] = None,
        config: Optional[Dict[str, Any]] = None,
        state: Optional[Dict[str, Any]] = None,
        message_count: int = 0,
        checkpoint_count: int = 0,
        branch_count: int = 0
    ):
        """初始化线程实体"""
        self._id = id
        self._status = ThreadStatus(status)
        self._type = ThreadType(type)
        self._graph_id = graph_id
        self._parent_thread_id = parent_thread_id
        self._source_checkpoint_id = source_checkpoint_id
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at or datetime.utcnow()
        self._metadata = metadata or ThreadMetadata()
        self._config = config or {}
        self._state = state or {}
        self._message_count = message_count
        self._checkpoint_count = checkpoint_count
        self._branch_count = branch_count

    # 实现IThread接口的属性
    @property
    def id(self) -> str:
        """线程ID"""
        return self._id

    @property
    def status(self) -> str:
        """线程状态"""
        return self._status.value

    @property
    def type(self) -> str:
        """线程类型"""
        return self._type.value

    @property
    def graph_id(self) -> Optional[str]:
        """关联的图ID"""
        return self._graph_id

    @property
    def parent_thread_id(self) -> Optional[str]:
        """父线程ID"""
        return self._parent_thread_id

    @property
    def source_checkpoint_id(self) -> Optional[str]:
        """源检查点ID"""
        return self._source_checkpoint_id

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
        """线程元数据"""
        return {
            "title": self._metadata.title,
            "description": self._metadata.description,
            "tags": self._metadata.tags,
            "custom_data": self._metadata.custom_data
        }

    @property
    def config(self) -> Dict[str, Any]:
        """线程配置"""
        return self._config

    @property
    def state(self) -> Dict[str, Any]:
        """线程状态"""
        return self._state

    @property
    def message_count(self) -> int:
        """消息数量"""
        return self._message_count

    @property
    def checkpoint_count(self) -> int:
        """检查点数量"""
        return self._checkpoint_count

    @property
    def branch_count(self) -> int:
        """分支数量"""
        return self._branch_count

    # 实现IThread接口的抽象方法
    def can_transition_to(self, new_status: str) -> bool:
        """检查是否可以转换到指定状态"""
        try:
            target_status = ThreadStatus(new_status)
        except ValueError:
            return False
            
        # 定义状态转换规则
        valid_transitions = {
            ThreadStatus.ACTIVE: [ThreadStatus.PAUSED, ThreadStatus.COMPLETED, ThreadStatus.FAILED, ThreadStatus.ARCHIVED, ThreadStatus.BRANCHED],
            ThreadStatus.PAUSED: [ThreadStatus.ACTIVE, ThreadStatus.COMPLETED, ThreadStatus.FAILED, ThreadStatus.ARCHIVED],
            ThreadStatus.COMPLETED: [ThreadStatus.ACTIVE, ThreadStatus.ARCHIVED],
            ThreadStatus.FAILED: [ThreadStatus.ACTIVE, ThreadStatus.ARCHIVED],
            ThreadStatus.ARCHIVED: [ThreadStatus.ACTIVE],  # 可以重新激活归档的线程
            ThreadStatus.BRANCHED: [ThreadStatus.ACTIVE, ThreadStatus.ARCHIVED]  # 分支状态可以重新激活或归档
        }
        
        return target_status in valid_transitions.get(self._status, [])
    
    def transition_to(self, new_status: str) -> bool:
        """转换线程状态"""
        if not self.can_transition_to(new_status):
            return False
        
        self._status = ThreadStatus(new_status)
        self.update_timestamp()
        return True
    
    def is_forkable(self) -> bool:
        """检查是否可以派生分支"""
        return self._status in [ThreadStatus.ACTIVE, ThreadStatus.PAUSED]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self._id,
            "status": self._status.value,
            "type": self._type.value,
            "graph_id": self._graph_id,
            "parent_thread_id": self._parent_thread_id,
            "source_checkpoint_id": self._source_checkpoint_id,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "metadata": self.metadata,
            "config": self._config,
            "state": self._state,
            "message_count": self._message_count,
            "checkpoint_count": self._checkpoint_count,
            "branch_count": self._branch_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Thread":
        """从字典创建实例"""
        metadata_data = data.get("metadata", {})
        metadata = ThreadMetadata(
            title=metadata_data.get("title"),
            description=metadata_data.get("description"),
            tags=metadata_data.get("tags", []),
            custom_data=metadata_data.get("custom_data", {})
        )
        
        return cls(
            id=data["id"],
            status=data.get("status", "active"),
            type=data.get("type", "main"),
            graph_id=data.get("graph_id"),
            parent_thread_id=data.get("parent_thread_id"),
            source_checkpoint_id=data.get("source_checkpoint_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else None,
            metadata=metadata,
            config=data.get("config", {}),
            state=data.get("state", {}),
            message_count=data.get("message_count", 0),
            checkpoint_count=data.get("checkpoint_count", 0),
            branch_count=data.get("branch_count", 0)
        )
    
    # 保持原有的方法
    def update_timestamp(self) -> None:
        """更新时间戳"""
        self._updated_at = datetime.utcnow()
    
    def increment_message_count(self) -> None:
        """增加消息计数"""
        self._message_count += 1
        self.update_timestamp()
    
    def increment_checkpoint_count(self) -> None:
        """增加检查点计数"""
        self._checkpoint_count += 1
        self.update_timestamp()
    
    def increment_branch_count(self) -> None:
        """增加分支计数"""
        self._branch_count += 1
        self.update_timestamp()


class ThreadBranch(IThreadBranch):
    """线程分支实体模型"""
    
    def __init__(
        self,
        id: str,
        thread_id: str,
        parent_thread_id: str,
        source_checkpoint_id: str,
        branch_name: str,
        branch_type: str = "user",
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """初始化线程分支实体"""
        self._id = id
        self._thread_id = thread_id
        self._parent_thread_id = parent_thread_id
        self._source_checkpoint_id = source_checkpoint_id
        self._branch_name = branch_name
        self._branch_type = branch_type
        self._created_at = created_at or datetime.utcnow()
        self._metadata = metadata or {}

    # 实现IThreadBranch接口的属性
    @property
    def id(self) -> str:
        """分支ID"""
        return self._id

    @property
    def thread_id(self) -> str:
        """所属线程ID"""
        return self._thread_id

    @property
    def parent_thread_id(self) -> str:
        """父线程ID"""
        return self._parent_thread_id

    @property
    def source_checkpoint_id(self) -> str:
        """源检查点ID"""
        return self._source_checkpoint_id

    @property
    def branch_name(self) -> str:
        """分支名称"""
        return self._branch_name

    @property
    def branch_type(self) -> str:
        """分支类型"""
        return self._branch_type

    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at

    @property
    def metadata(self) -> Dict[str, Any]:
        """分支元数据"""
        return self._metadata

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self._id,
            "thread_id": self._thread_id,
            "parent_thread_id": self._parent_thread_id,
            "source_checkpoint_id": self._source_checkpoint_id,
            "branch_name": self._branch_name,
            "branch_type": self._branch_type,
            "created_at": self._created_at.isoformat(),
            "metadata": self._metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreadBranch":
        """从字典创建实例"""
        return cls(
            id=data["id"],
            thread_id=data["thread_id"],
            parent_thread_id=data["parent_thread_id"],
            source_checkpoint_id=data["source_checkpoint_id"],
            branch_name=data["branch_name"],
            branch_type=data.get("branch_type", "user"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
            metadata=data.get("metadata", {})
        )


class ThreadSnapshot(IThreadSnapshot):
    """线程快照实体模型"""
    
    def __init__(
        self,
        id: str,
        thread_id: str,
        snapshot_name: str,
        description: Optional[str] = None,
        created_at: Optional[datetime] = None,
        state_snapshot: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        message_count: int = 0,
        checkpoint_count: int = 0
    ):
        """初始化线程快照实体"""
        self._id = id
        self._thread_id = thread_id
        self._snapshot_name = snapshot_name
        self._description = description
        self._created_at = created_at or datetime.utcnow()
        self._state_snapshot = state_snapshot or {}
        self._metadata = metadata or {}
        self._message_count = message_count
        self._checkpoint_count = checkpoint_count

    # 实现IThreadSnapshot接口的属性
    @property
    def id(self) -> str:
        """快照ID"""
        return self._id

    @property
    def thread_id(self) -> str:
        """所属线程ID"""
        return self._thread_id

    @property
    def snapshot_name(self) -> str:
        """快照名称"""
        return self._snapshot_name

    @property
    def description(self) -> Optional[str]:
        """快照描述"""
        return self._description

    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at

    @property
    def state_snapshot(self) -> Dict[str, Any]:
        """状态快照"""
        return self._state_snapshot

    @property
    def metadata(self) -> Dict[str, Any]:
        """快照元数据"""
        return self._metadata

    @property
    def message_count(self) -> int:
        """消息数量"""
        return self._message_count

    @property
    def checkpoint_count(self) -> int:
        """检查点数量"""
        return self._checkpoint_count

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self._id,
            "thread_id": self._thread_id,
            "snapshot_name": self._snapshot_name,
            "description": self._description,
            "created_at": self._created_at.isoformat(),
            "state_snapshot": self._state_snapshot,
            "metadata": self._metadata,
            "message_count": self._message_count,
            "checkpoint_count": self._checkpoint_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreadSnapshot":
        """从字典创建实例"""
        return cls(
            id=data["id"],
            thread_id=data["thread_id"],
            snapshot_name=data["snapshot_name"],
            description=data.get("description"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
            state_snapshot=data.get("state_snapshot", {}),
            metadata=data.get("metadata", {}),
            message_count=data.get("message_count", 0),
            checkpoint_count=data.get("checkpoint_count", 0)
        )