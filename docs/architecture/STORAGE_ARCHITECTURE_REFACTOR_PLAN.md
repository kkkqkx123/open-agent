# 存储架构重构方案

## 1. 当前架构问题总结

### 1.1 核心问题分析

基于对现有代码的深入分析，确认了以下核心问题：

#### 问题1：核心层职责缺失
- `src/core/storage/` 仅包含数据模型和错误处理
- 缺乏领域业务逻辑和领域服务
- 违反DDD核心层应包含业务逻辑的原则

#### 问题2：服务层职责过重
- `src/services/storage/manager.py` 包含适配器管理、配置管理等技术实现
- 服务层应该专注于业务编排，而非技术实现
- 违反了依赖倒置原则

#### 问题3：缺乏领域特定抽象
- 只有通用的存储接口，缺乏Thread、Checkpoint等特定领域的存储抽象
- 存储逻辑分散在多个层次中
- 缺乏清晰的领域边界

#### 问题4：配置与业务逻辑混合
- 配置管理逻辑在服务层
- 适配器注册逻辑在服务层
- 缺乏纯粹的业务抽象

## 2. 新DDD架构设计

### 2.1 整体架构层次

```
src/
├── interfaces/                    # 接口层（最外层）
│   ├── storage/                  # 通用存储接口
│   │   ├── base.py              # 基础存储接口
│   │   └── factory.py           # 存储工厂接口
│   └── threads/                  # Thread领域接口
│       ├── storage.py           # Thread存储接口
│       └── checkpoints.py       # Thread检查点接口
├── core/                         # 核心领域层（业务逻辑核心）
│   ├── storage/                  # 通用存储核心
│   │   ├── models.py            # 存储数据模型
│   │   ├── repository.py        # 存储仓储模式
│   │   ├── service.py           # 存储领域服务
│   │   └── exceptions.py        # 存储领域异常
│   └── threads/                  # Thread领域核心
│       ├── storage/             # Thread存储核心
│       │   ├── models.py       # Thread存储模型
│       │   ├── repository.py   # Thread存储仓储
│       │   └── service.py      # Thread存储领域服务
│       └── checkpoints/         # Thread检查点子模块
│           ├── storage/         # 检查点存储核心
│           │   ├── models.py   # 检查点存储模型
│           │   ├── repository.py # 检查点仓储
│           │   └── service.py  # 检查点领域服务
│           └── manager.py       # 检查点管理器
├── services/                     # 服务层（业务编排）
│   ├── storage/                  # 通用存储服务
│   │   └── orchestrator.py      # 存储编排器
│   └── threads/                  # Thread服务
│       ├── service.py           # Thread业务服务
│       └── storage.py           # Thread存储编排
└── adapters/                     # 适配器层（技术实现）
    ├── storage/                  # 存储适配器
    │   ├── backends/            # 存储后端
    │   └── repositories/        # 仓储实现
    └── threads/                  # Thread适配器
        └── checkpoints/         # 检查点适配器
            └── langgraph.py     # LangGraph适配器
```

### 2.2 核心层设计原则

#### 2.2.1 领域模型设计
- 包含业务行为和领域规则
- 实体和值对象封装业务逻辑
- 领域事件和领域服务

#### 2.2.2 仓储模式设计
- 抽象数据访问逻辑
- 聚合根的持久化边界
- 领域对象与存储技术的解耦

#### 2.2.3 领域服务设计
- 复杂业务逻辑的封装
- 跨聚合的业务操作
- 业务规则的验证和执行

### 2.3 服务层设计原则

#### 2.3.1 业务编排
- 协调多个领域服务
- 事务管理和一致性保证
- 外部系统集成

#### 2.3.2 应用服务
- 用例级别的业务流程
- 数据转换和适配
- 权限验证和安全控制

### 2.4 适配器层设计原则

#### 2.4.1 技术实现
- 具体的存储技术实现
- 外部API的适配
- 性能优化和监控

#### 2.4.2 反防腐层
- 领域模型与技术实现的转换
- 外部系统的适配和封装
- 技术细节的隔离

## 3. 详细重构计划

### 3.1 阶段一：核心层重构（高优先级）

