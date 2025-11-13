# LLM分组配置设计方案

## 当前架构分析

### 现有配置结构
1. **组配置** (`configs/llms/_group.yaml`) - 按提供商分组(OpenAI, Gemini, Anthropic)
2. **Provider通用配置** - 各提供商的通用模板
3. **具体模型配置** - 特定模型配置，继承通用配置
4. **降级策略** - 基于单个LLM配置的降级

### 现有问题
- 降级策略基于单个LLM配置，不够灵活
- 缺乏任务类型导向的配置分组
- 无并发数和RPM限制配置
- 节点级别无法灵活配置LLM组

## 新设计方案

### 1. 任务类型分组策略

#### 主模型分组（大模型）
基于任务类型 + 水平层级划分：

```
主模型组：
- fast_group: 快速响应任务
  - echelon1: 顶级模型 (gpt-4, claude-3-opus)
  - echelon2: 高级模型 (gpt-4-turbo, claude-3-sonnet)
  - echelon3: 标准模型 (gpt-3.5-turbo, claude-3-haiku)

- plan_group: 规划任务
  - echelon1: 顶级规划模型
  - echelon2: 高级规划模型
  - echelon3: 标准规划模型

- thinking_group: 思考任务
  - echelon1: 深度思考模型
  - echelon2: 标准思考模型
  - echelon3: 快速思考模型

- execute_group: 执行任务
  - echelon1: 高执行力模型
  - echelon2: 标准执行模型
  - echelon3: 基础执行模型

- review_group: 审核任务
  - echelon1: 高精度审核模型
  - echelon2: 标准审核模型
  - echelon3: 快速审核模型

- high_payload_group: 高并发任务
  - echelon1: 高并发顶级模型
  - echelon2: 高并发高级模型
  - echelon3: 高并发标准模型
```

#### 小模型分组
基于水平 + 任务类型：

```
小模型组：
- fast_small_group: 简单快速任务
  - translation: 翻译任务
  - analysis: 分析任务
  - execute: 工具调用/JSON格式化
  - thinking: 轻量级思考
  - high_payload: 小模型高并发
```

### 2. 配置结构设计

#### 新的组配置文件结构

```yaml
# configs/llms/groups/_task_groups.yaml
task_groups:
  # 主模型组
  fast_group:
    description: "快速响应任务组"
    echelon1:
      models: ["openai-gpt4", "anthropic-claude-opus"]
      concurrency_limit: 10
      rpm_limit: 100
      priority: 1
    echelon2:
      models: ["openai-gpt4-turbo", "anthropic-claude-sonnet"]
      concurrency_limit: 20
      rpm_limit: 200
      priority: 2
    echelon3:
      models: ["openai-gpt3.5-turbo", "anthropic-claude-haiku"]
      concurrency_limit: 50
      rpm_limit: 500
      priority: 3
    fallback_strategy: "echelon_down"  # echelon_down, model_rotate, provider_failover
    
  plan_group:
    description: "规划任务组"
    echelon1:
      models: ["openai-gpt4", "anthropic-claude-opus"]
      concurrency_limit: 5
      rpm_limit: 50
      priority: 1
    # ... 其他层级
    
  # 小模型组
  fast_small_group:
    description: "轻量级快速任务"
    translation:
      models: ["openai-gpt3.5-turbo", "gemini-pro"]
      concurrency_limit: 100
      rpm_limit: 1000
    analysis:
      models: ["openai-gpt3.5-turbo", "anthropic-claude-haiku"]
      concurrency_limit: 80
      rpm_limit: 800
    execute:
      models: ["openai-gpt3.5-turbo", "gemini-pro"]
      concurrency_limit: 120
      rpm_limit: 1200
      response_format: "json"  # 强制JSON输出

# 轮询池配置
polling_pools:
  single_turn_pool:
    description: "单轮对话轮询池"
    task_groups: ["fast_group", "fast_small_group"]
    rotation_strategy: "round_robin"  # round_robin, least_recently_used, weighted
    health_check_interval: 30  # 健康检查间隔（秒）
    failure_threshold: 3  # 失败阈值
    recovery_time: 60  # 恢复时间（秒）
```

