# Thread独特功能详细实现计划

## 第一阶段：基础扩展

### 1.1 扩展ThreadManager接口

**修改文件：**
- `src/domain/threads/interfaces.py` - 扩展IThreadManager接口
- `src/domain/threads/manager.py` - 实现新的接口方法

**具体修改：**

```python
# 在 IThreadManager 接口中添加新方法
@abstractmethod
async def fork_thread(
    self, 
    source_thread_id: str, 
    checkpoint_id: str,
    branch_name: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """从指定checkpoint创建thread分支"""
    pass

@abstractmethod
async def create_thread_snapshot(
    self,
    thread_id: str,
    snapshot_name: str,
    description: Optional[str] = None
) -> str:
    """创建thread状态快照"""
    pass

@abstractmethod
async def rollback_thread(
    self,
    thread_id: str,
    checkpoint_id: str
) -> bool:
    """回滚thread到指定checkpoint"""
    pass

@abstractmethod
async def get_thread_history(
    self,
    thread_id: str,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """获取thread历史记录"""
    pass
```

### 1.2 增强CheckpointManager

**修改文件：**
- `src/application/checkpoint/interfaces.py` - 扩展ICheckpointManager接口
- `src/infrastructure/checkpoint/manager.py` - 实现新的checkpoint操作

**新增方法：**
```python
@abstractmethod
async def copy_checkpoint(
    self,
    source_thread_id: str,
    source_checkpoint_id: str,
    target_thread_id: str
) -> str:
    """复制checkpoint到另一个thread"""
    pass

@abstractmethod
async def export_checkpoint(
    self,
    thread_id: str,
    checkpoint_id: str
) -> Dict[str, Any]:
    """导出checkpoint数据"""
    pass

@abstractmethod
async def import_checkpoint(
    self,
    thread_id: str,
    checkpoint_data: Dict[str, Any]
) -> str:
    """导入checkpoint数据"""
    pass
```

### 1.3 新增Thread分支元数据模型

**新增文件：**
- `src/domain/threads/models.py` - 定义Thread分支相关数据模型

```python
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

@dataclass
class ThreadBranch:
    """Thread分支信息"""
    branch_id: str
    source_thread_id: str
    source_checkpoint_id: str
    branch_name: str
    created_at: datetime
    metadata: Dict[str, Any]
    status: str = "active"

@dataclass
class ThreadSnapshot:
    """Thread快照信息"""
    snapshot_id: str
    thread_id: str
    snapshot_name: str
    description: Optional[str]
    checkpoint_ids: List[str]
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class ThreadHistory:
    """Thread历史记录"""
    thread_id: str
    checkpoints: List[Dict[str, Any]]
    branches: List[ThreadBranch]
    snapshots: List[ThreadSnapshot]
```

## 第二阶段：高级功能

### 2.1 实现Thread分支功能

**新增文件：**
- `src/application/threads/branch_manager.py` - Thread分支管理器
- `src/infrastructure/threads/branch_store.py` - 分支数据存储

**BranchManager实现：**
```python
class BranchManager:
    """Thread分支管理器"""
    
    async def fork_thread(
        self,
        source_thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建thread分支"""
        # 1. 验证源thread和checkpoint存在
        # 2. 复制checkpoint状态
        # 3. 创建新thread
        # 4. 记录分支关系
        # 5. 返回新thread_id
        pass
    
    async def get_thread_branches(
        self,
        thread_id: str
    ) -> List[ThreadBranch]:
        """获取thread的所有分支"""
        pass
    
    async def merge_branch(
        self,
        target_thread_id: str,
        source_thread_id: str,
        merge_strategy: str = "latest"
    ) -> bool:
        """合并分支到目标thread"""
        pass
```

### 2.2 实现Thread快照功能

**新增文件：**
- `src/application/threads/snapshot_manager.py` - Thread快照管理器
- `src/infrastructure/threads/snapshot_store.py` - 快照数据存储

**SnapshotManager实现：**
```python
class SnapshotManager:
    """Thread快照管理器"""
    
    async def create_snapshot(
        self,
        thread_id: str,
        snapshot_name: str,
        description: Optional[str] = None
    ) -> str:
        """创建thread快照"""
        # 1. 获取thread所有checkpoints
        # 2. 创建快照记录
        # 3. 保存快照元数据
        # 4. 返回快照ID
        pass
    
    async def restore_snapshot(
        self,
        thread_id: str,
        snapshot_id: str
    ) -> bool:
        """从快照恢复thread状态"""
        pass
    
    async def delete_snapshot(
        self,
        snapshot_id: str
    ) -> bool:
        """删除快照"""
        pass
```

### 2.3 实现历史回滚功能

**修改文件：**
- `src/domain/threads/manager.py` - 扩展ThreadManager的回滚功能

