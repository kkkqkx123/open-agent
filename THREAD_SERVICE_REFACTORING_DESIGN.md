# 线程服务重构设计方案

## 1. 架构问题分析

### 当前问题
1. **单一文件过大**：`ThreadService` 包含30+个未实现方法，全部实现将导致文件超过1000行
2. **职责混乱**：基础CRUD、工作流执行、分支管理、快照管理、协作功能混合在一个类中
3. **历史功能边界不清**：`get_thread_history` 等方法与现有 `HistoryManager` 职责重叠
4. **现有服务未充分利用**：已有 `ThreadBranchService` 和 `ThreadSnapshotService` 但未集成

### 现有资源
- `ThreadBranchService`：分支管理专用服务
- `ThreadSnapshotService`：快照管理专用服务  
- `HistoryManager`：通用历史记录管理
- `IThreadRepository`：线程数据访问接口

## 2. 重构方案设计

### 2.1 模块划分策略

按业务功能和职责边界，将线程服务拆分为以下模块：

```
src/services/threads/
├── service.py              # 主服务门面（协调各模块）
├── basic/                  # 基础线程管理
│   ├── __init__.py
│   ├── manager.py          # ThreadBasicManager
│   └── interfaces.py       # 基础管理接口
├── workflow/               # 工作流执行
│   ├── __init__.py
│   ├── executor.py         # ThreadWorkflowExecutor
│   └── interfaces.py       # 工作流执行接口
├── state/                  # 状态管理
│   ├── __init__.py
│   ├── manager.py          # ThreadStateManager
│   └── interfaces.py       # 状态管理接口
├── collaboration/          # 协作功能
│   ├── __init__.py
│   ├── manager.py          # ThreadCollaborationManager
│   └── interfaces.py       # 协作管理接口
└── history/                # 历史记录（线程特定）
    ├── __init__.py
    ├── manager.py          # ThreadHistoryManager
    └── interfaces.py       # 历史管理接口
```

### 2.2 各模块职责定义

#### 2.2.1 ThreadBasicManager（基础线程管理）
**职责**：
- 线程CRUD操作（创建、读取、更新、删除）
- 线程状态转换验证
- 线程存在性检查
- 线程列表和搜索
- 线程统计信息

**接口方法**：
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
```

#### 2.2.2 ThreadWorkflowExecutor（工作流执行）
**职责**：
- 工作流执行和流式执行
- 工作流配置管理
- 执行状态监控

**接口方法**：
```python
async def execute_workflow(self, thread_id: str, config: Optional[Dict[str, Any]] = None, initial_state: Optional[Dict[str, Any]] = None) -> IWorkflowState
async def stream_workflow(self, thread_id: str, config: Optional[Dict[str, Any]] = None, initial_state: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]
```

#### 2.2.3 ThreadStateManager（状态管理）
**职责**：
- 线程状态读写
- 状态快照和恢复
- 状态验证

**接口方法**：
```python
async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]
async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool
async def rollback_thread(self, thread_id: str, checkpoint_id: str) -> bool
```

#### 2.2.4 ThreadCollaborationManager（协作管理）
**职责**：
- 线程间状态共享
- 共享会话管理
- 线程状态同步

**接口方法**：
```python
async def share_thread_state(self, source_thread_id: str, target_thread_id: str, checkpoint_id: str, permissions: Optional[Dict[str, Any]] = None) -> bool
async def create_shared_session(self, thread_ids: List[str], session_config: Dict[str, Any]) -> str
async def sync_thread_states(self, thread_ids: List[str], sync_strategy: str = "bidirectional") -> bool
```

#### 2.2.5 ThreadHistoryManager（历史记录）
**职责**：
- 线程特定历史记录管理
- 与通用HistoryManager集成
- 线程历史查询和分析

**接口方法**：
```python
async def get_thread_history(self, thread_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]
async def record_thread_event(self, thread_id: str, event_type: str, event_data: Dict[str, Any]) -> None
async def get_thread_timeline(self, thread_id: str) -> List[Dict[str, Any]]
```

### 2.3 主服务门面设计

#### 2.3.1 ThreadService（主服务）
**职责**：
- 作为统一入口点
- 协调各专门管理器
- 提供完整的IThreadService接口实现
- 处理跨模块的业务逻辑

**组合模式实现**：
```python
class ThreadService(IThreadService):
    def __init__(self,
                 basic_manager: IThreadBasicManager,
                 workflow_executor: IThreadWorkflowExecutor,
                 state_manager: IThreadStateManager,
                 collaboration_manager: IThreadCollaborationManager,
                 history_manager: IThreadHistoryManager,
                 branch_service: IThreadBranchService,
                 snapshot_service: IThreadSnapshotService,
                 session_service: Optional[ISessionService] = None):
        self._basic_manager = basic_manager
        self._workflow_executor = workflow_executor
        self._state_manager = state_manager
        self._collaboration_manager = collaboration_manager
        self._history_manager = history_manager
        self._branch_service = branch_service
        self._snapshot_service = snapshot_service
        self._session_service = session_service
    
    # 委托给相应的管理器实现接口方法
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        return await self._basic_manager.create_thread(graph_id, metadata)
    
    # ... 其他方法的委托实现
