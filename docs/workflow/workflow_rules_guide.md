# 工作流规则指南

本文档描述了在使用 Modular Agent Framework 工作流系统时需要遵守的规则和最佳实践，以避免常见问题。

## 核心概念

### 工作流组件

- **节点（Nodes）**：工作流的基本执行单元
- **边（Edges）**：连接节点，定义执行流程
- **状态（State）**：在工作流中传递的数据结构
- **条件函数（Conditions）**：控制工作流分支的逻辑

## 关键规则

### 1. 条件边配置规则

#### ❌ 错误的做法：多个独立条件边

```yaml
edges:
  - from: plan_execute_agent
    to: plan_review
    type: conditional
    condition: plan_generated
  - from: plan_execute_agent
    to: final_summary
    type: conditional
    condition: plan_completed
  - from: plan_execute_agent
    to: error_handler
    type: conditional
    condition: has_error
```

**问题**：
- LangGraph 无法正确处理多个独立的条件边
- 会导致递归限制错误
- 工作流无法正确终止

#### ✅ 正确的做法：单一条件边使用 path_map

```yaml
edges:
  - from: plan_execute_agent
    to: plan_execute_agent  # 必需字段，但实际由 path_map 决定
    type: conditional
    condition: plan_execute_router
    path_map:
      plan_review: plan_review
      final_summary: final_summary
      error_handler: error_handler
      continue: plan_execute_agent
```

**优势**：
- 统一的路由逻辑
- 清晰的条件映射
- 避免递归问题

### 2. 条件函数设计规则

#### ❌ 错误的做法：返回不存在的节点

```python
def plan_generated(state) -> str:
    if state.get("has_plan"):
        return "plan_review"
    else:
        return "continue"  # "continue" 不是有效节点名
```

#### ✅ 正确的做法：返回有效节点名

```python
def plan_execute_router(state) -> str:
    """统一的路由函数"""
    if state.get("workflow_errors"):
        return "error_handler"
    
    context = state.get("context", {})
    if not context.get("current_plan"):
        return "continue"  # 对应 path_map 中的 "continue"
    
    if context.get("needs_review"):
        return "plan_review"
    
    if context.get("plan_completed"):
        return "final_summary"
    
    return "continue"
```

### 3. 状态字段命名规则

#### ❌ 错误的做法：使用 LangGraph 内置字段名

```yaml
state_schema:
  fields:
    messages: List[dict]  # 与 LangGraph 内置字段冲突
    iteration_count: int  # 与 LangGraph 内置字段冲突
```

#### ✅ 正确的做法：使用自定义前缀

```yaml
state_schema:
  fields:
    workflow_messages: List[dict]
    workflow_iteration_count: int
    workflow_tool_calls: List[dict]
```

### 4. 工作流终止规则

#### ❌ 错误的做法：没有明确的终止路径

```python
def router_function(state) -> str:
    if some_condition:
        return "next_node"
    else:
        return "current_node"  # 可能导致无限循环
```

#### ✅ 正确的做法：确保有终止路径

```python
def router_function(state) -> str:
    if state.get("errors"):
        return "error_handler"
    elif state.get("completed"):
        return "__end__"  # 明确的终止
    elif some_condition:
        return "next_node"
    else:
        return "current_node"  # 但要有其他条件能跳出循环
```

## 常见问题及解决方案

### 1. 递归限制错误

**症状**：`Recursion limit of X reached without hitting a stop condition`

**原因**：
- 条件边配置错误
- 条件函数逻辑问题
- 缺少终止条件

**解决方案**：
- 使用单一条件边和 path_map
- 检查条件函数的返回值
- 确保有明确的终止路径

### 2. 状态字段冲突

**症状**：`Channel 'field_name' already exists with a different type`

**原因**：
- 使用了 LangGraph 内置字段名

**解决方案**：
- 使用自定义前缀（如 `workflow_`）
- 检查状态字段命名

### 3. 工作流无法启动

**症状**：`无法找到节点函数: node_name`

**原因**：
- 节点类型未注册
- 节点函数名称错误

**解决方案**：
- 检查节点类型配置
- 确保节点函数已注册

## 最佳实践

### 1. 条件函数设计

- 使用描述性的函数名
- 包含完整的错误处理
- 确保所有路径都有明确的返回值
- 添加详细的注释

### 2. 状态管理

- 使用类型注解
- 避免状态字段冲突
- 限制状态对象大小
- 定期清理不需要的数据

### 3. 工作流结构

- 保持工作流简洁
- 避免过深的嵌套
- 使用有意义的节点和边名称
- 添加描述和注释

### 4. 测试和调试

- 使用静态检测工具
- 编写单元测试
- 添加日志记录
- 使用递归限制配置

## 配置示例

### 完整的工作流配置示例

```yaml
name: example_workflow
description: 示例工作流
version: 1.0

state_schema:
  name: ExampleWorkflowState
  fields:
    workflow_messages:
      type: List[dict]
      default: []
      description: 工作流消息历史
    workflow_context:
      type: Dict[str, Any]
      default: {}
      description: 工作流上下文

nodes:
  start_node:
    type: llm_node
    config:
      llm_client: mock
      system_prompt: 开始处理
    description: 开始节点

  process_node:
    type: process_node
    config:
      max_steps: 5
    description: 处理节点

  end_node:
    type: llm_node
    config:
      llm_client: mock
      system_prompt: 处理完成
    description: 结束节点

edges:
  - from: start_node
    to: start_node
    type: conditional
    condition: workflow_router
    path_map:
      process: process_node
      end: end_node
      continue: start_node

  - from: process_node
    to: start_node
    type: simple
    description: 处理完成后返回路由

  - from: end_node
    to: __end__
    type: simple
    description: 工作流结束

entry_point: start_node

additional_config:
  recursion_limit: 10
  enable_logging: true
```

## 工具和验证

使用 `WorkflowValidator` 模块进行静态检测：

```python
from src.infrastructure.graph.workflow_validator import WorkflowValidator

validator = WorkflowValidator()
issues = validator.validate_config_file("configs/workflows/example.yaml")

for issue in issues:
    print(f"{issue.severity}: {issue.message}")
```

这样可以及早发现和修复配置问题。