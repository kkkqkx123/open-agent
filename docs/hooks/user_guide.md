# Graph Hook系统用户指南

## 概述

Graph Hook系统是一个灵活的节点执行监控和干预机制，允许用户通过配置文件为图节点添加各种检查、监控和恢复功能。Hook系统弥补了LangGraph条件边在节点内部状态监控方面的不足，提供了细粒度的执行控制能力。

## 核心概念

### Hook执行点

Hook在节点的三个关键执行点被触发：

1. **BEFORE_EXECUTE** - 节点执行前
   - 用途：输入验证、状态检查、资源准备
   - 可以中断节点执行并强制切换到其他节点

2. **AFTER_EXECUTE** - 节点执行后
   - 用途：结果验证、性能监控、状态更新
   - 可以修改执行结果和下一节点选择

3. **ON_ERROR** - 节点执行出错时
   - 用途：错误恢复、重试逻辑、降级处理
   - 可以处理错误并决定是否继续执行

### Hook类型

系统提供了以下内置Hook类型：

- **dead_loop_detection** - 死循环检测
- **performance_monitoring** - 性能监控
- **error_recovery** - 错误恢复
- **logging** - 日志记录
- **metrics_collection** - 指标收集

## 快速开始

### 1. 基本使用

```python
import yaml
from src.infrastructure.config_loader import YamlConfigLoader
from src.infrastructure.graph.hooks import (
    NodeHookManager,
    create_hookable_node_class,
    HookAwareGraphBuilder,
    create_hook_aware_builder
)
from src.infrastructure.graph.config import GraphConfig

# 创建配置加载器
config_loader = YamlConfigLoader()

# 创建Hook管理器
hook_manager = NodeHookManager(config_loader)

# 加载Hook配置
hook_manager.load_hooks_from_config()

# 创建Hook感知的Graph构建器
builder = create_hook_aware_builder(
    hook_manager=hook_manager,
    config_loader=config_loader
)

# 构建图
with open("configs/graphs/my_workflow.yaml", 'r', encoding='utf-8') as f:
    config_data = yaml.safe_load(f)
config = GraphConfig.from_dict(config_data)
graph = builder.build_graph(config)

# 或者手动创建Hookable节点
HookableNode = create_hookable_node_class(OriginalNode, hook_manager)
node = HookableNode()
```

### 2. 手动配置Hook

```python
from src.infrastructure.graph.hooks import (
    DeadLoopDetectionHook,
    PerformanceMonitoringHook,
    ErrorRecoveryHook
)

# 创建死循环检测Hook
dead_loop_hook = DeadLoopDetectionHook({
    "max_iterations": 10,
    "fallback_node": "dead_loop_handler",
    "log_level": "WARNING"
})

# 注册到特定节点
hook_manager.register_hook(dead_loop_hook, ["agent_execution_node"])

# 创建性能监控Hook（全局）
performance_hook = PerformanceMonitoringHook({
    "timeout_threshold": 30.0,
    "log_slow_executions": True
})

# 注册为全局Hook
hook_manager.register_hook(performance_hook)
```

## 配置文件

### 全局Hook配置

在 `configs/hooks/global_hooks.yaml` 中定义全局Hook：

```yaml
global_hooks:
  - type: "logging"
    enabled: true
    priority: 10
    config:
      log_level: "INFO"
      structured_logging: true
  
  - type: "performance_monitoring"
    enabled: true
    priority: 20
    config:
      timeout_threshold: 30.0
      slow_execution_threshold: 10.0
```

### 节点特定Hook配置

在 `configs/hooks/{node_type}_hooks.yaml` 中定义节点特定Hook：

```yaml
agent_execution_node:
  inherit_global: true
  hooks:
    - type: "dead_loop_detection"
      enabled: true
      priority: 100
      config:
        max_iterations: 15
        fallback_node: "agent_dead_loop_handler"
    
    - type: "error_recovery"
      enabled: true
      priority: 90
      config:
        max_retries: 2
        fallback_node: "agent_error_handler"
```

### Hook组配置

在 `configs/hooks/_group.yaml` 中定义Hook组配置：

```yaml
dead_loop_detection_group:
  enabled: true
  config:
    max_iterations: 20
    fallback_node: "dead_loop_check"
    log_level: "WARNING"
    check_interval: 1
    reset_on_success: true
```

## 内置Hook详解

### 死循环检测Hook

监控节点执行次数，防止无限循环。

**配置参数：**
- `max_iterations` - 最大允许迭代次数
- `fallback_node` - 检测到死循环时的回退节点
- `log_level` - 日志级别
- `check_interval` - 检查间隔
- `reset_on_success` - 成功时是否重置计数

**使用场景：**
- Agent执行节点容易陷入重复思考
- 循环工作流需要防止无限循环
- 调试阶段发现潜在死循环

### 性能监控Hook

监控节点执行性能，检测超时和慢执行。

**配置参数：**
- `timeout_threshold` - 超时阈值（秒）
- `slow_execution_threshold` - 慢执行阈值（秒）
- `log_slow_executions` - 是否记录慢执行
- `metrics_collection` - 是否收集性能指标
- `enable_profiling` - 是否启用性能分析

**使用场景：**
- LLM调用节点需要监控响应时间
- 工具执行节点需要检测超时
- 生产环境性能监控

### 错误恢复Hook

提供自动重试和错误恢复机制。

**配置参数：**
- `max_retries` - 最大重试次数
- `fallback_node` - 重试失败后的回退节点
- `retry_delay` - 重试延迟（秒）
- `exponential_backoff` - 是否使用指数退避
- `retry_on_exceptions` - 需要重试的异常类型

**使用场景：**
- 网络调用节点需要重试机制
- API调用节点处理临时故障
- 外部服务集成节点

