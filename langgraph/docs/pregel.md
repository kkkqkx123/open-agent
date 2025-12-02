# LangGraph Pregel 实现

## 概述

`pregel` 目录包含 LangGraph 的核心运行时实现，基于 **Pregel 算法** 和 **同步并行批量（Bulk Synchronous Parallel, BSP）模型**。该实现在支持检查点、流式传输、错误处理和复杂节点交互的同时，管理有状态图工作流的执行。

---

## 核心组件

### 1. `main.py` - Pregel 类与 NodeBuilder

Pregel 实现的主要入口，包含两个核心类：

- **`Pregel`**：主运行时类，负责协调图工作流的执行。它管理节点执行、通道通信、检查点以及提供流式输出功能。
- **`NodeBuilder`**：用于构建 `PregelNode` 实例的流畅接口（Fluent Interface），支持订阅通道、定义节点行为及指定写操作。

`Pregel` 类的关键特性包括：
- 输入/输出通道管理
- 流模式（values、updates、custom、messages、checkpoints、tasks）
- 检查点与状态管理
- 节点前/后的中断处理
- 耐久性模式（sync、async、exit）
- 支持子图和嵌套执行
- 上下文模式（schema）处理

---

### 2. `protocol.py` - 接口定义

定义了抽象基类 `PregelProtocol`，为 Pregel 实现建立接口契约，包括：
- 流式方法（`stream`, `astream`）
- 状态管理方法（`get_state`, `update_state` 等）
- 图可视化方法（`get_graph`）
- 执行方法（`invoke`, `ainvoke`）

---

### 3. 算法实现文件

#### `_algo.py` - 核心算法逻辑
- 实现 Pregel 算法的核心逻辑
- `prepare_next_tasks()`：准备下一步要执行的任务集合
- `prepare_single_task()`：准备单个 PUSH/PULL 类型任务
- `apply_writes()`：应用已完成任务带来的通道更新
- `local_read()`：在节点执行期间读取当前状态的函数
- `should_interrupt()`：判断是否应中断执行的条件检查

#### `_loop.py` - 执行循环管理
- 实现 `SyncPregelLoop` 和 `AsyncPregelLoop` 类
- 管理主执行循环中的 tick / before_tick / after_tick 阶段
- 处理检查点创建与持久化
- 管理任务执行与写入传播
- 实现耐久性模式与流式输出

#### `_checkpoint.py` - 检查点管理
- 创建、复制和管理检查点的功能函数
- `create_checkpoint()`：根据当前状态创建新检查点
- `empty_checkpoint()`：创建初始空检查点
- `channels_from_checkpoint()`：从检查点数据恢复通道状态

#### `_io.py` - 输入/输出处理
- `map_input()`：将输入数据映射为通道写入操作
- `map_output_values()`：将当前通道值映射为输出结果
- `map_output_updates()`：将任务更新映射为流式输出
- `read_channels()`：从通道中读取值

#### `_read.py` - 节点处理逻辑
- `PregelNode` 类：表示计算图中的单个节点
- 输入处理与通道订阅逻辑
- 节点执行验证机制

---

### 4. 辅助实现文件

#### `_runner.py` - 任务执行管理
- 使用后台执行器管理任务的并发执行
- 实现基于“tick”的调度机制
- 处理任务提交与完成流程

#### `_executor.py` - 后台执行
- `BackgroundExecutor` 与 `AsyncBackgroundExecutor`：管理并行任务执行
- 提供线程安全的任务提交与结果处理

#### `_retry.py` - 重试策略管理
- `RetryPolicy` 类：定义失败任务的重试策略
- 与执行循环集成以实现故障恢复

#### `_cache.py` - 缓存实现（不在 pregel 目录中）
- 任务结果的缓存策略，避免重复计算

#### `debug.py` - 调试与可视化
- 调试信息格式化工具
- 任务可视化辅助函数

#### `_config.py` - 配置管理（未显示但可能存在）
- Pregel 执行的配置处理模块

#### `_log.py` - 日志记录
- Pregel 执行过程的日志工具

#### `_messages.py` - 消息流式传输
- `StreamMessagesHandler`：处理 LLM 消息的逐 token 流式输出

#### `_utils.py` - 工具函数
- 版本管理和状态处理的辅助函数
- 通道版本管理的实用工具

---

## 执行模型

Pregel 实现遵循 **同步并行批量（BSP）模型**，分为三个主要阶段：

1. **计划阶段（Plan Phase）**：根据通道更新和依赖关系，确定哪些节点需要执行  
2. **执行阶段（Execution Phase）**：并行执行所有选定节点，直到完成、失败或超时  
3. **更新阶段（Update Phase）**：应用已完成节点产生的通道更新  

整个执行过程按“步”推进：第 N 步的通道更新仅在第 N+1 步才可见，从而保证执行的确定性。

---

## 通道与通信机制

系统支持多种类型的通道：
- `LastValue`：仅保存最后一次写入该通道的值
- `Topic`：发布/订阅（PubSub）风格的通道，支持可配置的数据累积方式
- `Context`：管理外部资源的生命周期
- `BinaryOperatorAggregate`：通过二元操作符持续更新的持久化值

---

## 检查点与持久化

系统具备强大的检查点能力：
- 在执行过程中自动创建检查点
- 支持不同耐久性模式（同步/异步/退出时）
- 状态历史与版本追踪
- 支持带命名空间管理的子图检查点

---

## 流式输出与响应模式

支持多种流式输出模式：
- **Values**：每一步完成后输出状态值
- **Updates**：输出各节点的执行结果变更
- **Messages**：LLM 逐 token 的生成内容流
- **Custom**：节点自定义输出数据
- **Checkpoints**：检查点事件流
- **Tasks**：任务生命周期事件流