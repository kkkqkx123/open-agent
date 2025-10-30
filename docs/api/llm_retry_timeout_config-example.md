# LLM API 重试和超时配置

## 概述

本项目支持对 LLM API 调用的重试和超时行为进行精细化配置。这些配置项允许用户根据具体需求调整 API 调用的容错性和性能表现。

## 配置层级

配置系统采用分层结构，支持以下层级的配置：

1. **全局配置** - 在 `configs/global.yaml` 中定义
2. **模型组配置** - 在 `configs/llms/_group.yaml` 中定义
3. **具体模型配置** - 在 `configs/llms/*.yaml` 中定义

配置继承遵循 "具体模型 > 模型组 > 全局" 的优先级顺序。

## 重试配置 (RetryTimeoutConfig)

### 配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `max_retries` | int | 3 | 最大重试次数 |
| `base_delay` | float | 1.0 | 基础延迟时间（秒） |
| `max_delay` | float | 60.0 | 最大延迟时间（秒） |
| `jitter` | bool | True | 是否添加随机抖动 |
| `exponential_base` | float | 2.0 | 指数退避基数 |
| `retry_on_status_codes` | List[int] | [429, 500, 502, 503, 504] | 需要重试的HTTP状态码 |
| `retry_on_errors` | List[str] | ["timeout", "rate_limit", "service_unavailable"] | 需要重试的错误类型 |

### 配置示例

```yaml
retry_config:
  max_retries: 5
  base_delay: 2.0
  max_delay: 120.0
  jitter: true
  exponential_base: 2.5
  retry_on_status_codes:
    - 429  # Rate Limit
    - 500  # Internal Server Error
    - 502  # Bad Gateway
    - 503  # Service Unavailable
    - 504  # Gateway Timeout
  retry_on_errors:
    - "timeout"
    - "rate_limit"
    - "service_unavailable"
    - "insufficient_quota"
```

## 超时配置 (TimeoutConfig)

### 配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `request_timeout` | int | 30 | 请求总超时时间（秒） |
| `connect_timeout` | int | 10 | 连接超时时间（秒） |
| `read_timeout` | int | 30 | 读取超时时间（秒） |
| `write_timeout` | int | 30 | 写入超时时间（秒） |

### 配置示例

```yaml
timeout_config:
  request_timeout: 60
  connect_timeout: 15
  read_timeout: 60
  write_timeout: 60
```

## 配置文件示例

### 全局配置 (configs/global.yaml)

```yaml
llm:
  default_timeout: 30
  default_max_retries: 3
  retry_config:
    base_delay: 1.0
    max_delay: 60.0
    jitter: true
    exponential_base: 2.0
    retry_on_status_codes: [429, 500, 502, 503, 504]
    retry_on_errors: ["timeout", "rate_limit", "service_unavailable"]
  timeout_config:
    request_timeout: 30
    connect_timeout: 10
    read_timeout: 30
    write_timeout: 30
  performance:
    max_concurrent_requests: 10
    request_queue_size: 100
    connection_pool_size: 20
    connection_keep_alive: true
```

### 模型组配置 (configs/llms/_group.yaml)

```yaml
openai:
  model_type: openai
  base_url: ${OPENAI_BASE_URL:https://api.openai.com/v1}
  api_key: ${OPENAI_API_KEY}
  retry_config:
    max_retries: 3
    base_delay: 1.0
    max_delay: 60.0
    jitter: true
    exponential_base: 2.0
    retry_on_status_codes: [429, 500, 502, 503, 504]
    retry_on_errors: ["timeout", "rate_limit"]
  timeout_config:
    request_timeout: 60
    connect_timeout: 10
    read_timeout: 60
    write_timeout: 60
  parameters:
    temperature: 0.7
    max_tokens: 2048
```

### 具体模型配置 (configs/llms/openai-gpt4.yaml)

```yaml
model_type: openai
model_name: gpt-4
base_url: ${OPENAI_BASE_URL:https://api.openai.com/v1}
api_key: ${OPENAI_API_KEY}
retry_config:
  max_retries: 5
  base_delay: 2.0
  max_delay: 120.0
  jitter: true
  exponential_base: 2.5
  retry_on_status_codes: [429, 500, 502, 503, 504, 520]
  retry_on_errors: ["timeout", "rate_limit", "service_unavailable", "insufficient_quota"]
timeout_config:
  request_timeout: 120
  connect_timeout: 15
  read_timeout: 120
  write_timeout: 120
parameters:
  temperature: 0.7
  max_tokens: 4096
```

## 向后兼容性

系统保持与旧配置的向后兼容性：

- 旧的 `parameters.timeout` 和 `parameters.max_retries` 会在加载时自动迁移到新的配置结构
- 旧的配置格式仍然有效，但建议使用新的配置结构以获得更精细的控制

## 钩子集成

### SmartRetryHook

`SmartRetryHook` 现在支持通过 `retry_config` 参数接收完整的重试配置：

```python
from src.infrastructure.llm.hooks import SmartRetryHook

retry_config = {
    "max_retries": 6,
    "base_delay": 1.5,
    "max_delay": 90.0,
    "jitter": True,
    "exponential_base": 2.2,
    "retry_on_status_codes": [429, 500, 502, 503, 504],
    "retry_on_errors": ["timeout", "rate_limit", "service_unavailable"]
}

hook = SmartRetryHook(retry_config=retry_config)
```

## 最佳实践

1. **根据模型响应时间调整超时配置**：较复杂的模型（如 GPT-4）可能需要更长的超时时间
2. **合理设置重试次数**：过多的重试可能导致长时间延迟，过少的重试可能影响成功率
3. **监控重试统计**：使用 `SmartRetryHook.get_retry_stats()` 监控重试效果
4. **考虑成本**：重试会增加 API 调用次数，从而增加成本
5. **环境差异化配置**：开发环境和生产环境应使用不同的重试和超时策略

## 故障排除

### 常见问题

1. **配置不生效**：检查配置文件的层级关系和继承顺序
2. **超时错误频繁**：适当增加 `request_timeout` 和 `read_timeout`
3. **重试过多**：检查 `max_retries` 和 `max_delay` 设置
4. **性能问题**：调整 `performance` 部分的并发和连接池配置

### 调试方法

启用详细日志以查看重试和超时行为：

```yaml
log_level: DEBUG
log_outputs:
  - type: console
    level: DEBUG
    format: text