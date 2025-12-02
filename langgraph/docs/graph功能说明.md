# langgraph/graph 模块功能说明

`langgraph/graph` 模块是 LangGraph 库的核心组件，用于构建和管理有状态的图结构，使开发者能够创建复杂的工作流和状态机。

## 模块结构

```text
langgraph/graph/
├── __init__.py        # 模块入口点，导出主要类和函数
├── _branch.py         # 分支逻辑的内部实现
├── _node.py           # 节点定义和规范
├── message.py         # 消息图和消息处理功能
├── state.py           # 状态图的主要实现
└── ui.py              # UI 消息处理
```

## 核心功能

### 1. StateGraph（状态图）
`StateGraph` 是该模块的核心类，用于创建节点间通过读写共享状态进行通信的图结构。每个状态键可以有选择地用一个聚合函数进行注解，该函数将用于聚合从多个节点接收的该键的值。

**主要特性：**
- 节点通信：节点通过共享状态进行通信
- 状态聚合：支持使用聚合函数合并多个节点的输出
- 类型安全：支持类型注解和验证
- 依赖管理：自动处理节点间的依赖关系

**使用示例：**
```python
from typing_extensions import Annotated, TypedDict
from langgraph.graph import StateGraph

def reducer(a: list, b: int | None) -> list:
    if b is not None:
        return a + [b]
    return a

class State(TypedDict):
    x: Annotated[list, reducer]

graph = StateGraph(state_schema=State)

def node(state: State) -> dict:
    x = state["x"][-1]
    next_value = x + 1
    return {"x": next_value}

graph.add_node("A", node)
graph.set_entry_point("A")
graph.set_finish_point("A")
```

### 2. 节点管理

**添加节点：**
- `add_node()`：向图中添加新节点
- `add_sequence()`：按顺序添加节点序列

**节点类型支持：**
- 函数节点
- Runnable 对象
- 支持配置参数、存储、缓存策略的节点

### 3. 边缘管理

**边的类型：**
- `add_edge()`：添加有向边
- `add_conditional_edges()`：添加条件边
- `add_sequence()`：创建节点序列

**分支功能：**
- 条件分支：根据节点输出动态选择下一个执行节点
- 支持返回多个目标节点
- 支持异步路径函数

### 4. 消息处理

**MessagesState：**
预定义的包含消息列表状态的类型字典，使用 `add_messages` 作为聚合函数。

**add_messages 函数：**
- 合并两个消息列表
- 通过 ID 更新现有消息
- 支持 OpenAI 消息格式

### 5. MessageGraph（已弃用）
`MessageGraph` 是 `StateGraph` 的子类，其整个状态是单个追加式消息列表。注意：此功能已在 1.0 版本中弃用，将在 2.0 中移除。

## 文件说明

### `_branch.py`
内部分支逻辑实现，包含：
- `BranchSpec`：分支规范类
- 条件路由逻辑
- 路径映射和类型推断

### `_node.py`
节点定义和规范，包含：
- `StateNode`：节点接口定义
- `StateNodeSpec`：节点规范数据类
- 各种节点类型协议（带配置、带写入器、带存储等）

### `message.py`
消息处理功能，包含：
- `add_messages`：消息聚合函数
- `MessagesState`：消息状态类型
- `MessageGraph`：已弃用的消息图类
- `push_message`：手动推送消息功能

### `state.py`
状态图的主要实现，包含：
- `StateGraph`：核心状态图类
- `CompiledStateGraph`：编译后的状态图
- 通道管理和状态聚合
- 验证和编译逻辑
- 节点和边的连接逻辑

### `ui.py`
UI 消息处理，包含：
- `UIMessage`：UI 消息类型定义
- `RemoveUIMessage`：删除 UI 消息类型
- `push_ui_message`：推送 UI 消息
- `delete_ui_message`：删除 UI 消息
- `ui_message_reducer`：UI 消息聚合函数

## 高级功能

### 上下文模式
支持通过 `context_schema` 参数定义运行时上下文，可用于暴露用户 ID、数据库连接等不可变上下文数据。

### 缓存和重试策略
- `retry_policy`：节点重试策略
- `cache_policy`：节点缓存策略

### 中断和检查点
- 支持在节点执行前或执行后中断
- 提供检查点保存和恢复功能

### 图验证
- 自动验证图的结构完整性
- 检查节点和边的有效性
- 验证入口点和终点配置

## 总结

`langgraph/graph` 模块提供了构建复杂有状态工作流的完整框架，支持多种节点类型、条件分支、消息传递和状态管理，是 LangGraph 库中最重要的模块之一，为开发者提供了构建 AI 应用的强大工具集。