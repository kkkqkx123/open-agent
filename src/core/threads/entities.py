"""Thread实体定义"""

from enum import Enum
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass, field

from src.interfaces.threads.entities import IThread, IThreadBranch, IThreadSnapshot
from src.core.threads.checkpoints.models import ThreadCheckpoint as Checkpoint, CheckpointType, CheckpointStatistics

if TYPE_CHECKING:
    from src.core.threads.interfaces import IThreadCheckpointService


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
        self._checkpoint_service: Optional["IThreadCheckpointService"] = None

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
    
    @metadata.setter
    def metadata(self, value: ThreadMetadata) -> None:
        """设置线程元数据"""
        if isinstance(value, ThreadMetadata):
            self._metadata = value
        elif isinstance(value, dict):
            self._metadata = ThreadMetadata(
                title=value.get("title"),
                description=value.get("description"),
                tags=value.get("tags", []),
                custom_data=value.get("custom_data", {})
            )
        else:
            raise TypeError(f"Expected ThreadMetadata or dict, got {type(value)}")
    
    def get_metadata_object(self) -> ThreadMetadata:
        """获取线程元数据对象（用于修改）"""
        return self._metadata
    
    def set_metadata_object(self, metadata: ThreadMetadata) -> None:
        """设置线程元数据对象"""
        if not isinstance(metadata, ThreadMetadata):
            raise TypeError(f"Expected ThreadMetadata, got {type(metadata)}")
        self._metadata = metadata

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
    
    @checkpoint_count.setter
    def checkpoint_count(self, value: int) -> None:
        """设置检查点数量"""
        self._checkpoint_count = value

    @property
    def branch_count(self) -> int:
        """分支数量"""
        return self._branch_count
    
    @branch_count.setter
    def branch_count(self, value: int) -> None:
        """设置分支数量"""
        self._branch_count = value

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
    
    # Checkpoint相关方法
    def set_checkpoint_service(self, service: "IThreadCheckpointService") -> None:
        """设置检查点服务
        
        Args:
            service: 检查点服务
        """
        self._checkpoint_service = service
    
    def get_checkpoint_service(self) -> Optional["IThreadCheckpointService"]:
        """获取检查点服务
        
        Returns:
            检查点服务
        """
        return self._checkpoint_service
    
    async def create_checkpoint(
        self,
        state_data: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Checkpoint:
        """创建检查点
        
        Args:
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 元数据
            
        Returns:
            创建的检查点
            
        Raises:
            ValueError: 检查点服务未设置
        """
        if self._checkpoint_service is None:
            raise ValueError("Checkpoint service not set")
        
        checkpoint = await self._checkpoint_service.create_checkpoint(
            thread_id=self._id,
            state_data=state_data,
            checkpoint_type=checkpoint_type,
            metadata=metadata
        )
        
        # 更新检查点计数
        self.increment_checkpoint_count()
        return checkpoint
    
    async def create_manual_checkpoint(
        self,
        state_data: Dict[str, Any],
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Checkpoint:
        """创建手动检查点
        
        Args:
            state_data: 状态数据
            title: 标题
            description: 描述
            tags: 标签列表
            
        Returns:
            创建的检查点
        """
        if self._checkpoint_service is None:
            raise ValueError("Checkpoint service not set")
        
        checkpoint = await self._checkpoint_service.create_manual_checkpoint(
            thread_id=self._id,
            state_data=state_data,
            title=title,
            description=description,
            tags=tags
        )
        
        # 更新检查点计数
        self.increment_checkpoint_count()
        return checkpoint
    
    async def create_error_checkpoint(
        self,
        state_data: Dict[str, Any],
        error_message: str,
        error_type: Optional[str] = None
    ) -> Checkpoint:
        """创建错误检查点
        
        Args:
            state_data: 状态数据
            error_message: 错误消息
            error_type: 错误类型
            
        Returns:
            创建的检查点
        """
        if self._checkpoint_service is None:
            raise ValueError("Checkpoint service not set")
        
        checkpoint = await self._checkpoint_service.create_error_checkpoint(
            thread_id=self._id,
            state_data=state_data,
            error_message=error_message,
            error_type=error_type
        )
        
        # 更新检查点计数
        self.increment_checkpoint_count()
        return checkpoint
    
    async def create_milestone_checkpoint(
        self,
        state_data: Dict[str, Any],
        milestone_name: str,
        description: Optional[str] = None
    ) -> Checkpoint:
        """创建里程碑检查点
        
        Args:
            state_data: 状态数据
            milestone_name: 里程碑名称
            description: 描述
            
        Returns:
            创建的检查点
        """
        if self._checkpoint_service is None:
            raise ValueError("Checkpoint service not set")
        
        checkpoint = await self._checkpoint_service.create_milestone_checkpoint(
            thread_id=self._id,
            state_data=state_data,
            milestone_name=milestone_name,
            description=description
        )
        
        # 更新检查点计数
        self.increment_checkpoint_count()
        return checkpoint
    
    async def restore_from_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """从检查点恢复
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            恢复的状态数据
        """
        if self._checkpoint_service is None:
            raise ValueError("Checkpoint service not set")
        
        return await self._checkpoint_service.restore_from_checkpoint(checkpoint_id)
    
    async def get_checkpoint_history(self, limit: int = 50) -> List[Checkpoint]:
        """获取检查点历史
        
        Args:
            limit: 返回数量限制
            
        Returns:
            检查点历史列表
        """
        if self._checkpoint_service is None:
            raise ValueError("Checkpoint service not set")
        
        return await self._checkpoint_service.get_thread_checkpoint_history(
            thread_id=self._id,
            limit=limit
        )
    
    async def get_checkpoint_statistics(self) -> CheckpointStatistics:
        """获取检查点统计信息
        
        Returns:
            统计信息
        """
        if self._checkpoint_service is None:
            raise ValueError("Checkpoint service not set")
        
        return await self._checkpoint_service.get_checkpoint_statistics(thread_id=self._id)
    
    async def cleanup_expired_checkpoints(self) -> int:
        """清理过期检查点
        
        Returns:
            清理的检查点数量
        """
        if self._checkpoint_service is None:
            raise ValueError("Checkpoint service not set")
        
        return await self._checkpoint_service.cleanup_expired_checkpoints(thread_id=self._id)


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