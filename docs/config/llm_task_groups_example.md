# LLM任务组配置示例

## 任务组配置文件结构

```yaml
# configs/llms/groups/_task_groups.yaml
task_groups:
  # 主模型组 - 快速响应任务
  fast_group:
    description: "快速响应任务组 - 适用于需要快速响应的简单任务"
    echelon1:
      models: ["openai-gpt4", "anthropic-claude-3-opus"]
      concurrency_limit: 10
      rpm_limit: 100
      priority: 1
      timeout: 30
      max_retries: 3
    echelon2:
      models: ["openai-gpt4-turbo", "anthropic-claude-3-sonnet"]
      concurrency_limit: 20
      rpm_limit: 200
      priority: 2
      timeout: 25
      max_retries: 3
    echelon3:
      models: ["openai-gpt3.5-turbo", "anthropic-claude-3-haiku"]
      concurrency_limit: 50
      rpm_limit: 500
      priority: 3
      timeout: 20
      max_retries: 2
    fallback_strategy: "echelon_down"
    circuit_breaker:
      failure_threshold: 5
      recovery_time: 60
      half_open_requests: 1

  # 主模型组 - 规划任务
  plan_group:
    description: "规划任务组 - 适用于复杂的规划和策略制定"
    echelon1:
      models: ["openai-gpt4", "anthropic-claude-3-opus"]
      concurrency_limit: 5
      rpm_limit: 50
      priority: 1
      timeout: 60
      max_retries: 5
    echelon2:
      models: ["openai-gpt4-turbo", "anthropic-claude-3-sonnet"]
      concurrency_limit: 10
      rpm_limit: 100
      priority: 2
      timeout: 45
      max_retries: 4
    echelon3:
      models: ["openai-gpt3.5-turbo", "anthropic-claude-3-haiku"]
      concurrency_limit: 20
      rpm_limit: 200
      priority: 3
      timeout: 35
      max_retries: 3
    fallback_strategy: "echelon_down"

  # 主模型组 - 思考任务
  thinking_group:
    description: "思考任务组 - 适用于需要深度思考的分析任务"
    echelon1:
      models: ["openai-gpt4", "anthropic-claude-3-opus"]
      concurrency_limit: 3
      rpm_limit: 30
      priority: 1
      timeout: 120
      max_retries: 5
      thinking_config:
        enabled: true
        budget_tokens: 4000
    echelon2:
      models: ["openai-gpt4-turbo", "anthropic-claude-3-sonnet"]
      concurrency_limit: 8
      rpm_limit: 80
      priority: 2
      timeout: 90
      max_retries: 4
    echelon3:
      models: ["openai-gpt3.5-turbo", "anthropic-claude-3-haiku"]
      concurrency_limit: 15
      rpm_limit: 150
      priority: 3
      timeout: 60
      max_retries: 3
    fallback_strategy: "echelon_down"

  # 主模型组 - 执行任务
  execute_group:
    description: "执行任务组 - 适用于工具调用和指令执行"
    echelon1:
      models: ["openai-gpt4", "anthropic-claude-3-sonnet"]
      concurrency_limit: 15
      rpm_limit: 150
      priority: 1
      timeout: 45
      max_retries: 4
      function_calling: "required"
    echelon2:
      models: ["openai-gpt4-turbo", "gemini-pro"]
      concurrency_limit: 25
      rpm_limit: 250
      priority: 2
      timeout: 35
      max_retries: 3
      function_calling: "auto"
    echelon3:
      models: ["openai-gpt3.5-turbo", "gemini-pro"]
      concurrency_limit: 40
      rpm_limit: 400
      priority: 3
      timeout: 25
      max_retries: 2
      function_calling: "auto"
    fallback_strategy: "echelon_down"

  # 主模型组 - 审核任务
  review_group:
    description: "审核任务组 - 适用于内容审核和质量检查"
    echelon1:
      models: ["openai-gpt4", "anthropic-claude-3-opus"]
      concurrency_limit: 8
      rpm_limit: 80
      priority: 1
      timeout: 45
      max_retries: 4
    echelon2:
      models: ["openai-gpt4-turbo", "anthropic-claude-3-sonnet"]
      concurrency_limit: 15
      rpm_limit: 150
      priority: 2
      timeout: 35
      max_retries: 3
    echelon3:
      models: ["openai-gpt3.5-turbo", "anthropic-claude-3-haiku"]
      concurrency_limit: 25
      rpm_limit: 250
      priority: 3
      timeout: 25
      max_retries: 2
    fallback_strategy: "echelon_down"

  # 主模型组 - 高并发任务
  high_payload_group:
    description: "高并发任务组 - 适用于高并发场景"
    echelon1:
      models: ["openai-gpt4-turbo", "anthropic-claude-3-sonnet"]
      concurrency_limit: 100
      rpm_limit: 1000
      priority: 1
      timeout: 20
      max_retries: 2
    echelon2:
      models: ["openai-gpt3.5-turbo", "gemini-pro"]
      concurrency_limit: 200
      rpm_limit: 2000
      priority: 2
      timeout: 15
      max_retries: 2
    echelon3:
      models: ["gemini-pro", "anthropic-claude-3-haiku"]
      concurrency_limit: 500
      rpm_limit: 5000
      priority: 3
      timeout: 10
      max_retries: 1
    fallback_strategy: "provider_failover"

  # 小模型组 - 快速简单任务
  fast_small_group:
    description: "小模型快速任务组 - 适用于简单的快速任务"
    translation:
      models: ["openai-gpt3.5-turbo", "gemini-pro"]
      concurrency_limit: 100
      rpm_limit: 1000
      priority: 1
      timeout: 15
      max_retries: 2
      temperature: 0.3  # 翻译任务需要较低温度
    analysis:
      models: ["openai-gpt3.5-turbo", "anthropic-claude-3-haiku"]
      concurrency_limit: 80
      rpm_limit: 800
      priority: 2
      timeout: 20
      max_retries: 2
    execute:
      models: ["openai-gpt3.5-turbo", "gemini-pro"]
      concurrency_limit: 120
      rpm_limit: 1200
      priority: 3
      timeout: 10
      max_retries: 1
      response_format: "json"
      function_calling: "required"
    thinking:
      models: ["openai-gpt3.5-turbo", "anthropic-claude-3-haiku"]
      concurrency_limit: 50
      rpm_limit: 500
      priority: 4
      timeout: 30
      max_retries: 2
    high_payload:
      models: ["gemini-pro", "anthropic-claude-3-haiku"]
      concurrency_limit: 300
      rpm_limit: 3000
      priority: 5
      timeout: 8
      max_retries: 1
    fallback_strategy: "model_rotate"

# 轮询池配置
polling_pools:
  single_turn_pool:
    description: "单轮对话轮询池"
    task_groups: ["fast_group", "fast_small_group"]
    rotation_strategy: "round_robin"
    health_check_interval: 30
    failure_threshold: 3
    recovery_time: 60
    rate_limiting:
      enabled: true
      algorithm: "token_bucket"
      bucket_size: 1000
      refill_rate: 16.67  # 1000/60

  multi_turn_pool:
    description: "多轮对话轮询池"
    task_groups: ["thinking_group", "plan_group"]
    rotation_strategy: "least_recently_used"
    health_check_interval: 60
    failure_threshold: 2
    recovery_time: 120
    rate_limiting:
      enabled: true
      algorithm: "sliding_window"
      window_size: 60
      max_requests: 500

  high_concurrency_pool:
    description: "高并发轮询池"
    task_groups: ["high_payload_group", "fast_small_group.high_payload"]
    rotation_strategy: "weighted"
    health_check_interval: 15
    failure_threshold: 5
    recovery_time: 30
    rate_limiting:
      enabled: true
      algorithm: "token_bucket"
      bucket_size: 5000
      refill_rate: 83.33  # 5000/60

# 全局降级配置
global_fallback:
  enabled: true
  max_attempts: 3
  retry_delay: 1.0
  circuit_breaker:
    failure_threshold: 5
    recovery_time: 60
    half_open_requests: 1

# 并发控制配置
concurrency_control:
  enabled: true
  levels:
    - group_level:
        limit: 1000
        queue_size: 10000
    - echelon_level:
        limit: 300
        queue_size: 3000
    - model_level:
        limit: 100
        queue_size: 1000
    - node_level:
        limit: 50
        queue_size: 500

# 速率限制配置
rate_limiting:
  enabled: true
  algorithm: "token_bucket"  # token_bucket, sliding_window
  token_bucket:
    bucket_size: 10000
    refill_rate: 166.67  # 10000/60
  sliding_window:
    window_size: 60
    max_requests: 10000
```

