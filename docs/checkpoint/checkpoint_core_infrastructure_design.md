# Checkpoint Core与Infrastructure层设计规范

## 概述

本文档定义checkpoint模块core层和infrastructure层的重构设计规范，专注于统一数据模型和存储抽象，为后续的服务层和适配器层重构奠定基础。

## 设计原则

### 1. 分层职责原则
- **Core层**: 定义领域模型、业务规则和核心逻辑
- **Infrastructure层**: 提供技术实现、数据持久化和外部系统集成
- **依赖方向**: Infrastructure层只能依赖Core层的接口，不能依赖Service层

### 2. 统一抽象原则
- 统一checkpoint数据模型
- 统一存储接口抽象
- 统一异常处理机制
- 统一配置管理

### 3. 扩展性原则
- 支持Thread特定的业务扩展
- 支持多种存储后端
- 支持插件化功能扩展
- 支持配置驱动的行为

## Core层设计

### 1. 统一数据模型

#### 1.1 基础Checkpoint模型

```python
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
```

#### 1.2 业务规则和验证

```python
from typing import Dict, Any, List
from datetime import datetime, timedelta

class CheckpointValidator:
    """检查点验证器"""
    
    # 业务规则常量
    MAX_CHECKPOINTS_PER_THREAD = 100
    MAX_CHECKPOINT_SIZE_MB = 100
    MIN_CHECKPOINT_AGE_HOURS_FOR_CLEANUP = 1
    
    @classmethod
    def validate_checkpoint(cls, checkpoint: Checkpoint) -> None:
        """验证检查点
        
        Args:
            checkpoint: 检查点对象
            
        Raises:
            ValueError: 验证失败时抛出
        """
        if not checkpoint.id:
            raise ValueError("Checkpoint ID cannot be empty")
        
        if not checkpoint.channel_values and not checkpoint.state_data:
            raise ValueError("Checkpoint data cannot be empty")
        
        # 检查数据大小
        import json
        size_mb = len(json.dumps(checkpoint.to_dict())) / (1024 * 1024)
        if size_mb > cls.MAX_CHECKPOINT_SIZE_MB:
            raise ValueError(f"Checkpoint data too large: {size_mb:.2f}MB > {cls.MAX_CHECKPOINT_SIZE_MB}MB")
    
    @classmethod
    def validate_metadata(cls, metadata: CheckpointMetadata) -> None:
        """验证元数据
        
        Args:
            metadata: 元数据对象
            
        Raises:
            ValueError: 验证失败时抛出
        """
        if metadata.size_bytes < 0:
            raise ValueError("Size bytes cannot be negative")
        
        if metadata.restore_count < 0:
            raise ValueError("Restore count cannot be negative")
    
    @classmethod
    def validate_thread_checkpoint_limit(cls, current_count: int) -> None:
        """验证Thread检查点数量限制
        
        Args:
            current_count: 当前检查点数量
            
        Raises:
            ValueError: 超过限制时抛出
        """
        if current_count >= cls.MAX_CHECKPOINTS_PER_THREAD:
            raise ValueError(f"Thread checkpoint limit exceeded: {current_count} >= {cls.MAX_CHECKPOINTS_PER_THREAD}")
    
    @classmethod
    def should_cleanup_checkpoint(cls, checkpoint: Checkpoint) -> bool:
        """判断是否应该清理检查点
        
        Args:
            checkpoint: 检查点对象
            
        Returns:
            是否应该清理
        """
        # 手动和里程碑检查点不自动清理
        if checkpoint.checkpoint_type in [CheckpointType.MANUAL, CheckpointType.MILESTONE]:
            return False
        
        # 检查年龄
        age_hours = checkpoint.get_age_hours()
        if age_hours < cls.MIN_CHECKPOINT_AGE_HOURS_FOR_CLEANUP:
            return False
        
        # 错误检查点保留更长时间
        if checkpoint.checkpoint_type == CheckpointType.ERROR:
            return age_hours > 72  # 3天
        
        # 自动检查点保留24小时
        return age_hours > 24

class CheckpointFactory:
    """检查点工厂"""
    
    @staticmethod
    def create_checkpoint(
        thread_id: Optional[str] = None,
        state_data: Optional[Dict[str, Any]] = None,
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Checkpoint:
        """创建检查点
        
        Args:
            thread_id: Thread ID
            state_data: 状态数据
            checkpoint_type: 检查点类型
            metadata: 元数据
            
        Returns:
            检查点对象
        """
        checkpoint = Checkpoint(
            thread_id=thread_id,
            state_data=state_data or {},
            checkpoint_type=checkpoint_type
        )
        
        # 设置元数据
        if metadata:
            checkpoint.metadata.custom_data.update(metadata)
        
        return checkpoint
    
    @staticmethod
    def create_metadata(
        source: Optional[str] = None,
        step: Optional[int] = None,
        thread_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> CheckpointMetadata:
        """创建元数据
        
        Args:
            source: 来源
            step: 步数
            thread_id: Thread ID
            title: 标题
            description: 描述
            tags: 标签列表
            
        Returns:
            元数据对象
        """
        return CheckpointMetadata(
            source=source,
            step=step,
            thread_id=thread_id,
            title=title,
            description=description,
            tags=tags or []
        )
    
    @staticmethod
    def create_tuple(
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        parent_config: Optional[Dict[str, Any]] = None
    ) -> CheckpointTuple:
        """创建检查点元组
        
        Args:
            config: 配置
            checkpoint: 检查点
            parent_config: 父配置
            
        Returns:
            检查点元组
        """
        return CheckpointTuple(
            config=config,
            checkpoint=checkpoint,
            parent_config=parent_config
        )
    
    @staticmethod
    def extract_thread_id(config: Dict[str, Any]) -> Optional[str]:
        """从配置中提取Thread ID
        
        Args:
            config: 配置字典
            
        Returns:
            Thread ID
        """
        return config.get("configurable", {}).get("thread_id")
    
    @staticmethod
    def extract_checkpoint_id(config: Dict[str, Any]) -> Optional[str]:
        """从配置中提取检查点ID
        
        Args:
            config: 配置字典
            
        Returns:
            检查点ID
        """
        return config.get("configurable", {}).get("checkpoint_id")
    
    @staticmethod
    def create_config(
        thread_id: str,
        checkpoint_ns: str = "",
        checkpoint_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建配置
        
        Args:
            thread_id: Thread ID
            checkpoint_ns: 检查点命名空间
            checkpoint_id: 检查点ID
            
        Returns:
            配置字典
        """
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns
            }
        }
        
        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id
        
        return config
```

