# 灵活条件边设计方案

## 概述

本文档描述了对当前条件边实现的改进方案，旨在提供更灵活、可配置的条件边系统，使条件边能够在工作流中灵活组装，实现条件逻辑与路由目标的解耦。

## 当前实现的局限性

1. **硬编码的条件类型**：条件类型在 `ConditionType` 枚举中硬编码，扩展性差
2. **条件与边紧耦合**：条件逻辑直接嵌入在边定义中，无法复用
3. **路径映射固定**：条件边的目标节点在配置中固定，无法动态调整
4. **缺乏配置驱动的路由函数**：没有统一的配置系统来定义和管理路由函数
5. **条件评估器功能有限**：`ConditionEvaluator` 只支持预定义的条件类型

## 设计目标

1. **解耦条件逻辑与路由目标**：条件边只定义路由函数，具体指向的节点在工作流中定义
2. **支持配置驱动的路由函数**：在 `configs/edges` 中定义支持的路由函数
3. **提高可扩展性**：支持动态注册新的条件类型和路由函数
4. **增强复用性**：相同的条件逻辑可以在不同的工作流中复用
5. **简化配置**：提供更直观、简洁的配置方式

## 架构设计

### 1. 核心组件

#### 1.1 路由函数注册表 (RouteFunctionRegistry)

```python
class RouteFunctionRegistry:
    """路由函数注册表，管理所有可用的路由函数"""
    
    def register_route_function(self, name: str, function: Callable, config: RouteFunctionConfig) -> None:
        """注册路由函数"""
        
    def get_route_function(self, name: str) -> Optional[Callable]:
        """获取路由函数"""
        
    def list_route_functions(self) -> List[str]:
        """列出所有可用的路由函数"""
```

#### 1.2 路由函数配置 (RouteFunctionConfig)

```python
@dataclass
class RouteFunctionConfig:
    """路由函数配置"""
    name: str
    description: str
    parameters: Dict[str, Any]  # 路由函数的参数配置
    return_values: List[str]   # 可能的返回值列表
    category: str = "general"   # 路由函数分类
```

#### 1.3 灵活条件边 (FlexibleConditionalEdge)

```python
@dataclass
class FlexibleConditionalEdge:
    """灵活条件边
    
    只定义路由函数，具体指向的节点在工作流中定义
    """
    from_node: str
    route_function: str  # 路由函数名称
    route_parameters: Dict[str, Any]  # 路由函数参数
    description: Optional[str] = None
```

### 2. 配置系统

#### 2.1 路由函数配置文件结构

```
configs/edges/
├── _group.yaml              # 路由函数组配置
├── route_functions/         # 路由函数配置目录
│   ├── _group.yaml          # 路由函数组配置
│   ├── tool_based.yaml      # 基于工具的路由函数
│   ├── state_based.yaml     # 基于状态的路由函数
│   ├── message_based.yaml   # 基于消息的路由函数
│   └── custom.yaml          # 自定义路由函数
└── edge_types/              # 边类型配置目录
    ├── _group.yaml          # 边类型组配置
    ├── conditional.yaml     # 条件边配置
    └── simple.yaml          # 简单边配置
```

#### 2.2 路由函数配置示例

```yaml
# configs/edges/route_functions/tool_based.yaml
name: "基于工具的路由函数"
description: "基于工具调用状态的路由函数集合"
category: "tool"

route_functions:
  has_tool_calls:
    description: "检查是否有工具调用"
    parameters: {}
    return_values: ["continue", "end"]
    implementation: "builtin.has_tool_calls"
    
  tool_call_count:
    description: "基于工具调用数量的路由"
    parameters:
      type: "object"
      properties:
        threshold:
          type: "integer"
          description: "阈值"
          default: 1
    return_values: ["single", "multiple", "none"]
    implementation: "builtin.tool_call_count"
```

#### 2.3 工作流中的条件边配置

```yaml
# 工作流配置示例
edges:
  - from: "agent"
    type: "conditional"
    route_function: "has_tool_calls"
    route_parameters: {}
    path_map:
      continue: "tool_executor"
      end: "__end__"
    description: "根据是否有工具调用决定路由"
```

### 3. 实现细节

#### 3.1 路由函数实现

