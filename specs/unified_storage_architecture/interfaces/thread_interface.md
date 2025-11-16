# Thread模块接口设计

## 概述

Thread模块负责管理工作流线程的持久化存储，包括Thread实体、ThreadBranch和ThreadSnapshot。基于分析，Thread模块有复杂的实体关系管理需求，需要统一的适配器来处理多个相关实体的存储。

## 现有接口分析

### 当前接口

Thread模块当前有多个分散的接口：

1. **IThreadRepository** - Thread实体仓储
2. **IThreadBranchRepository** - Thread分支仓储
3. **IThreadSnapshotRepository** - Thread快照仓储
4. **IThreadMetadataStore** - Thread元数据存储

### 问题分析

1. **接口分散**：多个独立的接口，职责不清晰
2. **关系管理复杂**：Thread、Branch、Snapshot之间的关系需要在应用层处理
3. **数据一致性**：多个存储之间缺乏事务保证
4. **查询效率低**：跨实体的查询需要多次存储访问

## 新接口设计

### 统一Thread存储接口

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

class IThreadUnifiedStore(ABC):
    """统一的Thread存储接口"""
    
    # Thread相关方法
    @abstractmethod
    async def save_thread(self, thread: 'Thread') -> None:
        """保存Thread实体"""
        pass
    
    @abstractmethod
    async def get_thread(self, thread_id: str) -> Optional['Thread']:
        """获取Thread实体"""
        pass
    
    @abstractmethod
    async def delete_thread(self, thread_id: str) -> None:
        """删除Thread实体（包括相关的Branch和Snapshot）"""
        pass
    
    @abstractmethod
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None, 
                          limit: Optional[int] = None) -> List['Thread']:
        """列出Thread实体"""
        pass
    
    @abstractmethod
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在"""
        pass
    
    @abstractmethod
    async def update_thread(self, thread_id: str, updates: Dict[str, Any]) -> None:
        """更新Thread实体"""
        pass
    
    # Branch相关方法
    @abstractmethod
    async def save_branch(self, branch: 'ThreadBranch') -> None:
        """保存Thread分支"""
        pass
    
    @abstractmethod
    async def get_branch(self, branch_id: str) -> Optional['ThreadBranch']:
        """获取Thread分支"""
        pass
    
    @abstractmethod
    async def get_branches_by_thread(self, thread_id: str) -> List['ThreadBranch']:
        """获取Thread的所有分支"""
        pass
    
    @abstractmethod
    async def delete_branch(self, branch_id: str) -> None:
        """删除Thread分支"""
        pass
    
    @abstractmethod
    async def update_branch_status(self, branch_id: str, status: str) -> None:
        """更新分支状态"""
        pass
    
    # Snapshot相关方法
    @abstractmethod
    async def save_snapshot(self, snapshot: 'ThreadSnapshot') -> None:
        """保存Thread快照"""
        pass
    
    @abstractmethod
    async def get_snapshot(self, snapshot_id: str) -> Optional['ThreadSnapshot']:
        """获取Thread快照"""
        pass
    
    @abstractmethod
    async def get_snapshots_by_thread(self, thread_id: str) -> List['ThreadSnapshot']:
        """获取Thread的所有快照"""
        pass
    
    @abstractmethod
    async def delete_snapshot(self, snapshot_id: str) -> None:
        """删除Thread快照"""
        pass
    
    # 复合查询方法
    @abstractmethod
    async def get_thread_with_branches(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread及其所有分支"""
        pass
    
    @abstractmethod
    async def get_thread_with_snapshots(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread及其所有快照"""
        pass
    
    @abstractmethod
    async def get_thread_full(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread及其所有分支和快照"""
        pass
    
    # 批量操作方法
    @abstractmethod
    async def batch_save_branches(self, branches: List['ThreadBranch']) -> None:
        """批量保存分支"""
        pass
    
    @abstractmethod
    async def batch_save_snapshots(self, snapshots: List['ThreadSnapshot']) -> None:
        """批量保存快照"""
        pass
    
    # 事务操作方法
    @abstractmethod
    async def create_thread_with_branch(
        self, 
        thread: 'Thread', 
        branch: 'ThreadBranch'
    ) -> None:
        """创建Thread和Branch（事务操作）"""
        pass
    
    @abstractmethod
    async def fork_thread(
        self, 
        source_thread_id: str, 
        new_thread: 'Thread',
        new_branch: 'ThreadBranch'
    ) -> None:
        """fork Thread（事务操作）"""
        pass
```

### 基于统一存储的实现

```python
from typing import Dict, Any, Optional, List
from ...domain.storage.interfaces import IUnifiedStorage
from ...domain.storage.exceptions import StorageNotFoundError, StorageError
from ...domain.threads.models import Thread, ThreadBranch, ThreadSnapshot

class ThreadUnifiedStore(IThreadUnifiedStore):
    """统一的Thread存储实现"""
    
    def __init__(self, storage: IUnifiedStorage):
        self._storage = storage
    
    # Thread相关方法实现
    async def save_thread(self, thread: Thread) -> None:
        """保存Thread实体"""
        try:
            data = {
                "id": thread.thread_id,
                "type": "thread",
                "data": thread.to_dict(),
                "created_at": thread.created_at,
                "updated_at": thread.updated_at
            }
            await self._storage.save(data)
        except Exception as e:
            raise StorageError(f"Failed to save thread {thread.thread_id}: {e}")
    
    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        """获取Thread实体"""
        try:
            data = await self._storage.load(thread_id)
            if data and data.get("type") == "thread":
                return Thread.from_dict(data.get("data"))
            return None
        except Exception:
            return None
    
    async def delete_thread(self, thread_id: str) -> None:
        """删除Thread实体（包括相关的Branch和Snapshot）"""
        try:
            # 获取所有相关的分支和快照
            branches = await self.get_branches_by_thread(thread_id)
            snapshots = await self.get_snapshots_by_thread(thread_id)
            
            # 构建事务操作
            operations = []
            
            # 删除Thread
            operations.append({"type": "delete", "id": thread_id})
            
            # 删除所有Branch
            for branch in branches:
                operations.append({"type": "delete", "id": branch.branch_id})
            
            # 删除所有Snapshot
            for snapshot in snapshots:
                operations.append({"type": "delete", "id": snapshot.snapshot_id})
            
            # 执行事务
            await self._storage.transaction(operations)
        except Exception as e:
            raise StorageError(f"Failed to delete thread {thread_id}: {e}")
    
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None, 
                          limit: Optional[int] = None) -> List[Thread]:
        """列出Thread实体"""
        try:
            query_filters = {"type": "thread"}
            if filters:
                # 将过滤器转换为数据字段查询
                for key, value in filters.items():
                    query_filters[f"data.{key}"] = value
            
            results = await self._storage.list(query_filters, limit)
            return [Thread.from_dict(result.get("data")) for result in results]
        except Exception as e:
            raise StorageError(f"Failed to list threads: {e}")
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在"""
        try:
            data = await self._storage.load(thread_id)
            return data and data.get("type") == "thread"
        except Exception:
            return False
    
    async def update_thread(self, thread_id: str, updates: Dict[str, Any]) -> None:
        """更新Thread实体"""
        try:
            # 添加更新时间戳
            updates["updated_at"] = datetime.now().isoformat()
            await self._storage.update(thread_id, {"data": updates})
        except Exception as e:
            raise StorageError(f"Failed to update thread {thread_id}: {e}")
    
    # Branch相关方法实现
    async def save_branch(self, branch: ThreadBranch) -> None:
        """保存Thread分支"""
        try:
            data = {
                "id": branch.branch_id,
                "type": "thread_branch",
                "thread_id": branch.source_thread_id,
                "data": branch.to_dict(),
                "created_at": branch.created_at,
                "updated_at": datetime.now()
            }
            await self._storage.save(data)
        except Exception as e:
            raise StorageError(f"Failed to save branch {branch.branch_id}: {e}")
    
    async def get_branch(self, branch_id: str) -> Optional[ThreadBranch]:
        """获取Thread分支"""
        try:
            data = await self._storage.load(branch_id)
            if data and data.get("type") == "thread_branch":
                return ThreadBranch.from_dict(data.get("data"))
            return None
        except Exception:
            return None
    
    async def get_branches_by_thread(self, thread_id: str) -> List[ThreadBranch]:
        """获取Thread的所有分支"""
        try:
            filters = {
                "type": "thread_branch",
                "thread_id": thread_id
            }
            results = await self._storage.list(filters)
            return [ThreadBranch.from_dict(result.get("data")) for result in results]
        except Exception as e:
            raise StorageError(f"Failed to get branches for thread {thread_id}: {e}")
    
    async def delete_branch(self, branch_id: str) -> None:
        """删除Thread分支"""
        try:
            success = await self._storage.delete(branch_id)
            if not success:
                raise StorageNotFoundError(f"Branch not found: {branch_id}")
        except Exception as e:
            if isinstance(e, StorageNotFoundError):
                raise
            raise StorageError(f"Failed to delete branch {branch_id}: {e}")
    
    async def update_branch_status(self, branch_id: str, status: str) -> None:
        """更新分支状态"""
        try:
            updates = {"status": status, "updated_at": datetime.now().isoformat()}
            await self._storage.update(branch_id, {"data": updates})
        except Exception as e:
            raise StorageError(f"Failed to update branch status {branch_id}: {e}")
    
    # Snapshot相关方法实现
    async def save_snapshot(self, snapshot: ThreadSnapshot) -> None:
        """保存Thread快照"""
        try:
            data = {
                "id": snapshot.snapshot_id,
                "type": "thread_snapshot",
                "thread_id": snapshot.thread_id,
                "data": snapshot.to_dict(),
                "created_at": snapshot.created_at,
                "updated_at": datetime.now()
            }
            await self._storage.save(data)
        except Exception as e:
            raise StorageError(f"Failed to save snapshot {snapshot.snapshot_id}: {e}")
    
    async def get_snapshot(self, snapshot_id: str) -> Optional[ThreadSnapshot]:
        """获取Thread快照"""
        try:
            data = await self._storage.load(snapshot_id)
            if data and data.get("type") == "thread_snapshot":
                return ThreadSnapshot.from_dict(data.get("data"))
            return None
        except Exception:
            return None
    
    async def get_snapshots_by_thread(self, thread_id: str) -> List[ThreadSnapshot]:
        """获取Thread的所有快照"""
        try:
            filters = {
                "type": "thread_snapshot",
                "thread_id": thread_id
            }
            results = await self._storage.list(filters)
            return [ThreadSnapshot.from_dict(result.get("data")) for result in results]
        except Exception as e:
            raise StorageError(f"Failed to get snapshots for thread {thread_id}: {e}")
    
    async def delete_snapshot(self, snapshot_id: str) -> None:
        """删除Thread快照"""
        try:
            success = await self._storage.delete(snapshot_id)
            if not success:
                raise StorageNotFoundError(f"Snapshot not found: {snapshot_id}")
        except Exception as e:
            if isinstance(e, StorageNotFoundError):
                raise
            raise StorageError(f"Failed to delete snapshot {snapshot_id}: {e}")
    
    # 复合查询方法实现
    async def get_thread_with_branches(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread及其所有分支"""
        try:
            thread = await self.get_thread(thread_id)
            if not thread:
                return None
            
            branches = await self.get_branches_by_thread(thread_id)
            
            return {
                "thread": thread,
                "branches": branches
            }
        except Exception as e:
            raise StorageError(f"Failed to get thread with branches {thread_id}: {e}")
    
    async def get_thread_with_snapshots(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread及其所有快照"""
        try:
            thread = await self.get_thread(thread_id)
            if not thread:
                return None
            
            snapshots = await self.get_snapshots_by_thread(thread_id)
            
            return {
                "thread": thread,
                "snapshots": snapshots
            }
        except Exception as e:
            raise StorageError(f"Failed to get thread with snapshots {thread_id}: {e}")
    
    async def get_thread_full(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread及其所有分支和快照"""
        try:
            thread = await self.get_thread(thread_id)
            if not thread:
                return None
            
            branches = await self.get_branches_by_thread(thread_id)
            snapshots = await self.get_snapshots_by_thread(thread_id)
            
            return {
                "thread": thread,
                "branches": branches,
                "snapshots": snapshots
            }
        except Exception as e:
            raise StorageError(f"Failed to get full thread data {thread_id}: {e}")
    
    # 批量操作方法实现
    async def batch_save_branches(self, branches: List[ThreadBranch]) -> None:
        """批量保存分支"""
        try:
            operations = []
            now = datetime.now()
            
            for branch in branches:
                data = {
                    "id": branch.branch_id,
                    "type": "thread_branch",
                    "thread_id": branch.source_thread_id,
                    "data": branch.to_dict(),
                    "created_at": branch.created_at,
                    "updated_at": now
                }
                operations.append({"type": "save", "data": data})
            
            await self._storage.transaction(operations)
        except Exception as e:
            raise StorageError(f"Failed to batch save branches: {e}")
    
    async def batch_save_snapshots(self, snapshots: List[ThreadSnapshot]) -> None:
        """批量保存快照"""
        try:
            operations = []
            now = datetime.now()
            
            for snapshot in snapshots:
                data = {
                    "id": snapshot.snapshot_id,
                    "type": "thread_snapshot",
                    "thread_id": snapshot.thread_id,
                    "data": snapshot.to_dict(),
                    "created_at": snapshot.created_at,
                    "updated_at": now
                }
                operations.append({"type": "save", "data": data})
            
            await self._storage.transaction(operations)
        except Exception as e:
            raise StorageError(f"Failed to batch save snapshots: {e}")
    
    # 事务操作方法实现
    async def create_thread_with_branch(
        self, 
        thread: Thread, 
        branch: ThreadBranch
    ) -> None:
        """创建Thread和Branch（事务操作）"""
        try:
            operations = []
            now = datetime.now()
            
            # 保存Thread
            thread_data = {
                "id": thread.thread_id,
                "type": "thread",
                "data": thread.to_dict(),
                "created_at": thread.created_at,
                "updated_at": now
            }
            operations.append({"type": "save", "data": thread_data})
            
            # 保存Branch
            branch_data = {
                "id": branch.branch_id,
                "type": "thread_branch",
                "thread_id": branch.source_thread_id,
                "data": branch.to_dict(),
                "created_at": branch.created_at,
                "updated_at": now
            }
            operations.append({"type": "save", "data": branch_data})
            
            await self._storage.transaction(operations)
        except Exception as e:
            raise StorageError(f"Failed to create thread with branch: {e}")
    
    async def fork_thread(
        self, 
        source_thread_id: str, 
        new_thread: Thread,
        new_branch: ThreadBranch
    ) -> None:
        """fork Thread（事务操作）"""
        try:
            # 验证源Thread存在
            source_thread = await self.get_thread(source_thread_id)
            if not source_thread:
                raise StorageNotFoundError(f"Source thread not found: {source_thread_id}")
            
            # 创建新Thread和Branch
            await self.create_thread_with_branch(new_thread, new_branch)
        except Exception as e:
            raise StorageError(f"Failed to fork thread {source_thread_id}: {e}")
```

## 数据模型

### 统一数据模型

```python
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel

class ThreadData(BaseModel):
    """Thread数据模型"""
    thread_id: str
    graph_id: str
    status: str = "active"
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

class BranchData(BaseModel):
    """Branch数据模型"""
    branch_id: str
    source_thread_id: str
    source_checkpoint_id: str
    branch_name: str
    status: str = "active"
    metadata: Dict[str, Any] = {}
    created_at: datetime

class SnapshotData(BaseModel):
    """Snapshot数据模型"""
    snapshot_id: str
    thread_id: str
    snapshot_name: str
    description: Optional[str] = None
    state_data: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    created_at: datetime
```

## 迁移策略

### 从现有实现迁移

1. **数据迁移**：将现有的分散数据合并到统一存储
2. **接口适配**：提供适配器保持现有接口兼容性
3. **逐步替换**：先实现新接口，再逐步替换旧接口

```python
# 兼容性适配器
class ThreadRepositoryAdapter(IThreadRepository):
    """Thread仓储适配器"""
    
    def __init__(self, unified_store: IThreadUnifiedStore):
        self._unified_store = unified_store
    
    async def save(self, thread: Thread) -> bool:
        """适配保存方法"""
        try:
            await self._unified_store.save_thread(thread)
            return True
        except Exception:
            return False
    
    # 其他方法的适配...

class ThreadBranchRepositoryAdapter(IThreadBranchRepository):
    """Thread分支仓储适配器"""
    
    def __init__(self, unified_store: IThreadUnifiedStore):
        self._unified_store = unified_store
    
    async def save(self, branch: ThreadBranch) -> bool:
        """适配保存方法"""
        try:
            await self._unified_store.save_branch(branch)
            return True
        except Exception:
            return False
    
    # 其他方法的适配...
```

## 性能优化

### 查询优化

1. **索引策略**：
   - Thread表：按thread_id、status、graph_id索引
   - Branch表：按branch_id、source_thread_id索引
   - Snapshot表：按snapshot_id、thread_id索引

2. **缓存策略**：
   - 缓存常用的Thread数据
   - 缓存Thread的分支列表
   - 缓存Thread的快照列表

3. **批量操作**：
   - 批量保存分支和快照
   - 批量删除相关数据
   - 事务操作保证一致性

## 评估结论

### 可行性评估

1. **技术可行性**：高
   - 统一存储接口可以满足Thread模块的复杂需求
   - 事务支持可以保证数据一致性
   - 批量操作可以提高性能

2. **迁移风险**：中
   - 需要合并多个分散的存储实现
   - 数据关系复杂，需要仔细处理
   - 需要保证事务的正确性

3. **性能影响**：中
   - 统一存储可能增加一些开销
   - 但事务和批量操作可以提高整体性能
   - 缓存可以优化查询性能

### 推荐方案

**推荐使用统一Thread存储接口**

理由：
1. 解决了接口分散的问题
2. 提供了事务保证，确保数据一致性
3. 支持复合查询，提高查询效率
4. 简化了应用层的代码

### 实现优先级

1. **高优先级**：
   - 基本的CRUD操作
   - 事务操作支持
   - 复合查询方法

2. **中优先级**：
   - 批量操作
   - 性能优化
   - 缓存支持

3. **低优先级**：
   - 高级查询功能
   - 监控和日志
   - 性能调优