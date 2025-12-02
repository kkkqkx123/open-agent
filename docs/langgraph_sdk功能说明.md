# LangGraph SDK 功能说明文档

## 概述

LangGraph SDK 是一个用于与 LangGraph API 交互的客户端库，提供异步和同步两种方式来管理助手、线程、运行和定时任务等资源。

## 主要功能

### 1. 异步和同步客户端

LangGraph SDK 提供了两种类型的客户端：

- **异步客户端** (`get_client`): 用于异步操作，适合高并发场景
- **同步客户端** (`get_sync_client`): 用于同步操作，适合简单脚本或不需要异步功能的场景

两种客户端都提供相同的 API 接口，只是调用方式不同。

### 2. 认证和授权系统

通过 `Auth` 类提供灵活的认证和授权机制：

- 支持自定义用户认证协议
- 提供细粒度的授权规则
- 支持全局、资源级别和操作级别的授权处理
- 提供多种内置的授权类型和异常处理

### 3. 核心资源管理

#### 3.1 助手管理 (AssistantsClient)

助手代表版本化的图配置，主要功能包括：

- 创建、更新、删除助手
- 获取助手的图结构和模式
- 搜索和计数助手
- 管理助手版本

#### 3.2 线程管理 (ThreadsClient)

线程用于保持图在多个交互中的状态，主要功能包括：

- 创建、更新、删除线程
- 获取和更新线程状态
- 搜索和计数线程
- 获取线程历史记录
- 复制线程

#### 3.3 运行管理 (RunsClient)

运行代表单次图调用，主要功能包括：

- 创建和流式处理运行
- 等待运行完成并获取结果
- 列出、获取、取消和删除运行
- 加入运行并获取最终状态
- 批量创建运行

#### 3.4 定时任务管理 (CronClient)

定时任务用于定期执行图，主要功能包括：

- 为特定线程创建定时任务
- 创建全局定时任务
- 搜索和计数定时任务
- 删除定时任务

#### 3.5 存储管理 (StoreClient)

存储系统用于跨图执行持久化数据，主要功能包括：

- 存储、获取和删除项目
- 搜索命名空间中的项目
- 列出命名空间
- 支持TL（生存时间）管理

### 4. 数据模型

通过 `schema.py` 定义了与 API 交互的所有数据模型，包括：

- 运行状态和线程状态枚举
- 助手、线程、运行等核心数据结构
- 图模式和配置模型
- 流式传输的数据部分模型
- 命令和发送模型

### 5. SSE 流处理

通过 `sse.py` 模块处理服务器发送事件流，支持：

- 实时数据流传输
- 断线重连机制
- 事件解析和解码

## 使用示例

### 异步客户端使用

```python
from langgraph_sdk import get_client

# 获取异步客户端
client = get_client(url="http://localhost:8123")

# 创建助手
assistant = await client.assistants.create(graph_id="agent")

# 创建线程
thread = await client.threads.create()

# 运行助手
run = await client.runs.create(
    thread_id=thread["thread_id"],
    assistant_id=assistant["assistant_id"],
    input={"messages": [{"role": "user", "content": "Hello!"}]}
)
```

### 同步客户端使用

```python
from langgraph_sdk import get_sync_client

# 获取同步客户端
client = get_sync_client(url="http://localhost:8123")

# 创建助手
assistant = client.assistants.create(graph_id="agent")

# 创建线程
thread = client.threads.create()

# 运行助手
run = client.runs.create(
    thread_id=thread["thread_id"],
    assistant_id=assistant["assistant_id"],
    input={"messages": [{"role": "user", "content": "Hello!"}]}
)
```

## 高级功能

### 认证和授权配置

```python
from langgraph_sdk import Auth

auth = Auth()

# 注册认证处理程序
@auth.authenticate
async def authenticate(authorization: str) -> str:
    # 实现认证逻辑
    user_id = verify_token(authorization)
    return user_id

# 注册授权处理程序
@auth.on.threads.create
async def authorize_thread_create(ctx, value):
    # 实现线程创建授权逻辑
    return True
```

### 流式处理

```python
# 流式处理运行结果
async for chunk in client.runs.stream(
    thread_id=thread_id,
    assistant_id=assistant_id,
    input={"messages": [{"role": "user", "content": "Hello!"}]},
    stream_mode=["values", "messages", "events"]
):
    print(chunk)
```

## 错误处理

SDK 提供了完善的错误处理机制，包括：

- HTTP 状态错误处理
- 连接错误处理
- 认证和授权错误处理
- 自定义异常类型

## 总结

LangGraph SDK 提供了一套完整的工具来与 LangGraph API 进行交互，支持异步和同步操作，具有强大的认证授权系统，以及对助手、线程、运行和定时任务等核心资源的全面管理功能。