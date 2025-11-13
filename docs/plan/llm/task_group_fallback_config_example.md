# 任务组降级配置示例

## 快速响应任务组配置示例

```yaml
# configs/llms/groups/fast_group.yaml
name: "fast_group"
description: "快速响应任务组 - 适用于需要快速响应的简单任务"

# 层级配置
echelon1:
  models: ["openai-gpt4", "anthropic-claude-3-opus"]
  concurrency_limit: 10
  rpm_limit: 100
  priority: 1
  timeout: 30
  max_retries: 3
  temperature: 0.7
  max_tokens: 2000

echelon2:
  models: ["openai-gpt4-turbo", "anthropic-claude-3-sonnet"]
  concurrency_limit: 20
  rpm_limit: 200
  priority: 2
  timeout: 25
  max_retries: 3
  temperature: 0.7
  max_tokens: 2000

echelon3:
  models: ["openai-gpt3.5-turbo", "anthropic-claude-3-haiku"]
  concurrency_limit: 极速响应
  rpm_limit: 500
  priority: 3
  timeout: 20
  max_retries: 2
  temperature: 0.7
  max极速响应: 1500

# 降级配置（新增）
fallback_config:
  strategy: "echelon_down"  # 层级降级策略
  fallback_groups: ["fast_group.echelon2", "fast_group.echelon3"]
  max_attempts: 3
  retry_delay: 1.0
  circuit_breaker:
    failure_threshold: 5
    recovery_time: 60
    half_open_requests: 1
```

## 思考任务组配置示例

```yaml
# configs/llms/groups/thinking_group.yaml
name: "thinking_group"
description: "思考任务组 - 适用于需要深度思考的分析任务"

# 层级配置
echelon1:
  models: ["openai-gpt4", "anthropic-claude-3-opus"]
  concurrency_limit: 3
  rpm_limit: 30
  priority: 1
  timeout: 120
  max_retries: 5
  temperature: 0.8
  max_tokens: 4000
  thinking_config:
    enabled: true
    budget_tokens: 4000

echelon2:
  models: ["openai-gpt4-turbo", "anthropic-claude-3-sonnet"]
  concurrency_limit: 8
  rpm极速响应: 80
  priority: 2
  timeout: 90
  max_retries: 4
  temperature: 0.8
  max_tokens: 3000
  thinking_config:
    enabled: true
    budget_tokens: 3000

echelon3:
  models: ["openai-gpt3.5-turbo", "anthropic-claude-3-haiku"]
  concurrency_limit: 15
  rpm_limit: 150
  priority: 3
  timeout: 60
  max_retries: 3
  temperature: 0.8
  max_tokens: 2000
  thinking_config:
    enabled: true
    budget_tokens: 2000

# 降级配置（新增）
fallback_config:
  strategy: "echelon_down"  # 层级降级
  fallback_groups: ["thinking_group.echelon2", "thinking_group.echelon3", "fast_group.echelon1"]
  max_attempts: 5  # 思考任务允许更多尝试
  retry_delay: 2.0  # 更长的重试延迟
  circuit_breaker:
    failure_threshold: 3  # 更敏感的熔断器
    recovery_time: 120
    half_open_requests: 1
```

## 规划任务组配置示例

```yaml
# configs/llms/groups/plan_group.yaml
name: "plan_group"
description: "规划任务组 - 适用于复杂的规划和策略制定"

# 层级配置
echelon1:
  models: ["openai-gpt4", "anthropic-claude-3-opus"]
  concurrency_limit: 5
  rpm_limit: 50
  priority: 1
  timeout: 180
  max_retries: 5
  temperature: 0.9
  max_tokens: 8000

echelon2:
  models: ["openai-gpt4-turbo", "anthropic-claude-3-sonnet"]
  concurrency_limit: 10
  rpm_limit: 100
  priority: 2
  timeout: 120
  max_retries: 4
  temperature: 0.9
  max_tokens: 6000

# 降级配置（新增）
fallback_config:
  strategy: "task_group_switch"  # 任务组切换策略
  fallback_groups: ["thinking_group.echelon1", "thinking_group.echelon2"]
  max_attempts: 2
  retry_delay: 3.0
  circuit_breaker:
    failure_threshold: 2
    recovery_time: 180
    half_open_requests: 1
```