### 日志Hook

记录节点执行的详细日志。

**配置参数：**
- `log_level` - 日志级别
- `structured_logging` - 是否使用结构化日志
- `log_execution_time` - 是否记录执行时间
- `log_state_changes` - 是否记录状态变化
- `log_format` - 日志格式（json/text）

**使用场景：**
- 调试阶段需要详细日志
- 生产环境审计日志
- 问题排查和分析

### 指标收集Hook

收集节点执行的各种指标。

**配置参数：**
- `enable_performance_metrics` - 是否启用性能指标
- `enable_business_metrics` - 是否启用业务指标
- `enable_system_metrics` - 是否启用系统指标
- `metrics_endpoint` - 指标推送端点
- `collection_interval` - 收集间隔

**使用场景：**
- 监控系统整体性能
- 业务指标统计和分析
- 系统资源使用监控

## 自定义Hook

### 创建自定义Hook

```python
from src.infrastructure.graph.hooks.interfaces import INodeHook, HookContext, HookExecutionResult, HookPoint

class CustomValidationHook(INodeHook):
    """自定义验证Hook"""
    
    def __init__(self, hook_config):
        super().__init__(hook_config)
        self.validation_rules = hook_config.get("validation_rules", {})
    
    @property
    def hook_type(self) -> str:
        return "custom_validation"
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """执行前验证"""
        # 实现验证逻辑
        required_fields = self.validation_rules.get("required_fields", [])
        
        for field in required_fields:
            if not hasattr(context.state, field) or getattr(context.state, field) is None:
                return HookExecutionResult(
                    should_continue=False,
                    force_next_node="validation_error_handler",
                    metadata={
                        "validation_failed": True,
                        "missing_field": field
                    }
                )
        
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """执行后验证"""
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """错误处理"""
        return HookExecutionResult(should_continue=True)
```

### 注册自定义Hook

```python
# 创建自定义Hook
custom_hook = CustomValidationHook({
    "validation_rules": {
        "required_fields": ["input", "messages"],
        "max_input_length": 1000
    }
})

# 注册到Hook管理器
hook_manager.register_hook(custom_hook, ["analysis_node", "llm_node"])
```

## 最佳实践

### 1. Hook配置原则

- **全局Hook**用于通用功能（日志、性能监控）
- **节点特定Hook**用于节点特定逻辑（死循环检测、错误恢复）
- **优先级设置**：关键Hook设置高优先级
- **继承策略**：节点配置优先于全局配置

### 2. 性能考虑

- 避免在Hook中执行耗时操作
- 使用异步Hook处理IO密集型任务
- 合理设置Hook执行超时
- 定期清理Hook收集的指标数据

### 3. 错误处理

- Hook错误不应影响主流程
- 使用错误隔离机制
- 提供降级处理逻辑
- 记录Hook执行错误日志

### 4. 调试技巧

- 启用详细日志记录
- 使用性能监控Hook分析瓶颈
- 利用指标收集Hook监控系统状态
- 在测试环境验证Hook配置

## 故障排除

### 常见问题

1. **Hook不执行**
   - 检查Hook是否已正确注册
   - 验证Hook配置是否正确
   - 确认Hook是否启用

2. **Hook执行失败**
   - 查看Hook错误日志
   - 验证Hook配置参数
   - 检查Hook依赖的服务

3. **性能问题**
   - 检查Hook执行时间
   - 优化Hook逻辑
   - 调整Hook优先级

4. **配置冲突**
   - 检查全局和节点配置
   - 验证配置继承关系
   - 确认配置优先级

### 调试工具

```python
# 获取Hook统计信息
stats = builder.get_hook_statistics()
print(f"Hook统计: {stats}")

# 获取性能统计
perf_stats = hook_manager.get_performance_stats("node_type")
print(f"性能统计: {perf_stats}")

# 获取指标数据
if hasattr(metrics_hook, 'get_metrics'):
    metrics = metrics_hook.get_metrics()
    print(f"指标数据: {metrics}")
```

## 进阶用法

### 1. Hook链式执行

Hook按优先级顺序执行，前一个Hook的结果会影响后续Hook：

```python
# 高优先级Hook可以修改状态，影响后续Hook
high_priority_hook = HighPriorityHook(priority: 100)
low_priority_hook = LowPriorityHook(priority: 10)

hook_manager.register_hook(high_priority_hook)
hook_manager.register_hook(low_priority_hook)
```

### 2. 条件化Hook执行

通过配置实现Hook的条件化执行：

```yaml
hooks:
  - type: "custom_hook"
    enabled: "${ENABLE_CUSTOM_HOOK:true}"
    config:
      condition: "environment == 'production'"
```

### 3. Hook热重载

支持配置文件热重载，无需重启应用：

```python
# 启用配置热重载
config_loader = YamlConfigLoader(enable_hot_reload=True)
hook_manager = NodeHookManager(config_loader)
```

### 4. Hook性能优化

使用缓存和批处理优化Hook性能：

```python
class OptimizedHook(INodeHook):
    def __init__(self, hook_config):
        super().__init__(hook_config)
        self._cache = {}
        self._batch_size = hook_config.get("batch_size", 100)
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        # 使用缓存优化性能
        cache_key = self._get_cache_key(context)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = self._execute_logic(context)
        self._cache[cache_key] = result
        return result
```

## 总结

Graph Hook系统提供了强大的节点执行监控和干预能力，通过配置化的方式实现了灵活的功能扩展。合理使用Hook系统可以显著提升系统的可靠性、可观测性和可维护性。

在实际应用中，建议根据具体需求选择合适的Hook类型和配置，遵循最佳实践原则，确保系统的稳定性和性能。