# LangGraph _internal 模块功能说明

## 概述

`_internal` 模块是 LangGraph 内部使用的专用模块，不属于公共 API，因此稳定性无法保证。该模块包含了一系列内部工具和辅助功能，用于支持 LangGraph 核心功能的实现，包括配置管理、常量定义、字段处理、未来任务管理、队列操作、重试机制等。

## 各文件功能详情

### 1. `_cache.py` - 缓存管理模块
- **功能**: 提供缓存键的生成与冻结功能，确保复杂对象能够被转换为可哈希的键用于缓存。
- **主要函数**:
  - `_freeze(obj, depth)`: 将复杂对象递归冻结为可哈希的格式，支持字典、序列等数据结构。
  - `default_cache_key(*args, **kwargs)`: 基于参数和关键字参数生成默认缓存键，使用 pickle 进行序列化。

### 2. `_config.py` - 配置管理模块
- **功能**: 处理 LangGraph 运行配置，包括配置合并、补丁、回调管理等。
- **主要函数**:
  - `merge_configs(*configs)`: 合并多个配置为一个配置。
  - `patch_config(config, ...)`: 使用新值对配置进行补丁操作。
  - `ensure_config(*configs)`: 确保配置包含所有必要键并设置默认值。
  - `get_callback_manager_for_config(config)`: 获取配置对应的回调管理器。
  - `get_async_callback_manager_for_config(config)`: 获取配置对应的异步回调管理器。

### 3. `_constants.py` - 常量定义模块
- **功能**: 定义了 LangGraph 运行时所使用的所有常量，包括保留写入键、配置键和命名空间分隔符等。
- **重要常量**:
  - **保留写入键**: `INPUT`, `INTERRUPT`, `RESUME`, `ERROR`, `NO_WRITES`, `TASKS`, `RETURN`, `PREVIOUS`
  - **配置键**: `CONFIG_KEY_SEND`, `CONFIG_KEY_READ`, `CONFIG_KEY_CHECKPOINTER`, `CONFIG_KEY_STREAM`, `CONFIG_KEY_CACHE` 等
  - **命名空间**: `NS_SEP` (分隔符 `|`), `NS_END` (结束符 `:`)

### 4. `_fields.py` - 字段处理模块
- **功能**: 提供字段类型检查、默认值确定和类型提示获取等功能。
- **主要函数**:
  - `_is_optional_type(type_)`: 检查类型是否为 Optional。
  - `get_field_default(name, type_, schema)`: 确定字段的默认值。
  - `get_enhanced_type_hints(type)`: 提取字段的类型、默认值和描述信息。
  - `get_update_as_tuples(input, keys)`: 将 Pydantic 状态更新作为键值对元组列表返回。

### 5. `_future.py` - 异步任务管理模块
- **功能**: 管理异步任务和未来对象，包括任务链接、状态复制、线程安全执行等。
- **主要函数**:
  - `_chain_future(source, destination)`: 链接两个未来对象，一个完成时另一个也完成。
  - `run_coroutine_threadsafe(coro, loop, ...)`: 将协程提交到给定事件循环并返回 asyncio.Future。
  - `_ensure_future(coro_or_future, ...)`: 确保异步任务在指定事件循环中运行。

### 6. `_pydantic.py` - Pydantic 相关工具模块
- **功能**: 提供 Pydantic 模型的相关工具，包括模型创建、字段获取和类型检查等。
- **主要函数**:
  - `get_fields(model)`: 获取 Pydantic 模型的字段。
  - `create_model(model_name, ...)`: 创建具有给定字段定义的 Pydantic 模型。
  - `is_supported_by_pydantic(type_)`: 检查特定类型是否被 Pydantic 支持。

### 7. `_queue.py` - 队列实现模块
- **功能**: 提供同步和异步队列实现，支持等待操作。
- **主要类**:
  - `AsyncQueue`: 异步无界 FIFO 队列，继承自 asyncio.Queue，添加了 wait() 方法。
  - `SyncQueue`: 同步无界 FIFO 队列，提供 wait() 方法用于等待队列中有项目可用。

### 8. `_retry.py` - 重试机制模块
- **功能**: 提供默认的重试条件检查函数。
- **主要函数**:
  - `default_retry_on(exc)`: 定义默认的重试条件，对连接错误和 5xx HTTP 状态码进行重试。

### 9. `_runnable.py` - 可运行对象模块
- **功能**: 定义 LangGraph 中的可运行对象，包括同步和异步执行、配置注入和链式执行等。
- **主要类**:
  - `RunnableCallable`: 简化版的 RunnableLambda，要求同步和异步函数。
  - `RunnableSeq`: 可运行对象序列，其中每个对象的输出是下一个对象的输入。
- **主要函数**:
  - `coerce_to_runnable(thing)`: 将类似可运行对象转换为 Runnable。
  - `is_async_callable(func)`: 检查函数是否为异步函数。

### 10. `_scratchpad.py` - 临时存储模块
- **功能**: 提供临时存储空间，用于存储运行时的临时状态和中间结果。
- **主要类**:
  - `PregelScratchpad`: 定义了 Pregel 运行时的临时存储结构，包括步骤计数、中断计数、子图计数等。

### 11. `_typing.py` - 类型工具模块
- **功能**: 提供内部使用的类型工具和协议定义。
- **主要组件**:
  - `TypedDictLikeV1`, `TypedDictLikeV2`: 代表 TypedDict 行为的协议。
  - `DataclassLike`: 代表 dataclass 行为的协议。
  - `StateLike`: 状态类型别名，可以是 TypedDict、dataclass 或 Pydantic BaseModel。

## 总结

`_internal` 模块是 LangGraph 框架的核心基础设施，为上层功能提供底层支持。通过这些内部模块的协作，LangGraph 能够实现状态管理、异步执行、配置处理、缓存机制等关键功能。虽然这些模块不对外公开，但它们是 LangGraph 框架正常运行的基础。