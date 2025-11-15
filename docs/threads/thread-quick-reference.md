# Thread层快速参考指南

## 概述

本文档提供了Thread层核心功能的快速参考，包括常用API、使用模式和最佳实践。

## 核心API速查

### Thread管理

#### 创建Thread
```python
# 从配置文件创建
thread_id = await thread_manager.create_thread_from_config(
    "configs/workflows/plan_execute_workflow.yaml",
    metadata={"purpose": "data_analysis"}
)

# 从graph_id创建
thread_id = await thread_manager.create_thread(
    graph_id="default_graph",
    metadata={"purpose": "general"}
)
```

#### 执行工作流
```python
# 同步执行
result = await thread_manager.execute_workflow(
    thread_id,
    config={"temperature": 0.7},
    initial_state=initial_state
)

# 流式执行
async for state in await thread_manager.stream_workflow(thread_id, config):
    print(f"状态: {state}")
```

#### 状态管理
```python
# 获取状态
state = await thread_manager.get_thread_state(thread_id)

# 更新状态
success = await thread_manager.update_thread_state(thread_id, new_state)

# 获取历史
history = await thread_manager.get_thread_history(thread_id, limit=10)
```

#### 查询Thread
```python
# 获取Thread信息
info = await thread_manager.get_thread_info(thread_id)

# 列出所有Thread
threads = await thread_manager.list_threads(
    filters={"status": "active"},
    limit=20
)

# 检查Thread是否存在
exists = await thread_manager.thread_exists(thread_id)
```

### Session管理

#### 创建会话
```python
user_request = UserRequest(
    request_id="req_001",
    user_id="user_123",
    content="分析数据并生成报告",
    timestamp=datetime.now()
)

session_id = await session_manager.create_session(user_request)
```

#### 协调Thread
```python
thread_configs = [{
    "name": "data_analysis",
    "config_path": "configs/workflows/plan_execute_workflow.yaml",
    "initial_state": {"messages": [{"role": "user", "content": "分析任务"}]}
}]

thread_ids = await session_manager.coordinate_threads(session_id, thread_configs)
```

#### 在会话中执行
```python
# 执行工作流
result = await session_manager.execute_workflow_in_session(
    session_id, "data_analysis", config={"temperature": 0.7}
)

# 流式执行
async for state in session_manager.stream_workflow_in_session(
    session_id, "data_analysis", config={"temperature": 0.7}
):
    print(f"当前步骤: {state.get('current_step')}")
```

### 高级功能

#### Thread分支
```python
branch_thread_id = await thread_manager.fork_thread(
    source_thread_id="original_thread",
    checkpoint_id="latest",
    branch_name="experimental_branch",
    metadata={"experiment": "try_different_temperature"}
)
```

#### Thread快照
```python
# 创建快照
snapshot_id = await thread_manager.create_thread_snapshot(
    thread_id,
    snapshot_name="before_major_change",
    description="执行重要更改前的状态快照"
)

# 回滚到快照
success = await thread_manager.rollback_thread(thread_id, checkpoint_id)
```

#### Thread协作
```python
# 状态共享
await collaboration_manager.share_thread_state(
    source_thread_id="analysis_thread",
    target_thread_id="report_thread",
    checkpoint_id="latest",
    permissions={"read": True, "write": False}
)

# 创建共享会话
collaboration_id = await collaboration_manager.create_shared_session(
    thread_ids=["thread1", "thread2", "thread3"],
    session_config={"permissions": {"sync": True}}
)

# 同步状态
await collaboration_manager.sync_thread_states(
    thread_ids=["thread1", "thread2"],
    sync_strategy="bidirectional"
)
```

#### 高级查询
```python
# 多条件搜索
threads = await query_manager.search_threads({
    "status": "active",
    "created_after": datetime.now() - timedelta(days=7),
    "metadata": {"project": "data_analysis"}
})

# 获取统计信息
stats = await query_manager.get_thread_statistics()
```

## 常用使用模式

### 模式1: 基本工作流执行

```python
async def basic_workflow_execution():
    # 创建组件
    components = create_development_stack(Path("./storage"))
    session_manager = components["session_manager"]
    
    # 创建会话
    user_request = UserRequest(
        request_id="req_001",
        user_id="user_123",
        content="执行数据分析任务",
        timestamp=datetime.now()
    )
    session_id = await session_manager.create_session(user_request)
    
    # 创建Thread
    thread_configs = [{
        "name": "analysis",
        "config_path": "configs/workflows/data_analysis.yaml",
        "initial_state": {"data": "input_data"}
    }]
    thread_ids = await session_manager.coordinate_threads(session_id, thread_configs)
    
    # 执行工作流
    result = await session_manager.execute_workflow_in_session(
        session_id, "analysis", config={"temperature": 0.7}
    )
    
    return result
```

