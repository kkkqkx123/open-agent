# Checkpoint统一存储层设计

## 概述

本文档设计统一的checkpoint存储层，整合通用checkpoint存储和Thread特定checkpoint存储，提供统一的接口和实现，支持不同的存储后端和业务需求。

## 设计目标

### 1. 统一性
- 提供统一的存储接口，支持通用和Thread特定需求
- 统一数据模型，减少重复和冗余
- 统一操作语义，简化使用和维护

### 2. 扩展性
- 支持多种存储后端（内存、文件、数据库等）
- 支持业务逻辑扩展
- 支持性能优化和功能增强

### 3. 兼容性
- 保持向后兼容性
- 支持现有代码的平滑迁移
- 提供适配器模式连接不同实现

### 4. 性能
- 优化查询性能
- 减少存储开销
- 支持批量操作

## 架构设计

### 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    业务层 (Business Layer)                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           ThreadCheckpointService                   │    │
│  │           CheckpointService                         │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   适配器层 (Adapter Layer)                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           UnifiedStorageAdapter                    │    │
│  │           ThreadStorageAdapter                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   统一存储层 (Unified Storage)                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           IUnifiedCheckpointRepository             │    │
│  │           UnifiedCheckpointRepository              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   存储后端层 (Storage Backend)                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           MemoryStorageBackend                      │    │
│  │           FileStorageBackend                        │    │
│  │           SQLiteStorageBackend                      │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 统一数据模型

### UnifiedCheckpoint

```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class CheckpointType(str, Enum):
    """检查点类型枚举"""
    GENERIC = "generic"
    THREAD = "thread"
    MANUAL = "manual"
    AUTO = "auto"
    ERROR = "error"
    MILESTONE = "milestone"

class CheckpointStatus(str, Enum):
    """检查点状态枚举"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CORRUPTED = "corrupted"
    ARCHIVED = "archived"

@dataclass
class UnifiedCheckpoint:
    """统一检查点数据模型
    
    支持通用和Thread特定的checkpoint需求。
    """
    # 基础字段
    id: str
    thread_id: str
    checkpoint_type: CheckpointType = CheckpointType.GENERIC
    status: CheckpointStatus = CheckpointStatus.ACTIVE
    
    # 数据字段
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 时间字段
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # Thread特定字段
    size_bytes: int = 0
    restore_count: int = 0
    last_restored_at: Optional[datetime] = None
    
    # 扩展字段
    extensions: Dict[str, Any] = field(default_factory=dict)
    
    def is_thread_checkpoint(self) -> bool:
        """判断是否为Thread检查点"""
        return self.checkpoint_type in [
            CheckpointType.THREAD,
            CheckpointType.MANUAL,
            CheckpointType.AUTO,
            CheckpointType.ERROR,
            CheckpointType.MILESTONE
        ]
    
    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def can_restore(self) -> bool:
        """检查是否可以恢复"""
        return (
            self.status == CheckpointStatus.ACTIVE and
            not self.is_expired()
        )
    
    def get_age_hours(self) -> float:
        """获取检查点年龄（小时）"""
        return (datetime.now() - self.created_at).total_seconds() / 3600.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "checkpoint_type": self.checkpoint_type.value,
            "status": self.status.value,
            "data": self.data,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "size_bytes": self.size_bytes,
            "restore_count": self.restore_count,
            "last_restored_at": self.last_restored_at.isoformat() if self.last_restored_at else None,
            "extensions": self.extensions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedCheckpoint":
        """从字典创建实例"""
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
            checkpoint_type=CheckpointType(data.get("checkpoint_type", "generic")),
            status=CheckpointStatus(data.get("status", "active")),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at,
            expires_at=expires_at,
            size_bytes=data.get("size_bytes", 0),
            restore_count=data.get("restore_count", 0),
            last_restored_at=last_restored_at,
            extensions=data.get("extensions", {})
        )
```

## 统一存储接口

### IUnifiedCheckpointRepository

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

