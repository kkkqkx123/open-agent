# LLM包装器实现总结

## 概述

本文档总结了LLM任务组降级方案和轮询池包装器的完整实现。该实现提供了统一的接口，使任务组和轮询池能够直接作为LLM实例供LLM节点使用，支持基于任务组的精细化降级策略。

## 架构设计

### 核心组件

1. **基础包装器** (`BaseLLMWrapper`)
   - 实现了`ILLMClient`接口
   - 提供统一的包装器基础功能
   - 支持统计信息收集和重置

2. **任务组包装器** (`TaskGroupWrapper`)
   - 封装任务组管理器和降级管理器
   - 支持基于任务组配置的降级策略
   - 提供降级历史记录和统计

3. **轮询池包装器** (`PollingPoolWrapper`)
   - 封装轮询池管理器
   - 支持实例旋转降级策略
   - 提供健康检查和状态监控

4. **包装器工厂** (`LLMWrapperFactory`)
   - 统一创建和管理包装器实例
   - 支持批量创建和健康检查
   - 提供包装器统计和管理功能

### 配置模型扩展

1. **任务组降级配置** (`FallbackConfig`)
   - 支持多种降级策略
   - 可配置降级组列表和尝试次数
   - 集成熔断器配置

2. **轮询池降级配置** (`PollingPoolFallbackConfig`)
   - 支持实例旋转和简单重试策略
   - 可配置最大实例尝试次数

## 主要功能

### 1. 任务组降级

- **层级降级** (`echelon_down`): 同任务组内降级到下一层级
- **任务组切换** (`task_group_switch`): 切换到备用任务组
- **提供商故障转移** (`provider_failover`): 跨提供商故障转移

### 2. 轮询池降级

- **实例旋转** (`instance_rotation`): 直接从轮询池中取出新的实例
- **简单重试** (`simple_retry`): 在同一个实例上简单重试

### 3. LLM节点集成

- 支持通过`llm_wrapper`配置使用包装器
- 保持向后兼容性，仍支持传统的`llm_client`配置
- 优先级：包装器 > 任务组 > 轮询池 > 默认客户端

## 配置示例

### 任务组配置

```yaml
# configs/llms/groups/fast_group.yaml
name: "fast_group"
description: "快速响应任务组"

echelon1:
  models: ["openai-gpt4", "anthropic-claude-3-opus"]
  concurrency_limit: 10
  rpm_limit: 100
  priority: 1
  timeout: 30
  max_retries: 3
  temperature: 0.7
  max_tokens: 2000

# 降级配置
fallback_config:
  strategy: "echelon_down"
  fallback_groups: ["fast_group.echelon2", "fast_group.echelon3"]
  max_attempts: 3
  retry_delay: 1.0
  circuit_breaker:
    failure_threshold: 5
    recovery_time: 60
    half_open_requests: 1
```

### 轮询池配置

```yaml
# configs/llms/polling_pools/fast_pool.yaml
name: "fast_pool"
description: "快速响应任务专用轮询池"

task_groups: ["fast_group"]
rotation_strategy: "round_robin"
health_check_interval: 30
failure_threshold: 3
recovery_time: 60

# 轮询池专用降级策略
fallback_config:
  strategy: "instance_rotation"
  max_instance_attempts: 2
```

### LLM节点配置

```python
# 使用任务组包装器
workflow_config = {
    "nodes": {
        "llm_node": {
            "type": "llm_node",
            "config": {
                "llm_wrapper": "fast_group_wrapper",
                "system_prompt": "你是一个快速响应的助手",
                "max_tokens": 1000
            }
        }
    }
}

# 使用轮询池包装器
workflow_config = {
    "nodes": {
        "llm_node": {
            "type": "llm_node",
            "config": {
                "llm_wrapper": "thinking_pool_wrapper",
                "system_prompt": "你是一个深度思考的助手",
                "max_tokens": 4000
            }
        }
    }
}
```

## 使用示例

### 1. 创建包装器工厂

```python
from src.infrastructure.llm.wrappers import LLMWrapperFactory
from src.infrastructure.llm.task_group_manager import TaskGroupManager
from src.infrastructure.llm.polling_pool import PollingPoolManager
from src.infrastructure.llm.enhanced_fallback_manager import EnhancedFallbackManager

# 创建管理器
task_group_manager = TaskGroupManager(config_loader)
polling_pool_manager = PollingPoolManager(task_group_manager)
fallback_manager = EnhancedFallbackManager(task_group_manager)

# 创建包装器工厂
wrapper_factory = LLMWrapperFactory(
    task_group_manager=task_group_manager,
    polling_pool_manager=polling_pool_manager,
    fallback_manager=fallback_manager
)
```

### 2. 创建和使用包装器

