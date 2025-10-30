# LLM降级系统快速参考

## 快速开始

```python
from src.infrastructure.llm.fallback_client import FallbackClientWrapper
from src.infrastructure.llm.clients.openai_client import OpenAIClient

# 创建降级客户端
primary_client = OpenAIClient(config)
fallback_wrapper = FallbackClientWrapper(
    primary_client=primary_client,
    fallback_models=["gpt-3.5-turbo", "claude-instant"],
    strategy_type="sequential"
)

# 使用
response = fallback_wrapper.generate(messages)
```

## 降级策略

| 策略 | 适用场景 | 配置示例 |
|------|----------|----------|
| `sequential` | 按顺序尝试模型 | `strategy_type="sequential"` |
| `priority` | 根据错误类型选择模型 | `strategy_type="priority"` |
| `random` | 随机选择模型 | `strategy_type="random"` |
| `error_type` | 基于错误类型映射 | `strategy_type="error_type"` |
| `parallel` | 并行调用多个模型 | `strategy_type="parallel"` |
| `conditional` | 基于自定义条件 | `strategy_type="conditional"` |

## 常用配置

```python
from src.infrastructure.llm.fallback_system import FallbackConfig

# 基础配置
config = FallbackConfig(
    enabled=True,
    fallback_models=["gpt-3.5-turbo", "claude-instant"],
    strategy_type="sequential",
    max_attempts=3
)

# 高级配置
config = FallbackConfig(
    enabled=True,
    fallback_models=["gpt-3.5-turbo", "claude-instant", "gemini-pro"],
    strategy_type="priority",
    max_attempts=5,
    base_delay=0.5,
    max_delay=30.0,
    fallback_on_errors=["timeout", "rate_limit", "service_unavailable"]
)
```

## 条件降级

```python
from src.infrastructure.llm.fallback_system import ConditionalFallback

# 内置条件
conditions = [
    ConditionalFallback.on_timeout,
    ConditionalFallback.on_rate_limit,
    ConditionalFallback.on_service_unavailable
]

# 自定义条件
def custom_condition(error):
    return "quota exceeded" in str(error).lower()

conditions.append(custom_condition)
```

## 监控统计

```python
# 获取统计信息
stats = fallback_wrapper.get_fallback_stats()
print(f"成功率: {stats['success_rate']:.2%}")
print(f"降级率: {stats['fallback_rate']:.2%}")

# 获取会话历史
sessions = fallback_wrapper.get_fallback_sessions(limit=10)

# 重置统计
fallback_wrapper.reset_fallback_stats()
```

## 错误处理

```python
from src.infrastructure.llm.exceptions import LLMFallbackError

try:
    response = fallback_wrapper.generate(messages)
except LLMFallbackError as e:
    # 所有降级都失败
    logger.error(f"所有LLM模型都不可用: {e}")
    return get_default_response()
```

## 配置参数速查

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | bool | True | 是否启用降级 |
| `max_attempts` | int | 3 | 最大尝试次数 |
| `fallback_models` | List[str] | [] | 降级模型列表 |
| `strategy_type` | str | "sequential" | 策略类型 |
| `base_delay` | float | 1.0 | 基础延迟 |
| `max_delay` | float | 60.0 | 最大延迟 |
| `jitter` | bool | True | 是否添加抖动 |

## 最佳实践

1. **模型选择**：按成本/性能/质量优先级排序
2. **监控告警**：设置降级率和成功率阈值
3. **环境配置**：不同环境使用不同配置
4. **错误处理**：实现完整的降级失败处理逻辑
5. **性能优化**：使用客户端缓存和连接池

## 故障排除

- 降级不生效 → 检查 `enabled` 和 `fallback_models`
- 性能差 → 使用并行策略或优化缓存
- 统计异常 → 检查会话记录和重置逻辑

详细文档请参考 [fallback_system_guide.md](fallback_system_guide.md)