**具体实现：**
```python
async def rollback_thread(
    self,
    thread_id: str,
    checkpoint_id: str
) -> bool:
    """回滚thread到指定checkpoint"""
    # 1. 验证checkpoint存在
    checkpoint = await self.checkpoint_manager.get_checkpoint(thread_id, checkpoint_id)
    if not checkpoint:
        return False
    
    # 2. 创建回滚checkpoint（用于undo）
    rollback_metadata = {
        "rollback_from": checkpoint_id,
        "rollback_reason": "user_requested",
        "original_state": await self.get_thread_state(thread_id)
    }
    
    # 3. 恢复状态
    await self.checkpoint_manager.restore_from_checkpoint(thread_id, checkpoint_id)
    
    # 4. 记录回滚操作
    await self.metadata_store.update_metadata(thread_id, {
        "last_rollback": datetime.now().isoformat(),
        "rollback_checkpoint": checkpoint_id
    })
    
    return True
```

## 第三阶段：协作功能

### 3.1 实现Thread协作功能

**新增文件：**
- `src/application/threads/collaboration_manager.py` - Thread协作管理器
- `src/domain/threads/collaboration.py` - 协作相关数据模型

**CollaborationManager实现：**
```python
class CollaborationManager:
    """Thread协作管理器"""
    
    async def share_thread_state(
        self,
        source_thread_id: str,
        target_thread_id: str,
        checkpoint_id: str,
        permissions: Dict[str, Any] = None
    ) -> bool:
        """共享thread状态到其他thread"""
        pass
    
    async def create_shared_session(
        self,
        thread_ids: List[str],
        session_config: Dict[str, Any]
    ) -> str:
        """创建共享会话"""
        pass
    
    async def sync_thread_states(
        self,
        thread_ids: List[str],
        sync_strategy: str = "bidirectional"
    ) -> bool:
        """同步多个thread状态"""
        pass
```

### 3.2 扩展SessionThreadMapper

**修改文件：**
- `src/application/threads/session_thread_mapper.py` - 支持分支和协作

**新增方法：**
```python
async def fork_session_with_thread(
    self,
    source_session_id: str,
    checkpoint_id: str,
    branch_name: str
) -> Tuple[str, str]:
    """从现有session和thread创建分支"""
    pass

async def get_session_branches(
    self,
    session_id: str
) -> List[Dict[str, Any]]:
    """获取session的所有分支"""
    pass
```

## 第四阶段：API和集成

### 4.1 扩展SDK适配器

**修改文件：**
- `src/infrastructure/langgraph/sdk_adapter.py` - 添加新功能支持

**新增方法：**
```python
async def threads_fork(
    self,
    thread_id: str,
    checkpoint_id: str,
    branch_name: str
) -> Dict[str, Any]:
    """LangGraph兼容的thread分支功能"""
    pass

async def threads_rollback(
    self,
    thread_id: str,
    checkpoint_id: str
) -> Dict[str, Any]:
    """LangGraph兼容的thread回滚功能"""
    pass
```

### 4.2 新增REST API端点

**新增文件：**
- `src/presentation/api/routers/threads.py` - Thread管理API

**API端点：**
- `POST /api/threads/{thread_id}/fork` - 创建分支
- `POST /api/threads/{thread_id}/rollback` - 回滚到checkpoint
- `POST /api/threads/{thread_id}/snapshots` - 创建快照
- `GET /api/threads/{thread_id}/history` - 获取历史
- `POST /api/threads/{thread_id}/merge` - 合并分支

### 4.3 更新配置系统

**修改文件：**
- `configs/threads.yaml` - 添加thread功能配置

```yaml
thread_features:
  branching:
    enabled: true
    max_branches_per_thread: 10
  snapshots:
    enabled: true
    auto_snapshot_interval: 3600  # 1小时
  rollback:
    enabled: true
    max_history_days: 30
  collaboration:
    enabled: false  # 默认禁用，需要显式开启
```

## 测试计划

### 单元测试
**新增测试文件：**
- `tests/unit/threads/test_branch_manager.py`
- `tests/unit/threads/test_snapshot_manager.py`
- `tests/unit/threads/test_collaboration_manager.py`
- `tests/unit/threads/test_enhanced_thread_manager.py`

### 集成测试
**新增测试文件：**
- `tests/integration/test_thread_branching.py`
- `tests/integration/test_thread_snapshots.py`
- `tests/integration/test_thread_rollback.py`

### 性能测试
**新增测试文件：**
- `tests/performance/test_thread_scalability.py`

## 部署和迁移

### 数据库迁移
如果使用数据库存储，需要创建新的表：
- `thread_branches` - 分支关系表
- `thread_snapshots` - 快照表
- `thread_collaborations` - 协作关系表

### 配置更新
更新依赖注入配置，注册新的管理器：
- BranchManager
- SnapshotManager  
- CollaborationManager

## 总结

这个实现计划提供了完整的thread独特功能扩展方案，包括详细的文件修改和新增计划。每个阶段都可以独立开发和测试，确保系统的稳定性和可扩展性。建议按照阶段顺序逐步实施，每个阶段完成后进行充分的测试和验证。