#### 3.1.1 创建Thread检查点领域模型
```python
# src/core/threads/checkpoints/storage/models.py
@dataclass
class ThreadCheckpoint:
    """Thread检查点领域模型"""
    id: str
    thread_id: str
    state_data: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    # 领域方法
    def is_valid(self) -> bool:
        """验证检查点有效性"""
        return bool(self.id and self.thread_id and self.state_data)
    
    def can_restore(self) -> bool:
        """检查是否可以恢复"""
        return self.is_valid() and self.state_data is not None
    
    def get_age(self) -> int:
        """获取检查点年龄（秒）"""
        return int((datetime.now() - self.created_at).total_seconds())
```

#### 3.1.2 实现Thread检查点仓储
```python
# src/core/threads/checkpoints/storage/repository.py
class IThreadCheckpointRepository(ABC):
    """Thread检查点仓储接口"""
    
    @abstractmethod
    async def save(self, checkpoint: ThreadCheckpoint) -> bool:
        """保存检查点"""
        pass
    
    @abstractmethod
    async def find_by_id(self, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """根据ID查找检查点"""
        pass
    
    @abstractmethod
    async def find_by_thread(self, thread_id: str) -> List[ThreadCheckpoint]:
        """查找Thread的所有检查点"""
        pass
```

#### 3.1.3 实现Thread检查点领域服务
```python
# src/core/threads/checkpoints/storage/service.py
class ThreadCheckpointDomainService:
    """Thread检查点领域服务"""
    
    def __init__(self, repository: IThreadCheckpointRepository):
        self._repository = repository
    
    async def create_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ThreadCheckpoint:
        """创建检查点 - 包含业务逻辑"""
        
        # 业务规则验证
        if not thread_id:
            raise ValueError("Thread ID cannot be empty")
        
        if not state_data:
            raise ValueError("State data cannot be empty")
        
        # 业务逻辑：检查点数量限制
        existing_checkpoints = await self._repository.find_by_thread(thread_id)
        if len(existing_checkpoints) >= 100:  # 业务规则
            await self._cleanup_old_checkpoints(thread_id)
        
        # 创建检查点
        checkpoint = ThreadCheckpoint(
            id=self._generate_checkpoint_id(),
            thread_id=thread_id,
            state_data=state_data,
            metadata=metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存检查点
        await self._repository.save(checkpoint)
        
        return checkpoint
```

### 3.2 阶段二：服务层重构（中优先级）

#### 3.2.1 简化存储管理器
```python
# src/services/storage/orchestrator.py
class StorageOrchestrator:
    """存储编排器 - 业务编排层"""
    
    def __init__(
        self,
        checkpoint_service: ThreadCheckpointDomainService,
        checkpoint_manager: ThreadCheckpointManager
    ):
        self._checkpoint_service = checkpoint_service
        self._checkpoint_manager = checkpoint_manager
    
    async def create_and_backup_checkpoint(
        self, 
        thread_id: str, 
        state_data: Dict[str, Any]
    ) -> str:
        """创建并备份检查点 - 业务编排"""
        
        # 1. 创建检查点（调用领域服务）
        checkpoint = await self._checkpoint_service.create_checkpoint(
            thread_id, state_data
        )
        
        # 2. 创建备份（调用管理器）
        backup_id = await self._checkpoint_manager.create_backup(
            checkpoint.id
        )
        
        # 3. 发送事件（业务编排）
        await self._publish_checkpoint_created_event(
            thread_id, checkpoint.id, backup_id
        )
        
        return checkpoint.id
```

### 3.3 阶段三：适配器层重构（中优先级）

#### 3.3.1 实现LangGraph检查点适配器
```python
# src/adapters/threads/checkpoints/langgraph.py
class LangGraphCheckpointAdapter(IThreadCheckpointRepository):
    """LangGraph检查点适配器 - 纯技术实现"""
    
    def __init__(self, langgraph_checkpointer: BaseCheckpointSaver):
        self._checkpointer = langgraph_checkpointer
    
    async def save(self, checkpoint: ThreadCheckpoint) -> bool:
        """技术实现：转换为LangGraph格式并保存"""
        try:
            # 转换为LangGraph格式
            lg_config = self._create_langgraph_config(checkpoint.thread_id)
            lg_checkpoint = self._convert_to_langgraph_checkpoint(checkpoint)
            
            # 调用LangGraph API
            await self._checkpointer.put(lg_config, lg_checkpoint)
            return True
        except Exception as e:
            raise StorageTechnicalError(f"LangGraph save failed: {e}")
```

