# 监控触发器系统使用指南

本文档介绍如何使用新的监控触发器系统，包括各种触发器的功能、配置和使用方法。

## 概述

监控触发器系统提供了全面的监控功能，包括：

- **计时监控**：工具执行时间、LLM响应时间、工作流状态持续时间
- **状态监控**：工作流状态捕获、状态变更、错误状态
- **模式匹配**：用户输入、LLM输出、工具输出的模式匹配
- **系统监控**：内存使用、性能指标、系统资源

## 架构设计

### 基类结构

```
ITrigger (接口)
├── BaseTrigger (基础实现)
└── MonitoringTrigger (监控基类)
    ├── 计时触发器
    ├── 状态监控触发器
    ├── 模式匹配触发器
    └── 系统监控触发器
```

### 模块组织

- `monitoring_base.py` - 监控基类和数据结构
- `timing.py` - 计时相关触发器
- `state_monitoring.py` - 状态监控触发器
- `pattern_matching.py` - 模式匹配触发器
- `system_monitoring.py` - 系统监控触发器
- `factory.py` - 触发器工厂

## 计时触发器

### ToolExecutionTimingTrigger

监控工具执行过程的耗时，当执行时间超过阈值时触发。

**配置参数：**
- `timeout_threshold`: 超时阈值（秒）
- `warning_threshold`: 警告阈值（秒）
- `monitor_all_tools`: 是否监控所有工具
- `monitored_tools`: 特定监控的工具列表

**使用示例：**
```python
from src.infrastructure.graph.triggers import TriggerFactory

factory = TriggerFactory()

# 创建工具执行计时触发器
trigger = factory.create_monitoring_trigger(
    "tool_timing_monitor",
    "ToolExecutionTimingTrigger",
    {
        "timeout_threshold": 30.0,
        "warning_threshold": 10.0,
        "monitor_all_tools": True
    }
)

# 注册到触发器系统
trigger_system.register_trigger(trigger)
```

### LLMResponseTimingTrigger

监控LLM响应时间，当响应时间超过阈值时触发。

**配置参数：**
- `timeout_threshold`: 超时阈值（秒）
- `warning_threshold`: 警告阈值（秒）
- `monitor_all_models`: 是否监控所有模型
- `monitored_models`: 特定监控的模型列表

### WorkflowStateTimingTrigger

监控工作流状态切换后的时间，用于检查工作流是否被阻塞。

**配置参数：**
- `stall_threshold`: 停滞阈值（秒）
- `warning_threshold`: 警告阈值（秒）
- `monitored_states`: 特定监控的状态列表

## 状态监控触发器

### WorkflowStateCaptureTrigger

捕获工作流状态信息，用于分析和调试。

**配置参数：**
- `capture_interval`: 捕获间隔（秒）
- `capture_on_state_change`: 是否在状态变更时捕获
- `include_messages`: 是否包含消息
- `include_tool_results`: 是否包含工具结果

### WorkflowStateChangeTrigger

监控工作流状态变更，当状态发生特定变化时触发。

**配置参数：**
- `monitored_transitions`: 监控的状态转换列表
- `monitor_all_changes`: 是否监控所有状态变更

### WorkflowErrorStateTrigger

监控工作流错误状态，当出现错误时触发。

**配置参数：**
- `error_threshold`: 错误阈值
- `monitor_tool_errors`: 是否监控工具错误
- `monitor_llm_errors`: 是否监控LLM错误
- `monitor_system_errors`: 是否监控系统错误

## 模式匹配触发器

### UserInputPatternTrigger

监控用户输入，匹配特定模式时触发。

**配置参数：**
- `patterns`: 模式字典
- `case_sensitive`: 是否区分大小写

**使用示例：**
```python
trigger = factory.create_monitoring_trigger(
    "user_pattern_monitor",
    "UserInputPatternTrigger",
    {
        "patterns": {
            "urgent": r"(?i)(urgent|asap|immediately)",
            "help": r"(?i)(help|assist|support)",
            "error": r"(?i)(error|issue|problem)"
        },
        "case_sensitive": False
    }
)
```

### LLMOutputPatternTrigger

监控LLM输出，匹配特定模式时触发。

### ToolOutputPatternTrigger

监控工具输出，匹配特定模式时触发。

### StatePatternTrigger

监控工作流状态，匹配特定模式时触发。

## 系统监控触发器

### MemoryMonitoringTrigger

监控内存使用情况，当超过阈值时触发。

**配置参数：**
- `memory_threshold_mb`: 内存阈值（MB）
- `system_memory_threshold_percent`: 系统内存阈值（百分比）
- `check_interval`: 检查间隔（秒）

### PerformanceMonitoringTrigger

监控系统性能指标，当性能下降时触发。

**配置参数：**
- `cpu_threshold_percent`: CPU阈值（百分比）
- `response_time_threshold`: 响应时间阈值（秒）
- `check_interval`: 检查间隔（秒）

### ResourceMonitoringTrigger

监控系统资源使用情况，当资源不足时触发。

**配置参数：**
- `disk_threshold_percent`: 磁盘空间阈值（百分比）
- `memory_threshold_percent`: 内存阈值（百分比）
- `check_interval`: 检查间隔（秒）

