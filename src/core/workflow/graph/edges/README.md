# 边实现

本目录包含核心层的边实现，提供工作流图中节点之间的连接功能。

## 边类型

### 1. SimpleEdge（简单边）

简单边提供节点之间的直接连接，无条件判断。

**特点：**
- 无条件判断，总是可以遍历
- 支持配置合并和验证
- 提供详细的执行日志
- 支持元数据传递

**使用场景：**
- 顺序执行的工作流
- 固定的流程控制
- 简单的节点连接

**示例：**
```python
from src.core.workflow.graph.edges import SimpleEdge

# 创建简单边
edge = SimpleEdge(
    edge_id="simple_1",
    from_node="start_node",
    to_node="process_node",
    description="从开始节点到处理节点的连接"
)

# 检查是否可以遍历
can_traverse = edge.can_traverse(state)

# 获取下一个节点
next_nodes = edge.get_next_nodes(state, config)
```

### 2. ConditionalEdge（条件边）

条件边基于条件判断进行节点连接，支持多种条件类型。

**特点：**
- 支持多种内置条件类型（工具调用、错误、消息内容等）
- 支持自定义条件函数
- 提供条件评估缓存
- 支持条件组合和优先级

**内置条件类型：**
- `has_tool_calls`: 检查是否有工具调用
- `no_tool_calls`: 检查是否没有工具调用
- `has_tool_results`: 检查是否有工具结果
- `has_errors`: 检查是否有错误
- `no_errors`: 检查是否没有错误
- `message_contains`: 检查消息是否包含特定文本
- `max_iterations_reached`: 检查是否达到最大迭代次数
- `custom`: 自定义条件

**示例：**
```python
from src.core.workflow.graph.edges import ConditionalEdge

# 创建条件边
edge = ConditionalEdge(
    edge_id="conditional_1",
    from_node="llm_node",
    to_node="tool_node",
    condition_type="has_tool_calls",
    condition_parameters={},
    description="当LLM返回工具调用时，转到工具节点"
)

# 注册自定义条件
def custom_condition(state, parameters, config):
    return state.get_data("custom_flag", False)

edge.register_custom_condition("custom_flag_check", custom_condition)

# 检查是否可以遍历
can_traverse = edge.can_traverse(state)
```

### 3. FlexibleConditionalEdge（灵活条件边）

灵活条件边基于路由函数进行条件判断，支持条件逻辑与路由目标的解耦。

**特点：**
- 基于路由函数进行条件判断
- 支持路由函数参数化
- 支持路由函数注册和管理
- 提供路由函数缓存
- 支持动态路由目标

**使用场景：**
- 复杂的路由逻辑
- 需要复用的路由函数
- 动态目标节点选择

**示例：**
```python
from src.core.workflow.graph.edges import FlexibleConditionalEdge
from src.core.workflow.graph.registry import FunctionRegistry

# 创建函数注册器
function_registry = FunctionRegistry()

# 注册路由函数
def route_by_content(state):
    messages = state.get("messages", [])
    if not messages:
        return "default_node"
    
    content = messages[-1].get("content", "").lower()
    if "天气" in content:
        return "weather_node"
    elif "时间" in content:
        return "time_node"
    else:
        return "default_node"

function_registry.register_route_function("route_by_content", route_by_content)

# 创建灵活条件边
edge = FlexibleConditionalEdge(
    edge_id="flexible_1",
    from_node="input_node",
    route_function="route_by_content",
    route_parameters={},
    description="根据消息内容动态路由"
)

# 设置函数注册表
edge.set_function_registry(function_registry)

# 获取下一个节点
next_nodes = edge.get_next_nodes(state, config)
```

## 边注册器

EdgeRegistry 提供边的类型注册、实例管理和配置验证功能。

**功能：**
- 边类型注册和查询
- 边实例管理
- 配置验证
- 边类型元数据管理
- 注册器统计信息

**示例：**
```python
from src.core.workflow.graph.registry import EdgeRegistry
from src.core.workflow.graph.edges import SimpleEdge, ConditionalEdge

# 创建边注册器
edge_registry = EdgeRegistry()

# 注册边类型
edge_registry.register_edge("simple", SimpleEdge)
edge_registry.register_edge("conditional", ConditionalEdge)

# 设置边类型元数据
edge_registry.set_edge_metadata("simple", {
    "description": "简单边，无条件判断",
    "use_cases": ["顺序执行", "固定流程"]
})

# 创建边实例
edge = edge_registry.create_edge(
    "simple",
    edge_id="simple_1",
    from_node="node_a",
    to_node="node_b"
)

# 注册边实例
edge_registry.register_edge_instance(edge)

# 获取注册器统计信息
stats = edge_registry.get_registry_stats()
print(f"注册器统计: {stats}")
```

## 配置Schema

每种边类型都提供了配置Schema，用于验证配置参数：

### SimpleEdge 配置Schema
```json
{
    "type": "object",
    "properties": {
        "disabled": {
            "type": "boolean",
            "description": "是否禁用此边",
            "default": false
        },
        "dynamic_target": {
            "type": "string",
            "description": "动态目标节点ID（可选）",
            "default": ""
        },
        "timeout": {
            "type": "integer",
            "description": "遍历超时时间（秒）",
            "default": 30
        },
        "retry_count": {
            "type": "integer",
            "description": "重试次数",
            "default": 0
        }
    },
    "required": []
}
```

### ConditionalEdge 配置Schema
```json
{
    "type": "object",
    "properties": {
        "condition_type": {
            "type": "string",
            "description": "条件类型",
            "enum": ["has_tool_calls", "no_tool_calls", "has_tool_results", "has_errors", "no_errors", "message_contains", "max_iterations_reached", "custom"],
            "default": "has_tool_calls"
        },
        "condition_parameters": {
            "type": "object",
            "description": "条件参数",
            "default": {}
        },
        "disabled": {
            "type": "boolean",
            "description": "是否禁用此边",
            "default": false
        },
        "fail_on_error": {
            "type": "boolean",
            "description": "条件评估失败时是否返回False",
            "default": false
        }
    },
    "required": ["condition_type"]
}
```

### FlexibleConditionalEdge 配置Schema
```json
{
    "type": "object",
    "properties": {
        "route_function": {
            "type": "string",
            "description": "路由函数名称",
            "default": ""
        },
        "route_parameters": {
            "type": "object",
            "description": "路由函数参数",
            "default": {}
        },
        "disabled": {
            "type": "boolean",
            "description": "是否禁用此边",
            "default": false
        },
        "fallback_target": {
            "type": "string",
            "description": "路由失败时的备用目标节点",
            "default": ""
        }
    },
    "required": ["route_function"]
}
```

## 最佳实践

1. **选择合适的边类型**
   - 使用 SimpleEdge 进行简单的顺序连接
   - 使用 ConditionalEdge 进行基于状态的条件判断
   - 使用 FlexibleConditionalEdge 进行复杂的路由逻辑

2. **配置验证**
   - 始终使用边注册器的配置验证功能
   - 在创建边实例前验证配置参数

3. **错误处理**
   - 为条件边设置适当的错误处理策略
   - 使用 `fail_on_error` 参数控制错误行为

4. **性能优化**
   - 启用条件评估缓存以提高性能
   - 合理设置超时时间避免长时间等待

5. **日志记录**
   - 利用边实现的详细日志功能
   - 在调试时启用调试级别日志

## 示例代码

完整的使用示例请参考 `examples.py` 文件。