## 任务专用轮询池配置示例

### 快速响应轮询池

```yaml
# configs/llms/polling_pools/fast_pool.yaml
name: "fast_pool"
description: "快速响应任务专用轮询池"
task_groups: ["fast_group"]  # 只包含快速响应任务组
rotation_strategy: "round_robin"
health_check_interval: 30
failure_threshold: 3
recovery_time: 60

# 轮询池专用降级策略
fallback_strategy: "instance_rotation"  # 直接从池中旋转实例
max_instance_attempts: 2  # 每个实例最多尝试2次
rate_limiting:
  enabled: true
  algorithm: "token_bucket"
  bucket_size: 1000
  refill_rate: 16.67
```

### 思考任务轮询池

```yaml
# configs/llms/polling_pools/thinking_pool.yaml
name: "thinking_pool"
description: "思考任务专用轮询池"
task_groups: ["thinking_group"]  # 只包含思考任务组
rotation_strategy: "least_recently_used"
health_check_interval: 60
failure_threshold: 2
recovery_time: 120

# 轮询池专用降级策略
fallback_strategy: "instance_rotation"
max_instance_attempts: 3  # 思考任务允许更多尝试
rate_limiting:
  enabled: true
  algorithm: "sliding_window"
  window_size: 60
  max_requests: 100
```

## 配置验证规则

### 任务组降级配置验证

1. **策略验证**：必须是支持的降级策略之一
   - `echelon_down`: 层级降级
   - `task_group_switch`: 任务组切换
   - `provider_failover`: 提供商故障转移

2. **降级组验证**：降级组必须存在且可访问
3. **尝试次数验证**：`max_attempts` 必须在 1-10 范围内
4. **延迟验证**：`retry_delay` 必须 ≥ 0

### 轮询池配置验证

1. **任务组唯一性**：每个轮询池只能包含一个任务组
2. **降级策略验证**：必须是轮询池支持的策略
   - `instance_rotation`: 实例旋转
   - `simple_retry`: 简单重试
3. **尝试次数验证**：`max_instance_attempts` 必须在 1-5 范围内

## 迁移工具示例

```python
# 迁移全局降级配置到任务组配置的工具
def migrate_global_fallback_to_task_groups():
    """将全局降级配置迁移到各个任务组"""
    global_config = load_global_fallback_config()
    
    task_groups = get_all_task_groups()
    for group in task_groups:
        if not hasattr(group, 'fallback_config'):
            # 为每个任务组添加降级配置
            group.fallback_config = {
                'strategy': 'echelon_down',
                'fallback_groups': get_default_fallback_groups(group.name),
                'max_attempts': global_config.get('max_attempts', 3),
                'retry_delay': global_config.get('retry_delay', 1.0),
                'circuit_breaker': global_config.get('circuit_breaker', {})
            }
            save_task_group_config(group)
```

## 使用示例

### 基于任务组降级的调用

```python
from src.infrastructure.llm import EnhancedFallbackManager

# 创建降级管理器
fallback_manager = EnhancedFallbackManager(task_group_manager, polling_pool_manager)

# 使用任务组专用降级
result = await fallback_manager.execute_with_task_group_fallback(
    primary_target="fast_group.echelon1",
    prompt="请快速回答这个问题"
)

# 使用特定降级组
result = await fallback_manager.execute_with_fallback(
    primary_target="thinking_group.echelon1",
    fallback_groups=["thinking_group.echelon2", "fast_group.echelon1"],
    prompt="请深入分析这个问题"
)
```

### 轮询池专用降级调用

```python
# 获取轮询池
fast_pool = polling_pool_manager.get_pool("fast_pool")

# 使用轮询池的简单降级
result = await fast_pool.call_llm_with_fallback(
    prompt="快速响应请求"
)
```

## 监控指标

### 任务组降级监控
- `task_group_fallback_success_rate`: 任务组降级成功率
- `task_group_fallback_latency`: 降级响应延迟
- `task_group_circuit_breaker_state`: 熔断器状态

### 轮询池监控
- `polling_pool_instance_rotation_count`: 实例旋转次数
- `polling_pool_health_status`: 池健康状态
- `polling_pool_utilization`: 池利用率