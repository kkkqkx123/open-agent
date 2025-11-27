# 状态机子工作流模板

本模板提供了基于子工作流的状态机实现，复用现有的LLM节点、工具节点和触发器机制，实现LLM-工具-LLM的循环结构。

## 概述

### 主要特性

- **功能复用**：充分利用现有的LLM节点、工具节点和触发器系统
- **架构一致性**：与项目整体基于图的工作流架构保持一致
- **循环控制**：内置循环控制机制，支持最大迭代次数和终止条件
- **状态映射**：自动处理状态机状态与工作流状态之间的映射
- **配置迁移**：提供从传统状态机配置到子工作流配置的迁移工具

### 架构优势

1. **减少代码重复**：避免重新实现工具调用和LLM交互逻辑
2. **提高维护性**：统一的配置和部署方式
3. **增强扩展性**：易于添加新的节点类型和功能
4. **改善调试**：利用现有的工作流编排和监控功能

## 核心组件

### 1. StateMachineSubWorkflowTemplate

状态机子工作流模板，负责将状态机配置转换为基于图的子工作流。

```python
from src.core.workflow.templates.state_machine import StateMachineSubWorkflowTemplate

# 创建模板实例
template = StateMachineSubWorkflowTemplate()

# 从状态机配置创建子工作流
workflow = template.create_from_state_machine_config(
    state_machine_config=state_machine_config,
    name="my_state_machine",
    description="我的状态机工作流"
)
```

### 2. StateMachineConfigAdapter

配置适配器，负责将传统状态机配置转换为子工作流配置。

```python
from src.core.workflow.templates.state_machine import StateMachineConfigAdapter

# 创建适配器
adapter = StateMachineConfigAdapter()

# 转换配置
subworkflow_config = adapter.convert_to_subworkflow_config(state_machine_config)
```

### 3. StateMachineStateMapper

状态映射器，负责在状态机状态和工作流状态之间进行转换。

```python
from src.core.workflow.templates.state_machine import StateMachineStateMapper

# 创建映射器
mapper = StateMachineStateMapper()

# 初始化工作流状态
workflow_state = mapper.initialize_workflow_state(workflow_state, state_machine_config)

# 更新当前状态
workflow_state = mapper.update_current_state(workflow_state, "new_state")
```

### 4. StateMachineSubWorkflowNode

重构后的状态机节点，使用子工作流实现。

```python
from src.core.workflow.graph.nodes.state_machine.subworkflow_node import StateMachineSubWorkflowNode

# 创建节点实例
node = StateMachineSubWorkflowNode()

# 执行节点
result = await node.execute_async(state, config)
```

### 5. StateMachineMigrationTool

配置迁移工具，帮助将现有状态机配置迁移到新格式。

```python
from src.core.workflow.templates.state_machine import StateMachineMigrationTool

# 创建迁移工具
migration_tool = StateMachineMigrationTool()

# 迁移配置文件
success = migration_tool.migrate_from_file(
    input_file="old_config.yaml",
    output_file="new_config.yaml",
    backup=True
)
```

## 使用方法

### 1. 基本使用

```python
from src.core.workflow.templates.state_machine import StateMachineSubWorkflowTemplate
from src.core.workflow.graph.nodes.state_machine.state_machine_workflow import StateMachineConfig

# 创建状态机配置
state_machine_config = StateMachineConfig(
    name="example",
    description="示例状态机",
    initial_state="start"
)

# 添加状态和转移...

# 创建子工作流
template = StateMachineSubWorkflowTemplate()
workflow = template.create_from_state_machine_config(
    state_machine_config=state_machine_config,
    name="example_workflow",
    max_iterations=10
)

# 执行工作流
result = await workflow.execute(initial_state)
```

### 2. 配置文件使用

```yaml
# example_config.yaml
config_type: state_machine_subworkflow
name: example_state_machine
description: 示例状态机
initial_state: analyze
max_iterations: 10

states:
  analyze:
    type: "process"
    description: "分析用户输入"
    config:
      system_prompt: "请分析用户输入"
    transitions:
      - target: "execute_tool"
        condition: "has_tool_call"

  execute_tool:
    type: "process"
    description: "执行工具调用"
    config:
      tools: ["search", "calculator"]
    transitions:
      - target: "analyze"

transitions:
  - from: "analyze"
    to: "execute_tool"
    condition: "has_tool_call"
  - from: "execute_tool"
    to: "analyze"
```

```python
# 加载配置文件
from src.core.workflow.templates.state_machine import StateMachineMigrationTool

migration_tool = StateMachineMigrationTool()
config_data = migration_tool._read_config_file("example_config.yaml")

# 创建工作流
template = StateMachineSubWorkflowTemplate()
workflow = template.create_workflow(
    name="example",
    description="示例工作流",
    config=config_data
)
```

### 3. 在现有工作流中使用

```python
from src.core.workflow.graph.nodes.state_machine.subworkflow_node import StateMachineSubWorkflowNode

# 创建状态机节点
state_machine_node = StateMachineSubWorkflowNode()

# 配置节点
node_config = {
    "config_file": "my_state_machine.yaml",
    "max_iterations": 10,
    "llm_client": "gpt-4",
    "tool_manager": "default"
}

# 在工作流中使用
workflow.add_step(state_machine_node)
```

## 配置迁移

### 从传统状态机迁移

```bash
# 使用迁移工具
python -m src.core.workflow.templates.state_machine.migration_tool \
    --input old_state_machine.yaml \
    --output new_subworkflow.yaml \
    --backup
```

### 验证迁移结果

```python
# 验证迁移
migration_tool = StateMachineMigrationTool()
original_config = migration_tool._read_config_file("old_config.yaml")
migrated_config = migration_tool._read_config_file("new_config.yaml")

is_valid, errors = migration_tool.validate_migration(original_config, migrated_config)
if not is_valid:
    print("迁移验证失败:", errors)
```

## 最佳实践

### 1. 状态设计

- 保持状态简单明确，每个状态只负责一个特定功能
- 使用描述性的状态名称
- 合理设计状态转移条件

### 2. 循环控制

- 设置合理的最大迭代次数，避免无限循环
- 定义明确的终止条件
- 使用错误处理机制

### 3. 性能优化

- 合理配置并行工具调用
- 使用缓存机制减少重复计算
- 监控执行性能指标

### 4. 错误处理

- 定义错误恢复策略
- 设置重试机制
- 记录详细的错误信息

## 示例

参考 [`example_config.yaml`](example_config.yaml) 文件，了解完整的配置示例。

## 故障排除

### 常见问题

1. **配置解析失败**
   - 检查YAML/JSON格式是否正确
   - 确认必需字段是否存在

2. **状态转移不工作**
   - 验证条件表达式是否正确
   - 检查状态名称是否匹配

3. **循环不终止**
   - 检查终止条件设置
   - 验证最大迭代次数

4. **工具调用失败**
   - 确认工具管理器配置
   - 检查工具名称和参数

### 调试技巧

1. 启用详细日志记录
2. 使用状态历史跟踪执行流程
3. 检查工作流执行元数据
4. 使用迁移工具验证配置

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本的状态机子工作流功能
- 提供配置迁移工具
- 包含完整的文档和示例

## 贡献

欢迎提交问题报告和功能请求。在提交代码之前，请确保：

1. 代码符合项目编码规范
2. 添加适当的测试
3. 更新相关文档
4. 通过所有现有测试

## 许可证

本项目遵循项目主许可证。