# Thread 层次设计与职责划分

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│              Adapter Layer (适配器层)                         │
│  LangGraphSDKAdapter ← 使用IThreadManager接口               │
└─────────────────────────────────────────────────────────────┘
                           ↑ 使用
                           │
┌─────────────────────────────────────────────────────────────┐
│         Interface Layer (接口层)                              │
│                                                              │
│  IThreadManager (基础接口)                                   │
│  ├─ thread_exists()         ← 检查存在                       │
│  ├─ get_thread_state()      ← 获取执行状态                   │
│  ├─ update_thread_state()   ← 更新执行状态                   │
│  ├─ get_thread_info()       ← 获取线程信息                   │
│  ├─ update_thread_metadata() ← 更新元数据                    │
│  ├─ rollback_thread()       ← 回滚操作                       │
│  └─ [existing methods...]                                   │
│                                                              │
│  IThreadService (服务接口)                                   │
│  └─ 委托给具体的服务实现                                     │
└─────────────────────────────────────────────────────────────┘
                           ↑ 实现
                           │
┌─────────────────────────────────────────────────────────────┐
│         Service Layer (服务层)                               │
│                                                              │
│  ThreadService (主服务门面)                                  │
│  ├─ thread_exists()         → BasicThreadService             │
│  ├─ get_thread_info()       → BasicThreadService             │
│  ├─ update_thread_metadata() → BasicThreadService            │
│  ├─ get_thread_state()      → CollaborationService           │
│  ├─ update_thread_state()   → CollaborationService           │
│  └─ rollback_thread()       → CollaborationService           │
│                                                              │
│  BasicThreadService (基础服务)                               │
│  ├─ thread_exists()         (已实现)                         │
│  ├─ get_thread_info()       (已实现)                         │
│  └─ update_thread_metadata() (已实现)                        │
│                                                              │
│  CollaborationService (协作服务)                             │
│  ├─ get_thread_state()      (已实现)                         │
│  ├─ update_thread_state()   (已实现)                         │
│  └─ rollback_thread()       (已实现)                         │
└─────────────────────────────────────────────────────────────┘
                           ↑ 依赖
                           │
┌─────────────────────────────────────────────────────────────┐
│         Core Layer (核心层)                                  │
│                                                              │
│  IThreadCore (核心逻辑)                                      │
│  ├─ 线程状态转换逻辑                                        │
│  ├─ 线程数据验证                                            │
│  └─ 线程实体创建                                            │
│                                                              │
│  Thread Entity (线程实体)                                    │
│  ├─ id, status, type, graph_id                             │
│  ├─ created_at, updated_at                                 │
│  ├─ metadata, config, state                                │
│  └─ message_count, checkpoint_count, branch_count          │
│                                                              │
│  IThreadRepository (数据仓储)                                │
│  ├─ CRUD 操作                                               │
│  ├─ 搜索和过滤                                              │
│  └─ 统计查询                                                │
└─────────────────────────────────────────────────────────────┘
```

## 二、职责划分

### 2.1 Interface Layer (接口层)

**IThreadManager** - 基础接口
- 职责：定义Thread管理的所有public contract
- 范围：
  - ✅ 创建、读取、删除、列表查询
  - ✅ 状态管理（存在性检查、获取、更新、回滚）
  - ✅ 元数据管理
  - ✅ 分支和快照操作
- 不涉及：协作功能（协作由IThreadCollaborationService处理）

### 2.2 Core Layer (核心层)

**IThreadCore** - 核心业务逻辑
- 职责：
  - 线程状态转换规则（ACTIVE→PAUSED→COMPLETED等）
  - 线程数据验证（什么是有效的线程数据）
  - 线程实体创建时的初始化逻辑
  - 不进行IO操作，纯粹的业务规则
  
**Thread Entity** - 数据模型
- 职责：
  - 线程数据结构定义
  - 实体级别的计数器增加操作
  - 实体级别的时间戳管理
  - 不进行持久化，仅是数据容器

**IThreadRepository** - 数据存储接口
- 职责：
  - CRUD 操作（创建、读取、更新、删除）
  - 搜索和过滤
  - 统计查询
  - 不涉及业务逻辑，纯粹的数据操作

### 2.3 Service Layer (服务层)

**BasicThreadService** - 基础服务（已存在）
- 职责：
  ```
  thread_exists() 
    └─ repository.exists(thread_id)
  
  get_thread_info()
    └─ repository.get(thread_id) → 转换为字典
  
  update_thread_metadata()
    ├─ repository.get(thread_id)
    ├─ thread.metadata = new_metadata
    └─ repository.update(thread)
  ```

**CollaborationService** - 协作服务（已存在）
- 职责：
  ```
  get_thread_state()
    ├─ repository.get(thread_id)
    └─ return thread.state (执行状态)
  
  update_thread_state()
    ├─ repository.get(thread_id)
    ├─ thread.state.update(new_state)
    ├─ repository.update(thread)
    └─ history_manager.record_state_change()
  
  rollback_thread()
    ├─ checkpoint_manager.get_checkpoint(thread_id, checkpoint_id)
    ├─ repository.get(thread_id)
    ├─ thread.state = checkpoint.state
    └─ repository.update(thread)
  ```

**ThreadService** - 主服务门面（已存在）
- 职责：
  - 委托各个具体服务
  - 调度和协调
  - 暴露统一的接口

## 三、新增方法的实现位置

| 方法 | 接口层 | 核心层 | 服务层 | 仓储层 | 实现状态 |
|------|--------|--------|--------|--------|---------|
| `thread_exists()` | ✅ IThreadManager | ❌ | ✅ BasicThreadService.thread_exists() | ✅ IThreadRepository.exists() | ✅ 已实现 |
| `get_thread_info()` | ✅ IThreadManager | ❌ | ✅ BasicThreadService.get_thread_info() | ✅ IThreadRepository.get() | ✅ 已实现 |
| `update_thread_metadata()` | ✅ IThreadManager | ❌ | ✅ BasicThreadService.update_thread_metadata() | ✅ IThreadRepository.update() | ✅ 已实现 |
| `get_thread_state()` | ✅ IThreadManager | ❌ | ✅ CollaborationService.get_thread_state() | ✅ IThreadRepository.get() | ✅ 已实现 |
| `update_thread_state()` | ✅ IThreadManager | ❌ | ✅ CollaborationService.update_thread_state() | ✅ IThreadRepository.update() | ✅ 已实现 |
| `rollback_thread()` | ✅ IThreadManager | ❌ | ✅ CollaborationService.rollback_thread() | ✅ IThreadRepository.update() | ✅ 已实现 |

**所有方法的实现都已存在！只需要在ThreadService中正确委托即可。**

## 四、需要补充的内容

### 4.1 ThreadService 中的委托（需要补充）

```python
# src/services/threads/service.py