### 2. Core层接口定义

#### 2.1 存储接口

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from collections.abc import AsyncIterator

class ICheckpointRepository(ABC):
    """检查点仓储接口"""
    
    @abstractmethod
    async def save(self, checkpoint: Checkpoint) -> bool:
        """保存检查点
        
        Args:
            checkpoint: 检查点对象
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """加载检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            检查点对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def list(
        self,
        thread_id: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
        checkpoint_type: Optional[CheckpointType] = None,
        limit: Optional[int] = None
    ) -> List[Checkpoint]:
        """列出检查点
        
        Args:
            thread_id: Thread ID过滤
            status: 状态过滤
            checkpoint_type: 类型过滤
            limit: 返回数量限制
            
        Returns:
            检查点列表
        """
        pass
    
    @abstractmethod
    async def count(
        self,
        thread_id: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
        checkpoint_type: Optional[CheckpointType] = None
    ) -> int:
        """统计检查点数量
        
        Args:
            thread_id: Thread ID过滤
            status: 状态过滤
            checkpoint_type: 类型过滤
            
        Returns:
            检查点数量
        """
        pass
    
    @abstractmethod
    async def cleanup_expired(self, thread_id: Optional[str] = None) -> int:
        """清理过期检查点
        
        Args:
            thread_id: Thread ID，None表示清理所有
            
        Returns:
            清理的检查点数量
        """
        pass
    
    @abstractmethod
    async def get_statistics(
        self,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取统计信息
        
        Args:
            thread_id: Thread ID，None表示全局统计
            
        Returns:
            统计信息字典
        """
        pass

class ICheckpointStorage(ABC):
    """检查点存储接口（兼容LangGraph）"""
    
    @abstractmethod
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点"""
        pass
    
    @abstractmethod
    def get_tuple(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点元组"""
        pass
    
    @abstractmethod
    def list(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """列出匹配给定条件的检查点"""
        pass
    
    @abstractmethod
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """存储带有其配置和元数据的检查点"""
        pass
    
    @abstractmethod
    def put_writes(
        self,
        config: Dict[str, Any],
        writes: List[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """存储与检查点关联的中间写入"""
        pass
```

## Infrastructure层设计

### 1. 存储后端实现

#### 1.1 基础存储后端

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.core.checkpoint.models import Checkpoint, CheckpointStatus, CheckpointType
from src.core.checkpoint.interfaces import ICheckpointRepository

class BaseCheckpointBackend(ICheckpointRepository):
    """基础检查点存储后端"""
    
    def __init__(self, **config: Any) -> None:
        """初始化后端
        
        Args:
            config: 配置参数
        """
        self._config = config
        self._connected = False
    
    async def connect(self) -> None:
        """连接到存储后端"""
        if not self._connected:
            await self._do_connect()
            self._connected = True
    
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        if self._connected:
            await self._do_disconnect()
            self._connected = False
    
    @abstractmethod
    async def _do_connect(self) -> None:
        """执行连接操作"""
        pass
    
    @abstractmethod
    async def _do_disconnect(self) -> None:
        """执行断开连接操作"""
        pass
    
    def _check_connection(self) -> None:
        """检查连接状态"""
        if not self._connected:
            raise RuntimeError("Storage backend is not connected")
```

#### 1.2 内存存储后端

```python
import time
from typing import Dict, Any, Optional, List
from collections import defaultdict
from src.core.checkpoint.models import Checkpoint, CheckpointStatus, CheckpointType
from src.core.checkpoint.interfaces import ICheckpointRepository

class MemoryCheckpointBackend(BaseCheckpointBackend):
    """内存检查点存储后端"""
    
    def __init__(self, **config: Any) -> None:
        """初始化内存存储后端"""
        super().__init__(**config)
        
        # 内存存储
        self._checkpoints: Dict[str, Checkpoint] = {}
        self._thread_index: Dict[str, List[str]] = defaultdict(list)
        self._status_index: Dict[CheckpointStatus, List[str]] = defaultdict(list)
        self._type_index: Dict[CheckpointType, List[str]] = defaultdict(list)
        
        # 配置
        self.max_checkpoints = config.get("max_checkpoints", 1000)
        self.enable_ttl = config.get("enable_ttl", False)
        self.default_ttl_seconds = config.get("default_ttl_seconds", 3600)
    
    async def _do_connect(self) -> None:
        """连接到内存存储"""
        # 内存存储不需要连接操作
        pass
    
    async def _do_disconnect(self) -> None:
        """断开内存存储连接"""
        # 清理所有数据
        self._checkpoints.clear()
        self._thread_index.clear()
        self._status_index.clear()
        self._type_index.clear()
    
    async def save(self, checkpoint: Checkpoint) -> bool:
        """保存检查点"""
        self._check_connection()
        
        try:
            # 检查容量限制
            if len(self._checkpoints) >= self.max_checkpoints:
                await self._cleanup_oldest_checkpoints()
            
            # 更新索引
            self._update_indexes(checkpoint)
            
            # 保存检查点
            self._checkpoints[checkpoint.id] = checkpoint
            
            return True
            
        except Exception as e:
            # 记录错误日志
            return False
    
    async def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """加载检查点"""
        self._check_connection()
        
        checkpoint = self._checkpoints.get(checkpoint_id)
        if checkpoint:
            # 检查是否过期
            if self.enable_ttl and checkpoint.is_expired():
                await self.delete(checkpoint_id)
                return None
            return checkpoint
        
        return None
    
    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        self._check_connection()
        
        checkpoint = self._checkpoints.get(checkpoint_id)
        if checkpoint:
            # 从索引中删除
            self._remove_from_indexes(checkpoint)
            
            # 从存储中删除
            del self._checkpoints[checkpoint_id]
            return True
        
        return False
    
    async def list(
        self,
        thread_id: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
        checkpoint_type: Optional[CheckpointType] = None,
        limit: Optional[int] = None
    ) -> List[Checkpoint]:
        """列出检查点"""
        self._check_connection()
        
        # 获取候选检查点ID
        candidate_ids = None
        
        if thread_id:
            candidate_ids = set(self._thread_index.get(thread_id, []))
        
        if status:
            status_ids = set(self._status_index.get(status, []))
            candidate_ids = status_ids if candidate_ids is None else candidate_ids & status_ids
        
        if checkpoint_type:
            type_ids = set(self._type_index.get(checkpoint_type, []))
            candidate_ids = type_ids if candidate_ids is None else candidate_ids & type_ids
        
        if candidate_ids is None:
            candidate_ids = set(self._checkpoints.keys())
        
        # 获取检查点并过滤
        checkpoints = []
        for checkpoint_id in candidate_ids:
            checkpoint = self._checkpoints.get(checkpoint_id)
            if checkpoint:
                # 检查是否过期
                if self.enable_ttl and checkpoint.is_expired():
                    continue
                
                checkpoints.append(checkpoint)
        
        # 按创建时间排序
        checkpoints.sort(key=lambda c: c.ts, reverse=True)
        
        # 应用限制
        if limit:
            checkpoints = checkpoints[:limit]
        
        return checkpoints
    
    async def count(
        self,
        thread_id: Optional[str] = None,
        status: Optional[CheckpointStatus] = None,
        checkpoint_type: Optional[CheckpointType] = None
    ) -> int:
        """统计检查点数量"""
        checkpoints = await self.list(thread_id, status, checkpoint_type)
        return len(checkpoints)
    
    async def cleanup_expired(self, thread_id: Optional[str] = None) -> int:
        """清理过期检查点"""
        self._check_connection()
        
        if not self.enable_ttl:
            return 0
        
        expired_count = 0
        expired_checkpoints = []
        
        for checkpoint in self._checkpoints.values():
            if thread_id and checkpoint.thread_id != thread_id:
                continue
            
            if checkpoint.is_expired():
                expired_checkpoints.append(checkpoint)
        
        for checkpoint in expired_checkpoints:
            if await self.delete(checkpoint.id):
                expired_count += 1
        
        return expired_count
    
    async def get_statistics(
        self,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取统计信息"""
        self._check_connection()
        
        checkpoints = await self.list(thread_id)
        
        # 基础统计
        total_count = len(checkpoints)
        status_counts = {}
        type_counts = {}
        total_size = 0
        total_restores = 0
        
        for checkpoint in checkpoints:
            # 状态统计
            status = checkpoint.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # 类型统计
            cp_type = checkpoint.checkpoint_type.value
            type_counts[cp_type] = type_counts.get(cp_type, 0) + 1
            
            # 大小和恢复统计
            total_size += checkpoint.metadata.size_bytes
            total_restores += checkpoint.metadata.restore_count
        
        return {
            "total_checkpoints": total_count,
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "total_size_bytes": total_size,
            "average_size_bytes": total_size / total_count if total_count > 0 else 0,
            "total_restores": total_restores,
            "average_restores": total_restores / total_count if total_count > 0 else 0,
        }
    
    def _update_indexes(self, checkpoint: Checkpoint) -> None:
        """更新索引"""
        # Thread索引
        if checkpoint.thread_id:
            if checkpoint.id not in self._thread_index[checkpoint.thread_id]:
                self._thread_index[checkpoint.thread_id].append(checkpoint.id)
        
        # 状态索引
        if checkpoint.id not in self._status_index[checkpoint.status]:
            self._status_index[checkpoint.status].append(checkpoint.id)
        
        # 类型索引
        if checkpoint.id not in self._type_index[checkpoint.checkpoint_type]:
            self._type_index[checkpoint.checkpoint_type].append(checkpoint.id)
    
    def _remove_from_indexes(self, checkpoint: Checkpoint) -> None:
        """从索引中删除"""
        # Thread索引
        if checkpoint.thread_id and checkpoint.id in self._thread_index[checkpoint.thread_id]:
            self._thread_index[checkpoint.thread_id].remove(checkpoint.id)
        
        # 状态索引
        if checkpoint.id in self._status_index[checkpoint.status]:
            self._status_index[checkpoint.status].remove(checkpoint.id)
        
        # 类型索引
        if checkpoint.id in self._type_index[checkpoint.checkpoint_type]:
            self._type_index[checkpoint.checkpoint_type].remove(checkpoint.id)
    
    async def _cleanup_oldest_checkpoints(self) -> None:
        """清理最旧的检查点"""
        if len(self._checkpoints) < self.max_checkpoints:
            return
        
        # 按创建时间排序
        sorted_checkpoints = sorted(
            self._checkpoints.values(),
            key=lambda c: c.ts
        )
        
        # 删除最旧的10%
        cleanup_count = max(1, self.max_checkpoints // 10)
        for checkpoint in sorted_checkpoints[:cleanup_count]:
            await self.delete(checkpoint.id)
```

### 2. 存储适配器（Infrastructure层）

#### 2.1 LangGraph存储适配器

```python
from typing import Dict, Any, Optional, List
from collections.abc import AsyncIterator
from src.core.checkpoint.models import Checkpoint, CheckpointTuple, CheckpointFactory
from src.core.checkpoint.interfaces import ICheckpointRepository, ICheckpointStorage

class LangGraphStorageAdapter(ICheckpointStorage):
    """LangGraph存储适配器
    
    将ICheckpointRepository适配到LangGraph的ICheckpointStorage接口。
    """
    
    def __init__(self, repository: ICheckpointRepository):
        """初始化适配器
        
        Args:
            repository: 检查点仓储
        """
        self._repository = repository
    
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点"""
        checkpoint_id = CheckpointFactory.extract_checkpoint_id(config)
        if not checkpoint_id:
            # 尝试获取最新检查点
            thread_id = CheckpointFactory.extract_thread_id(config)
            if thread_id:
                checkpoints = await self._repository.list(thread_id=thread_id, limit=1)
                if checkpoints:
                    checkpoint = checkpoints[0]
                    return checkpoint.to_dict()
            return None
        
        checkpoint = await self._repository.load(checkpoint_id)
        if checkpoint:
            return checkpoint.to_dict()
        
        return None
    
    def get_tuple(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点元组"""
        checkpoint_data = self.get(config)
        if checkpoint_data:
            checkpoint = Checkpoint.from_dict(checkpoint_data)
            return CheckpointFactory.create_tuple(config, checkpoint).to_dict()
        
        return None
    
    def list(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """列出匹配给定条件的检查点"""
        thread_id = None
        if config:
            thread_id = CheckpointFactory.extract_thread_id(config)
        
        # 获取检查点列表
        checkpoints = await self._repository.list(thread_id=thread_id, limit=limit)
        
        # 应用过滤器
        for checkpoint in checkpoints:
            # TODO: 实现更复杂的过滤逻辑
            checkpoint_dict = checkpoint.to_dict()
            config_dict = CheckpointFactory.create_config(
                thread_id=checkpoint.thread_id or "",
                checkpoint_id=checkpoint.id
            )
            
            yield {
                "config": config_dict,
                "checkpoint": checkpoint_dict,
                "metadata": checkpoint.metadata.to_dict(),
                "parent_config": None
            }
    
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """存储带有其配置和元数据的检查点"""
        # 创建检查点对象
        thread_id = CheckpointFactory.extract_thread_id(config)
        checkpoint_obj = Checkpoint(
            thread_id=thread_id,
            channel_values=checkpoint.get("channel_values", {}),
            channel_versions=checkpoint.get("channel_versions", {}),
            versions_seen=checkpoint.get("versions_seen", {}),
            state_data=checkpoint.get("state_data", {})
        )
        
        # 设置元数据
        checkpoint_obj.metadata.custom_data.update(metadata)
        
        # 保存检查点
        success = await self._repository.save(checkpoint_obj)
        if not success:
            raise RuntimeError("Failed to save checkpoint")
        
        # 更新配置
        updated_config = config.copy()
        updated_config["configurable"]["checkpoint_id"] = checkpoint_obj.id
        
        return updated_config
    
    def put_writes(
        self,
        config: Dict[str, Any],
        writes: List[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """存储与检查点关联的中间写入"""
        # TODO: 实现写入记录存储
        pass
```

## 配置管理

### 1. 配置模型

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class CheckpointStorageConfig:
    """检查点存储配置"""
    
    # 存储类型
    storage_type: str = "memory"  # memory, sqlite, file
    
    # 内存存储配置
    max_checkpoints: int = 1000
    enable_ttl: bool = False
    default_ttl_seconds: int = 3600
    
    # SQLite存储配置
    db_path: str = "checkpoints.db"
    connection_pool_size: int = 5
    enable_wal_mode: bool = True
    enable_foreign_keys: bool = True
    
    # 文件存储配置
    storage_path: str = "./checkpoints"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointStorageConfig':
        """从字典创建配置"""
        return cls(
            storage_type=data.get("storage_type", "memory"),
            max_checkpoints=data.get("max_checkpoints", 1000),
            enable_ttl=data.get("enable_ttl", False),
            default_ttl_seconds=data.get("default_ttl_seconds", 3600),
            db_path=data.get("db_path", "checkpoints.db"),
            connection_pool_size=data.get("connection_pool_size", 5),
            enable_wal_mode=data.get("enable_wal_mode", True),
            enable_foreign_keys=data.get("enable_foreign_keys", True),
            storage_path=data.get("storage_path", "./checkpoints"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "storage_type": self.storage_type,
            "max_checkpoints": self.max_checkpoints,
            "enable_ttl": self.enable_ttl,
            "default_ttl_seconds": self.default_ttl_seconds,
            "db_path": self.db_path,
            "connection_pool_size": self.connection_pool_size,
            "enable_wal_mode": self.enable_wal_mode,
            "enable_foreign_keys": self.enable_foreign_keys,
            "storage_path": self.storage_path,
        }
```

### 2. 存储工厂

```python
from typing import Dict, Any
from src.core.checkpoint.interfaces import ICheckpointRepository
from src.infrastructure.checkpoint.memory import MemoryCheckpointBackend
# 其他存储后端导入...

class CheckpointStorageFactory:
    """检查点存储工厂"""
    
    @staticmethod
    def create_repository(config: CheckpointStorageConfig) -> ICheckpointRepository:
        """创建检查点仓储
        
        Args:
            config: 存储配置
            
        Returns:
            检查点仓储实例
        """
        if config.storage_type == "memory":
            return MemoryCheckpointBackend(**config.to_dict())
        elif config.storage_type == "sqlite":
            return SqliteCheckpointBackend(**config.to_dict())
        elif config.storage_type == "file":
            return FileCheckpointBackend(**config.to_dict())
        else:
            raise ValueError(f"Unsupported storage type: {config.storage_type}")
    
    @staticmethod
    def create_langraph_storage(config: CheckpointStorageConfig) -> ICheckpointStorage:
        """创建LangGraph存储适配器
        
        Args:
            config: 存储配置
            
        Returns:
            LangGraph存储适配器实例
        """
        repository = CheckpointStorageFactory.create_repository(config)
        return LangGraphStorageAdapter(repository)
```

## 总结

本设计规范定义了checkpoint模块core层和infrastructure层的统一架构，通过以下方式实现了代码的统一和简化：

1. **统一数据模型**: 将Thread特定的checkpoint模型和通用checkpoint模型统一为一个可扩展的模型
2. **统一存储接口**: 提供了统一的存储抽象，支持多种存储后端
3. **分层架构**: 明确了core层和infrastructure层的职责边界
4. **配置驱动**: 通过配置管理支持不同的存储类型和行为
5. **适配器模式**: 提供了LangGraph接口的适配器，保持兼容性

这个设计为后续的服务层重构和适配器层实现奠定了坚实的基础，同时保持了系统的可扩展性和可维护性。