## 节点配置示例

```yaml
# 工作流节点配置示例
workflow_nodes:
  planning_node:
    type: "llm"
    llm_group: "plan_group.echelon1"
    fallback_groups: ["plan_group.echelon2", "thinking_group.echelon1"]
    task_config:
      timeout: 120
      max_retries: 3
    concurrency_config:
      limit: 10
      queue_size: 100
    
  execution_node:
    type: "llm"
    llm_group: "execute_group.echelon2"
    task_type: "execute"
    fallback_groups: ["execute_group.echelon3", "fast_small_group.execute"]
    polling_pool: "high_concurrency_pool"
    
  thinking_node:
    type: "llm"
    llm_group: "thinking_group.echelon1"
    fallback_groups: ["thinking_group.echelon2"]
    thinking_config:
      enabled: true
      budget_tokens: 4000
    
  fast_response_node:
    type: "llm"
    llm_group: "fast_group.echelon3"
    polling_pool: "single_turn_pool"
    fallback_groups: ["fast_small_group.fast"]
```

## 使用示例

### 在代码中使用任务组

```python
# 获取任务组配置
task_group_config = config_manager.get_task_group_config("plan_group", "echelon1")

# 使用任务组创建LLM客户端
llm_client = llm_factory.create_client_from_group("plan_group.echelon1")

# 节点级别配置
node_config = {
    "type": "llm",
    "llm_group": "thinking_group.echelon1",
    "fallback_groups": ["thinking_group.echelon2"],
    "task_config": {
        "timeout": 120,
        "thinking_config": {"enabled": True}
    }
}
```

### 降级策略使用

```python
# 自动降级
try:
    result = await llm_client.call_with_group("plan_group.echelon1", prompt)
except LLMError as e:
    # 自动尝试降级组
    result = await llm_client.call_with_fallback_groups(
        ["plan_group.echelon2", "fast_group.echelon1"], 
        prompt
    )