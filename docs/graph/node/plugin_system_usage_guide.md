# 插件系统使用指南

## 概述

Modular Agent Framework的插件系统已经完成合并，现在提供了统一的插件架构，支持START节点插件、END节点插件和Hook插件。本指南将详细介绍如何使用和配置插件系统。

## 插件类型

### 1. START插件
在工作流开始时执行，用于环境检查、上下文初始化等。

**内置START插件：**
- `context_summary` - 生成项目上下文摘要
- `environment_check` - 检查执行环境
- `metadata_collector` - 收集元数据

### 2. END插件
在工作流结束时执行，用于结果汇总、资源清理等。

**内置END插件：**
- `result_summary` - 生成执行结果汇总
- `execution_stats` - 收集执行统计信息
- `file_tracker` - 跟踪文件操作
- `cleanup_manager` - 清理资源

### 3. HOOK插件
在节点执行过程中拦截和增强，用于性能监控、错误恢复等。

**内置Hook插件：**
- `dead_loop_detection` - 死循环检测
- `performance_monitoring` - 性能监控
- `error_recovery` - 错误恢复
- `logging` - 日志记录
- `metrics_collection` - 指标收集

## 配置文件

插件系统通过YAML配置文件进行管理。配置文件结构如下：

```yaml
# START插件配置
start_plugins:
  builtin:
    - name: "context_summary"
      enabled: true
      priority: 10
      config:
        max_summary_length: 1000
        include_file_structure: true
        include_git_status: true
        include_recent_changes: true
        file_patterns: ["*.py", "*.yaml", "*.yml", "*.md"]
        exclude_patterns: ["__pycache__", "*.pyc", ".git"]
        max_files: 50
    
    - name: "environment_check"
      enabled: true
      priority: 20
      config:
        check_dependencies: true
        check_resources: true
        check_permissions: true
        fail_on_error: false
        required_packages: ["yaml", "pydantic"]
        required_commands: ["git"]
        min_memory_mb: 512
        min_disk_space_mb: 1024
    
    - name: "metadata_collector"
      enabled: true
      priority: 30
      config: {}
  
  external:
    - name: "custom_start_plugin"
      enabled: false
      module: "my_plugins.custom"
      class: "CustomStartPlugin"
      config:
        custom_option: "value"

# END插件配置
end_plugins:
  builtin:
    - name: "result_summary"
      enabled: true
      priority: 10
      config:
        include_tool_results: true
        include_error_analysis: true
        include_recommendations: true
        output_format: "markdown"
        save_to_file: true
        output_directory: "./output"
        max_summary_length: 5000
    
    - name: "execution_stats"
      enabled: true
      priority: 20
      config: {}
    
    - name: "file_tracker"
      enabled: true
      priority: 30
      config: {}
    
    - name: "cleanup_manager"
      enabled: true
      priority: 40
      config: {}
  
  external: []

# Hook插件配置
hook_plugins:
  global:
    # 全局Hook插件，适用于所有节点
    - name: "performance_monitoring"
      enabled: true
      priority: 10
      config:
        timeout_threshold: 10.0
        log_slow_executions: true
        metrics_collection: true
        slow_execution_threshold: 5.0
        enable_profiling: false
    
    - name: "logging"
      enabled: true
      priority: 20
      config:
        log_level: "INFO"
        structured_logging: true
        log_execution_time: true
        log_state_changes: false
        log_format: "json"
    
    - name: "metrics_collection"
      enabled: false
      priority: 30
      config:
        enable_performance_metrics: true
        enable_business_metrics: true
        enable_system_metrics: false
        collection_interval: 60
  
  node_specific:
    # 节点特定Hook插件
    llm_node:
      - name: "dead_loop_detection"
        enabled: true
        priority: 10
        config:
          max_iterations: 20
          fallback_node: "dead_loop_check"
          log_level: "WARNING"
          check_interval: 1
          reset_on_success: true
      
      - name: "error_recovery"
        enabled: true
        priority: 20
        config:
          max_retries: 3
          fallback_node: "error_handler"
          retry_delay: 1.0
          exponential_backoff: true
          retry_on_exceptions: ["Exception"]
    
    tool_node:
      - name: "error_recovery"
        enabled: true
        priority: 10
        config:
          max_retries: 2
          fallback_node: "tool_error_handler"
          retry_delay: 0.5
          exponential_backoff: false

# 执行配置
execution:
  parallel_execution: false
  max_parallel_plugins: 3
  error_handling:
    continue_on_error: true
    log_errors: true
    fail_on_critical_error: false
  timeout:
    default_timeout: 30
    per_plugin_timeout: 60
```

## 使用方法

### 1. 基本使用

```python
from infrastructure.graph.plugins import PluginManager

# 创建插件管理器
manager = PluginManager()

# 初始化（使用默认配置）
manager.initialize()

# 执行START插件
state = {}
context = PluginContext(
    workflow_id="test-workflow",
    thread_id="test-thread",
    session_id="test-session"
)
updated_state = manager.execute_plugins(PluginType.START, state, context)

# 执行END插件
final_state = manager.execute_plugins(PluginType.END, updated_state, context)

# 清理资源
manager.cleanup()
```

### 2. 使用自定义配置

