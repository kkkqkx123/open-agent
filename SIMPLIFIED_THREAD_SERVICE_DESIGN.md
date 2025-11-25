# 简化的线程服务重构方案

## 1. 设计原则
- 避免过度抽象，直接实现功能
- 按职责拆分，但不创建额外的接口层
- 充分利用现有服务（BranchService、SnapshotService）
- 保持代码简洁和可维护性

## 2. 服务拆分方案

### 2.1 BasicThreadService（基础线程管理）
**职责**：
- 线程CRUD操作
- 线程状态管理
- 线程搜索和统计
- 基础验证功能

**文件**：`src/services/threads/basic_service.py`

### 2.2 WorkflowThreadService（工作流执行）
**职责**：
- 工作流执行和流式执行
- 工作流状态管理
- 执行配置处理

**文件**：`src/services/threads/workflow_service.py`

### 2.3 ThreadCollaborationService（协作功能）
**职责**：
- 线程间状态共享
- 共享会话管理
- 线程状态同步
- 历史记录集成

**文件**：`src/services/threads/collaboration_service.py`

### 2.4 ThreadService（主服务门面）
**职责**：
- 实现IThreadService接口
- 协调各个专门服务
- 处理跨模块业务逻辑
- 集成现有BranchService和SnapshotService

**文件**：`src/services/threads/service.py`（重构现有文件）

## 3. 方法分配

### 3.1 BasicThreadService
```python
async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> str
async def create_thread_from_config(self, config_path: str, metadata: Optional[Dict[str, Any]] = None) -> str
async def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]
async def update_thread_status(self, thread_id: str, status: str) -> bool
async def delete_thread(self, thread_id: str) -> bool
async def list_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]
async def thread_exists(self, thread_id: str) -> bool
async def validate_thread_state(self, thread_id: str) -> bool
async def can_transition_to_status(self, thread_id: str, new_status: str) -> bool
async def get_thread_statistics(self) -> Dict[str, Any]
async def search_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]
async def list_threads_by_type(self, thread_type: str) -> List[Dict[str, Any]]
```

### 3.2 WorkflowThreadService
```python
async def execute_workflow(self, thread_id: str, config: Optional[Dict[str, Any]] = None, initial_state: Optional[Dict[str, Any]] = None) -> IWorkflowState
async def stream_workflow(self, thread_id: str, config: Optional[Dict[str, Any]] = None, initial_state: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]
```

### 3.3 ThreadCollaborationService
```python
async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]
async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool
async def rollback_thread(self, thread_id: str, checkpoint_id: str) -> bool
async def share_thread_state(self, source_thread_id: str, target_thread_id: str, checkpoint_id: str, permissions: Optional[Dict[str, Any]] = None) -> bool
async def create_shared_session(self, thread_ids: List[str], session_config: Dict[str, Any]) -> str
async def sync_thread_states(self, thread_ids: List[str], sync_strategy: str = "bidirectional") -> bool
async def get_thread_history(self, thread_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]
```

### 3.4 ThreadService（主服务）
- 实现IThreadService的所有方法
- 委托给相应的专门服务
- 集成BranchService和SnapshotService
- 处理create_thread_with_session等复合方法

## 4. 依赖关系

```
ThreadService
├── BasicThreadService
├── WorkflowThreadService  
├── ThreadCollaborationService
├── ThreadBranchService (现有)
├── ThreadSnapshotService (现有)
└── HistoryManager (现有)
```

## 5. 实现优先级

1. **BasicThreadService** - 核心基础功能
2. **ThreadService** - 主服务门面，集成基础服务
3. **WorkflowThreadService** - 工作流执行
4. **ThreadCollaborationService** - 协作和历史功能

## 6. 优势

- **简洁性**：避免过度抽象，代码更直观
- **实用性**：每个服务都有明确的职责和实际价值
- **可维护性**：文件大小合理，职责清晰
- **扩展性**：新功能可以轻松添加到相应服务中
- **复用性**：充分利用现有服务和组件

这个简化方案既解决了文件规模问题，又保持了架构的简洁和实用。