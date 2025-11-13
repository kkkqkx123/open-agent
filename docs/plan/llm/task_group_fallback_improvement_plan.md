# LLM任务组降级方案改进计划

## 当前问题分析

### 1. 全局降级方案的问题
- 使用统一的全局配置（`global_fallback.yaml`），无法针对不同任务类型进行差异化降级
- 所有任务组共享相同的降级策略和参数，缺乏灵活性
- 无法根据任务特性（如响应速度、成本、质量要求）进行智能降级
- 轮询池应当可以直接作为llm节点使用的实例[docs\plan\llm\task_group_polling_pool_wrapper_design.md]

### 2. 轮询池使用问题
- 目前的轮询池（configs\llms\polling_pools目录）包含多种任务组，违反了任务隔离原则
- 轮询池中的降级机制不清晰，没有明确的降级策略
- 轮询池应该专用于单轮对话，多轮对话需要不同的处理机制
- 轮询池应当可以直接作为llm节点使用的实例[docs\plan\llm\task_group_polling_pool_wrapper_design.md]

## 改进目标

1. **基于任务组的降级**：将全局降级改为基于每个任务组定义的降级配置
2. **任务专用轮询池**：为每种任务类型创建独立的轮询池，避免任务混合
3. **清晰的降级策略**：轮询池中的降级应该直接从池中取出新的实例，而不是复杂的降级逻辑

## 架构改进方案

### 1. 任务组降级配置结构

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

echelon2:
  models: ["openai-gpt4-turbo", "anthropic-claude-3-sonnet"]
  concurrency_limit: 8
  rpm_limit: 80
  priority: 2
  timeout: 90
  max_retries: 4

# 降级配置（新增）
fallback_config:
  strategy: "echelon_down"  # 层级降级
  fallback_groups: ["thinking_group.echelon2", "thinking_group.echelon3"]
  max_attempts: 3
  retry_delay: 1.0
  circuit_breaker:
    failure_threshold: 5
    recovery_time: 60
    half_open_requests: 1
```

### 2. 任务专用轮询池配置

```yaml
# configs/llms/polling_pools/thinking_pool.yaml
name: "thinking_pool"
description: "思考任务专用轮询池"
task_groups: ["thinking_group"]  # 只包含思考任务组
rotation_strategy: "round_robin"
health_check_interval: 60
failure_threshold: 2
recovery_time: 120

# 轮询池专用降级策略
fallback_strategy: "instance_rotation"  # 直接从池中旋转实例
max_instance_attempts: 2  # 每个实例最多尝试2次
```

### 3. 降级策略实现

#### 3.1 任务组降级策略
- **层级降级** (`echelon_down`): 同任务组内降级到下一层级
- **任务组切换** (`task_group_switch`): 切换到备用任务组
- **提供商故障转移** (`provider_failover`): 跨提供商故障转移

#### 3.2 轮询池降级策略  
- **实例旋转** (`instance_rotation`): 直接从轮询池中取出新的实例
- **简单重试** (`simple_retry`): 在同一个实例上简单重试

## 实施步骤

### 阶段一：配置结构调整
1. **修改任务组配置**：在每个任务组配置中添加 `fallback_config` 节
2. **创建任务专用轮询池**：为每种任务类型创建独立的轮询池
3. **移除全局降级配置**：废弃 `global_fallback.yaml`

### 阶段二：代码实现改进
1. **增强 EnhancedFallbackManager**：
   - 支持从任务组配置读取降级策略
   - 实现任务组专用的降级逻辑
   
2. **改进轮询池管理器**：
   - 添加轮询池专用的简单降级策略
   - 确保轮询池只用于单轮对话

3. **多轮对话处理**：
   - 为多轮对话创建专门的会话管理机制
   - 禁止在多轮对话中使用轮询池

### 阶段三：测试和验证
1. **单元测试**：为新的降级策略添加测试用例
2. **集成测试**：验证任务组降级和轮询池降级的正确性
3. **性能测试**：确保新方案不会影响系统性能

## 代码修改示例

### 1. 任务组降级配置读取

```python
# src/infrastructure/llm/task_group_manager.py
def get_fallback_config(self, group_name: str) -> Dict[str, Any]:
    """获取任务组的降级配置"""
    task_group = self.get_task_group(group_name)
    if not task_group:
        return {}
    
    return getattr(task_group, 'fallback_config', {})
```

### 2. 增强降级管理器

```python
# src/infrastructure/llm/enhanced_fallback_manager.py
async def execute_with_task_group_fallback(self,
                                         primary_target: str,
                                         prompt: str,
                                         **kwargs) -> Any:
    """基于任务组配置执行降级"""
    # 获取任务组降级配置
    group_name, _ = self.task_group_manager.parse_group_reference(primary_target)
    fallback_config = self.task_group_manager.get_fallback_config(group_name)
    
    # 使用配置中的降级组
    fallback_groups = fallback_config.get('fallback_groups', [])
    max_attempts = fallback_config.get('max_attempts', 3)
    
    return await self.execute_with_fallback(
        primary_target, fallback_groups, prompt, **kwargs
    )
```

### 3. 轮询池简单降级策略

```python
# src/infrastructure/llm/polling_pool.py
async def call_llm_with_fallback(self, prompt: str, **kwargs) -> Any:
    """轮询池专用简单降级"""
    for attempt in range(self.config.max_instance_attempts):
        instance = self.scheduler.select_instance(self.instances)
        if not instance:
            break
            
        try:
            return await instance.call_llm(prompt, **kwargs)
        except Exception as e:
            logger.warning(f"实例调用失败: {instance.instance_id}, 错误: {e}")
            continue
            
    raise LLMError("轮询池所有实例都失败")
```

## 迁移计划

### 1. 向后兼容性
- 保持现有全局降级配置的临时支持
- 提供配置迁移工具
- 逐步废弃全局降级方案

### 2. 监控和告警
- 添加降级成功率监控
- 设置熔断器状态告警
- 监控轮询池实例健康状态

### 3. 文档更新
- 更新配置指南文档
- 编写新的降级策略使用示例
- 更新API文档

## 预期收益

1. **更好的任务隔离**：每种任务类型有独立的降级策略和轮询池
2. **更高的可靠性**：针对性的降级策略提高系统容错能力
3. **更优的资源利用**：避免任务混合导致的资源争用
4. **更清晰的架构**：降级逻辑更加明确和可维护

## 风险评估

1. **配置复杂性增加**：需要为每个任务组配置降级策略
2. **迁移期间的不稳定性**：需要确保平滑过渡
3. **监控需求增加**：需要监控更多维度的降级指标

## 时间计划

- **第1周**：配置结构调整和基础代码修改
- **第2周**：增强降级管理器和轮询池实现
- **第3周**：测试和性能优化
- **第4周**：逐步迁移和监控部署

## 总结

本次改进将LLM降级系统从全局统一方案改为基于任务组的精细化方案，同时确保轮询池专用于单轮对话并采用简单的实例旋转降级策略。这将显著提高系统的可靠性、可维护性和资源利用效率。