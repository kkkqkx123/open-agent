# 增强降级管理器集成指南

## 概述

本文档介绍了如何在 Modular Agent Framework 中集成和使用增强降级管理器（Enhanced Fallback Manager）。增强降级管理器提供了更高级的降级策略，包括任务组管理、轮询池管理和熔断器功能。

## 架构说明

### 传统降级管理器 vs 增强降级管理器

| 特性 | 传统降级管理器 | 增强降级管理器 |
|------|----------------|----------------|
| 降级策略 | 顺序、优先级、并行 | 任务组、轮询池、熔断器 |
| 配置方式 | 模型列表 | 任务组层级配置 |
| 熔断器支持 | 无 | 有 |
| 监控能力 | 基础统计 | 详细统计和历史记录 |
| 扩展性 | 有限 | 高度可扩展 |

## 集成方式

### 1. 使用 FallbackClientWrapper

`FallbackClientWrapper` 现在支持两种降级管理器：

```python
from src.infrastructure.llm.fallback_client import FallbackClientWrapper
from src.infrastructure.llm.task_group_manager import TaskGroupManager
from src.infrastructure.llm.polling_pool import PollingPoolManager

# 使用传统降级管理器（默认）
fallback_client = FallbackClientWrapper(
    primary_client=primary_client,
    fallback_models=["gpt-3.5-turbo", "claude-instant"],
    strategy_type="sequential",
    max_attempts=3
)

# 使用增强降级管理器
task_group_manager = TaskGroupManager()
polling_pool_manager = PollingPoolManager()

fallback_client = FallbackClientWrapper(
    primary_client=primary_client,
    fallback_models=[],  # 不再需要指定降级模型列表
    use_enhanced_fallback=True,
    task_group_manager=task_group_manager,
    polling_pool_manager=polling_pool_manager
)
```

### 2. 配置文件支持

在配置文件中启用增强降级管理器：

```yaml
# configs/llms/provider/openai/openai-gpt4.yaml
model_type: openai
model_name: gpt-4
provider: openai

# 启用增强降级管理器
enhanced_fallback:
  enabled: true
  task_group: "fast_group"
  fallback_groups:
    - "medium_group"
    - "slow_group"
```

## 使用示例

### 1. 基本使用

```python
# 创建任务组管理器
task_group_manager = TaskGroupManager()
task_group_manager.add_group("fast_group", ["gpt-4-turbo", "claude-3-opus"])
task_group_manager.add_group("medium_group", ["gpt-4", "claude-3-sonnet"])
task_group_manager.add_group("slow_group", ["gpt-3.5-turbo"])

# 创建轮询池管理器（可选）
polling_pool_manager = PollingPoolManager()
polling_pool_manager.create_pool("fast_pool", ["gpt-4-turbo", "claude-3-opus"], "round_robin")

# 创建增强降级客户端
fallback_client = FallbackClientWrapper(
    primary_client=primary_client,
    fallback_models=[],
    use_enhanced_fallback=True,
    task_group_manager=task_group_manager,
    polling_pool_manager=polling_pool_manager
)

# 使用增强降级客户端
messages = [HumanMessage(content="解释量子计算的概念")]
response = await fallback_client.generate_async(messages)
```

### 2. 高级使用

```python
# 指定主任务组和降级组
response = await fallback_client.generate_async(
    messages,
    primary_target="fast_group",
    fallback_groups=["medium_group", "slow_group"]
)

# 获取降级统计信息
stats = fallback_client.get_fallback_stats()
print(f"成功率: {stats['success_rate']:.2%}")
print(f"平均响应时间: {stats['avg_response_time']:.2f}s")

# 重置统计信息
fallback_client.reset_fallback_stats()
```

## 配置说明

### 任务组配置

任务组允许将模型按性能和成本分组：

```yaml
task_group_levels:
  fast_group:
    models:
      - "gpt-4-turbo"
      - "claude-3-opus"
    timeout: 30
    max_retries: 2
  
  medium_group:
    models:
      - "gpt-4"
      - "claude-3-sonnet"
    timeout: 60
    max_retries: 3
```

### 轮询池配置

轮询池提供负载均衡功能：

```yaml
polling_pool_config:
  enabled: true
  pools:
    fast_pool:
      models:
        - "gpt-4-turbo"
        - "claude-3-opus"
      strategy: "round_robin"
      timeout: 30
```

### 熔断器配置

熔断器防止对已知故障的服务进行无效调用：

```yaml
strategy_config:
  circuit_breaker:
    failure_threshold: 5    # 连续失败5次后开启熔断器
    recovery_time: 60       # 60秒后尝试半开状态
    failure_rate_threshold: 0.5  # 失败率超过50%时开启熔断器
```

## 监控和统计

增强降级管理器提供详细的监控和统计功能：

```python
# 获取统计信息
stats = fallback_client.get_fallback_stats()
print(f"总尝试次数: {stats['total_attempts']}")
print(f"成功次数: {stats['successful_attempts']}")
print(f"成功率: {stats['success_rate']:.2%}")
print(f"最常用策略: {stats['most_used_strategy']}")

# 获取降级历史
history = fallback_client.get_fallback_sessions(limit=10)
for attempt in history:
    print(f"尝试 {attempt.attempt_number}: {attempt.target} - {'成功' if attempt.success else '失败'}")

# 获取熔断器状态
circuit_breaker_status = fallback_client.enhanced_fallback_manager.get_circuit_breaker_status()
for target, status in circuit_breaker_status.items():
    print(f"目标 {target}: 状态 {status['state']}, 失败次数 {status['failure_count']}")
```

## 最佳实践

### 1. 任务组设计

- 将模型按响应时间和成本分组
- 为每个组设置合适的超时和重试参数
- 定期评估和调整组配置

### 2. 熔断器配置

- 根据服务的稳定性调整失败阈值
- 设置合理的恢复时间
- 监控熔断器状态并及时调整

### 3. 监控和告警

- 定期检查成功率和响应时间
- 设置合理的告警阈值
- 分析降级模式以优化配置

## 迁移指南

### 从传统降级管理器迁移

1. 更新配置文件以启用增强降级管理器
2. 创建任务组管理器并配置任务组
3. （可选）创建轮询池管理器
4. 更新代码以使用新的 `FallbackClientWrapper` 构造函数

```python
# 旧代码
fallback_client = FallbackClientWrapper(
    primary_client=primary_client,
    fallback_models=["gpt-3.5-turbo", "claude-instant"],
    strategy_type="sequential"
)

# 新代码
task_group_manager = TaskGroupManager()
task_group_manager.add_group("primary_group", ["gpt-4-turbo"])
task_group_manager.add_group("fallback_group", ["gpt-3.5-turbo", "claude-instant"])

fallback_client = FallbackClientWrapper(
    primary_client=primary_client,
    fallback_models=[],
    use_enhanced_fallback=True,
    task_group_manager=task_group_manager
)
```

## 故障排除

### 常见问题

1. **任务组未找到**
   - 确保任务组管理器已正确初始化
   - 检查任务组名称是否正确

2. **熔断器始终开启**
   - 检查目标服务是否正常运行
   - 调整熔断器配置参数

3. **降级不生效**
   - 确保 `use_enhanced_fallback` 设置为 `True`
   - 检查任务组配置是否正确

### 日志和调试

启用详细日志以帮助调试：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

查看日志输出以了解降级过程的详细信息。