class ThreadService(IThreadService):
    
    # 新增以下委托方法：
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在"""
        return await self._basic_service.thread_exists(thread_id)
    
    async def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread信息"""
        return await self._basic_service.get_thread_info(thread_id)
    
    async def update_thread_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """更新Thread元数据"""
        return await self._basic_service.update_thread_metadata(thread_id, metadata)
    
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread状态"""
        return await self._collaboration_service.get_thread_state(thread_id)
    
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """更新Thread状态"""
        return await self._collaboration_service.update_thread_state(thread_id, state)
    
    async def rollback_thread(self, thread_id: str, checkpoint_id: str) -> bool:
        """回滚Thread到指定检查点"""
        return await self._collaboration_service.rollback_thread(thread_id, checkpoint_id)
```

### 4.2 检查CollaborationService是否已实现rollback_thread()

需要验证：`src/services/threads/collaboration_service.py` 中的 `rollback_thread()` 方法是否完整实现。

## 五、实现步骤

### Step 1: 验证现有实现 ✅
- [x] IThreadManager 接口已补充8个新方法
- [ ] 验证 BasicThreadService 中的3个方法是否完整
- [ ] 验证 CollaborationService 中的3个方法是否完整

### Step 2: 补充ThreadService中的委托 (TODO)
- [ ] 在 ThreadService 中添加6个新的委托方法
- [ ] 确保类型注解正确
- [ ] 添加适当的错误处理

### Step 3: 验证依赖注入 (TODO)
- [ ] 确认 DI 容器中 ThreadService 的注册方式
- [ ] 确认所有依赖项（BasicThreadService, CollaborationService）正确注入

### Step 4: 类型检查 (TODO)
- [ ] 运行 mypy 验证所有类型注解
- [ ] 修复任何类型不匹配

### Step 5: 测试 (TODO)
- [ ] 为新方法添加单元测试
- [ ] 为新方法添加集成测试

## 六、关键注意事项

1. **不需要在Core层添加方法** - 业务逻辑已经在BasicThreadService和CollaborationService中实现

2. **状态管理的位置**
   - 执行状态（state）：属于线程本身，由CollaborationService管理
   - 元数据：属于线程本身，由BasicThreadService管理
   - 存活状态（status）：属于线程生命周期，由BasicThreadService管理

3. **与Checkpoint的关系**
   - Thread.state：当前的执行状态
   - Checkpoint.state：历史某个时刻的执行状态
   - rollback_thread()：将Thread.state恢复为某个Checkpoint.state

4. **IThreadManager vs IThreadService**
   - IThreadManager：供外部使用（Adapter层）
   - IThreadService：供内部使用（各服务之间）
   - ThreadService 实现 IThreadService 并委托给各个具体服务

5. **错误处理**
   - thread_exists：返回boolean，不抛异常
   - 其他方法：需要检查是否需要抛出异常（参考existing实现）
