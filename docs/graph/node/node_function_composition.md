# 节点内部函数配置化方案

## 概述

节点内部函数配置化方案允许通过配置文件定义节点内部的函数组合，从而实现节点功能的灵活组装和复用。该方案提供了以下核心功能：

1. **配置驱动的函数定义**：通过YAML配置文件定义节点内部函数
2. **函数组合管理**：支持将多个函数组合成一个节点的内部处理逻辑
3. **执行顺序控制**：可配置函数的执行顺序和依赖关系
4. **输入输出映射**：支持函数间的数据传递和映射

## 架构设计

### 核心组件

#### 1. 节点函数配置 (NodeFunctionConfig)
定义单个节点内部函数的配置信息：
- `name`: 函数名称
- `description`: 函数描述
- `function_type`: 函数类型（llm, tool, analysis, condition等）
- `parameters`: 函数参数
- `implementation`: 实现方式（builtin, config, custom）
- `dependencies`: 依赖的其他函数
- `return_schema`: 返回值结构定义
- `input_schema`: 输入参数结构定义

#### 2. 节点组合配置 (NodeCompositionConfig)
定义节点内部函数的组合配置：
- `name`: 组合名称
- `description`: 组合描述
- `functions`: 节点内部的函数列表
- `execution_order`: 函数执行顺序
- `input_mapping`: 输入映射
- `output_mapping`: 输出映射
- `error_handling`: 错误处理配置

#### 3. 节点函数注册表 (NodeFunctionRegistry)
管理所有注册的节点函数和组合配置：
- 函数注册和查找
- 组合配置管理
- 按类型分类管理

#### 4. 节点函数加载器 (NodeFunctionLoader)
从配置文件加载节点函数和组合配置：
- 配置文件解析
- 函数实例化
- 注册到注册表

#### 5. 节点函数管理器 (NodeFunctionManager)
提供统一的节点函数管理接口：
- 配置加载
- 函数注册
- 组合执行

#### 6. 节点函数执行器 (NodeFunctionExecutor)
执行节点函数和组合：
- 单个函数执行
- 组合执行
- 错误处理

## 配置文件结构

### 节点函数配置文件

```yaml
# 内置节点函数配置示例
name: "内置节点函数"
description: "系统内置的节点函数"
category: "builtin"

node_functions:
  llm_processor:
    description: "LLM处理函数"
    function_type: "llm"
    parameters:
      model: "gpt-4"
      temperature: 0.7
    implementation: "builtin"
    metadata:
      author: "system"
      version: "1.0"
      tags: ["llm", "processor"]
    dependencies: []
    return_schema:
      type: "object"
      properties:
        response: {type: "string"}
    input_schema:
      type: "object"
      properties:
        prompt: {type: "string"}
```

### 节点组合配置文件

```yaml
# Agent节点内部函数组合配置示例
name: "agent_processor"
description: "Agent处理节点的内部函数组合"

functions:
  - name: "input_validator"
    description: "输入验证函数"
    function_type: "validator"
    parameters:
      validation_rules:
        required_fields: ["input"]
    implementation: "config"
    dependencies: []
    # ... 其他配置

  - name: "llm_processor"
    description: "LLM处理函数"
    function_type: "llm"
    parameters:
      model: "gpt-4"
    implementation: "config"
    dependencies: ["input_validator"]
    # ... 其他配置

execution_order: ["input_validator", "llm_processor"]
input_mapping:
  "input": "input_validator.input"
output_mapping:
  "response": "llm_processor.response"
```

## 使用示例

### 1. 在工作流配置中使用节点组合

```yaml
# 工作流配置示例
nodes:
  agent_processor:
    function: "agent_processor"  # 使用节点内部函数组合
    composition_name: "agent_processor"  # 指定组合名称
    description: "Agent处理节点"
    config:
      model: "gpt-4"
```

### 2. 在代码中使用节点函数管理器

```python
from src.infrastructure.graph.node_functions import get_node_function_manager

# 获取节点函数管理器
manager = get_node_function_manager("configs")

# 执行节点组合
result = manager.execute_composition("agent_processor", state)
```

## 实现细节

### 1. 函数类型支持

系统支持多种函数类型：
- `llm`: 大语言模型处理函数
- `tool`: 工具执行函数
- `analysis`: 分析函数
- `condition`: 条件判断函数
- `validator`: 验证函数
- `transformer`: 数据转换函数
- `custom`: 自定义函数

### 2. 实现方式

函数可以通过三种方式实现：
- `builtin`: 使用系统内置实现
- `config`: 基于配置生成实现
- `custom.module.path`: 从自定义模块加载实现

### 3. 依赖管理

函数可以声明依赖关系，系统会确保依赖的函数在当前函数之前执行。

### 4. 错误处理

支持配置化的错误处理策略：
- 重试机制
- 错误状态返回
- 自定义错误处理函数

## 优势

1. **灵活性**：通过配置文件即可定义复杂的节点内部逻辑
2. **复用性**：函数和组合可以跨工作流复用
3. **可维护性**：配置与代码分离，便于维护和更新
4. **可扩展性**：支持自定义函数类型和实现方式
5. **类型安全**：提供输入输出结构定义和验证

## 最佳实践

1. **合理划分函数粒度**：函数应该具有单一职责
2. **明确依赖关系**：正确声明函数间的依赖关系
3. **定义清晰的接口**：为函数定义明确的输入输出结构
4. **使用组合而非继承**：通过组合函数来构建复杂逻辑
5. **配置版本管理**：对配置文件进行版本控制