```python
# 创建任务组包装器
fast_wrapper = wrapper_factory.create_task_group_wrapper(
    name="fast_wrapper",
    config={
        "target": "fast_group.echelon1",
        "fallback_groups": ["fast_group.echelon2", "fast_group.echelon3"]
    }
)

# 创建轮询池包装器
pool_wrapper = wrapper_factory.create_polling_pool_wrapper(
    name="fast_pool_wrapper",
    config={"max_instance_attempts": 2}
)

# 使用包装器
messages = [HumanMessage(content="你好，请介绍一下自己")]
response = await fast_wrapper.generate_async(messages)
print(response.content)
```

### 3. 在LLM节点中使用

```python
from src.infrastructure.graph.nodes.llm_node import LLMNode

# 创建LLM节点
llm_node = LLMNode(
    llm_client=default_client,
    wrapper_factory=wrapper_factory
)

# 执行节点
state = {"messages": []}
config = {
    "llm_wrapper": "fast_wrapper",
    "system_prompt": "你是一个智能助手"
}

result = llm_node.execute(state, config)
```

## 配置迁移

### 迁移工具使用

```bash
# 执行迁移（创建备份）
python scripts/migrate_llm_config.py

# 执行迁移（不创建备份）
python scripts/migrate_llm_config.py --no-backup

# 仅验证配置
python scripts/migrate_llm_config.py --validate-only

# 详细输出
python scripts/migrate_llm_config.py --verbose
```

### 编程方式迁移

```python
from src.infrastructure.llm.migration import ConfigMigrator

# 创建迁移器
migrator = ConfigMigrator(task_group_manager)

# 迁移任务组配置
success = migrator.migrate_global_fallback_to_task_groups()

# 迁移轮询池配置
success = migrator.migrate_polling_pools()

# 验证迁移结果
validation_result = migrator.validate_migration()
```

## 监控和统计

### 包装器统计

```python
# 获取单个包装器统计
stats = fast_wrapper.get_stats()
print(f"总请求数: {stats['total_requests']}")
print(f"成功率: {stats['successful_requests'] / stats['total_requests']}")

# 获取工厂统计
factory_stats = wrapper_factory.get_wrapper_stats()
print(f"包装器总数: {factory_stats['total_wrappers']}")
print(f"各类型数量: {factory_stats['wrapper_types']}")
```

### 健康检查

```python
# 检查所有包装器健康状态
health_status = wrapper_factory.health_check_all()
for name, status in health_status.items():
    print(f"{name}: {'健康' if status['healthy'] else '不健康'}")

# 轮询池健康检查
pool_health = await pool_wrapper.health_check()
print(f"健康实例数: {pool_health['healthy_instances']}")
print(f"总实例数: {pool_health['total_instances']}")
```

## 测试

### 运行单元测试

```bash
# 运行所有测试
pytest tests/test_llm_wrappers.py -v

# 运行特定测试
pytest tests/test_llm_wrappers.py::TestTaskGroupWrapper -v

# 运行配置迁移测试
pytest tests/test_config_migrator.py -v
```

### 运行集成测试

```bash
# 运行集成测试
pytest tests/test_llm_integration.py -v

# 运行特定集成测试
pytest tests/test_llm_integration.py::TestLLMIntegration::test_end_to_end_workflow -v
```

### 运行示例

```bash
# 运行使用示例
python examples/llm_wrapper_usage_example.py
```

## 性能优化

1. **包装器缓存**: 包装器实例缓存，避免重复创建
2. **连接池复用**: 轮询池实例复用，减少创建开销
3. **异步优化**: 所有包装器方法支持异步
4. **统计信息优化**: 高效的统计信息收集和查询

## 最佳实践

1. **任务隔离**: 为不同类型的任务创建专用的任务组和轮询池
2. **降级策略**: 根据任务特性配置合适的降级策略
3. **监控告警**: 设置降级成功率和熔断器状态告警
4. **定期验证**: 定期验证配置迁移结果和系统健康状态

## 故障排除

### 常见问题

1. **包装器创建失败**
   - 检查任务组管理器和轮询池管理器是否正确初始化
   - 确认配置文件路径和格式正确

2. **降级不生效**
   - 检查降级配置是否正确设置
   - 确认降级组是否存在且可访问

3. **性能问题**
   - 检查包装器统计信息，识别瓶颈
   - 考虑调整并发限制和超时设置

### 日志调试

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("src.infrastructure.llm.wrappers")
logger.setLevel(logging.DEBUG)
```

## 未来扩展

1. **更多降级策略**: 支持更多自定义降级策略
2. **动态配置**: 支持运行时动态调整配置
3. **分布式支持**: 支持分布式环境下的包装器管理
4. **性能监控**: 集成更详细的性能监控和指标收集

## 总结

LLM包装器实现提供了一个灵活、可扩展的框架，使任务组和轮询池能够无缝集成到LLM节点中。通过基于任务组的精细化降级策略，系统可以根据不同任务类型提供最优的可靠性和性能表现。

该实现保持了向后兼容性，同时提供了丰富的功能和配置选项，满足了不同场景下的需求。通过完善的测试和文档，确保了系统的稳定性和可维护性。