# GraphWorkflow 使用指南

GraphWorkflow 是基于 LangGraph 的工作流基类，提供统一、简洁的 API 来创建、配置和执行基于图的工作流。

## 特性

- 🎯 **统一接口**: 提供一致的 API 用于同步、异步、流式执行
- 🔧 **配置驱动**: 支持 YAML、JSON、字典等多种配置格式
- 🚀 **高性能**: 基于 LangGraph 构建，支持异步和流式执行
- 🛡️ **类型安全**: 完整的类型注解和配置验证
- 📊 **可视化**: 内置工作流可视化支持
- 🔌 **可扩展**: 支持自定义节点、函数和状态模式

## 快速开始

### 1. 基本使用

```python
from src.application.workflow.graph_workflow import GraphWorkflow

# 从配置文件创建工作流
workflow = GraphWorkflow("config/workflow.yaml")

# 运行工作流
result = workflow.run({"input": "Hello World"})
print(result)
```

### 2. 使用字典配置

```python
from src.application.workflow.graph_workflow import GraphWorkflow

# 定义配置
config = {
    "name": "simple_workflow",
    "description": "简单工作流示例",
    "version": "1.0",
    "entry_point": "start_node",
    "nodes": {
        "start_node": {
            "name": "start_node",
            "function_name": "process_input",
            "description": "处理输入",
            "config": {"param1": "value1"}
        },
        "end_node": {
            "name": "end_node", 
            "function_name": "generate_output",
            "description": "生成输出"
        }
    },
    "edges": [
        {
            "from": "start_node",
            "to": "end_node",
            "type": "simple"
        }
    ],
    "state_schema": {
        "name": "WorkflowState",
        "fields": {
            "messages": {
                "type": "List[dict]",
                "default": []
            },
            "result": {
                "type": "str",
                "default": ""
            }
        }
    }
}

# 创建工作流
workflow = GraphWorkflow(config)

# 运行工作流
result = workflow.run({"messages": [{"role": "user", "content": "Hello"}]})
```

### 3. 使用 SimpleGraphWorkflow 快速创建

```python
from src.application.workflow.graph_workflow import SimpleGraphWorkflow

# 定义节点
nodes = [
    {
        "name": "input_processor",
        "function_name": "process_input",
        "description": "处理输入数据"
    },
    {
        "name": "output_generator", 
        "function_name": "generate_output",
        "description": "生成输出"
    }
]

# 定义边
edges = [
    {
        "from": "input_processor",
        "to": "output_generator",
        "type": "simple"
    }
]

# 创建工作流
workflow = SimpleGraphWorkflow(
    name="quick_workflow",
    nodes=nodes,
    edges=edges,
    description="快速创建工作流"
)

# 运行
result = workflow.run({"input": "test"})
```

## 配置详解

### 工作流配置结构

```yaml
# workflow.yaml
name: my_workflow
description: 我的工作流
version: "1.0"
entry_point: start_node

# 状态模式定义
state_schema:
  name: WorkflowState
  fields:
    messages:
      type: List[dict]
      default: []
      description: 消息列表
    context:
      type: Dict[str, Any]
      default: {}
      description: 上下文数据
    result:
      type: str
      default: ""
      description: 结果

# 节点定义
nodes:
  start_node:
    name: start_node
    function_name: process_start
    description: 开始节点
    config:
      param1: value1
      
  process_node:
    name: process_node
    function_name: process_data
    description: 处理节点
    
  end_node:
    name: end_node
    function_name: process_end
    description: 结束节点

# 边定义
edges:
  - from: start_node
    to: process_node
    type: simple
    description: 从开始到处理
    
  - from: process_node
    to: end_node
    type: conditional
    condition: should_continue
    description: 条件边
    path_map:
      true: end_node
      false: start_node

# 可选配置
interrupt_before: [process_node]  # 在这些节点前中断
interrupt_after: [start_node]     # 在这些节点后中断
checkpointer: memory              # 检查点类型: memory, sqlite
```

### 节点配置

```python
{
    "name": "node_name",           # 节点名称（唯一）
    "function_name": "func_name",  # 对应的函数名
    "description": "节点描述",     # 可选：节点描述
    "config": {                    # 可选：节点配置
        "param1": "value1",
        "param2": 123
    },
    "input_state": "InputState",   # 可选：输入状态类型
    "output_state": "OutputState"  # 可选：输出状态类型
}
```

### 边配置

```python
# 简单边
{
    "from": "node1",
    "to": "node2", 
    "type": "simple",
    "description": "边描述"  # 可选
}

# 条件边
{
    "from": "node1",
    "to": "node2",
    "type": "conditional",
    "condition": "condition_func",  # 条件函数名
    "description": "条件边",
    "path_map": {                   # 条件路径映射
        "true": "node2",
        "false": "node3"
    }
}
```

### 状态模式配置

```python
{
    "name": "MyState",      # 状态类名称
    "fields": {             # 字段定义
        "messages": {
            "type": "List[dict]",      # 字段类型
            "default": [],             # 默认值
            "reducer": "extend",        # reducer函数
            "description": "消息列表"   # 字段描述
        },
        "count": {
            "type": "int",
            "default": 0,
            "reducer": "operator.add"
        }
    }
}
```

## 执行模式

### 1. 同步执行

```python
# 基本执行
result = workflow.run(initial_data)

# 带配置的执行
result = workflow.run(
    initial_data={"messages": [{"role": "user", "content": "Hello"}]},
    config={"recursion_limit": 50}
)
```

