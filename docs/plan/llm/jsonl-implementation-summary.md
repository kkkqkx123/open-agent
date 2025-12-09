# LLM节点工具调用配置选项实现总结（简化版本）

## 概述

本文档总结了LLM节点工具调用配置选项的简化实现工作，根据用户反馈，大幅简化了配置逻辑，只保留最核心的功能。

## 简化后的配置结构

### 1. 极简配置结构
```yaml
llm_node:
  # 工具配置
  tools:
    enabled: false  # 是否启用工具
    available_tools: []  # 可用工具列表
```

### 2. 自动策略选择
- **Function Calling优先**：如果LLM API支持function calling，自动使用标准方法
- **JSONL回退**：如果不支持function calling，自动使用JSONL格式
- **移除structured_output和json格式**：简化为只支持两种格式

#### 实现位置
- **配置Schema**: [`src/core/workflow/graph/nodes/llm_node.py`](src/core/workflow/graph/nodes/llm_node.py:572-631)
- **配置处理逻辑**: [`src/core/workflow/graph/nodes/llm_node.py`](src/core/workflow/graph/nodes/llm_node.py:111-192)
- **默认配置**: [`configs/nodes/_group.yaml`](configs/nodes/_group.yaml:69-85)

#### 核心方法
1. `_process_tool_calling_config()`: 处理工具调用配置，设置默认值
2. `_determine_tool_calling_strategy()`: 确定工具调用策略
3. `_should_enable_tools()`: 判断是否应该启用工具
4. 集成到`execute_async()`方法中，在执行时应用配置

### 2. 工具格式化器简化

#### 简化内容
1. **移除StructuredOutputFormatter**: 不再需要结构化输出格式
2. **移除JSON格式**: 只保留function_calling和jsonl两种格式
3. **简化ToolFormatter**: 减少策略选择逻辑，只支持两种格式
4. **保留JSONL批量解析**: 维持真正的JSONL解析能力

#### 实现位置
- **简化后的格式化器**: [`src/infrastructure/tools/formatters/formatter.py`](src/infrastructure/tools/formatters/formatter.py:298-496)
- **JSONL格式化器**: [`src/infrastructure/tools/formatters/formatter.py`](src/infrastructure/tools/formatters/formatter.py:498-645)

## Function Calling vs JSONL 对比

### 1. 格式差异

#### Function Calling
- 原生API支持，无需特殊格式化
- 通过LLM的function calling参数传递工具定义
- 响应通过additional_kwargs中的tool_calls返回

#### JSONL (JSON Lines)
```json
{"name": "tool_1", "parameters": {"param_1": "value1"}}
{"name": "tool_2", "parameters": {"param_2": "value2"}}
```

### 2. 提示词差异

#### Function Calling
- 无需特殊提示词，LLM原生支持
- 工具定义通过API参数传递

#### JSONL提示词
```
请按以下JSONL格式调用工具（每行一个JSON对象）：
{"name": "工具名称", "parameters": {"参数1": "值1", "参数2": "值2"}}

可用工具：
- tool_1: 测试工具1
- tool_2: 测试工具2

请只返回JSONL格式的工具调用，每行一个JSON对象，不要包含其他文本。
```

### 3. 解析能力差异

| 特性 | Function Calling | JSONL |
|------|------------------|-------|
| 单工具调用 | ✅ | ✅ |
| 批量工具调用 | ✅ | ✅ |
| 流式处理 | ✅ | ✅ |
| 错误恢复 | 部分 | ✅ (跳过错误行) |
| 工具Schema | ✅ | ✅ |
| 原生支持 | ✅ | ❌ |

### 4. 使用场景

#### Function Calling适用场景
- LLM API原生支持function calling
- 需要最高可靠性和性能
- 复杂的工具定义和参数验证

#### JSONL适用场景
- LLM不支持function calling
- 需要批量工具调用
- 需要错误恢复能力
- 通用兼容性要求

## 自动策略选择机制

### 策略选择逻辑
```python
def _determine_tools_strategy(llm_client):
    # 如果LLM支持function calling，优先使用
    if llm_client.supports_function_calling():
        return "function_calling"
    # 否则使用JSONL
    else:
        return "jsonl"
```

### 优势
- **零配置**: 用户无需了解底层策略差异
- **自动优化**: 根据LLM能力自动选择最佳策略
- **简化维护**: 减少配置选项和复杂度

## 测试覆盖

### 1. LLM节点配置测试
- 配置处理逻辑测试
- 默认值验证
- 策略选择测试
- 工具启用判断测试

### 2. 格式化器差异测试
- JSONL vs Structured Output格式对比
- 批量解析能力测试
- 错误处理测试
- 向后兼容性测试

### 测试文件
- [`tests/test_llm_node_tool_calling_config.py`](tests/test_llm_node_tool_calling_config.py)
- [`tests/test_jsonl_vs_structured_output.py`](tests/test_jsonl_vs_structured_output.py)

## 使用示例

### 1. 启用工具调用
```yaml
nodes:
  analysis_node:
    type: llm_node
    config:
      tools:
        enabled: true
        available_tools: ["search_tool", "calculator", "weather_tool"]
```

### 2. 禁用工具调用
```yaml
nodes:
  simple_chat:
    type: llm_node
    config:
      tools:
        enabled: false
```

### 3. 自动策略选择
- 如果LLM支持function calling，自动使用Function Calling
- 如果LLM不支持function calling，自动使用JSONL
- 用户无需手动指定策略

## 总结

通过这次实现，我们：

1. **完整实现了文档要求的配置选项**，包括tool_calling和tools配置
2. **修复了JSONL格式化器**，使其真正支持批量工具调用
3. **明确了JSONL和Structured Output的差异**，提供了清晰的使用指导
4. **建立了配置优先级机制**，确保灵活性和向后兼容性
5. **提供了完整的测试覆盖**，确保功能的可靠性

这些改进使得LLM节点能够更灵活地处理不同能力的LLM模型，同时为用户提供了细粒度的工具调用控制能力。