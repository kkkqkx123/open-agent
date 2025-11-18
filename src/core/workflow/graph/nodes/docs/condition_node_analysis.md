# ConditionNode 功能分析与扩展指南

## 概述

`ConditionNode` 是工作流图中的条件判断节点，负责根据当前状态信息进行条件判断，决定工作流的分支走向。它是实现复杂工作流逻辑的关键组件，提供了多种内置条件判断和自定义条件扩展能力。

## 当前实现功能

### 1. 核心架构

- **节点类型**: `condition_node`
- **继承关系**: 继承自 `BaseNode`
- **注册方式**: 使用 `@node("condition_node")` 装饰器注册

### 2. 条件判断机制

#### 2.1 条件配置结构
```yaml
conditions:
  - type: "条件类型"
    next_node: "满足条件时的下一个节点"
    parameters:
      # 条件特定参数
default_next_node: "默认下一个节点（没有条件满足时）"
custom_condition_code: "自定义条件代码（当条件类型为custom时使用）"
```

#### 2.2 条件评估流程
1. 获取节点配置中的条件列表
2. 如果没有配置条件，使用默认条件 `has_tool_calls`
3. 按顺序评估每个条件
4. 返回第一个满足条件的下一个节点
5. 如果没有条件满足，使用默认节点

### 3. 内置条件类型

| 条件类型 | 功能描述 | 参数 |
|---------|---------|------|
| `has_tool_calls` | 检查是否有工具调用 | 无 |
| `no_tool_calls` | 检查是否没有工具调用 | 无 |
| `has_tool_results` | 检查是否有工具执行结果 | 无 |
| `max_iterations_reached` | 检查是否达到最大迭代次数 | 无 |
| `has_errors` | 检查是否有错误 | 无 |
| `no_errors` | 检查是否没有错误 | 无 |
| `message_contains` | 检查消息是否包含指定内容 | `text` (必需), `case_sensitive` (可选) |
| `iteration_count_equals` | 检查迭代次数是否等于指定值 | `count` (必需) |
| `iteration_count_greater_than` | 检查迭代次数是否大于指定值 | `count` (必需) |
| `custom` | 执行自定义条件代码 | `custom_condition_code` (必需) |

### 4. 扩展能力

#### 4.1 自定义条件函数注册
```python
def register_condition_function(self, name: str, func: Callable) -> None:
    """注册自定义条件函数
    
    Args:
        name: 条件函数名称
        func: 条件函数，签名为 (state, parameters, config) -> bool
    """
```

#### 4.2 自定义条件代码执行
- 支持通过配置传入自定义Python代码
- 提供安全的执行环境，限制可用的内置函数
- 错误处理机制，执行失败时返回False而不中断流程

### 5. 配置Schema

提供了完整的JSON Schema配置验证，包括：
- 条件列表配置
- 默认节点配置
- 自定义条件代码配置

## 扩展建议

### 1. 短期扩展（高优先级）

#### 1.1 增强条件类型
- **时间相关条件**:
  - `time_elapsed`: 检查工作流执行时间
  - `time_of_day`: 根据当前时间判断
  - `deadline_reached`: 检查是否到达截止时间

- **状态相关条件**:
  - `state_value_equals`: 检查状态字段值
  - `state_value_in_range`: 检查状态字段值范围
  - `state_field_exists`: 检查状态字段是否存在

- **消息相关条件**:
  - `message_count_equals`: 检查消息数量
  - `last_message_from`: 检查最后一条消息的发送者
  - `message_pattern_match`: 使用正则表达式匹配消息内容

#### 1.2 条件组合逻辑
- **AND条件组合**: 支持多个条件同时满足
- **OR条件组合**: 支持任一条件满足
- **NOT条件**: 支持条件取反
- **嵌套条件**: 支持条件组合的嵌套

#### 1.3 性能优化
- **条件缓存**: 缓存条件评估结果
- **短路评估**: 优化AND/OR条件的评估顺序
- **并行评估**: 对独立条件进行并行评估

### 2. 中期扩展（中优先级）

#### 2.1 高级条件功能
- **条件模板**: 预定义常用条件组合
- **条件继承**: 支持条件配置的继承和覆盖
- **条件版本管理**: 支持条件配置的版本控制

#### 2.2 集成增强
- **外部条件源**: 支持从外部API获取条件判断结果
- **机器学习条件**: 集成ML模型进行智能条件判断
- **规则引擎集成**: 集成规则引擎进行复杂条件判断

#### 2.3 调试和监控
- **条件执行日志**: 详细记录条件评估过程
- **条件性能监控**: 监控条件执行性能
- **条件测试工具**: 提供条件测试和验证工具

### 3. 长期扩展（低优先级）

#### 3.1 可视化支持
- **条件图形化编辑**: 提供可视化条件编辑器
- **条件流程图**: 生成条件判断流程图
- **条件依赖分析**: 分析条件之间的依赖关系

#### 3.2 高级特性
- **条件学习**: 从历史执行数据中学习优化条件
- **条件自适应**: 根据执行情况自动调整条件
- **条件预测**: 预测条件可能的执行结果

## 实现示例

### 1. 添加新的内置条件

```python
def _time_elapsed(self, state: AgentState, parameters: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """检查工作流执行时间是否超过指定值"""
    if "max_seconds" not in parameters:
        return False
    
    if not hasattr(state, 'start_time'):
        return False
    
    import time
    elapsed = time.time() - state.start_time
    max_seconds = parameters["max_seconds"]
    return elapsed > max_seconds

# 在__init__方法中注册
self._condition_functions["time_elapsed"] = self._time_elapsed
```

### 2. 条件组合配置示例

```yaml
conditions:
  - type: "and"
    next_node: "process_data"
    parameters:
      conditions:
        - type: "has_tool_results"
        - type: "no_errors"
        - type: "iteration_count_greater_than"
          parameters:
            count: 2
```

### 3. 自定义条件代码示例

```yaml
conditions:
  - type: "custom"
    next_node: "special_handler"
    parameters:
      custom_condition_code: |
        # 检查是否有特定类型的工具调用
        for result in state.tool_results:
            if result.tool_name == "data_analyzer" and result.success:
                return True
        return False
```

## 最佳实践

### 1. 条件设计原则
- **单一职责**: 每个条件只负责一个明确的判断逻辑
- **可测试性**: 条件函数应该易于单元测试
- **性能考虑**: 避免在条件中进行耗时操作
- **错误处理**: 条件函数应该有适当的错误处理机制

### 2. 配置最佳实践
- **明确性**: 条件配置应该清晰易懂
- **默认值**: 为可选参数提供合理的默认值
- **文档化**: 为自定义条件提供详细文档
- **验证**: 使用配置Schema验证条件配置

### 3. 扩展最佳实践
- **向后兼容**: 新增功能不应破坏现有配置
- **渐进增强**: 通过插件方式逐步增强功能
- **测试覆盖**: 为新功能提供充分的测试覆盖
- **性能监控**: 监控扩展功能的性能影响

## 总结

`ConditionNode` 作为工作流条件判断的核心组件，已经提供了丰富的基础功能和良好的扩展能力。通过建议的扩展方案，可以进一步增强其功能，满足更复杂的业务需求。在扩展过程中，应该遵循最佳实践，确保代码质量和系统稳定性。