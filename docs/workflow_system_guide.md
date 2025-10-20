# 工作流系统使用指南

本指南介绍如何使用基于LangGraph的YAML配置化工作流系统。

## 目录

1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [工作流配置](#工作流配置)
4. [节点系统](#节点系统)
5. [边和条件](#边和条件)
6. [会话管理](#会话管理)
7. [触发器系统](#触发器系统)
8. [性能优化](#性能优化)
9. [可视化调试](#可视化调试)
10. [最佳实践](#最佳实践)

## 系统概述

工作流系统是一个基于LangGraph的YAML配置化工作流引擎，支持：

- **YAML配置化工作流定义**：通过YAML文件定义复杂工作流
- **动态节点注册**：支持自定义节点类型
- **条件边和触发器**：灵活的工作流控制
- **会话管理**：工作流状态的持久化和恢复
- **性能优化**：缓存和并行执行
- **可视化调试**：集成LangGraph Studio

## 目录结构
src/
├── workflow/                   # 工作流模块
│   ├── config.py               # 配置模型
│   ├── manager.py              # 工作流管理器
│   ├── registry.py             # 节点注册表
│   ├── builder.py              # 工作流构建器
│   ├── auto_discovery.py       # 自动发现
│   ├── visualization.py        # 可视化
│   ├── performance.py          # 性能优化
│   ├── nodes/                  # 节点实现
│   ├── edges/                  # 边实现
│   └── triggers/               # 触发器系统
├── session/                    # 会话管理
│   ├── manager.py              # 会话管理器
│   ├── store.py                # 存储后端
│   ├── event_collector.py      # 事件收集器
│   ├── player.py               # 回放器
│   └── git_manager.py          # Git管理器
└── tests/workflow/             # 测试模块
    ├── test_config.py          # 配置测试
    ├── test_builder.py         # 构建器测试
    └── test_integration.py     # 集成测试

configs/workflows/              # 工作流配置
├── react.yaml                 # ReAct工作流
├── plan_execute.yaml          # Plan-and-Execute工作流
├── human_review.yaml          # 人工审核工作流
└── collaborative.yaml          # 协作工作流

docs/                           # 文档
├── workflow_system_guide.md   # 使用指南
└── workflow_api_reference.md   # API参考

## 快速开始

### 1. 基本使用

```python
from src.workflow import WorkflowManager, WorkflowBuilder
from src.prompts.agent_state import AgentState

# 创建工作流管理器
manager = WorkflowManager()

# 加载工作流配置
workflow_id = manager.load_workflow("configs/workflows/react.yaml")

# 创建初始状态
initial_state = AgentState()
initial_state.add_message(HumanMessage(content="查询今天的天气"))

# 运行工作流
result = manager.run_workflow(workflow_id, initial_state)
print(result.messages[-1].content)
```

### 2. 流式执行

```python
# 流式运行工作流
for state in manager.stream_workflow(workflow_id, initial_state):
    print(f"当前步骤: {state.current_step}")
    print(f"消息数量: {len(state.messages)}")
```

### 3. 异步执行

```python
import asyncio

# 异步运行工作流
result = await manager.run_workflow_async(workflow_id, initial_state)
```

## 工作流配置

### 基本结构

```yaml
name: workflow_name
description: 工作流描述
version: 1.0

state_schema:
  messages: List[BaseMessage]
  tool_calls: List[ToolCall]
  tool_results: List[ToolResult]
  iteration_count: int
  max_iterations: int

nodes:
  node_name:
    type: node_type
    config:
      # 节点特定配置
    description: 节点描述

edges:
  - from: source_node
    to: target_node
    type: simple|conditional
    condition: condition_expression  # 仅条件边需要

entry_point: start_node

additional_config:
  max_iterations: 10
  timeout: 300
  enable_streaming: true
```

### 状态模式配置

```yaml
state_schema:
  messages: List[BaseMessage]
  tool_calls: List[ToolCall]
  tool_results: List[ToolResult]
  iteration_count: int
  max_iterations: int
  # 自定义字段
  custom_field: str
  user_data: Dict[str, Any]
```

### 节点配置

#### 分析节点 (analysis_node)

```yaml
analyze:
  type: analysis_node
  config:
    llm_client: openai-gpt4
    system_prompt: |
      你是一个智能助手，负责分析用户输入。
    max_tokens: 2000
    temperature: 0.7
    tool_threshold: 0.5
    available_tools: [weather_tool, calculator]
```

#### 工具节点 (tool_node)

```yaml
execute_tool:
  type: tool_node
  config:
    tool_manager: default
    timeout: 30
    max_parallel_calls: 1
    retry_on_failure: false
    continue_on_error: true
```

#### LLM节点 (llm_node)

```yaml
final_answer:
  type: llm_node
  config:
    llm_client: openai-gpt4
    system_prompt: |
      请根据上下文提供准确的回答。
    max_tokens: 2000
    temperature: 0.3
    include_tool_results: true
```

#### 条件节点 (condition_node)

```yaml
check_condition:
  type: condition_node
  config:
    conditions:
      - type: has_tool_calls
        next_node: execute_tool
      - type: max_iterations_reached
        next_node: end_workflow
    default_next_node: analyze
```

### 边配置

#### 简单边

```yaml
edges:
  - from: start
    to: analyze
    type: simple
    description: 开始分析
```

#### 条件边

```yaml
edges:
  - from: analyze
    to: execute_tool
    condition: has_tool_calls
    type: conditional
    description: 有工具调用时执行工具
```

### 内置条件

- `has_tool_calls` / `no_tool_calls`：检查是否有工具调用
- `has_tool_results`：检查是否有工具执行结果
- `max_iterations_reached`：检查是否达到最大迭代次数
- `has_errors` / `no_errors`：检查是否有错误
- `message_contains:text`：检查消息是否包含指定文本
- `iteration_count_equals:n`：检查迭代次数是否等于n
- `iteration_count_greater_than:n`：检查迭代次数是否大于n

## 节点系统

### 内置节点类型

1. **analysis_node**：分析用户输入，判断是否需要调用工具
2. **tool_node**：执行工具调用
3. **llm_node**：调用LLM生成响应
4. **condition_node**：根据条件决定工作流走向

### 自定义节点

```python
from src.workflow.registry import BaseNode, NodeExecutionResult, register_node

@register_node("custom_node")
class CustomNode(BaseNode):
    @property
    def node_type(self) -> str:
        return "custom_node"
    
    def execute(self, state: AgentState, config: dict) -> NodeExecutionResult:
        # 实现节点逻辑
        return NodeExecutionResult(
            state=state,
            next_node="next_node",
            metadata={"custom": True}
        )
    
    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "custom_param": {"type": "string"}
            },
            "required": ["custom_param"]
        }
```

### 节点配置验证

```python
# 验证节点配置
node = get_node("analysis_node")
errors = node.validate_config({
    "llm_client": "openai-gpt4",
    "max_tokens": 2000
})

if errors:
    print(f"配置错误: {errors}")
```

## 边和条件

### 条件表达式

条件表达式支持以下格式：

1. **内置条件**：`has_tool_calls`
2. **带参数的条件**：`message_contains:hello`
3. **自定义表达式**：`len(state.messages) > 5`

### 自定义条件函数

```python
from src.workflow.builder import WorkflowBuilder

builder = WorkflowBuilder()

def custom_condition(state: AgentState) -> bool:
    return len(state.tool_results) >= 3

builder.register_condition_function("enough_results", custom_condition)
```

## 会话管理

### 创建会话

```python
from src.session import SessionManager, FileSessionStore

# 创建会话管理器
session_store = FileSessionStore(Path("./sessions"))
session_manager = SessionManager(
    workflow_manager=manager,
    session_store=session_store
)

# 创建会话
session_id = session_manager.create_session(
    workflow_config_path="configs/workflows/react.yaml",
    agent_config={"model": "gpt-4"}
)
```

### 恢复会话

```python
# 恢复会话
workflow, state = session_manager.restore_session(session_id)

# 继续执行
result = workflow.invoke(state)
```

### 保存会话

```python
# 保存会话状态
session_manager.save_session(session_id, workflow, state)
```

### 会话历史

```python
# 获取会话历史
history = session_manager.get_session_history(session_id)
for event in history:
    print(f"{event['timestamp']}: {event['message']}")
```

## 触发器系统

### 内置触发器

#### 时间触发器

```python
from src.workflow.triggers import TimeTrigger

# 每小时触发一次
trigger = TimeTrigger(
    trigger_id="hourly_trigger",
    trigger_time="3600"  # 秒数
)
```

#### 状态触发器

```python
from src.workflow.triggers import StateTrigger

# 当迭代次数达到10时触发
trigger = StateTrigger(
    trigger_id="iteration_trigger",
    condition="state.iteration_count >= 10"
)
```

#### 事件触发器

```python
from src.workflow.triggers import EventTrigger

# 当发生错误时触发
trigger = EventTrigger(
    trigger_id="error_trigger",
    event_type="error",
    event_pattern="critical"  # 可选的正则表达式
)
```

### 自定义触发器

```python
from src.workflow.triggers import CustomTrigger

def evaluate_func(state: AgentState, context: dict) -> bool:
    return len(context.get("events", [])) > 5

def execute_func(state: AgentState, context: dict) -> dict:
    return {"message": "自定义触发器执行", "timestamp": datetime.now()}

trigger = CustomTrigger(
    trigger_id="custom_trigger",
    evaluate_func=evaluate_func,
    execute_func=execute_func
)
```

### 触发器系统使用

```python
from src.workflow.triggers import TriggerSystem

# 创建触发器系统
trigger_system = TriggerSystem()

# 注册触发器
trigger_system.register_trigger(trigger)

# 启动系统
trigger_system.start()

# 评估触发器
events = trigger_system.evaluate_triggers(state, context)

# 停止系统
trigger_system.stop()
```

## 性能优化

### 配置缓存

```python
from src.workflow.performance import get_global_optimizer

optimizer = get_global_optimizer()

# 配置加载会自动缓存
config = optimizer.optimize_config_loading("configs/workflows/react.yaml")
```

### 并行节点执行

```python
from src.workflow.performance import ParallelExecutor

executor = ParallelExecutor(max_workers=4)

# 定义并行任务
tasks = [
    lambda: node1.execute(state, config1),
    lambda: node2.execute(state, config2),
    lambda: node3.execute(state, config3)
]

# 并行执行
results = executor.execute_parallel(tasks)
```

### 性能监控

```python
from src.workflow.performance import PerformanceMonitor

monitor = PerformanceMonitor()

# 开始性能测量
metric = monitor.start_measurement("workflow_execution")

# 执行工作流
result = workflow.invoke(state)

# 结束测量
metric.finish(success=True)

# 获取统计信息
stats = monitor.get_statistics("workflow_execution")
print(f"平均执行时间: {stats['avg_duration_ms']:.2f}ms")
```

## 可视化调试

### LangGraph Studio集成

```python
from src.workflow.visualization import create_visualizer

# 创建可视化器
visualizer = create_visualizer()

# 可视化工作流
url = visualizer.visualize_workflow(workflow_config)
print(f"Studio URL: {url}")

# 启动Studio
visualizer.start_studio(port=8079)

# 获取Studio URL
studio_url = visualizer.get_studio_url()
print(f"访问 {studio_url} 查看工作流")
```

### 导出工作流图

```python
# 导出为PNG图像
visualizer.export_graph_image(
    workflow_config,
    Path("workflow.png"),
    format="png"
)

# 导出为SVG
visualizer.export_graph_image(
    workflow_config,
    Path("workflow.svg"),
    format="svg"
)
```

## 最佳实践

### 1. 工作流设计

- **保持简单**：避免过度复杂的工作流结构
- **明确职责**：每个节点应该有明确的单一职责
- **合理分支**：避免过多的条件分支
- **错误处理**：为关键节点添加错误处理路径

### 2. 配置管理

- **版本控制**：为工作流配置添加版本号
- **环境分离**：为不同环境使用不同的配置
- **参数化**：使用环境变量和参数化配置
- **文档化**：为复杂工作流添加详细描述

### 3. 性能优化

- **缓存配置**：利用配置缓存减少加载时间
- **并行执行**：对独立节点使用并行执行
- **资源限制**：设置合理的超时和迭代限制
- **监控性能**：定期检查性能指标

### 4. 错误处理

- **优雅降级**：设计备用路径处理错误情况
- **详细日志**：记录关键步骤和错误信息
- **重试机制**：为临时性错误添加重试逻辑
- **用户反馈**：为关键错误提供用户友好的反馈

### 5. 测试策略

- **单元测试**：为每个节点编写单元测试
- **集成测试**：测试完整的工作流执行
- **边界测试**：测试边界条件和异常情况
- **性能测试**：验证工作流在负载下的表现

## 示例工作流

### ReAct工作流

```yaml
name: react_workflow
description: ReAct工作流模式，支持推理-行动-观察循环
version: 1.0

nodes:
  analyze:
    type: analysis_node
    config:
      llm_client: openai-gpt4
      system_prompt: |
        你是一个智能助手，负责分析用户输入并决定是否需要调用工具。
      max_tokens: 2000
      temperature: 0.7

  execute_tool:
    type: tool_node
    config:
      tool_manager: default
      timeout: 30

  final_answer:
    type: llm_node
    config:
      llm_client: openai-gpt4
      system_prompt: |
        请根据工具执行结果提供准确的回答。
      max_tokens: 2000
      temperature: 0.3

edges:
  - from: start
    to: analyze
    type: simple
    
  - from: analyze
    to: execute_tool
    condition: has_tool_calls
    type: conditional
    
  - from: analyze
    to: final_answer
    condition: no_tool_calls
    type: conditional
    
  - from: execute_tool
    to: analyze
    type: simple

entry_point: analyze
```

### 人工审核工作流

```yaml
name: human_review_workflow
description: 人工审核工作流模式，在关键节点插入人工审核步骤
version: 1.0

nodes:
  analyze:
    type: analysis_node
    config:
      llm_client: openai-gpt4
      system_prompt: |
        分析用户输入，判断是否需要人工审核。

  check_review_needed:
    type: condition_node
    config:
      conditions:
        - type: custom
          parameters:
            expression: "state.requires_human_review"
          next_node: human_review
        - type: has_tool_calls
          next_node: execute_tool
      default_next_node: final_answer

  human_review:
    type: llm_node
    config:
      llm_client: openai-gpt4
      system_prompt: |
        等待人工审核员提供反馈。

  process_review_result:
    type: condition_node
    config:
      conditions:
        - type: custom
          parameters:
            expression: "state.human_review_result == 'approved'"
          next_node: final_answer
        - type: custom
          parameters:
            expression: "state.human_review_result == 'rejected'"
          next_node: analyze
      default_next_node: human_review

  execute_tool:
    type: tool_node
    config:
      tool_manager: default
      timeout: 30

  final_answer:
    type: llm_node
    config:
      llm_client: openai-gpt4
      system_prompt: |
        根据审核结果提供最终回答。

edges:
  - from: start
    to: analyze
    type: simple
    
  - from: analyze
    to: check_review_needed
    type: simple
    
  - from: check_review_needed
    to: human_review
    type: conditional
    
  - from: check_review_needed
    to: execute_tool
    type: conditional
    
  - from: check_review_needed
    to: final_answer
    type: conditional
    
  - from: human_review
    to: process_review_result
    type: simple
    
  - from: execute_tool
    to: check_review_needed
    type: simple
    
  - from: process_review_result
    to: analyze
    type: conditional
    
  - from: process_review_result
    to: final_answer
    type: conditional

entry_point: analyze
```

## 故障排除

### 常见问题

1. **工作流配置验证失败**
   - 检查YAML语法是否正确
   - 确保所有必需字段都已填写
   - 验证节点和边的引用是否正确

2. **节点执行失败**
   - 检查节点配置是否符合模式要求
   - 验证LLM客户端和工具管理器是否正确配置
   - 查看错误日志获取详细信息

3. **性能问题**
   - 检查是否有无限循环
   - 优化条件表达式
   - 考虑使用并行执行

4. **会话恢复失败**
   - 检查会话文件是否存在
   - 验证会话数据格式是否正确
   - 确保工作流配置没有发生重大变更

### 调试技巧

1. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **使用可视化工具**
   ```python
   visualizer = create_visualizer()
   url = visualizer.visualize_workflow(workflow_config)
   ```

3. **检查性能指标**
   ```python
   optimizer = get_global_optimizer()
   report = optimizer.get_performance_report()
   print(report)
   ```

4. **单步调试**
   ```python
   # 逐个节点执行
   for node_name in workflow_config.nodes:
       node = get_node(workflow_config.nodes[node_name].type)
       result = node.execute(state, workflow_config.nodes[node_name].config)
       print(f"节点 {node_name} 执行完成")
   ```

## 参考资料

- [LangGraph文档](https://langchain-ai.github.io/langgraph/)
- [LangGraph Studio](https://github.com/langchain-ai/langgraph-studio)
- [YAML配置规范](https://yaml.org/spec/)
- [Python类型提示](https://docs.python.org/3/library/typing.html)

---

*更新日期：2025-10-20*