# Adapter 层导入更新指南

## 概述

对 Adapter 层的导入进行了更新，以确保所有接口定义都在 Core 层，实现了完整的单向依赖架构。

## 文件修改清单

### 1. Storage Adapter 实现类

#### `src/adapters/storage/sqlite.py`
**修改**：导入位置从 Adapter 层改为 Core 层

```python
# 修改前
from .interfaces import IStateStorageAdapter
from src.core.state.entities import StateSnapshot, StateHistoryEntry

# 修改后
from src.core.state.interfaces import IStateStorageAdapter
from src.core.state.entities import StateSnapshot, StateHistoryEntry
```

**原因**：`IStateStorageAdapter` 接口现在定义在 Core 层，Adapter 层应该直接从 Core 导入

#### `src/adapters/storage/memory.py`
**修改**：同上

```python
# 修改前
from .interfaces import IStateStorageAdapter

# 修改后
from src.core.state.interfaces import IStateStorageAdapter
```

### 2. Storage Adapter 工厂类

#### `src/adapters/storage/factory.py`
**已正确**：工厂类已从 Core 层导入两个接口

```python
from src.core.state.interfaces import IStateStorageAdapter, IStorageAdapterFactory
```

**修复**：
- 添加了 `__all__` 导出列表
- 修复了 `get_all_adapter_info()` 的返回类型注解

### 3. 接口重新导出文件

#### `src/adapters/storage/interfaces.py`
**修改**：将此文件转换为重新导出文件，保持向后兼容性

```python
# 从 Core 层导入接口
from src.core.state.interfaces import (
    IStateStorageAdapter,
    IStorageAdapterFactory, 
    IStorageMigration
)

# 重新导出以保持向后兼容性
__all__ = [
    'IStateStorageAdapter',
    'IStorageAdapterFactory',
    'IStorageMigration'
]
```

**作用**：
- 现有代码可以继续从 `src/adapters/storage/interfaces` 导入
- 新代码应该直接从 Core 导入

#### `src/adapters/storage/__init__.py`
**保持不变**：继续从 `interfaces.py` 导入和重新导出

## Core 层接口定义

### `src/core/state/interfaces.py`
**添加**了三个新接口：

1. **IStateStorageAdapter**（已有）
   - 定义状态存储的统一接口
   - 支持历史记录和快照操作

2. **IStorageAdapterFactory**（新添加）
   - 定义存储适配器的工厂接口
   - 方法：`create_adapter()`, `get_supported_types()`, `validate_config()`

3. **IStorageMigration**（新添加）
   - 定义存储数据迁移功能
   - 方法：`migrate_from()`, `validate_migration()`

## 依赖关系图

### 修改前

```
Adapter Layer
├── sqlite.py ──→ interfaces.py (IStateStorageAdapter 定义)
├── memory.py ──→ interfaces.py (IStateStorageAdapter 定义)
├── factory.py ──→ core.state.interfaces (IStorageAdapterFactory)
└── interfaces.py ──→ core.state.entities

Service Layer
├── snapshots.py ──→ core.state.interfaces (导入接口)
├── history.py ──→ core.state.interfaces (导入接口)
└── persistence.py ──→ core.state.interfaces (导入接口)
```

### 修改后

```
Adapter Layer
├── sqlite.py ──→ core.state.interfaces (IStateStorageAdapter)
├── memory.py ──→ core.state.interfaces (IStateStorageAdapter)
├── factory.py ──→ core.state.interfaces (所有接口)
└── interfaces.py ──→ core.state.interfaces (重新导出)

Service Layer
├── snapshots.py ──→ core.state.interfaces (IStateStorageAdapter)
├── history.py ──→ core.state.interfaces (IStateStorageAdapter)
└── persistence.py ──→ core.state.interfaces (IStateStorageAdapter)

Core Layer
└── state/interfaces.py (IStateStorageAdapter, IStorageAdapterFactory, IStorageMigration)
```

## 向后兼容性

保证了完全的向后兼容性：

1. **Adapter 层中的现有导入**仍然可以工作
   ```python
   from src.adapters.storage.interfaces import IStateStorageAdapter  # 仍然有效
   ```

2. **重新导出机制**
   - `src/adapters/storage/interfaces.py` 从 Core 层导入并重新导出
   - 现有代码无需修改

3. **推荐做法**
   - 新代码应直接从 Core 层导入：
   ```python
   from src.core.state.interfaces import IStateStorageAdapter
   ```

## 验证

所有诊断检查已通过：
- ✓ `src/adapters/storage/` - 无诊断错误
- ✓ `src/core/state/` - 无诊断错误
- ✓ `src/services/state/` - 无诊断错误

## 架构优势

1. **清晰的依赖流向** - 所有依赖指向 Core 层
2. **单一职责** - Core 层定义接口，Adapter 层实现接口
3. **易于测试** - 可以轻松替换 Adapter 实现
4. **易于扩展** - 添加新的 Adapter 只需实现 Core 接口
5. **代码复用** - Service 层不依赖 Adapter 层，完全解耦

## 总结表

| 文件 | 修改前 | 修改后 | 说明 |
|------|--------|--------|------|
| sqlite.py | `.interfaces` | `core.state.interfaces` | 直接导入接口 |
| memory.py | `.interfaces` | `core.state.interfaces` | 直接导入接口 |
| factory.py | ✓ 已正确 | ✓ 保持不变 | Core 已定义工厂接口 |
| interfaces.py | 接口定义 | 重新导出 | 向后兼容性 |