### 模式2: 流式执行与监控

```python
async def streaming_workflow_with_monitoring():
    components = create_development_stack(Path("./storage"))
    session_manager = components["session_manager"]
    
    # 创建会话和Thread（同上）
    # ...
    
    # 流式执行
    step_count = 0
    async for state in session_manager.stream_workflow_in_session(
        session_id, "analysis", config={"temperature": 0.7}
    ):
        step_count += 1
        current_step = state.get('current_step', 'unknown')
        print(f"步骤 {step_count}: {current_step}")
        
        # 监控错误
        if state.get('status') == 'error':
            print(f"执行错误: {state.get('error_message')}")
            break
            
        # 监控进度
        progress = state.get('progress', 0)
        print(f"进度: {progress}%")
```

### 模式3: 实验性分支执行

```python
async def experimental_branch_execution():
    components = create_development_stack(Path("./storage"))
    thread_manager = components["thread_manager"]
    
    # 创建主Thread
    main_thread_id = await thread_manager.create_thread_from_config(
        "configs/workflows/data_analysis.yaml"
    )
    
    # 执行主Thread
    main_result = await thread_manager.execute_workflow(
        main_thread_id, config={"temperature": 0.7}
    )
    
    # 创建实验分支
    branch_thread_id = await thread_manager.fork_thread(
        main_thread_id,
        checkpoint_id="latest",
        branch_name="high_temp_experiment",
        metadata={"experiment": "temperature_0.9"}
    )
    
    # 在分支中执行不同配置
    branch_result = await thread_manager.execute_workflow(
        branch_thread_id, config={"temperature": 0.9}
    )
    
    # 比较结果
    comparison = compare_results(main_result, branch_result)
    return comparison
```

### 模式4: 多Thread协作

```python
async def multi_thread_collaboration():
    components = create_development_stack(Path("./storage"))
    session_manager = components["session_manager"]
    collaboration_manager = components["collaboration_manager"]
    
    # 创建会话
    user_request = UserRequest(
        request_id="req_002",
        user_id="user_123",
        content="执行数据分析并生成报告",
        timestamp=datetime.now()
    )
    session_id = await session_manager.create_session(user_request)
    
    # 创建多个Thread
    thread_configs = [
        {
            "name": "data_analysis",
            "config_path": "configs/workflows/data_analysis.yaml",
            "initial_state": {"data": "input_data"}
        },
        {
            "name": "report_generation",
            "config_path": "configs/workflows/report_generation.yaml",
            "initial_state": {"template": "standard"}
        }
    ]
    thread_ids = await session_manager.coordinate_threads(session_id, thread_configs)
    
    # 执行分析Thread
    analysis_result = await session_manager.execute_workflow_in_session(
        session_id, "data_analysis"
    )
    
    # 共享分析结果到报告Thread
    await collaboration_manager.share_thread_state(
        source_thread_id=thread_ids["data_analysis"],
        target_thread_id=thread_ids["report_generation"],
        checkpoint_id="latest",
        permissions={"read": True, "write": True}
    )
    
    # 执行报告生成
    report_result = await session_manager.execute_workflow_in_session(
        session_id, "report_generation"
    )
    
    return report_result
```

## 错误处理模式

### 基本错误处理

```python
async def basic_error_handling():
    try:
        result = await session_manager.execute_workflow_in_session(
            session_id, "analysis", config={"temperature": 0.7}
        )
        return result
    except ValueError as e:
        print(f"参数错误: {e}")
        # 处理参数错误
    except RuntimeError as e:
        print(f"运行时错误: {e}")
        # 处理运行时错误
    except Exception as e:
        print(f"未知错误: {e}")
        # 处理未知错误
```

### 错误恢复

