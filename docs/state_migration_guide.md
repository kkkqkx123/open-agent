# 状态管理模块迁移指南

## 概述

本文档描述了从旧架构（Domain层）到新架构（Core+Services+Adapters）的状态管理模块迁移过程，以及新增功能的使用说明。

## 旧架构功能映射

### 1. 接口变化

| 旧架构接口 | 新架构接口 | 说明 |
|------------|------------|------|
| `IStateCrudManager` | `EnhancedStateManager` | 基础CRUD操作已集成到增强管理器中 |
| `IStateLifecycleManager` | `IEnhancedStateManager` | 生命周期管理功能已重构 |

### 2. 实现类变化

| 旧架构实现 | 新架构实现 | 说明 |
|------------|------------|------|
| `StateManager` | `EnhancedStateManager` | 增强了历史记录和快照功能 |
| `StateLifecycleManagerImpl` | `StateHistoryService`, `StateSnapshotService` | 功能已拆分到专门的服务中 |

## 新增功能

### 1. 冲突解决策略

新架构引入了冲突解决相关类型：

- `ConflictType`: 冲突类型枚举
- `ConflictResolutionStrategy`: 冲突解决策略枚举
- `StateConflict`: 状态冲突实体

### 2. 带状态管理的执行

`execute_with_state_management` 方法提供了安全的状态执行机制：

```python
# 示例用法
result, success = state_manager.execute_with_state_management(
    state_id="example_state",
    executor=lambda state: (state.update({"new_field": "value"}), True)
)
```

### 3. 工作流状态管理

`WorkflowStateManager` 专门处理工作流状态：

```python
# 示例用法
workflow_manager = container.get(WorkflowStateManager)
state = workflow_manager.create_workflow_state(
    state_id="workflow_state_1",
    initial_state={"messages": [], "current_step": "start"},
    agent_id="workflow_agent_1"
)
```

## 使用示例

### 1. 基础状态管理

```python
from src.services.state import EnhancedStateManager

# 通过依赖注入获取实例
state_manager = container.get(EnhancedStateManager)

# 创建状态
state = state_manager.create_state("state_1", {"key": "value"})

# 更新状态
updated_state = state_manager.update_state("state_1", {"new_key": "new_value"})

# 获取状态
retrieved_state = state_manager.get_state("state_1")
```

### 2. 历史记录功能

```python
# 记录状态变化
history_id = state_manager.history_manager.record_state_change(
    agent_id="agent_1",
    old_state={"key": "old_value"},
    new_state={"key": "new_value"},
    action="update"
)

# 获取历史记录
history = state_manager.history_manager.get_state_history("agent_1")
```

### 3. 快照功能

```python
# 创建快照
snapshot_id = state_manager.create_state_snapshot(
    state_id="state_1",
    agent_id="agent_1",
    snapshot_name="backup"
)

# 从快照恢复
restored_state = state_manager.restore_state_from_snapshot(
    snapshot_id=snapshot_id,
    state_id="state_1"
)
```

## 依赖注入配置

新架构中的状态管理服务通过依赖注入容器进行管理：

```python
from src.services.state.di_config import configure_state_services

# 配置状态服务
configure_state_services(container, config)
```

## 向后兼容性

旧架构的接口通过适配器模式保持向后兼容：

- `LegacyStateManagerAdapter`: 适配IStateCrudManager
- `LegacyHistoryManagerAdapter`: 适配IStateHistoryManager
- `LegacySnapshotStoreAdapter`: 适配IStateSnapshotStore

## 最佳实践

1. **使用适当的状态管理器**：
   - 一般用途：使用`EnhancedStateManager`
   - 工作流专用：使用`WorkflowStateManager`

2. **利用快照功能**：
   - 在重要操作前创建快照
   - 定期清理旧快照以节省存储空间

3. **合理使用历史记录**：
   - 仅记录重要的状态变化
   - 定期清理历史记录以控制存储增长

## 性能优化

1. **缓存机制**：新架构包含内存缓存以提高访问性能
2. **压缩功能**：状态数据自动压缩以节省存储空间
3. **批量操作**：支持批量状态操作以提高效率