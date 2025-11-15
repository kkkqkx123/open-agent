# 触发器函数架构文档

## 概述

本文档描述了重构后的触发器函数架构，该架构参考了现有的edge/route_functions和node/node_function的设计模式，实现了基础模块和函数的分离，并通过配置文件定义触发器拥有的函数，提供了高度的配置灵活性。

## 架构设计

### 核心概念

1. **触发器函数(Trigger Functions)**: 分离的评估函数和执行函数
2. **触发器组合(Trigger Compositions)**: 将评估函数和执行函数组合成完整的触发器
3. **配置驱动**: 通过YAML配置文件定义函数和组合
4. **模块化设计**: 支持内置函数、配置函数和自定义函数

### 架构层次

```
triggers/
├── base.py              # 基础接口和抽象类
├── builtin_triggers.py  # 内置触发器实现
├── system.py           # 触发器系统管理
├── factory.py          # 触发器工厂（新增）
└── __init__.py         # 模块导出

trigger_functions/      # 新增模块
├── config.py           # 配置系统
├── registry.py         # 函数注册表
├── loader.py           # 函数加载器
├── manager.py          # 函数管理器
├── builtin.py          # 内置函数
└── __init__.py         # 模块导出
```

## 使用示例

### 1. 基本使用

```python
from src.infrastructure.graph.triggers import get_trigger_factory
from src.infrastructure.graph.trigger_functions import get_trigger_function_manager

# 获取工厂和管理器
factory = get_trigger_factory()
function_manager = get_trigger_function_manager()

# 创建时间触发器
time_trigger = factory.create_trigger(
    trigger_id="daily_report",
    trigger_type=TriggerType.TIME,
    config={"trigger_time": "09:00"}
)

# 创建自定义触发器
custom_trigger = factory.create_trigger(
    trigger_id="error_monitor",
    trigger_type=TriggerType.CUSTOM,
    config={"error_threshold": 3},
    evaluate_function="tool_error_evaluate",
    execute_function="tool_error_execute"
)
```

### 2. 使用触发器组合

```python
# 从预定义组合创建触发器
scheduled_trigger = factory.create_trigger_from_composition(
    trigger_id="weekly_report",
    composition_name="scheduled_report_trigger",
    config={
        "trigger_time": "monday_09:00",
        "report_format": "pdf",
        "include_charts": True
    }
)

# 查看可用组合
compositions = factory.list_available_compositions()
for comp_name in compositions:
    info = factory.get_composition_info(comp_name)
    print(f"{comp_name}: {info['description']}")
```

### 3. 配置文件示例

#### 触发器函数配置 (configs/trigger_functions/custom_time_trigger.yaml)

```yaml
category: "custom"

trigger_functions:
  custom_time_evaluate:
    description: "自定义时间触发器评估函数"
    function_type: "evaluate"
    implementation: "config"
    parameters:
      time_patterns:
        - type: "interval"
          value: 300  # 5分钟间隔
        - type: "cron"
          value: "0 */6 * * *"  # 每6小时
    metadata:
      author: "system"
      version: "1.0"
      tags: ["time", "schedule", "custom"]

  custom_time_execute:
    description: "自定义时间触发器执行函数"
    function_type: "execute"
    implementation: "config"
    parameters:
      include_state_summary: true
      include_next_trigger: true
    metadata:
      author: "system"
      version: "1.0"
      tags: ["time", "report", "custom"]
```

#### 触发器组合配置 (configs/trigger_compositions/scheduled_report_trigger.yaml)

```yaml
name: "scheduled_report_trigger"
description: "定时报告触发器"
trigger_type: "time"

evaluate_function:
  name: "time_evaluate"
  description: "时间评估函数"
  function_type: "evaluate"
  implementation: "builtin"

execute_function:
  name: "state_execute"
  description: "状态执行函数"
  function_type: "execute"
  implementation: "builtin"

default_config:
  enabled: true
  rate_limit: 3600
  max_triggers: 24
  report_format: "json"
```

### 4. 自定义函数实现