## 配置文件

### 触发器函数配置

触发器函数配置文件位于 `configs/trigger_functions/` 目录：

- `tool_timing.yaml` - 工具执行计时函数
- `llm_timing.yaml` - LLM响应计时函数
- `state_monitoring.yaml` - 状态监控函数
- `pattern_matching.yaml` - 模式匹配函数
- `system_monitoring.yaml` - 系统监控函数

### 触发器组合配置

触发器组合配置文件位于 `configs/trigger_compositions/` 目录：

- `tool_timing_monitor.yaml` - 工具执行计时监控组合
- `memory_monitor.yaml` - 内存监控组合
- `user_input_pattern_monitor.yaml` - 用户输入模式匹配监控组合

## 使用工厂创建触发器

### 创建监控触发器

```python
from src.infrastructure.graph.triggers import TriggerFactory

factory = TriggerFactory()

# 创建内存监控触发器
memory_trigger = factory.create_monitoring_trigger(
    "memory_monitor",
    "MemoryMonitoringTrigger",
    {
        "memory_threshold_mb": 1024,
        "system_memory_threshold_percent": 90,
        "check_interval": 60
    }
)

# 创建用户输入模式匹配触发器
pattern_trigger = factory.create_monitoring_trigger(
    "user_pattern_monitor",
    "UserInputPatternTrigger",
    {
        "patterns": {
            "urgent": r"(?i)(urgent|asap)",
            "help": r"(?i)(help|assist)"
        }
    }
)
```

### 从配置创建触发器

```python
# 从组合配置创建触发器
trigger = factory.create_trigger_from_composition(
    "memory_monitor_trigger",
    "memory_monitor",
    {
        "memory_threshold_mb": 2048  # 覆盖默认配置
    }
)
```

### 批量创建触发器

```python
trigger_configs = [
    {
        "trigger_id": "tool_timing_1",
        "trigger_class": "ToolExecutionTimingTrigger",
        "config": {"timeout_threshold": 30.0}
    },
    {
        "trigger_id": "memory_monitor_1",
        "trigger_class": "MemoryMonitoringTrigger",
        "config": {"memory_threshold_mb": 1024}
    }
]

triggers = factory.create_batch_triggers(trigger_configs)
```

## 集成到工作流

### 注册触发器

```python
from src.infrastructure.graph.triggers import TriggerSystem

# 创建触发器系统
trigger_system = TriggerSystem()

# 注册触发器
for trigger in triggers:
    trigger_system.register_trigger(trigger)

# 启动触发器系统
trigger_system.start()
```

### 评估触发器

```python
# 在工作流执行过程中评估触发器
state = {
    "current_step": "processing",
    "messages": [...],
    "tool_results": [...]
}

context = {
    "workflow_id": "workflow_123",
    "timestamp": datetime.now().isoformat()
}

events = trigger_system.evaluate_triggers(state, context)

# 处理触发事件
for event in events:
    print(f"触发器 {event.trigger_id} 被触发: {event.data}")
```

## 最佳实践

1. **合理设置阈值**：根据实际需求设置合适的阈值，避免过于频繁的触发
2. **使用配置文件**：将触发器配置放在配置文件中，便于管理和修改
3. **监控关键指标**：重点监控对系统性能和用户体验影响最大的指标
4. **定期清理历史数据**：设置合适的历史记录大小，避免内存占用过高
5. **组合使用触发器**：结合多种触发器实现全面的监控覆盖

## 扩展开发

### 创建自定义监控触发器

```python
from src.infrastructure.graph.triggers.monitoring_base import MonitoringTrigger, TriggerType

class CustomMonitoringTrigger(MonitoringTrigger):
    def __init__(self, trigger_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(trigger_id, TriggerType.CUSTOM, config or {})
    
    def evaluate(self, state: WorkflowState, context: Dict[str, Any]) -> bool:
        # 实现评估逻辑
        return False
    
    def execute(self, state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        # 实现执行逻辑
        return {"message": "自定义触发器执行"}
```

### 注册到工厂

```python
# 在工厂中添加对自定义触发器的支持
def _create_custom_trigger(self, trigger_id: str, config: Dict[str, Any]) -> ITrigger:
    special_type = config.get("special_type")
    
    if special_type == "custom_monitoring":
        return CustomMonitoringTrigger(trigger_id, config)
    
    # 其他逻辑...
```

## 故障排除

### 常见问题

1. **触发器不触发**
   - 检查触发器是否已启用
   - 验证配置参数是否正确
   - 确认评估条件是否满足

2. **性能问题**
   - 减少触发器数量
   - 调整检查间隔
   - 优化模式匹配表达式

3. **内存占用过高**
   - 减少历史记录大小
   - 定期清理监控数据
   - 使用更高效的数据结构

### 调试技巧

1. 启用详细日志记录
2. 使用触发器系统的统计功能
3. 检查触发器事件历史
4. 验证配置文件语法

## 总结

监控触发器系统提供了强大而灵活的监控能力，可以帮助开发者及时发现和解决系统问题。通过合理配置和使用，可以显著提高系统的可靠性和可维护性。