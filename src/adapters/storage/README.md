# 存储适配器

存储适配器模块提供状态存储的统一接口实现，支持同步和异步操作。

## 架构设计

### 模块结构

```
storage/
├── sync_adapter.py      # 同步状态存储适配器
├── async_adapter.py     # 异步状态存储适配器
├── factory.py           # 存储适配器工厂
├── metrics.py           # 指标收集器
├── transaction.py       # 事务管理器
├── error_handler.py     # 错误处理器
├── usage_example.py     # 使用示例
└── README.md           # 本文档
```

### 设计原则

1. **单一职责原则**：每个模块只负责一个特定功能
2. **关注点分离**：将存储逻辑、指标收集、事务管理和错误处理分离
3. **接口隔离**：提供同步和异步两种接口
4. **依赖注入**：通过构造函数注入依赖项

## 核心组件

### 1. 同步适配器 (SyncStateStorageAdapter)

- 实现 `IStateStorageAdapter` 接口
- 提供同步的状态存储操作
- 适用于不需要异步操作的场景

### 2. 异步适配器 (AsyncStateStorageAdapter)

- 实现 `IAsyncStateStorageAdapter` 接口
- 提供异步的状态存储操作
- 适用于高并发场景

### 3. 指标收集器 (StorageMetrics)

- 收集存储操作的性能指标
- 提供操作计数、耗时统计、错误率等信息

### 4. 事务管理器 (TransactionManager)

- 管理存储操作的事务生命周期
- 支持嵌套事务

### 5. 错误处理器 (StorageErrorHandler)

- 统一处理存储操作中的错误
- 提供错误分类和重试机制

## 使用示例

### 同步适配器使用

```python
from src.adapters.storage import StorageAdapterFactory
from src.core.state.entities import StateSnapshot, StateHistoryEntry
from datetime import datetime

# 创建配置
config = {
    "database_path": "example.db"
}

# 创建同步适配器
factory = StorageAdapterFactory()
adapter = factory.create_adapter('sqlite', config)

# 创建状态快照
snapshot = StateSnapshot(
    snapshot_id="snap_001",
    agent_id="agent_001",
    domain_state={"counter": 42, "status": "active"},
    timestamp=datetime.now(),
    snapshot_name="Initial State"
)

# 保存快照
success = adapter.save_snapshot(snapshot)
print(f"保存快照: {success}")

# 加载快照
loaded_snapshot = adapter.load_snapshot("snap_001")
print(f"加载快照: {loaded_snapshot}")

# 关闭连接
adapter.close()
```

### 异步适配器使用

```python
import asyncio
from src.adapters.storage import AsyncStorageAdapterFactory
from src.core.state.entities import StateSnapshot, StateHistoryEntry
from datetime import datetime

async def main():
    # 创建配置
    config = {
        "database_path": "example.db"
    }
    
    # 创建异步适配器
    factory = AsyncStorageAdapterFactory()
    adapter = await factory.create_adapter('sqlite', config)
    
    # 创建状态快照
    snapshot = StateSnapshot(
        snapshot_id="async_snap_001",
        agent_id="async_agent_001",
        domain_state={"counter": 100, "status": "running"},
        timestamp=datetime.now(),
        snapshot_name="Async Initial State"
    )
    
    # 保存快照
    success = await adapter.save_snapshot(snapshot)
    print(f"保存快照: {success}")
    
    # 加载快照
    loaded_snapshot = await adapter.load_snapshot("async_snap_001")
    print(f"加载快照: {loaded_snapshot}")
    
    # 关闭连接
    await adapter.close()

# 运行异步函数
asyncio.run(main())
```

### 使用便捷函数

```python
from src.adapters.storage import create_storage_adapter

# 创建同步适配器
sync_adapter = create_storage_adapter('sqlite', {"database_path": "example.db"}, async_mode=False)

# 创建异步适配器
async_adapter = create_storage_adapter('sqlite', {"database_path": "example.db"}, async_mode=True)
```

## 存储类型支持

- **SQLite**: 基于文件的轻量级数据库
- **Memory**: 内存存储，适用于测试和临时数据
- **File**: 基于文件的存储

## 最佳实践

1. **选择合适的适配器类型**：根据应用需求选择同步或异步适配器
2. **使用工厂模式**：通过工厂类创建适配器实例
3. **监控指标**：定期检查存储操作的性能指标
4. **错误处理**：使用提供的错误处理机制
5. **资源管理**：记得在使用完毕后关闭适配器

## 迁移指南

从旧的 `OptimizedStateStorageAdapter` 迁移到新架构：

1. 替换导入路径
2. 使用工厂类创建适配器实例
3. 根据需要选择同步或异步适配器
4. 更新错误处理逻辑
5. 利用新的指标收集功能