### 2. 异步执行

```python
import asyncio

async def run_workflow():
    result = await workflow.run_async(initial_data)
    return result

# 运行异步工作流
result = asyncio.run(run_workflow())
```

### 3. 流式执行

```python
# 同步流式
for chunk in workflow.stream(initial_data):
    print(f"中间结果: {chunk}")

# 异步流式
async for chunk in workflow.stream_async(initial_data):
    print(f"中间结果: {chunk}")
```

## 高级功能

### 1. 工作流验证

```python
# 验证配置
errors = workflow.validate()
if errors:
    print(f"配置错误: {errors}")
else:
    print("配置有效")
```

### 2. 获取工作流信息

```python
# 基本信息
print(f"名称: {workflow.name}")
print(f"描述: {workflow.description}")
print(f"版本: {workflow.version}")

# 状态模式
schema = workflow.get_state_schema()
print(f"状态模式: {schema}")

# 节点和边
nodes = workflow.get_nodes()
edges = workflow.get_edges()
print(f"节点: {len(nodes)} 个")
print(f"边: {len(edges)} 条")
```

### 3. 可视化支持

```python
# 获取可视化数据
viz_data = workflow.get_visualization_data()

# 导出配置
config_data = workflow.export_config()
```

### 4. 自定义函数注册

```python
from src.infrastructure.graph.function_registry import FunctionRegistry

# 创建自定义函数注册表
function_registry = FunctionRegistry()

# 注册函数
@function_registry.register("my_custom_function")
def my_function(state):
    # 自定义逻辑
    return {"result": "custom result"}

# 使用自定义注册表创建工作流
workflow = GraphWorkflow(config, function_registry=function_registry)
```

## 错误处理

```python
from src.application.workflow.graph_workflow import (
    GraphWorkflowError,
    GraphWorkflowConfigError,
    GraphWorkflowExecutionError
)

try:
    workflow = GraphWorkflow(config)
    result = workflow.run(data)
except GraphWorkflowConfigError as e:
    print(f"配置错误: {e}")
except GraphWorkflowExecutionError as e:
    print(f"执行错误: {e}")
except GraphWorkflowError as e:
    print(f"工作流错误: {e}")
```

## 最佳实践

### 1. 配置管理

```python
# 使用配置文件
workflow = GraphWorkflow("configs/workflows/my_workflow.yaml")

# 环境特定的配置
import os
env = os.getenv("ENV", "dev")
workflow = GraphWorkflow(f"configs/workflows/{env}/workflow.yaml")
```

### 2. 函数组织

```python
# 将相关函数组织到模块中
from my_app.workflows.functions import *

# 自动注册模块中的所有函数
function_registry.register_functions_from_module("my_app.workflows.functions")
```

### 3. 状态管理

```python
# 定义清晰的状态模式
state_schema = {
    "name": "AppState",
    "fields": {
        "messages": {"type": "List[dict]", "reducer": "extend"},
        "context": {"type": "Dict[str, Any]"},
        "metadata": {"type": "Dict[str, Any]"}
    }
}
```

### 4. 性能优化

```python
# 使用异步执行提高并发性能
results = await asyncio.gather(
    workflow1.run_async(data1),
    workflow2.run_async(data2),
    workflow3.run_async(data3)
)

# 使用流式执行处理大数据
async for chunk in workflow.stream_async(large_data):
    process_chunk(chunk)
```

## 迁移指南

### 从状态机工作流迁移

```python
# 旧的状态机工作流
from old_workflow import StateMachineWorkflow

old_workflow = StateMachineWorkflow(old_config)
result = old_workflow.execute(state)

# 新的图工作流
from src.application.workflow.graph_workflow import GraphWorkflow

# 转换配置（如果需要）
new_config = convert_state_machine_to_graph_config(old_config)

# 创建新的图工作流
new_workflow = GraphWorkflow(new_config)
result = new_workflow.run(initial_data)
```

### 从 UniversalWorkflowLoader 迁移

```python
# 旧的加载器方式
from src.application.workflow.universal_loader import UniversalWorkflowLoader

loader = UniversalWorkflowLoader()
instance = loader.load_from_file("workflow.yaml")
result = instance.run(data)

# 新的图工作流方式
from src.application.workflow.graph_workflow import GraphWorkflow

workflow = GraphWorkflow("workflow.yaml")
result = workflow.run(data)
```

## 常见问题

### Q: 如何处理循环依赖？
A: 使用条件边和路径映射来处理循环逻辑：

```python
{
    "from": "node_a",
    "to": "node_b", 
    "type": "conditional",
    "condition": "should_loop",
    "path_map": {
        "true": "node_a",  # 循环回自身
        "false": "end_node"
    }
}
```

### Q: 如何调试工作流？
A: 使用流式执行和日志：

```python
import logging

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

# 使用流式执行查看中间状态
for state in workflow.stream(data):
    print(f"当前状态: {state}")
```

### Q: 如何处理大规模数据？
A: 使用异步和流式执行：

```python
# 异步处理
async def process_large_dataset(dataset):
    for chunk in dataset.chunks():
        result = await workflow.run_async(chunk)
        yield result

# 流式处理
async for result in workflow.stream_async(large_data):
    process_partial_result(result)
```

## 相关文档

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [工作流配置参考](./workflow-config-reference.md)
- [节点函数开发指南](./node-function-guide.md)
- [状态模式设计](./state-schema-design.md)
- [性能优化指南](./performance-optimization.md)