### 3. 节点级别配置支持

#### 节点配置中支持LLM组

```yaml
# 节点配置示例
nodes:
  planning_node:
    type: "llm"
    llm_group: "plan_group.echelon1"  # 指定具体组
    # 或者
    llm_config: "openai-gpt4"  # 兼容现有单个LLM配置
    fallback_groups: ["plan_group.echelon2", "fast_group.echelon1"]
    
  execution_node:
    type: "llm"
    llm_group: "execute_group.echelon2"
    task_type: "execute"  # 用于自动选择小模型组
```

### 4. 降级策略重构

#### 新的降级策略
1. **层级降级** (echelon_down): 同任务组内降级到下一层级
2. **模型轮询** (model_rotate): 同层级内模型轮询
3. **提供商故障转移** (provider_failover): 跨提供商故障转移
4. **任务组切换** (task_group_switch): 切换到备用任务组

#### 降级配置示例
```yaml
fallback_config:
  strategy: "echelon_down"  # 主要策略
  fallback_groups: ["plan_group.echelon2", "fast_group.echelon1"]
  max_attempts: 3
  retry_delay: 1.0
  circuit_breaker:  # 熔断器配置
    failure_threshold: 5
    recovery_time: 60
    half_open_requests: 1
```

### 5. 并发控制机制

#### 多级并发控制
1. **组级别**: 整个任务组的并发限制
2. **层级级别**: 特定层级的并发限制
3. **模型级别**: 单个模型的并发限制
4. **节点级别**: 特定节点的并发限制

#### 并发配置
```yaml
concurrency_control:
  enabled: true
  levels:
    - group_level:  # 组级别
        limit: 100
        queue_size: 1000
    - echelon_level:  # 层级级别
        limit: 30
        queue_size: 300
    - model_level:  # 模型级别
        limit: 10
        queue_size: 100
    - node_level:  # 节点级别
        limit: 5
        queue_size: 50
```

### 6. RPM限制机制

#### 令牌桶算法实现
- 每个任务组/模型维护独立的令牌桶
- 支持平滑的速率限制
- 可配置的桶大小和填充速率

#### RPM配置
```yaml
rate_limiting:
  enabled: true
  algorithm: "token_bucket"  # token_bucket, sliding_window
  token_bucket:
    bucket_size: 100  # 桶大小
    refill_rate: 1.67  # 每秒填充速率 (100/60)
  sliding_window:
    window_size: 60  # 窗口大小（秒）
    max_requests: 100  # 最大请求数
```

## 实施计划

### 阶段1: 配置模型扩展
1. 扩展LLMConfig模型支持新的分组字段
2. 创建TaskGroupConfig和PollingPoolConfig模型
3. 更新配置验证器

### 阶段2: 配置加载器重构
1. 修改LLMConfigManager支持组配置加载
2. 实现任务组配置解析
3. 添加轮询池配置支持

### 阶段3: 降级策略重构
1. 实现新的降级策略类
2. 集成熔断器模式
3. 更新降级逻辑

### 阶段4: 并发和RPM控制
1. 实现多级并发控制器
2. 实现令牌桶限流器
3. 集成到LLM客户端

### 阶段5: 节点级别支持
1. 扩展节点配置支持LLM组
2. 实现节点级别的组选择逻辑
3. 更新工作流引擎

### 阶段6: 测试和验证
1. 编写单元测试
2. 集成测试
3. 性能测试

## 兼容性考虑

1. **向后兼容**: 保持现有单个LLM配置的支持
2. **渐进迁移**: 支持新旧配置并存
3. **配置验证**: 确保新配置的正确性
4. **错误处理**: 完善的错误处理和回退机制

## 性能优化

1. **配置缓存**: 多级配置缓存机制
2. **懒加载**: 按需加载配置
3. **连接池**: 优化的连接池管理
4. **异步处理**: 支持异步配置更新