```

## 3. 历史功能职责边界

### 3.1 职责划分
- **HistoryManager**：通用历史记录（LLM请求/响应、Token使用、成本等）
- **ThreadHistoryManager**：线程特定历史（状态变更、分支创建、快照等）
- **ThreadService**：通过ThreadHistoryManager提供线程历史接口

### 3.2 集成方案
```python
class ThreadHistoryManager:
    def __init__(self, history_manager: IHistoryManager):
        self._history_manager = history_manager
    
    async def get_thread_history(self, thread_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        # 1. 从通用历史管理器获取相关记录
        # 2. 从线程特定历史存储获取记录
        # 3. 合并并按时间排序
        # 4. 返回统一的历史记录
```

## 4. 接口完善需求

### 4.1 IThreadRepository 需要添加的方法
```python
async def list_by_type(self, thread_type: ThreadType) -> List[Thread]
async def get_statistics(self) -> Dict[str, Any]
async def search_with_filters(self, filters: Dict[str, Any], limit: Optional[int] = None, offset: Optional[int] = None) -> List[Thread]
```

## 5. 依赖注入更新

### 5.1 新的绑定配置
```python
def register_thread_services(container, config: Dict[str, Any]) -> None:
    # 注册基础管理器
    register_thread_basic_manager(container, config)
    
    # 注册工作流执行器
    register_thread_workflow_executor(container, config)
    
    # 注册状态管理器
    register_thread_state_manager(container, config)
    
    # 注册协作管理器
    register_thread_collaboration_manager(container, config)
    
    # 注册历史管理器
    register_thread_history_manager(container, config)
    
    # 注册主服务
    register_thread_service(container, config)
```

## 6. 实现优先级

1. **高优先级**：基础线程管理（ThreadBasicManager）
2. **中优先级**：工作流执行（ThreadWorkflowExecutor）、状态管理（ThreadStateManager）
3. **低优先级**：协作管理（ThreadCollaborationManager）、历史记录（ThreadHistoryManager）

## 7. 优势分析

### 7.1 代码组织
- 每个模块职责单一，易于理解和维护
- 文件大小控制在合理范围内（每个模块200-400行）
- 便于单元测试和集成测试

### 7.2 扩展性
- 新功能可以独立添加到相应模块
- 模块间依赖关系清晰
- 支持模块级别的性能优化

### 7.3 复用性
- 各管理器可以独立使用
- 现有服务（BranchService、SnapshotService）得到充分利用
- 历史功能与通用HistoryManager良好集成

## 8. 风险控制

### 8.1 兼容性风险
- 保持IThreadService接口不变
- 现有API调用方式保持一致
- 渐进式迁移，避免破坏性变更

### 8.2 复杂性风险
- 清晰的模块边界定义
- 详细的接口文档
- 完善的错误处理机制

这个重构方案既解决了文件规模问题，又保持了良好的架构设计和代码组织结构。