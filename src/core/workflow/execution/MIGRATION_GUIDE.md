# 执行器架构迁移指南

本文档帮助您从旧的执行器架构迁移到新的基于职责的分层架构。

## 架构变更概述

### 旧架构问题
- 按照类型划分执行器导致职责重叠
- 抽象层次不一致
- 功能耦合严重
- 扩展性差

### 新架构优势
- 按照职责清晰分层
- 抽象层次分明
- 高内聚低耦合
- 易于扩展和维护

## 迁移映射表

| 旧文件 | 新位置 | 说明 |
|---------|--------|------|
| `executor.py` | `core/workflow_executor.py` | 核心工作流执行逻辑 |
| `async_executor.py` | `core/node_executor.py` | 节点执行逻辑 |
| `runner.py` | `services/execution_manager.py` | 执行管理功能 |
| `retry_executor.py` | `strategies/retry_strategy.py` | 重试策略 |
| `batch_executor.py` | `strategies/batch_strategy.py` | 批量策略 |
| `streaming.py` | `strategies/streaming_strategy.py` | 流式策略 |
| `collaboration_executor.py` | `strategies/collaboration_strategy.py` | 协作策略 |
| `base/executor_base.py` | `base/executor_base.py` | 保持不变 |

## 代码迁移示例

### 1. 基本工作流执行

**旧代码：**
```python
from src.core.workflow.execution.runner import WorkflowRunner

runner = WorkflowRunner()
result = runner.run_workflow("config.yaml", initial_data)
```

**新代码：**
```python
from src.core.workflow.execution import ExecutionManager

manager = ExecutionManager()
result = manager.execute_workflow(workflow, initial_data)
```

### 2. 带重试的执行

**旧代码：**
```python
from src.core.workflow.execution.retry_executor import RetryExecutor, RetryConfig

config = RetryConfig(max_retries=3)
executor = RetryExecutor(config)
result = executor.execute(workflow, initial_data)
```

**新代码：**
```python
from src.core.workflow.execution import ExecutionManager, RetryStrategy, RetryConfig

manager = ExecutionManager()
retry_strategy = RetryStrategy(RetryConfig(max_retries=3))
manager.register_strategy(retry_strategy)

result = manager.execute_workflow(workflow, initial_data, config={"retry_enabled": True})
```

### 3. 批量执行

**旧代码：**
```python
from src.core.workflow.execution.batch_executor import BatchExecutor, BatchExecutionConfig

executor = BatchExecutor()
config = BatchExecutionConfig(mode=ExecutionMode.THREAD_POOL, max_workers=3)
result = executor.execute(jobs, config)
```

**新代码：**
```python
from src.core.workflow.execution import ExecutionManager, BatchStrategy, BatchConfig

manager = ExecutionManager()
batch_strategy = BatchStrategy(BatchConfig(max_workers=3))
manager.register_strategy(batch_strategy)

result = manager.execute_workflow(workflow, initial_data, config={"batch_enabled": True})
```

### 4. 异步执行

**旧代码：**
```python
from src.core.workflow.execution.async_executor import AsyncNodeExecutor

executor = AsyncNodeExecutor()
result = await executor.execute(state, config)
```

**新代码：**
```python
from src.core.workflow.execution import ExecutionManager, AsyncMode

manager = ExecutionManager()
async_mode = AsyncMode()
manager.register_mode(async_mode)

result = await manager.execute_workflow_async(workflow, initial_data)
```

## 新架构使用指南

### 1. 基本使用

```python
from src.core.workflow.execution import ExecutionManager

# 创建执行管理器
manager = ExecutionManager()

# 执行工作流
result = manager.execute_workflow(workflow, initial_data)
```

### 2. 使用策略

```python
from src.core.workflow.execution import (
    ExecutionManager, 
    RetryStrategy, 
    BatchStrategy, 
    StreamingStrategy
)

# 创建管理器
manager = ExecutionManager()

# 注册策略
manager.register_strategy(RetryStrategy())
manager.register_strategy(BatchStrategy())
manager.register_strategy(StreamingStrategy())

# 执行工作流（自动选择合适的策略）
result = manager.execute_workflow(workflow, initial_data)
```

### 3. 使用模式

```python
from src.core.workflow.execution import (
    ExecutionManager,
    SyncMode,
    AsyncMode,
    HybridMode
)

# 创建管理器
manager = ExecutionManager()

# 注册模式
manager.register_mode(SyncMode())
manager.register_mode(AsyncMode())
manager.register_mode(HybridMode())

# 强制使用异步模式
result = manager.execute_workflow(
    workflow, 
    initial_data, 
    config={"mode": "async"}
)
```

### 4. 监控和调度

```python
from src.core.workflow.execution import (
    ExecutionManager,
    ExecutionMonitor,
    ExecutionScheduler
)

# 创建管理器
manager = ExecutionManager()

# 添加监控
monitor = ExecutionMonitor()
manager.register_monitor(monitor)

# 添加调度器
scheduler = ExecutionScheduler()
scheduler.start()

# 提交任务到调度器
task_id = scheduler.submit_task(workflow, context)

# 获取任务状态
status = scheduler.get_task_status(task_id)
```

## 配置迁移

### 旧配置格式
```python
# 直接在执行器中配置
executor = RetryExecutor(
    max_retries=3,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF
)
```

### 新配置格式
```python
# 通过上下文配置
context = ExecutionContext(
    workflow_id="workflow_1",
    execution_id="exec_1",
    config={
        "retry_enabled": True,
        "retry_config": {
            "max_retries": 3,
            "strategy": "exponential_backoff"
        }
    }
)
```

## 向后兼容性

新架构保持了向后兼容性，您仍然可以使用旧的导入方式：

```python
# 旧的导入方式仍然有效
from src.core.workflow.execution import WorkflowRunner
from src.core.workflow.execution import RetryExecutor
from src.core.workflow.execution import BatchExecutor
```

但这些只是兼容性包装器，建议逐步迁移到新架构。

## 迁移步骤

1. **评估现有代码**：识别使用旧架构的地方
2. **更新导入**：使用新的导入路径
3. **重构执行逻辑**：使用新的执行管理器
4. **添加策略和模式**：根据需要注册策略和模式
5. **测试验证**：确保功能正常
6. **清理旧代码**：移除不再需要的旧代码

## 常见问题

### Q: 如何选择合适的策略？
A: 新架构会自动根据上下文选择合适的策略。您也可以通过配置强制指定策略。

### Q: 如何处理自定义执行逻辑？
A: 可以通过实现 `IExecutionStrategy` 接口来创建自定义策略。

### Q: 性能会有影响吗？
A: 新架构经过优化，性能不会下降，而且在某些场景下会有提升。

### Q: 如何监控执行性能？
A: 使用 `ExecutionMonitor` 可以获得详细的性能指标和告警。

## 获取帮助

如果在迁移过程中遇到问题，可以：
1. 查看本文档的示例代码
2. 检查新架构的接口定义
3. 参考单元测试用例
4. 联系开发团队获取支持