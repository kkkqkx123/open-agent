# langgraph/func/__init__.py 功能说明

## 概述

`langgraph/func/__init__.py` 文件提供了 LangGraph 的函数式 API，使开发者能够通过简单的函数定义和装饰器来构建复杂的工作流。该文件提供了两个核心装饰器：`@task` 和 `@entrypoint`，用于定义可重用的任务函数和工作流入口点。

## 核心功能

### 1. `@task` 装饰器

`@task` 装饰器用于定义 LangGraph 任务。任务是工作流中的基本执行单元，可以是同步或异步函数。

#### 特性：
- 支持 Python 3.11+ 的同步和异步函数
- 任务函数只能从 `@entrypoint` 或 `StateGraph` 内部调用
- 调用任务函数会返回一个 future 对象，便于并行化任务
- 当启用检查点时，函数输入和输出必须是可序列化的

#### 参数：
- `name`: 任务的可选名称，如果不提供则使用函数名
- `retry_policy`: 任务失败时的重试策略（或策略列表）
- `cache_policy`: 任务结果的缓存策略

#### 示例：
```python
from langgraph.func import entrypoint, task

@task
def add_one(a: int) -> int:
    return a + 1

@entrypoint()
def add_one(numbers: list[int]) -> list[int]:
    futures = [add_one(n) for n in numbers]
    results = [f.result() for f in futures]
    return results

# 调用入口点
add_one.invoke([1, 2, 3])  # 返回 [2, 3, 4]
```

### 2. `@entrypoint` 装饰器

`@entrypoint` 装饰器用于定义 LangGraph 工作流。它将普通函数转换为可执行的工作流图。

#### 特性：
- 支持同步和异步函数
- 函数必须接受一个参数作为输入（使用字典传递多个参数）
- 可以自动注入额外参数：`config`、`previous`、`runtime`
- 可与检查点、存储和缓存系统集成

#### 注入参数：
- `config`: 运行时配置对象（RunnableConfig）
- `previous`: 给定线程的前一个返回值（仅在提供检查点时可用）
- `runtime`: 包含当前运行信息的 Runtime 对象

#### 参数：
- `checkpointer`: 检查点保存器，用于持久化工作流状态
- `store`: 键值存储，可能支持语义搜索
- `cache`: 缓存系统
- `context_schema`: 运行时上下文的模式
- `cache_policy`: 工作流结果的缓存策略
- `retry_policy`: 工作流失败时的重试策略

#### 示例：
```python
import time
from langgraph.func import entrypoint, task
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

@task
def compose_essay(topic: str) -> str:
    time.sleep(1.0)  # 模拟慢速操作
    return f"An essay about {topic}"

@entrypoint(checkpointer=InMemorySaver())
def review_workflow(topic: str) -> dict:
    """管理生成和审查文章的工作流"""
    essay_future = compose_essay(topic)
    essay = essay_future.result()
    human_review = interrupt({
        "question": "Please provide a review",
        "essay": essay
    })
    return {
        "essay": essay,
        "review": human_review,
    }
```

### 3. `entrypoint.final` 类

`entrypoint.final` 是一个特殊类，允许在工作流中分离返回值和保存到检查点的值。

#### 用法：
- `value`: 返回给调用者的值
- `save`: 保存到检查点的值，将在下次调用时作为 `previous` 参数

#### 示例：
```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint

@entrypoint(checkpointer=InMemorySaver())
def my_workflow(
    number: int,
    *,
    previous: Any = None,
) -> entrypoint.final[int, int]:
    previous = previous or 0
    # 这将返回 previous 值给调用者，同时保存 2 * number 到检查点
    # 该值将在下次调用时用于 previous 参数
    return entrypoint.final(value=previous, save=2 * number)
```

## 内部实现

- `_TaskFunction` 类：包装任务函数，处理重试和缓存策略
- `entrypoint` 类：装饰器类，将函数转换为 Pregel 图
- 与 LangGraph 的其他组件（通道、检查点、存储等）紧密集成

## 使用场景

1. **并行任务处理**：通过 future 对象轻松并行化任务
2. **工作流编排**：组合多个任务函数创建复杂工作流
3. **状态管理**：通过检查点系统管理长期运行的工作流状态
4. **中断和恢复**：支持工作流中断和恢复机制
5. **缓存和重试**：内置缓存和重试策略，提高可靠性