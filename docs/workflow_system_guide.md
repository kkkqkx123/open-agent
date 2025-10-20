# YAML配置化工作流系统使用指南

## 概述

本系统基于LangGraph实现了一个YAML配置化的工作流系统，支持ReAct、Plan-and-Execute等工作流模式。通过YAML配置文件可以灵活定义工作流的结构、节点和边，无需编写代码即可创建复杂的工作流。

## 核心特性

- **YAML配置驱动**: 通过YAML文件定义工作流，支持热重载
- **预定义节点类型**: 提供分析节点、工具节点、LLM节点、条件节点等常用节点
- **灵活的条件路由**: 支持基于状态的条件判断和分支
- **可扩展架构**: 支持自定义节点类型和条件函数
- **LangGraph集成**: 原生支持LangGraph的可视化和调试功能
- **完整的测试覆盖**: 提供单元测试和集成测试

## 系统架构

```
src/workflow/
├── __init__.py              # 模块入口
├── manager.py               # 工作流管理器
├── config.py                # 配置模型定义
├── registry.py              # 节点注册系统
├── builder.py               # 工作流构建器
├── nodes/                   # 预定义节点
│   ├── analysis_node.py     # 分析节点
│   ├── tool_node.py         # 工具执行节点
│   ├── llm_node.py          # LLM调用节点
│   └── condition_node.py    # 条件判断节点
└── edges/                   # 边定义
    ├── simple_edge.py       # 简单边
    └── conditional_edge.py  # 条件边
```

## 快速开始

### 1. 基本使用

```python
from workflow.manager import WorkflowManager

# 创建工作流管理器
manager = WorkflowManager()

# 加载工作流配置
workflow_id = manager.load_workflow("configs/workflows/react.yaml")

# 创建初始状态
from prompts.agent_state import AgentState, HumanMessage
initial_state = AgentState()
initial_state.add_message(HumanMessage(content="查询今天的天气"))

# 运行工作流
result = manager.run_workflow(workflow_id, initial_state)
```

### 2. YAML配置示例

```yaml
name: react_workflow
description: ReAct工作流模式
version: 1.0

state_schema:
  messages: List[BaseMessage]
  tool_calls: List[ToolCall]
  tool_results: List[ToolResult]
  iteration_count: int
  max_iterations: int

nodes:
  analyze:
    type: analysis_node
    config:
      llm_client: openai-gpt4
      system_prompt: "分析用户输入并决定是否需要调用工具"
      max_tokens: 2000

  execute_tool:
    type: tool_node
    config:
      tool_manager: default
      timeout: 30

  final_answer:
    type: llm_node
    config:
      llm_client: openai-gpt4
      system_prompt: "基于工具结果提供最终答案"

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

## 节点类型详解

### 1. 分析节点 (analysis_node)

负责分析用户输入和上下文，判断是否需要调用工具。

**配置参数**:
- `llm_client`: LLM客户端配置名称（必需）
- `system_prompt`: 系统提示词
- `max_tokens`: 最大生成token数（默认2000）
- `temperature`: 生成温度（默认0.7）
- `tool_threshold`: 工具调用阈值（默认0.5）

### 2. 工具节点 (tool_node)

负责执行工具调用并处理结果。

**配置参数**:
- `tool_manager`: 工具管理器配置名称（必需）
- `timeout`: 工具执行超时时间（默认30秒）
- `max_parallel_calls`: 最大并行调用数（默认1）
- `retry_on_failure`: 失败时是否重试（默认false）
- `continue_on_error`: 遇到错误时是否继续执行（默认true）

### 3. LLM节点 (llm_node)

负责调用LLM生成最终答案或执行其他LLM相关任务。

**配置参数**:
- `llm_client`: LLM客户端配置名称（必需）
- `system_prompt`: 系统提示词
- `max_tokens`: 最大生成token数（默认2000）
- `temperature`: 生成温度（默认0.7）
- `include_tool_results`: 是否在提示词中包含工具执行结果（默认true）

### 4. 条件节点 (condition_node)

负责根据状态信息进行条件判断，决定工作流的分支走向。

**配置参数**:
- `conditions`: 条件列表
- `default_next_node`: 默认下一个节点
- `custom_condition_code`: 自定义条件代码

## 条件类型

系统支持以下内置条件类型：

- `has_tool_calls`: 检查是否有工具调用
- `no_tool_calls`: 检查是否没有工具调用
- `has_tool_results`: 检查是否有工具执行结果
- `max_iterations_reached`: 检查是否达到最大迭代次数
- `has_errors`: 检查是否有错误
- `no_errors`: 检查是否没有错误
- `message_contains`: 检查消息是否包含指定内容
- `iteration_count_equals`: 检查迭代次数是否等于指定值
- `iteration_count_greater_than`: 检查迭代次数是否大于指定值

## 自定义节点

### 1. 创建自定义节点

```python
from workflow.registry import BaseNode, NodeExecutionResult, register_node