class IUnifiedCheckpointRepository(ABC):
    """统一检查点仓储接口
    
    提供统一的checkpoint存储抽象，支持通用和Thread特定需求。
    """
    
    # 基础CRUD操作
    @abstractmethod
    async def save(self, checkpoint: UnifiedCheckpoint) -> bool:
        """保存检查点
        
        Args:
            checkpoint: 统一检查点对象
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, checkpoint_id: str) -> Optional[UnifiedCheckpoint]:
        """根据ID查找检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            检查点对象，不存在返回None
        """
        pass
    
    @abstractmethod
    async def update(self, checkpoint: UnifiedCheckpoint) -> bool:
        """更新检查点
        
        Args:
            checkpoint: 检查点对象
            
        Returns:
            是否更新成功
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
    
    # 查询操作
    @abstractmethod
    async def find_by_thread(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[UnifiedCheckpoint]:
        """查找Thread的所有检查点
        
        Args:
            thread_id: Thread ID
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            检查点列表
        """
        pass
    
    @abstractmethod
    async def find_by_type(
        self,
        checkpoint_type: CheckpointType,
        thread_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[UnifiedCheckpoint]:
        """根据类型查找检查点
        
        Args:
            checkpoint_type: 检查点类型
            thread_id: Thread ID（可选）
            limit: 限制数量
            
        Returns:
            检查点列表
        """
        pass
    
    @abstractmethod
    async def find_by_status(
        self,
        status: CheckpointStatus,
        thread_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[UnifiedCheckpoint]:
        """根据状态查找检查点
        
        Args:
            status: 检查点状态
            thread_id: Thread ID（可选）
            limit: 限制数量
            
        Returns:
            检查点列表
        """
        pass
    
    @abstractmethod
    async def find_expired(
        self,
        before_time: Optional[datetime] = None,
        thread_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[UnifiedCheckpoint]:
        """查找过期的检查点
        
        Args:
            before_time: 过期时间点，None表示当前时间
            thread_id: Thread ID（可选）
            limit: 限制数量
            
        Returns:
            过期检查点列表
        """
        pass
    
    @abstractmethod
    async def find_latest_by_thread(self, thread_id: str) -> Optional[UnifiedCheckpoint]:
        """查找Thread的最新检查点
        
        Args:
            thread_id: Thread ID
            
        Returns:
            最新检查点，不存在返回None
        """
        pass
    
    # 统计操作
    @abstractmethod
    async def count_by_thread(self, thread_id: str) -> int:
        """统计Thread的检查点数量
        
        Args:
            thread_id: Thread ID
            
        Returns:
            检查点数量
        """
        pass
    
    @abstractmethod
    async def count_by_type(
        self,
        checkpoint_type: CheckpointType,
        thread_id: Optional[str] = None
    ) -> int:
        """根据类型统计检查点数量
        
        Args:
            checkpoint_type: 检查点类型
            thread_id: Thread ID（可选）
            
        Returns:
            检查点数量
        """
        pass
    
    @abstractmethod
    async def count_by_status(
        self,
        status: CheckpointStatus,
        thread_id: Optional[str] = None
    ) -> int:
        """根据状态统计检查点数量
        
        Args:
            status: 检查点状态
            thread_id: Thread ID（可选）
            
        Returns:
            检查点数量
        """
        pass
    
    @abstractmethod
    async def get_statistics(
        self,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取检查点统计信息
        
        Args:
            thread_id: Thread ID，None表示全局统计
            
        Returns:
            统计信息
        """
        pass
    
    # 批量操作
    @abstractmethod
    async def save_batch(self, checkpoints: List[UnifiedCheckpoint]) -> List[bool]:
        """批量保存检查点
        
        Args:
            checkpoints: 检查点列表
            
        Returns:
            保存结果列表
        """
        pass
    
    @abstractmethod
    async def delete_batch(self, checkpoint_ids: List[str]) -> List[bool]:
        """批量删除检查点
        
        Args:
            checkpoint_ids: 检查点ID列表
            
        Returns:
            删除结果列表
        """
        pass
    
    @abstractmethod
    async def delete_by_thread(self, thread_id: str) -> int:
        """删除Thread的所有检查点
        
        Args:
            thread_id: Thread ID
            
        Returns:
            删除的检查点数量
        """
        pass
    
    @abstractmethod
    async def delete_expired(
        self,
        before_time: Optional[datetime] = None,
        thread_id: Optional[str] = None
    ) -> int:
        """删除过期的检查点
        
        Args:
            before_time: 过期时间点，None表示当前时间
            thread_id: Thread ID（可选）
            
        Returns:
            删除的检查点数量
        """
        pass
    
    # 维护操作
    @abstractmethod
    async def exists(self, checkpoint_id: str) -> bool:
        """检查检查点是否存在
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def cleanup(
        self,
        thread_id: Optional[str] = None,
        max_count: Optional[int] = None,
        max_age_hours: Optional[int] = None
    ) -> Dict[str, int]:
        """清理检查点
        
        Args:
            thread_id: Thread ID（可选）
            max_count: 最大保留数量（可选）
            max_age_hours: 最大保留小时数（可选）
            
        Returns:
            清理结果统计
        """
        pass
    
    @abstractmethod
    async def optimize(self) -> Dict[str, Any]:
        """优化存储
        
        Returns:
            优化结果
        """
        pass
```

## 存储后端接口

### IStorageBackend

```python
class IStorageBackend(ABC):
    """存储后端接口
    
    定义存储后端的抽象接口。
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化存储后端"""
        pass
    
    @abstractmethod
    async def save(self, key: str, data: Dict[str, Any]) -> bool:
        """保存数据
        
        Args:
            key: 键
            data: 数据
            
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    async def load(self, key: str) -> Optional[Dict[str, Any]]:
        """加载数据
        
        Args:
            key: 键
            
        Returns:
            数据，不存在返回None
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除数据
        
        Args:
            key: 键
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查数据是否存在
        
        Args:
            key: 键
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    async def list_keys(
        self,
        prefix: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[str]:
        """列出键
        
        Args:
            prefix: 前缀（可选）
            limit: 限制数量（可选）
            
        Returns:
            键列表
        """
        pass
    
    @abstractmethod
    async def query(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """查询数据
        
        Args:
            filters: 过滤条件
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            数据列表
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Dict[str, Any]) -> int:
        """统计数量
        
        Args:
            filters: 过滤条件
            
        Returns:
            数量
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> Dict[str, int]:
        """清理存储
        
        Returns:
            清理结果
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息
        
        Returns:
            统计信息
        """
        pass
```

## 统一存储实现

### UnifiedCheckpointRepository

```python
class UnifiedCheckpointRepository(IUnifiedCheckpointRepository):
    """统一检查点仓储实现
    
    基于存储后端的统一检查点仓储实现。
    """
    
    def __init__(self, backend: IStorageBackend):
        """初始化仓储
        
        Args:
            backend: 存储后端
        """
        self._backend = backend
        self._index_manager = IndexManager(backend)
        self._query_optimizer = QueryOptimizer(backend)
    
    async def save(self, checkpoint: UnifiedCheckpoint) -> bool:
        """保存检查点"""
        try:
            # 验证检查点
            self._validate_checkpoint(checkpoint)
            
            # 更新时间戳
            checkpoint.updated_at = datetime.now()
            
            # 转换为存储格式
            data = checkpoint.to_dict()
            
            # 保存到后端
            key = f"checkpoint:{checkpoint.id}"
            success = await self._backend.save(key, data)
            
            if success:
                # 更新索引
                await self._index_manager.update_index(checkpoint)
                
                # 记录日志
                logger.info(f"Saved checkpoint {checkpoint.id} for thread {checkpoint.thread_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint {checkpoint.id}: {e}")
            raise
    
    async def find_by_id(self, checkpoint_id: str) -> Optional[UnifiedCheckpoint]:
        """根据ID查找检查点"""
        try:
            key = f"checkpoint:{checkpoint_id}"
            data = await self._backend.load(key)
            
            if data is None:
                return None
            
            return UnifiedCheckpoint.from_dict(data)
            
        except Exception as e:
            logger.error(f"Failed to find checkpoint {checkpoint_id}: {e}")
            raise
    
    async def find_by_thread(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[UnifiedCheckpoint]:
        """查找Thread的所有检查点"""
        try:
            # 使用索引优化查询
            checkpoint_ids = await self._index_manager.get_by_thread(thread_id)
            
            # 应用分页
            if offset:
                checkpoint_ids = checkpoint_ids[offset:]
            if limit:
                checkpoint_ids = checkpoint_ids[:limit]
            
            # 批量加载
            checkpoints = []
            for checkpoint_id in checkpoint_ids:
                checkpoint = await self.find_by_id(checkpoint_id)
                if checkpoint:
                    checkpoints.append(checkpoint)
            
            # 按创建时间排序
            checkpoints.sort(key=lambda x: x.created_at, reverse=True)
            
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to find checkpoints for thread {thread_id}: {e}")
            raise
    
    async def find_by_type(
        self,
        checkpoint_type: CheckpointType,
        thread_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[UnifiedCheckpoint]:
        """根据类型查找检查点"""
        try:
            # 构建查询条件
            filters = {"checkpoint_type": checkpoint_type.value}
            if thread_id:
                filters["thread_id"] = thread_id
            
            # 执行查询
            results = await self._backend.query(filters, limit=limit)
            
            # 转换为检查点对象
            checkpoints = []
            for data in results:
                checkpoint = UnifiedCheckpoint.from_dict(data)
                checkpoints.append(checkpoint)
            
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to find checkpoints by type {checkpoint_type}: {e}")
            raise
    
    async def get_statistics(
        self,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取检查点统计信息"""
        try:
            # 获取检查点列表
            if thread_id:
                checkpoints = await self.find_by_thread(thread_id)
            else:
                # 获取所有检查点
                results = await self._backend.query({})
                checkpoints = [
                    UnifiedCheckpoint.from_dict(data) 
                    for data in results
                ]
            
            # 计算统计信息
            stats = {
                "total_checkpoints": len(checkpoints),
                "by_type": {},
                "by_status": {},
                "size_stats": {},
                "restore_stats": {},
                "age_stats": {}
            }
            
            if not checkpoints:
                return stats
            
            # 类型统计
            for checkpoint in checkpoints:
                cp_type = checkpoint.checkpoint_type.value
                stats["by_type"][cp_type] = stats["by_type"].get(cp_type, 0) + 1
            
            # 状态统计
            for checkpoint in checkpoints:
                status = checkpoint.status.value
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # 大小统计
            sizes = [cp.size_bytes for cp in checkpoints]
            stats["size_stats"] = {
                "total_bytes": sum(sizes),
                "average_bytes": sum(sizes) / len(sizes),
                "max_bytes": max(sizes),
                "min_bytes": min(sizes)
            }
            
            # 恢复统计
            restore_counts = [cp.restore_count for cp in checkpoints]
            stats["restore_stats"] = {
                "total_restores": sum(restore_counts),
                "average_restores": sum(restore_counts) / len(restore_counts),
                "max_restores": max(restore_counts)
            }
            
            # 年龄统计
            ages = [cp.get_age_hours() for cp in checkpoints]
            stats["age_stats"] = {
                "oldest_hours": max(ages),
                "newest_hours": min(ages),
                "average_hours": sum(ages) / len(ages)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise
    
    def _validate_checkpoint(self, checkpoint: UnifiedCheckpoint) -> None:
        """验证检查点"""
        if not checkpoint.id:
            raise ValueError("Checkpoint ID is required")
        if not checkpoint.thread_id:
            raise ValueError("Thread ID is required")
        if not checkpoint.data:
            raise ValueError("Checkpoint data is required")
```

## 适配器实现

### UnifiedStorageAdapter

```python
class UnifiedStorageAdapter:
    """统一存储适配器
    
    提供统一存储接口到现有接口的适配。
    """
    
    def __init__(self, unified_repository: IUnifiedCheckpointRepository):
        """初始化适配器
        
        Args:
            unified_repository: 统一检查点仓储
        """
        self._unified_repository = unified_repository
    
    def to_icheckpoint_repository(self) -> ICheckpointRepository:
        """转换为通用检查点仓储接口"""
        return GenericCheckpointRepositoryAdapter(self._unified_repository)
    
    def to_ithread_checkpoint_repository(self) -> IThreadCheckpointRepository:
        """转换为Thread检查点仓储接口"""
        return ThreadCheckpointRepositoryAdapter(self._unified_repository)
```

## 总结

通过统一存储层设计，我们实现了：

1. **统一数据模型**: 支持通用和Thread特定的checkpoint需求
2. **统一接口**: 提供一致的存储操作接口
3. **灵活扩展**: 支持多种存储后端和业务逻辑扩展
4. **性能优化**: 通过索引和查询优化提高性能
5. **向后兼容**: 通过适配器模式保持兼容性

这种设计为checkpoint模块的重构提供了坚实的存储基础，确保系统的可维护性和扩展性。