```python
# 自定义评估函数
def custom_evaluate(state: WorkflowState, context: Dict[str, Any]) -> bool:
    """自定义评估逻辑"""
    trigger_config = context.get("trigger_config", {})
    threshold = trigger_config.get("threshold", 10)
    
    # 检查状态中的某个指标
    current_value = state.get("metric", 0)
    return current_value >= threshold

# 自定义执行函数
def custom_execute(state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
    """自定义执行逻辑"""
    trigger_config = context.get("trigger_config", {})
    
    return {
        "action": "custom_action",
        "executed_at": datetime.now().isoformat(),
        "config": trigger_config,
        "state_snapshot": {
            "metric": state.get("metric", 0),
            "timestamp": state.get("timestamp")
        }
    }

# 注册自定义函数
function_manager.register_custom_function("custom_evaluate", custom_evaluate)
function_manager.register_custom_function("custom_execute", custom_execute)
```

## 配置灵活性

### 1. 函数组合

通过配置文件可以灵活组合不同的评估函数和执行函数：

```yaml
# 组合1: 时间触发 + 状态报告
evaluate_function: "time_evaluate"
execute_function: "state_execute"

# 组合2: 状态触发 + 错误处理
evaluate_function: "state_evaluate"
execute_function: "error_execute"

# 组合3: 事件触发 + 自定义处理
evaluate_function: "event_evaluate"
execute_function: "custom_execute"
```

### 2. 参数化配置

支持通过配置文件传递参数：

```yaml
default_config:
  threshold: 100
  interval: 300
  format: "json"
  destination: "log"
```

### 3. 继承和覆盖

支持配置继承和覆盖：

```yaml
# 基础配置
inherits_from: "_group.yaml"

# 覆盖特定设置
default_config:
  threshold: 50  # 覆盖默认值
```

## 扩展性

### 1. 添加新的内置函数

在 `trigger_functions/builtin.py` 中添加新函数：

```python
@staticmethod
def new_evaluate_function(state: WorkflowState, context: Dict[str, Any]) -> bool:
    """新的评估函数"""
    # 实现逻辑
    return True

@staticmethod
def new_execute_function(state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
    """新的执行函数"""
    # 实现逻辑
    return {"result": "success"}
```

### 2. 添加配置函数

在配置文件中定义新函数：

```yaml
trigger_functions:
  my_custom_function:
    description: "我的自定义函数"
    function_type: "evaluate"
    implementation: "config"
    parameters:
      # 参数定义
```

### 3. 添加自定义模块函数

```python
# my_custom_module.py
def my_custom_function(state: WorkflowState, context: Dict[str, Any]) -> bool:
    """自定义模块函数"""
    return True
```

然后在配置中引用：

```yaml
trigger_functions:
  my_custom_function:
    description: "自定义模块函数"
    implementation: "custom.my_custom_module"
```

## 最佳实践

1. **函数职责分离**: 评估函数只负责判断是否触发，执行函数只负责执行动作
2. **配置驱动**: 尽量通过配置文件而不是代码来定义触发器行为
3. **参数化**: 使用参数化配置提高复用性
4. **错误处理**: 在函数中添加适当的错误处理
5. **文档化**: 为自定义函数和配置添加详细文档

## 与现有架构的对比

### 之前的问题

1. 触发器逻辑耦合在单个类中
2. 难以复用评估和执行逻辑
3. 配置灵活性不足
4. 扩展新功能需要修改核心代码

### 重构后的优势

1. **模块化**: 评估和执行逻辑分离，可以独立复用
2. **配置驱动**: 通过配置文件灵活组合函数
3. **可扩展**: 支持内置、配置和自定义三种实现方式
4. **一致性**: 与route_functions和node_functions架构保持一致
5. **可维护**: 清晰的模块边界和职责分离

## 总结

新的触发器函数架构通过借鉴现有的成功模式，实现了高度模块化和配置化的设计。这种架构不仅提高了代码的复用性和可维护性，还为用户提供了极大的配置灵活性，使得创建和管理触发器变得更加简单和高效。