@register_node("custom_node")
class CustomNode(BaseNode):
    @property
    def node_type(self) -> str:
        return "custom_node"
    
    def execute(self, state: AgentState, config: dict) -> NodeExecutionResult:
        # 实现节点逻辑
        return NodeExecutionResult(state=state)
    
    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string"}
            },
            "required": ["param1"]
        }
```

### 2. 在YAML中使用自定义节点

```yaml
nodes:
  custom_step:
    type: custom_node
    config:
      param1: "value1"
```

## 工作流模式

### 1. ReAct模式

推理-行动-观察循环，适合需要多步推理和工具调用的任务。

```yaml
name: react_workflow
description: ReAct工作流模式
# ... 配置内容
```

### 2. Plan-and-Execute模式

先生成计划，然后分步执行计划，适合复杂任务分解。

```yaml
name: plan_execute_workflow
description: Plan-and-Execute工作流模式
# ... 配置内容
```

## 高级功能

### 1. 流式执行

```python
# 流式运行工作流
for chunk in manager.stream_workflow(workflow_id, initial_state):
    print(f"中间状态: {chunk}")
```

### 2. 异步执行

```python
import asyncio

# 异步运行工作流
result = await manager.run_workflow_async(workflow_id, initial_state)
```

### 3. 工作流重载

```python
# 重新加载工作流配置
success = manager.reload_workflow(workflow_id)
```

### 4. 工作流元数据

```python
# 获取工作流元数据
metadata = manager.get_workflow_metadata(workflow_id)
print(f"使用次数: {metadata['usage_count']}")
print(f"最后使用时间: {metadata['last_used']}")
```

## 测试

运行单元测试：

```bash
pytest tests/unit/workflow/
```

运行集成测试：

```bash
pytest tests/unit/workflow/test_integration.py
```

## 演示脚本

运行演示脚本查看系统功能：

```bash
python demo_workflow_system.py
```

## 最佳实践

1. **配置组织**: 将工作流配置按功能分类存放在不同目录
2. **节点复用**: 创建通用的自定义节点，提高复用性
3. **错误处理**: 在关键节点添加错误处理逻辑
4. **性能优化**: 合理设置超时时间和并行度
5. **监控日志**: 利用工作流元数据进行性能监控

## 故障排除

### 常见问题

1. **工作流加载失败**
   - 检查YAML语法是否正确
   - 验证节点类型是否已注册
   - 确认边配置的有效性

2. **节点执行失败**
   - 检查节点配置参数
   - 验证依赖服务是否可用
   - 查看错误日志获取详细信息

3. **条件路由异常**
   - 验证条件表达式语法
   - 检查状态字段是否正确
   - 确认条件函数是否已注册

## 扩展开发

### 添加新的边类型

1. 在`src/workflow/edges/`目录下创建新的边类
2. 继承适当的基类并实现必要方法
3. 在工作流构建器中注册新的边类型

### 集成外部服务

1. 创建自定义节点封装外部服务调用
2. 在节点配置中添加服务连接参数
3. 实现适当的错误处理和重试逻辑

## 版本历史

- v1.0: 初始版本，支持基本工作流功能
- v1.1: 添加条件节点和自定义条件支持
- v1.2: 增强错误处理和监控功能
- v1.3: 添加流式执行和异步支持

## 贡献指南

欢迎贡献代码和文档！请遵循以下步骤：

1. Fork项目仓库
2. 创建功能分支
3. 编写测试用例
4. 提交Pull Request

## 许可证

本项目采用MIT许可证，详见LICENSE文件。