路由函数可以是：
1. **内置函数**：系统提供的常用路由函数
2. **配置函数**：通过配置文件定义的简单路由逻辑
3. **自定义函数**：用户注册的复杂路由函数

```python
# 内置路由函数示例
def has_tool_calls(state: WorkflowState) -> str:
    """检查是否有工具调用的路由函数"""
    messages = state.get("messages", [])
    if not messages:
        return "end"
    
    last_message = messages[-1]
    if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
        return "continue"
    
    return "end"
```

#### 3.2 配置驱动的路由函数

支持通过配置文件定义简单的路由逻辑：

```yaml
# configs/edges/route_functions/config_based.yaml
route_functions:
  state_value_check:
    description: "检查状态值的路由函数"
    implementation: "config_based"
    config:
      state_key: "status"
      value_mapping:
        "success": "complete"
        "error": "error_handler"
        "pending": "continue"
      default: "continue"
```

#### 3.3 路由函数加载器

```python
class RouteFunctionLoader:
    """路由函数加载器，从配置文件加载路由函数"""
    
    def load_from_config(self, config_path: str) -> Dict[str, Callable]:
        """从配置文件加载路由函数"""
        
    def register_builtin_functions(self, registry: RouteFunctionRegistry) -> None:
        """注册内置路由函数"""
```

### 4. 工作流集成

#### 4.1 图构建器修改

```python
class GraphBuilder:
    def _add_conditional_edge(self, builder: Any, edge: FlexibleConditionalEdge) -> None:
        """添加条件边到图"""
        route_function = self.route_function_registry.get_route_function(edge.route_function)
        if route_function:
            # 创建包装函数，注入路由参数
            wrapped_function = self._wrap_route_function(route_function, edge.route_parameters)
            builder.add_conditional_edges(edge.from_node, wrapped_function, edge.path_map)
```

#### 4.2 路由函数包装

```python
def _wrap_route_function(self, route_function: Callable, parameters: Dict[str, Any]) -> Callable:
    """包装路由函数，注入参数"""
    def wrapped_function(state: WorkflowState) -> str:
        # 将参数注入到状态中
        enhanced_state = {**state, "_route_parameters": parameters}
        return route_function(enhanced_state)
    return wrapped_function
```

## 优势

1. **灵活性**：条件边只定义路由函数，具体路由目标在工作流中配置
2. **可复用性**：相同的路由函数可以在多个工作流中使用
3. **可扩展性**：支持动态注册新的路由函数
4. **配置驱动**：通过配置文件管理路由函数，无需修改代码
5. **类型安全**：路由函数的返回值和参数都有明确的类型定义

## 迁移策略

1. **向后兼容**：保留现有的条件边实现，逐步迁移
2. **渐进式改进**：先实现新的路由函数系统，再逐步替换现有实现
3. **工具支持**：提供迁移工具，自动转换现有配置

## 示例

### 基本用法

```yaml
# 定义路由函数
# configs/edges/route_functions/message_based.yaml
route_functions:
  message_content_check:
    description: "基于消息内容的路由"
    parameters:
      type: "object"
      properties:
        keywords:
          type: "array"
          items:
            type: "string"
          description: "关键词列表"
    return_values: ["matched", "not_matched"]
    implementation: "builtin.message_content_check"

# 工作流中使用
edges:
  - from: "classifier"
    type: "conditional"
    route_function: "message_content_check"
    route_parameters:
      keywords: ["error", "failed", "exception"]
    path_map:
      matched: "error_handler"
      not_matched: "normal_processor"
```

### 高级用法

```yaml
# 复杂路由函数配置
route_functions:
  multi_condition_router:
    description: "多条件路由器"
    implementation: "custom.multi_condition_router"
    parameters:
      conditions:
        - type: "state_check"
          state_key: "iteration_count"
          operator: ">"
          value: 10
          target: "max_iterations_reached"
        - type: "tool_check"
          has_tool_calls: true
          target: "tool_executor"
        - type: "message_check"
          message_contains: ["complete", "done"]
          target: "finish"
      default_target: "continue"
    return_values: ["max_iterations_reached", "tool_executor", "finish", "continue"]
```

## 总结

这个设计方案通过引入路由函数注册表和配置驱动的路由函数系统，实现了条件边与路由目标的解耦，提供了更灵活、可扩展的条件边配置方式。同时，通过配置文件管理路由函数，使得系统更加模块化和可维护。