```python
async def error_recovery():
    try:
        result = await session_manager.execute_workflow_in_session(
            session_id, "analysis", config={"temperature": 0.7}
        )
    except Exception as e:
        # 查看错误交互记录
        interactions = await session_manager.get_interaction_history(session_id)
        error_interactions = [i for i in interactions if "error" in i.interaction_type]
        
        # 分析错误原因
        if error_interactions:
            last_error = error_interactions[-1]
            error_type = last_error.metadata.get("error_type")
            
            # 根据错误类型采取不同恢复策略
            if error_type == "TimeoutError":
                # 增加超时时间重试
                result = await session_manager.execute_workflow_in_session(
                    session_id, "analysis", 
                    config={"temperature": 0.7, "timeout": 120}
                )
            elif error_type == "ValidationError":
                # 修复参数后重试
                fixed_config = fix_validation_error(last_error.metadata)
                result = await session_manager.execute_workflow_in_session(
                    session_id, "analysis", config=fixed_config
                )
            else:
                # 创建快照并回滚
                thread_id = get_thread_id_from_session(session_id, "analysis")
                snapshot_id = await thread_manager.create_thread_snapshot(
                    thread_id, "before_error", "错误前状态"
                )
                # 尝试回滚到上一个稳定状态
                await thread_manager.rollback_thread(thread_id, "previous_checkpoint")
```

## 性能优化技巧

### 1. 批量操作

```python
# 推荐：批量创建Thread
thread_configs = [
    {"name": "task1", "config_path": "config1.yaml"},
    {"name": "task2", "config_path": "config2.yaml"},
    {"name": "task3", "config_path": "config3.yaml"}
]
thread_ids = await session_manager.coordinate_threads(session_id, thread_configs)

# 避免：逐个创建Thread
# for config in thread_configs:
#     thread_id = await thread_manager.create_thread_from_config(config["config_path"])
```

### 2. 缓存管理

```python
# 定期清理缓存
await thread_manager.clear_graph_cache()

# 获取缓存信息
cache_info = await thread_manager.get_cache_info()
if cache_info["graph_cache_size"] > 100:
    await thread_manager.clear_graph_cache()
```

### 3. 资源清理

```python
async def cleanup_resources():
    # 清理旧Thread
    old_threads = await query_manager.search_threads({
        "created_before": datetime.now() - timedelta(days=30),
        "status": "completed"
    })
    
    for thread in old_threads:
        await thread_manager.delete_thread(thread["thread_id"])
    
    # 清理缓存
    await thread_manager.clear_graph_cache()
```

## 监控与调试

### 状态监控

```python
async def monitor_thread_status(thread_id):
    thread_info = await thread_manager.get_thread_info(thread_id)
    
    print(f"Thread ID: {thread_id}")
    print(f"状态: {thread_info['status']}")
    print(f"创建时间: {thread_info['created_at']}")
    print(f"更新时间: {thread_info['updated_at']}")
    print(f"Checkpoint数量: {thread_info['checkpoint_count']}")
    print(f"总步数: {thread_info['total_steps']}")
    
    # 检查错误
    if thread_info['status'] == 'error':
        print(f"错误信息: {thread_info.get('last_error', 'Unknown')}")
```

### 性能监控

```python
async def monitor_performance():
    stats = await query_manager.get_thread_statistics()
    
    print(f"总Thread数: {stats['total_threads']}")
    print(f"活跃Thread数: {stats['by_status']['active']}")
    print(f"完成Thread数: {stats['by_status']['completed']}")
    print(f"错误Thread数: {stats['by_status']['error']}")
    
    if 'performance' in stats:
        print(f"平均执行时间: {stats['performance']['avg_execution_time']}秒")
        print(f"成功率: {stats['performance']['success_rate']}%")
```

## 最佳实践

### 1. 资源管理
- 使用完Thread后清理缓存
- 定期清理旧的Thread和checkpoint
- 监控内存使用情况

### 2. 错误处理
- 捕获并记录所有异常
- 提供有意义的错误消息
- 实现适当的错误恢复机制

### 3. 性能优化
- 使用批量操作减少API调用
- 合理设置缓存大小
- 根据使用场景选择存储后端

### 4. 安全考虑
- 验证所有输入参数
- 实现适当的权限控制
- 记录关键操作日志

### 5. 可维护性
- 使用描述性的Thread名称
- 添加有意义的元数据
- 保持配置文件结构清晰

## 常见问题

### Q: 如何处理长时间运行的工作流？
A: 使用流式执行模式，定期检查状态，并实现适当的超时机制。

### Q: 如何比较不同配置的执行结果？
A: 使用Thread分支功能，从同一checkpoint创建多个分支，使用不同配置执行后比较结果。

### Q: 如何实现工作流的暂停和恢复？
A: 使用checkpoint机制保存状态，需要时从特定checkpoint恢复执行。

### Q: 如何优化大量Thread的性能？
A: 使用批量操作、合理设置缓存、定期清理不需要的Thread，考虑使用分布式架构。

### Q: 如何调试工作流执行问题？
A: 查看Thread历史、检查交互记录、使用日志记录、分析checkpoint状态。