### 3.4 阶段四：依赖注入更新（低优先级）

#### 3.4.1 更新容器配置
```python
# src/services/container/storage_bindings.py
def register_thread_storage_services(container, config: Dict[str, Any]) -> None:
    """注册Thread存储相关服务"""
    
    # 注册核心领域服务
    container.register_singleton(
        IThreadCheckpointRepository,
        lambda c: ThreadCheckpointRepository(
            c.resolve(IThreadStorageBackend)
        )
    )
    
    container.register_singleton(
        ThreadCheckpointDomainService,
        lambda c: ThreadCheckpointDomainService(
            c.resolve(IThreadCheckpointRepository)
        )
    )
    
    # 注册应用服务
    container.register_singleton(
        ThreadStorageService,
        lambda c: ThreadStorageService(
            c.resolve(ThreadCheckpointDomainService),
            c.resolve(ThreadCheckpointManager)
        )
    )
```

## 4. 迁移策略

### 4.1 渐进式迁移
1. **并行运行**：新旧架构并行运行，逐步切换
2. **功能对等**：确保新架构功能完全覆盖旧架构
3. **性能验证**：验证新架构性能不低于旧架构
4. **回滚机制**：保留回滚到旧架构的能力

### 4.2 数据迁移
1. **数据兼容性**：确保现有数据格式兼容
2. **迁移脚本**：编写自动化数据迁移脚本
3. **验证机制**：迁移后数据完整性验证
4. **备份策略**：迁移前完整数据备份

### 4.3 测试策略
1. **单元测试**：核心层业务逻辑测试覆盖率≥90%
2. **集成测试**：各层间集成测试覆盖率≥80%
3. **端到端测试**：完整业务流程测试覆盖率≥70%
4. **性能测试**：关键操作性能基准测试

## 5. 实施时间表

### 5.1 第一周：核心层重构
- 创建Thread检查点领域模型
- 实现仓储接口和基础实现
- 实现领域服务和业务逻辑

### 5.2 第二周：服务层重构
- 重构存储管理器为编排器
- 实现Thread存储编排服务
- 更新服务间依赖关系

### 5.3 第三周：适配器层重构
- 实现LangGraph检查点适配器
- 更新现有适配器实现
- 实现反防腐层

### 5.4 第四周：集成和测试
- 更新依赖注入配置
- 编写迁移脚本
- 执行全面测试

## 6. 风险评估和缓解

### 6.1 技术风险
- **风险**：新架构性能问题
- **缓解**：性能基准测试和优化

### 6.2 业务风险
- **风险**：功能缺失或回归
- **缓解**：全面的功能测试和验证

### 6.3 时间风险
- **风险**：重构时间超出预期
- **缓解**：分阶段实施和并行开发

## 7. 成功标准

### 7.1 架构质量
- 符合DDD原则的清晰分层
- 高内聚、低耦合的模块设计
- 可测试性和可维护性提升

### 7.2 功能完整性
- 所有现有功能正常工作
- 新架构支持未来扩展需求
- 性能不低于现有实现

### 7.3 代码质量
- 代码覆盖率达标
- 代码质量指标改善
- 文档完整和准确

## 8. 结论

通过这次重构，我们将建立一个符合DDD原则、职责清晰、易于维护的存储架构。新架构将：

1. **明确层次职责**：核心层专注业务逻辑，服务层专注编排，适配器层专注技术实现
2. **提升可维护性**：清晰的领域边界和抽象层次
3. **增强可扩展性**：支持新领域和存储技术的快速集成
4. **改善可测试性**：各层独立测试，依赖注入支持模拟

这个重构方案将解决当前架构的所有核心问题，为系统的长期发展奠定坚实基础。