```python
from infrastructure.graph.plugins import PluginManager

# 使用自定义配置文件
manager = PluginManager(config_path="path/to/plugin_config.yaml")
manager.initialize()

# 或者直接传入配置字典
custom_config = {
    "start_plugins": {
        "builtin": [
            {"name": "context_summary", "enabled": True, "priority": 10, "config": {
                "max_summary_length": 500
            }}
        ]
    },
    "hook_plugins": {
        "global": [
            {"name": "performance_monitoring", "enabled": True, "priority": 10, "config": {
                "timeout_threshold": 5.0
            }}
        ]
    }
}

manager = PluginManager()
manager.plugin_configs = custom_config
manager.initialize()
```

### 3. Hook插件使用

```python
from infrastructure.graph.plugins import PluginManager, HookContext, HookPoint
from infrastructure.graph.states.base import create_base_state

manager = PluginManager()
manager.initialize()

# 创建Hook上下文
state = create_base_state()
state["iteration_count"] = 1

context = HookContext(
    node_type="llm_node",
    state=state,
    config={"model": "gpt-4"},
    hook_point=HookPoint.BEFORE_EXECUTE
)

# 执行Hook插件
result = manager.execute_hooks(HookPoint.BEFORE_EXECUTE, context)

# 使用统一的Hook执行接口
def mock_node_executor(state, config):
    # 节点执行逻辑
    return NodeExecutionResult(
        state=state,
        next_node="next_node"
    )

result = manager.execute_with_hooks(
    node_type="llm_node",
    state=state,
    config={"model": "gpt-4"},
    node_executor_func=mock_node_executor
)
```

### 4. 创建自定义插件

#### 创建START插件

```python
from infrastructure.graph.plugins import IStartPlugin, PluginMetadata, PluginType, PluginContext

class CustomStartPlugin(IStartPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="custom_start",
            version="1.0.0",
            description="自定义START插件",
            author="developer",
            plugin_type=PluginType.START,
            config_schema={
                "type": "object",
                "properties": {
                    "custom_option": {"type": "string", "default": "default_value"}
                }
            }
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self.custom_option = config.get("custom_option", "default_value")
        return True
    
    def execute(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        state["custom_start_data"] = f"Processed with {self.custom_option}"
        return state
    
    def cleanup(self) -> bool:
        return True
```

#### 创建Hook插件

```python
from infrastructure.graph.plugins import IHookPlugin, PluginMetadata, PluginType, HookContext, HookPoint, HookExecutionResult

class CustomHookPlugin(IHookPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="custom_hook",
            version="1.0.0",
            description="自定义Hook插件",
            author="developer",
            plugin_type=PluginType.HOOK,
            supported_hook_points=[HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE]
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self.enabled = config.get("enabled", True)
        return True
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        if self.enabled:
            context.metadata["custom_hook_before"] = True
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        if self.enabled:
            context.metadata["custom_hook_after"] = True
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        return HookExecutionResult(should_continue=True)
    
    def cleanup(self) -> bool:
        return True
```

### 5. 注册外部插件

```python
from infrastructure.graph.plugins import PluginManager

manager = PluginManager()

# 注册外部插件
external_plugin = CustomStartPlugin()
manager.registry.register_plugin(external_plugin)

# 或者通过配置文件注册
# 在配置文件中添加：
# external:
#   - name: "custom_start"
#     enabled: true
#     module: "my_plugins.custom"
#     class: "CustomStartPlugin"
#     config:
#       custom_option: "value"

manager.initialize()
```

## 最佳实践

### 1. 插件优先级
- 优先级数字越小，执行顺序越靠前
- 建议START插件：环境检查(10) → 上下文摘要(20) → 元数据收集(30)
- 建议END插件：结果汇总(10) → 执行统计(20) → 文件追踪(30) → 清理管理(40)
- 建议Hook插件：性能监控(10) → 日志记录(20) → 业务逻辑(30+)

### 2. 错误处理
- 设置 `continue_on_error: true` 确保单个插件失败不影响整体流程
- 使用 `fail_on_error: false` 避免关键插件失败时中断工作流
- 在插件中实现适当的异常处理和日志记录

### 3. 性能优化
- 对于耗时插件，设置合理的超时时间
- 使用 `parallel_execution: true` 并行执行独立插件
- 定期清理插件资源，避免内存泄漏

### 4. 配置管理
- 使用环境变量注入敏感配置：`${API_KEY:default_value}`
- 为不同环境创建不同的配置文件
- 定期验证配置文件的正确性

## 故障排除

### 1. 插件初始化失败
- 检查配置文件格式是否正确
- 验证插件依赖是否满足
- 查看日志中的详细错误信息

### 2. Hook插件不执行
- 确认插件已启用：`enabled: true`
- 检查节点类型是否匹配配置
- 验证Hook执行点是否正确

### 3. 性能问题
- 检查插件执行时间统计
- 优化插件配置，禁用不必要的插件
- 考虑使用并行执行

### 4. 内存泄漏
- 确保所有插件都实现了 `cleanup()` 方法
- 定期调用 `manager.cleanup()` 清理资源
- 监控内存使用情况

## 总结

合并后的插件系统提供了统一、灵活、可扩展的架构。通过合理配置和使用插件，可以大大增强工作流的功能和可靠性。建议根据具体需求选择合适的插件组合，并遵循最佳实践以确保系统稳定运行。