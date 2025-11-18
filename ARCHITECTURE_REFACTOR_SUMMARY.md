# 架构重构总结：Service 层依赖调整

## 问题描述

Service 层直接依赖 Adapter 层的 `IStateStorageAdapter` 接口，违反了扁平化架构的单向依赖规则：

```
❌ 原始架构：Service → Adapter → Core
```

## 解决方案

将 `IStateStorageAdapter` 接口定义从 Adapter 层移至 Core 层，确保正确的依赖流向：

```
✓ 新架构：Service → Core
         Adapter → Core (实现接口)
```

## 具体变更

### 1. Core 层修改

**文件**: `src/core/state/interfaces.py`

- 添加 `IStateStorageAdapter` 接口定义，包括以下方法：
  - 历史记录管理：`save_history_entry`, `get_history_entries`, `delete_history_entry`, `clear_agent_history`
  - 快照管理：`save_snapshot`, `load_snapshot`, `get_snapshots_by_agent`, `delete_snapshot`
  - 统计信息：`get_history_statistics`, `get_snapshot_statistics`
  - 事务管理：`begin_transaction`, `commit_transaction`, `rollback_transaction`
  - 其他：`close`, `health_check`

- 添加必要的导入：`StateSnapshot`, `StateHistoryEntry` 从 `.entities`

### 2. Service 层修改

更新以下文件的导入，从 Core 层而不是 Adapter 层导入 `IStateStorageAdapter`：

**`src/services/state/snapshots.py`**
```python
# 修改前
from src.adapters.storage.interfaces import IStateStorageAdapter

# 修改后
from src.core.state.interfaces import IStateSnapshotManager, IStateSerializer, IStateStorageAdapter
```

**`src/services/state/history.py`**
```python
# 修改前
from src.adapters.storage.interfaces import IStateStorageAdapter

# 修改后
from src.core.state.interfaces import IStateHistoryManager, IStateSerializer, IStateStorageAdapter
```

**`src/services/state/persistence.py`**
```python
# 修改前
from src.adapters.storage.interfaces import IStateStorageAdapter

# 修改后
from src.core.state.interfaces import IStateStorageAdapter
```

### 3. Adapter 层修改

**文件**: `src/adapters/storage/interfaces.py`

- 删除 `IStateStorageAdapter` 的冗余定义
- 从 Core 层导入 `IStateStorageAdapter` 进行重新导出，维持向后兼容性
- 保留 `IStorageAdapterFactory` 和 `IStorageMigration` 接口

```python
# 从 Core 层导入接口以保持向后兼容性
from src.core.state.interfaces import IStateStorageAdapter

# 重新导出以便向后兼容
__all__ = ['IStateStorageAdapter', 'IStorageAdapterFactory', 'IStorageMigration']
```

**影响的实现类**（无需修改代码，自动通过重新导出）：
- `src/adapters/storage/sqlite.py`: `SQLiteStateStorageAdapter`
- `src/adapters/storage/memory.py`: `MemoryStateStorageAdapter`
- `src/adapters/storage/factory.py`: `StorageAdapterFactory`

## 依赖关系对比

### 修改前的依赖图

```
Services/State
├── snapshots.py ──→ adapters.storage.interfaces (IStateStorageAdapter)
├── history.py ──→ adapters.storage.interfaces (IStateStorageAdapter)
└── persistence.py ──→ adapters.storage.interfaces (IStateStorageAdapter)

Adapters/Storage
├── sqlite.py ──→ interfaces.py (IStateStorageAdapter定义)
├── memory.py ──→ interfaces.py (IStateStorageAdapter定义)
└── interfaces.py ──→ core.state.entities
```

### 修改后的依赖图

```
Services/State
├── snapshots.py ──→ core.state.interfaces (IStateStorageAdapter)
├── history.py ──→ core.state.interfaces (IStateStorageAdapter)
└── persistence.py ──→ core.state.interfaces (IStateStorageAdapter)

Adapters/Storage
├── sqlite.py ──→ interfaces.py (重新导出)
├── memory.py ──→ interfaces.py (重新导出)
└── interfaces.py ──→ core.state.interfaces (IStateStorageAdapter导入)

Core/State
└── interfaces.py (IStateStorageAdapter定义)
```

## 架构原则遵循

本次重构遵循了以下架构原则：

1. **单向依赖** ✓
   - Service → Core (通过接口）
   - Adapter → Core (实现接口)
   - 不存在循环依赖

2. **接口隔离** ✓
   - 所有接口定义在 Core 层
   - Service 层只依赖接口，不依赖实现

3. **关注点分离** ✓
   - Core 层：接口定义、实体、基类
   - Service 层：业务逻辑
   - Adapter 层：具体实现

4. **向后兼容性** ✓
   - 保留 `src/adapters/storage/interfaces.py` 中的导入
   - 现有代码无需修改即可继续工作

## 文件修改清单

- [x] `src/core/state/interfaces.py` - 添加 `IStateStorageAdapter` 接口
- [x] `src/services/state/snapshots.py` - 更新导入
- [x] `src/services/state/history.py` - 更新导入
- [x] `src/services/state/persistence.py` - 更新导入
- [x] `src/adapters/storage/interfaces.py` - 重构为重新导出

## 验证

所有诊断检查已通过：
- ✓ `src/services/state/` - 无诊断错误
- ✓ `src/core/state/` - 无诊断错误
- ✓ `src/adapters/storage/` - 无诊断错误

## 后续建议

1. 考虑对其他层级进行类似审计，确保所有依赖都遵循架构规则
2. 在 AGENTS.md 中记录这一架构变更
3. 可以考虑创建一个架构验证脚本来自动检查依赖关系
