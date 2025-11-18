# 导入参考指南

## 状态管理接口导入位置

### Core 层接口（所有接口都在这里）

**位置**: `src/core/state/interfaces.py`

```python
from src.core.state.interfaces import (
    # 状态管理接口
    IStateHistoryManager,      # 历史管理器接口
    IStateSnapshotManager,     # 快照管理器接口
    IStateSerializer,          # 序列化器接口
    IEnhancedStateManager,     # 增强状态管理器接口
    
    # 存储适配器接口
    IStateStorageAdapter,      # 存储适配器接口
    IStorageAdapterFactory,    # 存储工厂接口
    IStorageMigration,         # 存储迁移接口
)
```

### Core 层实体和基类

**位置**: `src/core/state/base.py`

```python
from src.core.state.base import (
    BaseStateSerializer,        # 基础序列化器实现
    BaseStateHistoryManager,    # 基础历史管理器
    BaseStateSnapshotManager,   # 基础快照管理器
    BaseStateManager,           # 基础状态管理器
    StateValidationMixin,       # 状态验证混入类
)
```

### Core 层实体类

**位置**: `src/core/state/entities.py`

```python
from src.core.state.entities import (
    StateSnapshot,              # 快照实体
    StateHistoryEntry,          # 历史记录实体
    StateDiff,                  # 状态差异实体
    StateStatistics,            # 统计信息实体
)
```

### Service 层实现类

**位置**: `src/services/state/`

```python
from src.services.state import (
    # 核心服务
    EnhancedStateManager,       # 增强状态管理器实现
    StateHistoryService,        # 历史管理服务
    StateSnapshotService,       # 快照管理服务
    StatePersistenceService,    # 持久化服务
    StateBackupService,         # 备份服务
)
```

### Adapter 层实现类

**位置**: `src/adapters/storage/`

```python
# 存储适配器实现
from src.adapters.storage import (
    MemoryStateStorageAdapter,  # 内存存储适配器
    SQLiteStateStorageAdapter,  # SQLite存储适配器
    StorageAdapterFactory,      # 存储工厂实现
    StorageAdapterManager,      # 存储管理器
)
```

## 推荐导入方式

### 在 Service 层中

```python
# ✓ 推荐：导入接口
from src.core.state.interfaces import (
    IStateStorageAdapter,
    IStateHistoryManager,
    IStateSnapshotManager,
)

# ✗ 不推荐：导入 Adapter 层的东西
from src.adapters.storage import ...  # 避免
```

### 在 Adapter 层中

```python
# ✓ 推荐：导入接口（因为需要实现）
from src.core.state.interfaces import (
    IStateStorageAdapter,
    IStorageAdapterFactory,
)

# ✓ 也可以：向后兼容的重新导出
from src.adapters.storage.interfaces import IStateStorageAdapter
```

### 在 Core 层中

```python
# ✓ 推荐：使用相对导入
from .interfaces import IStateStorageAdapter
from .entities import StateSnapshot

# ✓ 也可以：使用绝对导入
from src.core.state.interfaces import IStateStorageAdapter
from src.core.state.entities import StateSnapshot
```

## 架构规则

### 禁止的导入模式

```python
# ❌ Service 导入 Adapter 实现类
from src.adapters.storage import SQLiteStateStorageAdapter

# ❌ Adapter 导入 Service 类
from src.services.state import StateHistoryService

# ❌ 跨层不相关的导入
from src.adapters.storage import StateHistoryService
```

### 允许的导入模式

```python
# ✓ Service 导入 Core 接口
from src.core.state.interfaces import IStateStorageAdapter

# ✓ Adapter 导入 Core 接口
from src.core.state.interfaces import IStateStorageAdapter

# ✓ Service 导入 Core 实体
from src.core.state.entities import StateSnapshot

# ✓ Adapter 导入 Core 实体
from src.core.state.entities import StateHistoryEntry
```

## 快速检查清单

导入时，检查以下条件：

- [ ] 是否导入接口？→ 应该从 Core 导入
- [ ] 是否导入实体？→ 应该从 Core/entities 导入
- [ ] 是否导入具体实现？→ 检查所在层级是否允许
- [ ] 是否跨层导入？→ 只能 Service/Adapter → Core，不能反向
- [ ] 是否造成循环依赖？→ 使用 `isinstance()` 和类型注解来避免

## 常见错误及修正

### 错误1：从 Adapter 导入接口

```python
# ❌ 错误
from src.adapters.storage.interfaces import IStateStorageAdapter

# ✓ 正确
from src.core.state.interfaces import IStateStorageAdapter
```

### 错误2：从 Adapter 导入 Service

```python
# ❌ 错误
from src.adapters.storage import StateHistoryService

# ✓ 正确
from src.services.state import StateHistoryService
```

### 错误3：Service 导入 Adapter 实现

```python
# ❌ 错误
from src.adapters.storage import SQLiteStateStorageAdapter

# ✓ 正确 - 使用接口，由 DI 容器注入实现
from src.core.state.interfaces import IStateStorageAdapter
```

## 版本历史

- **v1.0** (当前)：完整的接口定义在 Core 层，向后兼容的重新导出
