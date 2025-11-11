# 异步执行机制使用指南

本文档旨在说明项目中同步与异步方法的实现现状、使用场景和最佳实践。

## 1. 实现现状

项目中的工具系统采用了“同步优先”的设计原则，通过 `BaseTool` 类为所有工具提供统一的异步执行能力。

### 1.1 `BaseTool` 的默认实现

在 [`src/domain/tools/base.py`](src/domain/tools/base.py:66) 中，`execute_async` 方法提供了默认实现，它使用 `loop.run_in_executor()` 在线程池中执行同步的 `execute` 方法。这使得所有继承 `BaseTool` 的子类都能自动获得异步执行能力。

```python
async def execute_async(self, **kwargs: Any) -> Any:
    """异步执行工具（默认实现）
    
    默认实现使用线程池执行同步方法，子类可以重写此方法提供真正的异步实现。
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: self.execute(**kwargs))
```

### 1.2 `MCPTool` 和 `NativeTool` 的实现

`MCPTool` 和 `NativeTool` 都实现了真正的异步 I/O 操作，使用 `aiohttp` 进行网络通信。

- **`execute_async`**: 提供了真正的异步实现，用于处理 I/O 密集型任务。
- **`execute`**: 作为同步适配器，通过创建新的事件循环来调用 `execute_async`。**这是当前的性能瓶颈**，因为它每次调用都创建和销毁事件循环，开销巨大。

### 1.3 事件循环管理

项目提供了 `EventLoopManager` ([`src/infrastructure/async_utils/event_loop_manager.py`](src/infrastructure/async_utils/event_loop_manager.py:1)) 来统一管理事件循环。更优的实现是让 `execute` 方法使用 `EventLoopManager.run_async()`，而不是自己创建事件循环。

## 2. 使用场景与性能

### 2.1 `execute_async` 的效率

`execute_async` 能否提高效率取决于使用场景：

- **能提高效率的场景 (I/O 密集型)**：
  - **并发执行**：当需要同时调用多个工具或工作流时，使用 `asyncio.gather` 可以显著提高吞吐量（如 [`docs/architecture/workflow-graph/technical-optimization-completion.md`](docs/architecture/workflow-graph/technical-optimization-completion.md:75) 所示，并发吞吐量可达 317 执行/秒）。
  - **流式处理**：处理来自 LLM 或 MCP 服务器的流式响应时，异步是必需的。

- **可能降低效率的场景 (CPU 密集型或简单任务)**：
  - **单次简单调用**：对于非 I/O 密集的单次调用，`execute_async` 由于其固有的开销（协程调度、事件循环管理），执行时间（平均 16.3ms）反而可能高于同步方法（平均 10.5ms），如 [`docs/architecture/workflow-graph/technical-optimization-completion.md`](docs/architecture/workflow-graph/technical-optimization-completion.md:74) 所示。

## 3. 最佳实践

### 3.1 接口选择

- **优先使用同步接口 `execute`**：除非你明确需要并发或流式处理，否则应优先使用同步接口，以避免不必要的异步开销。
- **使用异步接口 `execute_async`**：在需要并发执行多个工具、处理流式数据或与异步框架集成时使用。

### 3.2 性能优化

- **避免在 `execute` 中创建新事件循环**：当前 `MCPTool` 和 `NativeTool` 的 `execute` 实现是低效的。未来的优化方向是重构它们，使用 `EventLoopManager` 来运行 `execute_async`，从而避免频繁创建和销毁事件循环。

### 3.3 代码示例

```python
# 推荐：同步执行单个工具
result = tool.execute(param1="value")

# 推荐：异步并发执行多个工具
results = await asyncio.gather(
    tool1.execute_async(**args1),
    tool2.execute_async(**args2),
    tool3.execute_async(**args3)
)

# 推荐：流式处理
async for chunk in llm_client.stream_generate_async(prompt):
    print(chunk)